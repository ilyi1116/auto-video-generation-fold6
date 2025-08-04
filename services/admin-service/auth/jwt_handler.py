"""
JWT 處理器

提供 JWT 令牌的生成、驗證、刷新和管理功能。
"""

import jwt
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

logger = logging.getLogger(__name__)


class JWTHandler:
    """JWT 處理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # JWT 配置
        self.secret_key = self.config.get("secret_key", self._generate_secret_key())
        self.algorithm = self.config.get("algorithm", "HS256")
        self.access_token_expire_minutes = self.config.get("access_token_expire_minutes", 30)
        self.refresh_token_expire_days = self.config.get("refresh_token_expire_days", 7)
        self.issuer = self.config.get("issuer", "admin-service")
        self.audience = self.config.get("audience", "admin-users")
        
        # 支持 RSA 算法
        if self.algorithm.startswith("RS"):
            self.private_key, self.public_key = self._generate_rsa_keys()
        else:
            self.private_key = self.secret_key
            self.public_key = self.secret_key
        
        # 黑名單令牌（已撤銷的令牌）
        self.blacklisted_tokens: set = set()
        
        # 刷新令牌存儲
        self.refresh_tokens: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"JWT 處理器初始化完成，算法: {self.algorithm}")
    
    def _generate_secret_key(self) -> str:
        """生成安全的密鑰"""
        return secrets.token_urlsafe(64)
    
    def _generate_rsa_keys(self):
        """生成 RSA 密鑰對"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        return private_pem, public_pem
    
    def create_access_token(self, 
                          user_id: str, 
                          username: str, 
                          role: str,
                          permissions: List[str],
                          extra_claims: Optional[Dict[str, Any]] = None) -> str:
        """
        創建訪問令牌
        
        Args:
            user_id: 用戶ID
            username: 用戶名
            role: 用戶角色
            permissions: 用戶權限列表
            extra_claims: 額外聲明
            
        Returns:
            JWT 訪問令牌
        """
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_id,  # Subject (用戶ID)
            "username": username,
            "role": role,
            "permissions": permissions,
            "iat": now,  # Issued At
            "exp": expire,  # Expiration Time
            "iss": self.issuer,  # Issuer
            "aud": self.audience,  # Audience
            "type": "access",
            "jti": secrets.token_urlsafe(16)  # JWT ID
        }
        
        if extra_claims:
            payload.update(extra_claims)
        
        try:
            token = jwt.encode(payload, self.private_key, algorithm=self.algorithm)
            logger.debug(f"為用戶 {username} 創建訪問令牌")
            return token
        except Exception as e:
            logger.error(f"創建訪問令牌失敗: {e}")
            raise
    
    def create_refresh_token(self, 
                           user_id: str, 
                           username: str,
                           session_id: str) -> str:
        """
        創建刷新令牌
        
        Args:
            user_id: 用戶ID
            username: 用戶名
            session_id: 會話ID
            
        Returns:
            JWT 刷新令牌
        """
        now = datetime.utcnow()
        expire = now + timedelta(days=self.refresh_token_expire_days)
        
        jti = secrets.token_urlsafe(32)
        
        payload = {
            "sub": user_id,
            "username": username,
            "session_id": session_id,
            "iat": now,
            "exp": expire,
            "iss": self.issuer,
            "aud": self.audience,
            "type": "refresh",
            "jti": jti
        }
        
        try:
            token = jwt.encode(payload, self.private_key, algorithm=self.algorithm)
            
            # 存儲刷新令牌信息
            self.refresh_tokens[jti] = {
                "user_id": user_id,
                "username": username,
                "session_id": session_id,
                "created_at": now,
                "expires_at": expire,
                "is_active": True
            }
            
            logger.debug(f"為用戶 {username} 創建刷新令牌")
            return token
        except Exception as e:
            logger.error(f"創建刷新令牌失敗: {e}")
            raise
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """
        驗證令牌
        
        Args:
            token: JWT 令牌
            token_type: 令牌類型 ("access" 或 "refresh")
            
        Returns:
            解碼後的載荷（如果有效）
        """
        try:
            # 檢查是否在黑名單中
            if token in self.blacklisted_tokens:
                logger.warning("嘗試使用已撤銷的令牌")
                return None
            
            # 解碼令牌
            payload = jwt.decode(
                token, 
                self.public_key, 
                algorithms=[self.algorithm],
                issuer=self.issuer,
                audience=self.audience
            )
            
            # 檢查令牌類型
            if payload.get("type") != token_type:
                logger.warning(f"令牌類型不匹配，期望: {token_type}, 實際: {payload.get('type')}")
                return None
            
            # 對於刷新令牌，檢查是否仍然活躍
            if token_type == "refresh":
                jti = payload.get("jti")
                if jti not in self.refresh_tokens or not self.refresh_tokens[jti]["is_active"]:
                    logger.warning("刷新令牌已失效")
                    return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("令牌已過期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"無效的令牌: {e}")
            return None
        except Exception as e:
            logger.error(f"令牌驗證失敗: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        使用刷新令牌獲取新的訪問令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的令牌對 (access_token, refresh_token)
        """
        # 驗證刷新令牌
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        user_id = payload["sub"]
        username = payload["username"]
        session_id = payload["session_id"]
        
        # 這裡應該從數據庫獲取用戶的最新角色和權限
        # 為了示例，我們使用默認值
        role = "admin"
        permissions = ["system:read", "user:read"]
        
        try:
            # 創建新的訪問令牌
            new_access_token = self.create_access_token(
                user_id=user_id,
                username=username,
                role=role,
                permissions=permissions
            )
            
            # 創建新的刷新令牌
            new_refresh_token = self.create_refresh_token(
                user_id=user_id,
                username=username,
                session_id=session_id
            )
            
            # 撤銷舊的刷新令牌
            old_jti = payload["jti"]
            if old_jti in self.refresh_tokens:
                self.refresh_tokens[old_jti]["is_active"] = False
            
            logger.info(f"為用戶 {username} 刷新令牌")
            
            return {
                "access_token": new_access_token,
                "refresh_token": new_refresh_token,
                "token_type": "bearer"
            }
            
        except Exception as e:
            logger.error(f"刷新令牌失敗: {e}")
            return None
    
    def revoke_token(self, token: str):
        """
        撤銷令牌
        
        Args:
            token: 要撤銷的令牌
        """
        try:
            # 添加到黑名單
            self.blacklisted_tokens.add(token)
            
            # 如果是刷新令牌，標記為非活躍
            payload = jwt.decode(token, self.public_key, algorithms=[self.algorithm], options={"verify_exp": False})
            if payload.get("type") == "refresh":
                jti = payload.get("jti")
                if jti in self.refresh_tokens:
                    self.refresh_tokens[jti]["is_active"] = False
            
            logger.info("令牌已撤銷")
            
        except Exception as e:
            logger.error(f"撤銷令牌失敗: {e}")
    
    def revoke_user_tokens(self, user_id: str):
        """
        撤銷用戶的所有令牌
        
        Args:
            user_id: 用戶ID
        """
        # 撤銷所有相關的刷新令牌
        for jti, token_info in self.refresh_tokens.items():
            if token_info["user_id"] == user_id:
                token_info["is_active"] = False
        
        logger.info(f"已撤銷用戶 {user_id} 的所有令牌")
    
    def get_token_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        獲取令牌信息（不驗證過期時間）
        
        Args:
            token: JWT 令牌
            
        Returns:
            令牌信息
        """
        try:
            payload = jwt.decode(
                token, 
                self.public_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            return payload
        except Exception as e:
            logger.error(f"獲取令牌信息失敗: {e}")
            return None
    
    def cleanup_expired_tokens(self):
        """清理過期的令牌"""
        now = datetime.utcnow()
        expired_tokens = []
        
        for jti, token_info in self.refresh_tokens.items():
            if token_info["expires_at"] < now:
                expired_tokens.append(jti)
        
        for jti in expired_tokens:
            del self.refresh_tokens[jti]
        
        # 清理黑名單中的過期令牌（這需要解碼令牌來檢查過期時間）
        # 為了性能考慮，這裡暫時不實現
        
        logger.info(f"清理了 {len(expired_tokens)} 個過期刷新令牌")
    
    def get_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        獲取用戶的活躍會話
        
        Args:
            user_id: 用戶ID
            
        Returns:
            活躍會話列表
        """
        sessions = []
        
        for jti, token_info in self.refresh_tokens.items():
            if (token_info["user_id"] == user_id and 
                token_info["is_active"] and 
                token_info["expires_at"] > datetime.utcnow()):
                
                sessions.append({
                    "session_id": token_info["session_id"],
                    "created_at": token_info["created_at"].isoformat(),
                    "expires_at": token_info["expires_at"].isoformat(),
                    "jti": jti
                })
        
        return sessions
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取 JWT 統計信息"""
        active_refresh_tokens = sum(
            1 for token_info in self.refresh_tokens.values() 
            if token_info["is_active"] and token_info["expires_at"] > datetime.utcnow()
        )
        
        return {
            "algorithm": self.algorithm,
            "access_token_expire_minutes": self.access_token_expire_minutes,
            "refresh_token_expire_days": self.refresh_token_expire_days,
            "total_refresh_tokens": len(self.refresh_tokens),
            "active_refresh_tokens": active_refresh_tokens,
            "blacklisted_tokens": len(self.blacklisted_tokens)
        }


# 全局 JWT 處理器實例
jwt_handler = JWTHandler()


def init_jwt_handler(config: Optional[Dict[str, Any]] = None) -> JWTHandler:
    """初始化 JWT 處理器"""
    global jwt_handler
    jwt_handler = JWTHandler(config)
    return jwt_handler