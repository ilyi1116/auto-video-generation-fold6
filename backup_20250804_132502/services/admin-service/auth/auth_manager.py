"""
認證管理器

提供統一的用戶認證、授權和管理功能。
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Tuple
import uuid

from .models import AuthStatus, AuthAttempt
from .password_manager import password_manager
from .jwt_handler import jwt_handler
from .role_manager import role_manager
from .session_manager import session_manager
from .permission_manager import permission_manager

logger = logging.getLogger(__name__)


class AuthManager:
    """認證管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 認證配置
        self.require_email_verification = self.config.get("require_email_verification", False)
        self.enable_two_factor = self.config.get("enable_two_factor", False)
        self.password_reset_token_expire_hours = self.config.get("password_reset_token_expire_hours", 24)
        
        # 認證嘗試記錄
        self.auth_attempts: List[AuthAttempt] = []
        
        # 密碼重置令牌存儲
        self.reset_tokens: Dict[str, Dict[str, Any]] = {}
        
        # 郵箱驗證令牌存儲
        self.verification_tokens: Dict[str, Dict[str, Any]] = {}
        
        logger.info("認證管理器初始化完成")
    
    def authenticate_user(self, 
                         username: str,
                         password: str,
                         ip_address: str,
                         user_agent: str) -> Tuple[AuthStatus, Optional[Dict[str, Any]]]:
        """
        用戶認證
        
        Args:
            username: 用戶名或郵箱
            password: 密碼
            ip_address: IP地址
            user_agent: 用戶代理
            
        Returns:
            (認證狀態, 認證結果)
        """
        # 記錄認證嘗試
        attempt = AuthAttempt(
            attempt_id=str(uuid.uuid4()),
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            status=AuthStatus.FAILED
        )
        
        try:
            # 檢查IP是否被鎖定
            if session_manager.is_ip_locked(ip_address):
                attempt.status = AuthStatus.LOCKED
                attempt.error_message = "IP地址已被鎖定"
                self._record_auth_attempt(attempt)
                return AuthStatus.LOCKED, {"message": "IP地址已被鎖定，請稍後重試"}
            
            # 這裡應該從數據庫獲取用戶信息
            # 為了示例，我們創建一個模擬的用戶查詢函數
            user_info = self._get_user_by_username(username)
            
            if not user_info:
                attempt.error_message = "用戶不存在"
                self._record_auth_attempt(attempt)
                session_manager.record_login_attempt(username, ip_address, False)
                return AuthStatus.FAILED, {"message": "用戶名或密碼錯誤"}
            
            # 檢查用戶是否啟用
            if not user_info.get("is_active", True):
                attempt.status = AuthStatus.DISABLED
                attempt.error_message = "用戶已被禁用"
                self._record_auth_attempt(attempt)
                return AuthStatus.DISABLED, {"message": "用戶已被禁用"}
            
            # 驗證密碼
            if not password_manager.verify_password(password, user_info["hashed_password"]):
                attempt.error_message = "密碼錯誤"
                self._record_auth_attempt(attempt)
                session_manager.record_login_attempt(username, ip_address, False)
                return AuthStatus.FAILED, {"message": "用戶名或密碼錯誤"}
            
            # 檢查密碼是否過期
            password_created_at = user_info.get("password_created_at", datetime.utcnow())
            if password_manager.is_password_expired(password_created_at):
                attempt.status = AuthStatus.EXPIRED
                attempt.error_message = "密碼已過期"
                self._record_auth_attempt(attempt)
                return AuthStatus.EXPIRED, {"message": "密碼已過期，請重置密碼"}
            
            # 檢查郵箱驗證（如果啟用）
            if self.require_email_verification and not user_info.get("email_verified", False):
                attempt.error_message = "郵箱未驗證"
                self._record_auth_attempt(attempt)
                return AuthStatus.FAILED, {"message": "請先驗證郵箱"}
            
            # 認證成功
            attempt.status = AuthStatus.SUCCESS
            self._record_auth_attempt(attempt)
            session_manager.record_login_attempt(username, ip_address, True)
            
            # 創建會話
            session = session_manager.create_session(
                user_id=user_info["id"],
                username=username,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"auth_method": "password"}
            )
            
            # 獲取用戶角色和權限
            user_roles = role_manager.get_user_roles(user_info["id"])
            user_permissions = role_manager.get_user_permissions(user_info["id"])
            
            # 創建 JWT 令牌
            access_token = jwt_handler.create_access_token(
                user_id=user_info["id"],
                username=username,
                role=user_info.get("role", "user"),
                permissions=list(user_permissions)
            )
            
            refresh_token = jwt_handler.create_refresh_token(
                user_id=user_info["id"],
                username=username,
                session_id=session.session_id
            )
            
            # 更新用戶登錄信息
            self._update_user_login_info(user_info["id"])
            
            return AuthStatus.SUCCESS, {
                "user": {
                    "id": user_info["id"],
                    "username": username,
                    "email": user_info.get("email"),
                    "full_name": user_info.get("full_name"),
                    "role": user_info.get("role"),
                    "roles": [role.to_dict() for role in user_roles],
                    "permissions": list(user_permissions)
                },
                "session": session.to_dict(),
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer",
                    "expires_in": jwt_handler.access_token_expire_minutes * 60
                }
            }
            
        except Exception as e:
            logger.error(f"認證過程中發生錯誤: {e}")
            attempt.error_message = f"認證錯誤: {str(e)}"
            self._record_auth_attempt(attempt)
            return AuthStatus.FAILED, {"message": "認證過程中發生錯誤"}
    
    def logout_user(self, session_id: str, revoke_all_sessions: bool = False) -> bool:
        """
        用戶登出
        
        Args:
            session_id: 會話ID
            revoke_all_sessions: 是否撤銷所有會話
            
        Returns:
            是否登出成功
        """
        try:
            session = session_manager.get_session(session_id)
            if not session:
                return False
            
            user_id = session.user_id
            
            if revoke_all_sessions:
                # 撤銷用戶所有會話
                session_manager.revoke_user_sessions(user_id)
                jwt_handler.revoke_user_tokens(user_id)
            else:
                # 只撤銷當前會話
                session_manager.revoke_session(session_id)
            
            logger.info(f"用戶 {session.username} 登出")
            return True
            
        except Exception as e:
            logger.error(f"登出過程中發生錯誤: {e}")
            return False
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        刷新訪問令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的令牌對
        """
        try:
            return jwt_handler.refresh_access_token(refresh_token)
        except Exception as e:
            logger.error(f"刷新令牌失敗: {e}")
            return None
    
    def create_user(self, 
                   username: str,
                   email: str,
                   password: str,
                   full_name: Optional[str] = None,
                   role: str = "user",
                   permissions: Optional[List[str]] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        創建用戶
        
        Args:
            username: 用戶名
            email: 郵箱
            password: 密碼
            full_name: 全名
            role: 角色
            permissions: 權限列表
            
        Returns:
            (是否成功, 結果信息)
        """
        try:
            # 驗證密碼強度
            is_valid, errors = password_manager.validate_password_policy(password)
            if not is_valid:
                return False, {"message": "密碼不符合安全策略", "errors": errors}
            
            # 檢查用戶名和郵箱是否已存在
            if self._user_exists(username, email):
                return False, {"message": "用戶名或郵箱已存在"}
            
            # 加密密碼
            hashed_password = password_manager.hash_password(password)
            
            # 創建用戶記錄（這裡應該保存到數據庫）
            user_id = str(uuid.uuid4())
            user_data = {
                "id": user_id,
                "username": username,
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name,
                "role": role,
                "is_active": True,
                "email_verified": not self.require_email_verification,
                "created_at": datetime.utcnow(),
                "password_created_at": datetime.utcnow()
            }
            
            # 分配角色
            role_obj = role_manager.get_role_by_name(role)
            if role_obj:
                role_manager.assign_role_to_user(user_id, role_obj.role_id)
            
            # 分配額外權限
            if permissions:
                for permission in permissions:
                    # 這裡可以創建自定義角色或直接分配權限
                    pass
            
            # 添加密碼到歷史記錄
            password_manager.add_password_to_history(user_id, hashed_password)
            
            # 如果需要郵箱驗證，生成驗證令牌
            verification_token = None
            if self.require_email_verification:
                verification_token = self._generate_email_verification_token(user_id, email)
            
            logger.info(f"創建用戶: {username}")
            
            return True, {
                "user_id": user_id,
                "username": username,
                "email": email,
                "verification_token": verification_token,
                "requires_verification": self.require_email_verification
            }
            
        except Exception as e:
            logger.error(f"創建用戶失敗: {e}")
            return False, {"message": f"創建用戶失敗: {str(e)}"}
    
    def reset_password_request(self, email: str) -> Tuple[bool, Dict[str, Any]]:
        """
        請求密碼重置
        
        Args:
            email: 郵箱地址
            
        Returns:
            (是否成功, 結果信息)
        """
        try:
            # 查找用戶
            user_info = self._get_user_by_email(email)
            if not user_info:
                # 為了安全，不透露用戶是否存在
                return True, {"message": "如果郵箱存在，重置鏈接已發送"}
            
            # 生成重置令牌
            reset_token = password_manager.generate_password_reset_token(user_info["id"])
            
            # 存儲重置令牌
            self.reset_tokens[reset_token] = {
                "user_id": user_info["id"],
                "email": email,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(hours=self.password_reset_token_expire_hours),
                "used": False
            }
            
            logger.info(f"生成密碼重置令牌: {email}")
            
            return True, {
                "message": "重置鏈接已發送",
                "reset_token": reset_token  # 在實際應用中應該通過郵件發送
            }
            
        except Exception as e:
            logger.error(f"密碼重置請求失敗: {e}")
            return False, {"message": "密碼重置請求失敗"}
    
    def reset_password(self, reset_token: str, new_password: str) -> Tuple[bool, Dict[str, Any]]:
        """
        執行密碼重置
        
        Args:
            reset_token: 重置令牌
            new_password: 新密碼
            
        Returns:
            (是否成功, 結果信息)
        """
        try:
            # 驗證重置令牌
            token_info = self.reset_tokens.get(reset_token)
            if not token_info:
                return False, {"message": "無效的重置令牌"}
            
            if token_info["used"]:
                return False, {"message": "重置令牌已使用"}
            
            if datetime.utcnow() > token_info["expires_at"]:
                return False, {"message": "重置令牌已過期"}
            
            # 驗證新密碼
            is_valid, errors = password_manager.validate_password_policy(new_password)
            if not is_valid:
                return False, {"message": "密碼不符合安全策略", "errors": errors}
            
            user_id = token_info["user_id"]
            
            # 檢查密碼重複使用
            if password_manager.check_password_reuse(user_id, new_password):
                return False, {"message": "不能使用最近使用過的密碼"}
            
            # 更新密碼
            hashed_password = password_manager.hash_password(new_password)
            self._update_user_password(user_id, hashed_password)
            
            # 添加到密碼歷史
            password_manager.add_password_to_history(user_id, hashed_password)
            
            # 標記令牌為已使用
            token_info["used"] = True
            
            # 撤銷用戶所有會話
            session_manager.revoke_user_sessions(user_id)
            jwt_handler.revoke_user_tokens(user_id)
            
            logger.info(f"密碼重置成功: 用戶 {user_id}")
            
            return True, {"message": "密碼重置成功"}
            
        except Exception as e:
            logger.error(f"密碼重置失敗: {e}")
            return False, {"message": "密碼重置失敗"}
    
    def change_password(self, 
                       user_id: str,
                       old_password: str,
                       new_password: str) -> Tuple[bool, Dict[str, Any]]:
        """
        更改密碼
        
        Args:
            user_id: 用戶ID
            old_password: 舊密碼
            new_password: 新密碼
            
        Returns:
            (是否成功, 結果信息)
        """
        try:
            # 獲取用戶信息
            user_info = self._get_user_by_id(user_id)
            if not user_info:
                return False, {"message": "用戶不存在"}
            
            # 驗證舊密碼
            if not password_manager.verify_password(old_password, user_info["hashed_password"]):
                return False, {"message": "原密碼錯誤"}
            
            # 驗證新密碼
            is_valid, errors = password_manager.validate_password_policy(new_password)
            if not is_valid:
                return False, {"message": "密碼不符合安全策略", "errors": errors}
            
            # 檢查密碼重複使用
            if password_manager.check_password_reuse(user_id, new_password):
                return False, {"message": "不能使用最近使用過的密碼"}
            
            # 更新密碼
            hashed_password = password_manager.hash_password(new_password)
            self._update_user_password(user_id, hashed_password)
            
            # 添加到密碼歷史
            password_manager.add_password_to_history(user_id, hashed_password)
            
            logger.info(f"用戶 {user_id} 更改密碼成功")
            
            return True, {"message": "密碼更改成功"}
            
        except Exception as e:
            logger.error(f"更改密碼失敗: {e}")
            return False, {"message": "更改密碼失敗"}
    
    def verify_email(self, verification_token: str) -> Tuple[bool, Dict[str, Any]]:
        """
        驗證郵箱
        
        Args:
            verification_token: 驗證令牌
            
        Returns:
            (是否成功, 結果信息)
        """
        try:
            token_info = self.verification_tokens.get(verification_token)
            if not token_info:
                return False, {"message": "無效的驗證令牌"}
            
            if token_info["used"]:
                return False, {"message": "驗證令牌已使用"}
            
            if datetime.utcnow() > token_info["expires_at"]:
                return False, {"message": "驗證令牌已過期"}
            
            # 更新用戶郵箱驗證狀態
            user_id = token_info["user_id"]
            self._update_user_email_verified(user_id, True)
            
            # 標記令牌為已使用
            token_info["used"] = True
            
            logger.info(f"郵箱驗證成功: 用戶 {user_id}")
            
            return True, {"message": "郵箱驗證成功"}
            
        except Exception as e:
            logger.error(f"郵箱驗證失敗: {e}")
            return False, {"message": "郵箱驗證失敗"}
    
    def _record_auth_attempt(self, attempt: AuthAttempt):
        """記錄認證嘗試"""
        self.auth_attempts.append(attempt)
        
        # 限制記錄數量
        if len(self.auth_attempts) > 10000:
            self.auth_attempts = self.auth_attempts[-5000:]
    
    def _get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根據用戶名獲取用戶（模擬數據庫查詢）"""
        # 這裡應該實現實際的數據庫查詢
        # 為了示例，返回模擬數據
        if username == "admin":
            return {
                "id": "admin-user-id",
                "username": "admin",
                "email": "admin@example.com",
                "hashed_password": password_manager.hash_password("admin123"),
                "full_name": "系統管理員",
                "role": "super_admin",
                "is_active": True,
                "email_verified": True,
                "created_at": datetime.utcnow(),
                "password_created_at": datetime.utcnow()
            }
        return None
    
    def _get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """根據郵箱獲取用戶"""
        # 這裡應該實現實際的數據庫查詢
        return None
    
    def _get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根據用戶ID獲取用戶"""
        # 這裡應該實現實際的數據庫查詢
        return None
    
    def _user_exists(self, username: str, email: str) -> bool:
        """檢查用戶是否已存在"""
        # 這裡應該實現實際的數據庫查詢
        return username == "admin"
    
    def _update_user_login_info(self, user_id: str):
        """更新用戶登錄信息"""
        # 這裡應該實現實際的數據庫更新
        pass
    
    def _update_user_password(self, user_id: str, hashed_password: str):
        """更新用戶密碼"""
        # 這裡應該實現實際的數據庫更新
        pass
    
    def _update_user_email_verified(self, user_id: str, verified: bool):
        """更新用戶郵箱驗證狀態"""
        # 這裡應該實現實際的數據庫更新
        pass
    
    def _generate_email_verification_token(self, user_id: str, email: str) -> str:
        """生成郵箱驗證令牌"""
        token = str(uuid.uuid4())
        
        self.verification_tokens[token] = {
            "user_id": user_id,
            "email": email,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
            "used": False
        }
        
        return token
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """獲取認證統計"""
        total_attempts = len(self.auth_attempts)
        successful_attempts = sum(1 for attempt in self.auth_attempts if attempt.status == AuthStatus.SUCCESS)
        
        return {
            "total_auth_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "failed_attempts": total_attempts - successful_attempts,
            "success_rate": successful_attempts / total_attempts if total_attempts > 0 else 0,
            "active_reset_tokens": len([t for t in self.reset_tokens.values() if not t["used"]]),
            "active_verification_tokens": len([t for t in self.verification_tokens.values() if not t["used"]])
        }
    
    def cleanup_expired_tokens(self):
        """清理過期令牌"""
        now = datetime.utcnow()
        
        # 清理過期的重置令牌
        expired_reset_tokens = [
            token for token, info in self.reset_tokens.items()
            if now > info["expires_at"]
        ]
        for token in expired_reset_tokens:
            del self.reset_tokens[token]
        
        # 清理過期的驗證令牌
        expired_verification_tokens = [
            token for token, info in self.verification_tokens.items()
            if now > info["expires_at"]
        ]
        for token in expired_verification_tokens:
            del self.verification_tokens[token]
        
        if expired_reset_tokens or expired_verification_tokens:
            logger.info(f"清理過期令牌: 重置令牌 {len(expired_reset_tokens)} 個，驗證令牌 {len(expired_verification_tokens)} 個")


# 全局認證管理器實例
auth_manager = AuthManager()


def init_auth_system(config: Optional[Dict[str, Any]] = None) -> AuthManager:
    """初始化認證系統"""
    global auth_manager
    auth_manager = AuthManager(config)
    return auth_manager