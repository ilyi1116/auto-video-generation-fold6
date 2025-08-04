"""
會話管理器

提供用戶會話的創建、管理、追蹤和控制功能。
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from collections import defaultdict
import uuid

from .models import UserSession, SessionStatus, LoginAttemptStats, SecurityAlert

logger = logging.getLogger(__name__)


class SessionManager:
    """會話管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 會話配置
        self.session_timeout_hours = self.config.get("session_timeout_hours", 24)
        self.max_sessions_per_user = self.config.get("max_sessions_per_user", 5)
        self.max_failed_attempts = self.config.get("max_failed_attempts", 5)
        self.lockout_duration_minutes = self.config.get("lockout_duration_minutes", 15)
        self.cleanup_interval_minutes = self.config.get("cleanup_interval_minutes", 60)
        
        # 會話存儲
        self.sessions: Dict[str, UserSession] = {}
        
        # 用戶會話映射 (用戶ID -> 會話ID列表)
        self.user_sessions: Dict[str, List[str]] = defaultdict(list)
        
        # 登錄嘗試統計
        self.login_attempts: Dict[str, LoginAttemptStats] = {}  # IP -> 統計
        
        # 安全警報
        self.security_alerts: List[SecurityAlert] = []
        
        # 會話活動記錄
        self.session_activity: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        logger.info("會話管理器初始化完成")
    
    def create_session(self, 
                      user_id: str, 
                      username: str,
                      ip_address: str,
                      user_agent: str,
                      metadata: Optional[Dict[str, Any]] = None) -> UserSession:
        """
        創建新會話
        
        Args:
            user_id: 用戶ID
            username: 用戶名
            ip_address: IP地址
            user_agent: 用戶代理
            metadata: 額外元數據
            
        Returns:
            創建的會話
        """
        # 檢查用戶會話數量限制
        self._cleanup_expired_sessions(user_id)
        user_session_count = len(self.user_sessions.get(user_id, []))
        
        if user_session_count >= self.max_sessions_per_user:
            # 移除最舊的會話
            oldest_session_id = self.user_sessions[user_id][0]
            self.revoke_session(oldest_session_id)
            logger.info(f"用戶 {username} 達到最大會話數限制，移除最舊會話")
        
        # 創建會話
        session = UserSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {}
        )
        
        # 設置會話過期時間
        session.expires_at = datetime.utcnow() + timedelta(hours=self.session_timeout_hours)
        
        # 存儲會話
        self.sessions[session.session_id] = session
        self.user_sessions[user_id].append(session.session_id)
        
        # 記錄會話活動
        self._record_session_activity(session.session_id, "session_created", {
            "ip_address": ip_address,
            "user_agent": user_agent
        })
        
        logger.info(f"為用戶 {username} 創建會話: {session.session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[UserSession]:
        """
        獲取會話
        
        Args:
            session_id: 會話ID
            
        Returns:
            會話對象
        """
        session = self.sessions.get(session_id)
        
        if session and session.is_valid():
            # 更新最後訪問時間
            session.last_accessed_at = datetime.utcnow()
            return session
        
        return None
    
    def refresh_session(self, session_id: str) -> bool:
        """
        刷新會話
        
        Args:
            session_id: 會話ID
            
        Returns:
            是否刷新成功
        """
        session = self.sessions.get(session_id)
        
        if session and session.is_valid():
            session.refresh(self.session_timeout_hours)
            
            self._record_session_activity(session_id, "session_refreshed")
            
            logger.debug(f"刷新會話: {session_id}")
            return True
        
        return False
    
    def revoke_session(self, session_id: str) -> bool:
        """
        撤銷會話
        
        Args:
            session_id: 會話ID
            
        Returns:
            是否撤銷成功
        """
        session = self.sessions.get(session_id)
        
        if session:
            session.revoke()
            
            # 從用戶會話列表中移除
            user_id = session.user_id
            if user_id in self.user_sessions:
                if session_id in self.user_sessions[user_id]:
                    self.user_sessions[user_id].remove(session_id)
            
            self._record_session_activity(session_id, "session_revoked")
            
            logger.info(f"撤銷會話: {session_id}")
            return True
        
        return False
    
    def revoke_user_sessions(self, user_id: str) -> int:
        """
        撤銷用戶的所有會話
        
        Args:
            user_id: 用戶ID
            
        Returns:
            撤銷的會話數量
        """
        session_ids = self.user_sessions.get(user_id, []).copy()
        revoked_count = 0
        
        for session_id in session_ids:
            if self.revoke_session(session_id):
                revoked_count += 1
        
        logger.info(f"撤銷用戶 {user_id} 的 {revoked_count} 個會話")
        return revoked_count
    
    def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """
        獲取用戶的所有活躍會話
        
        Args:
            user_id: 用戶ID
            
        Returns:
            會話列表
        """
        session_ids = self.user_sessions.get(user_id, [])
        sessions = []
        
        for session_id in session_ids:
            session = self.sessions.get(session_id)
            if session and session.is_valid():
                sessions.append(session)
        
        return sessions
    
    def record_login_attempt(self, username: str, ip_address: str, success: bool) -> bool:
        """
        記錄登錄嘗試
        
        Args:
            username: 用戶名
            ip_address: IP地址
            success: 是否成功
            
        Returns:
            是否允許繼續嘗試（未被鎖定）
        """
        # 獲取或創建登錄嘗試統計
        if ip_address not in self.login_attempts:
            self.login_attempts[ip_address] = LoginAttemptStats(
                ip_address=ip_address,
                username=username
            )
        
        stats = self.login_attempts[ip_address]
        
        # 檢查是否已被鎖定
        if stats.is_locked_now():
            logger.warning(f"IP {ip_address} 仍在鎖定期內")
            return False
        
        # 記錄嘗試
        stats.add_attempt(success)
        
        if success:
            logger.info(f"用戶 {username} 從 {ip_address} 登錄成功")
        else:
            logger.warning(f"用戶 {username} 從 {ip_address} 登錄失敗，失敗次數: {stats.failed_count}")
            
            # 檢查是否需要鎖定
            if stats.should_lock(self.max_failed_attempts):
                stats.lock(self.lockout_duration_minutes)
                
                # 創建安全警報
                self._create_security_alert(
                    alert_type="multiple_failed_logins",
                    severity="medium",
                    title="多次登錄失敗",
                    description=f"IP {ip_address} 嘗試登錄用戶 {username} 失敗 {stats.failed_count} 次，已鎖定 {self.lockout_duration_minutes} 分鐘",
                    ip_address=ip_address,
                    username=username
                )
                
                logger.warning(f"IP {ip_address} 因多次登錄失敗被鎖定")
                return False
        
        return True
    
    def is_ip_locked(self, ip_address: str) -> bool:
        """
        檢查IP是否被鎖定
        
        Args:
            ip_address: IP地址
            
        Returns:
            是否被鎖定
        """
        if ip_address not in self.login_attempts:
            return False
        
        return self.login_attempts[ip_address].is_locked_now()
    
    def unlock_ip(self, ip_address: str) -> bool:
        """
        解鎖IP
        
        Args:
            ip_address: IP地址
            
        Returns:
            是否解鎖成功
        """
        if ip_address in self.login_attempts:
            self.login_attempts[ip_address].unlock()
            logger.info(f"手動解鎖IP: {ip_address}")
            return True
        
        return False
    
    def get_session_activity(self, session_id: str) -> List[Dict[str, Any]]:
        """
        獲取會話活動記錄
        
        Args:
            session_id: 會話ID
            
        Returns:
            活動記錄列表
        """
        return self.session_activity.get(session_id, [])
    
    def cleanup_expired_sessions(self):
        """清理過期會話"""
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if not session.is_valid():
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            session = self.sessions[session_id]
            user_id = session.user_id
            
            # 從存儲中移除
            del self.sessions[session_id]
            
            # 從用戶會話列表中移除
            if user_id in self.user_sessions:
                if session_id in self.user_sessions[user_id]:
                    self.user_sessions[user_id].remove(session_id)
        
        if expired_sessions:
            logger.info(f"清理了 {len(expired_sessions)} 個過期會話")
    
    def _cleanup_expired_sessions(self, user_id: str):
        """清理特定用戶的過期會話"""
        if user_id not in self.user_sessions:
            return
        
        valid_sessions = []
        
        for session_id in self.user_sessions[user_id]:
            session = self.sessions.get(session_id)
            if session and session.is_valid():
                valid_sessions.append(session_id)
            elif session_id in self.sessions:
                del self.sessions[session_id]
        
        self.user_sessions[user_id] = valid_sessions
    
    def _record_session_activity(self, session_id: str, activity_type: str, details: Optional[Dict[str, Any]] = None):
        """記錄會話活動"""
        activity = {
            "timestamp": datetime.utcnow().isoformat(),
            "activity_type": activity_type,
            "details": details or {}
        }
        
        self.session_activity[session_id].append(activity)
        
        # 限制活動記錄數量
        if len(self.session_activity[session_id]) > 100:
            self.session_activity[session_id] = self.session_activity[session_id][-50:]
    
    def _create_security_alert(self, 
                              alert_type: str,
                              severity: str,
                              title: str,
                              description: str,
                              user_id: Optional[str] = None,
                              username: Optional[str] = None,
                              ip_address: Optional[str] = None):
        """創建安全警報"""
        alert = SecurityAlert(
            alert_id=str(uuid.uuid4()),
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            user_id=user_id,
            username=username,
            ip_address=ip_address
        )
        
        self.security_alerts.append(alert)
        
        # 限制警報數量
        if len(self.security_alerts) > 1000:
            self.security_alerts = self.security_alerts[-500:]
        
        logger.warning(f"安全警報: {title}")
    
    def get_security_alerts(self, 
                           severity: Optional[str] = None,
                           limit: int = 100) -> List[SecurityAlert]:
        """
        獲取安全警報
        
        Args:
            severity: 嚴重程度過濾
            limit: 返回數量限制
            
        Returns:
            安全警報列表
        """
        alerts = self.security_alerts
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        # 按時間倒序排列
        alerts = sorted(alerts, key=lambda a: a.created_at, reverse=True)
        
        return alerts[:limit]
    
    def resolve_security_alert(self, alert_id: str) -> bool:
        """
        解決安全警報
        
        Args:
            alert_id: 警報ID
            
        Returns:
            是否解決成功
        """
        for alert in self.security_alerts:
            if alert.alert_id == alert_id:
                alert.resolve()
                logger.info(f"解決安全警報: {alert.title}")
                return True
        
        return False
    
    def get_active_users(self) -> List[Dict[str, Any]]:
        """獲取當前活躍用戶"""
        active_users = []
        user_last_activity = {}
        
        # 統計每個用戶的最後活動時間
        for session in self.sessions.values():
            if session.is_valid():
                user_id = session.user_id
                last_activity = session.last_accessed_at
                
                if user_id not in user_last_activity or last_activity > user_last_activity[user_id]:
                    user_last_activity[user_id] = last_activity
        
        # 構建活躍用戶列表
        for user_id, last_activity in user_last_activity.items():
            user_sessions = self.get_user_sessions(user_id)
            if user_sessions:
                active_users.append({
                    "user_id": user_id,
                    "username": user_sessions[0].username,
                    "session_count": len(user_sessions),
                    "last_activity": last_activity.isoformat()
                })
        
        return sorted(active_users, key=lambda u: u["last_activity"], reverse=True)
    
    def get_login_stats(self) -> Dict[str, Any]:
        """獲取登錄統計"""
        total_attempts = 0
        successful_attempts = 0
        failed_attempts = 0
        locked_ips = 0
        
        for stats in self.login_attempts.values():
            total_attempts += stats.success_count + stats.failed_count
            successful_attempts += stats.success_count
            failed_attempts += stats.failed_count
            
            if stats.is_locked_now():
                locked_ips += 1
        
        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "failed_attempts": failed_attempts,
            "success_rate": successful_attempts / total_attempts if total_attempts > 0 else 0,
            "locked_ips": locked_ips,
            "active_sessions": len([s for s in self.sessions.values() if s.is_valid()]),
            "total_users_with_sessions": len(self.user_sessions)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取會話管理統計"""
        active_sessions = sum(1 for session in self.sessions.values() if session.is_valid())
        
        return {
            "total_sessions": len(self.sessions),
            "active_sessions": active_sessions,
            "expired_sessions": len(self.sessions) - active_sessions,
            "users_with_sessions": len(self.user_sessions),
            "security_alerts": len(self.security_alerts),
            "unresolved_alerts": len([a for a in self.security_alerts if not a.is_resolved]),
            "login_attempts_tracked": len(self.login_attempts),
            "locked_ips": sum(1 for stats in self.login_attempts.values() if stats.is_locked_now()),
            "config": {
                "session_timeout_hours": self.session_timeout_hours,
                "max_sessions_per_user": self.max_sessions_per_user,
                "max_failed_attempts": self.max_failed_attempts,
                "lockout_duration_minutes": self.lockout_duration_minutes
            }
        }


# 全局會話管理器實例
session_manager = SessionManager()


def init_session_manager(config: Optional[Dict[str, Any]] = None) -> SessionManager:
    """初始化會話管理器"""
    global session_manager
    session_manager = SessionManager(config)
    return session_manager