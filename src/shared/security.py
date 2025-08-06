"""
統一安全中間件和工具
提供認證、授權、加密和安全頭部等功能
"""

import base64
import hashlib
import hmac
import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import bcrypt
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

logger = logging.getLogger(__name__)


# ========================================
# 安全配置模型
# ========================================
class SecurityConfig(BaseModel):
    """安全配置"""

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7
    password_min_length: int = 8
    password_require_special: bool = True
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60
    cors_origins: List[str] = []
    security_headers_enabled: bool = True


# ========================================
# JWT Token 處理
# ========================================
class JWTHandler:
    """JWT 令牌處理器"""

    def __init__(self, config: SecurityConfig):
        self.config = config

    def create_access_token(
        self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """創建訪問令牌"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.config.jwt_expire_minutes
            )

        to_encode.update(
            {"exp": expire, "iat": datetime.utcnow(), "type": "access"}
        )

        return jwt.encode(
            to_encode,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm,
        )

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """創建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            days=self.config.jwt_refresh_expire_days
        )

        to_encode.update(
            {"exp": expire, "iat": datetime.utcnow(), "type": "refresh"}
        )

        return jwt.encode(
            to_encode,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm,
        )

    def verify_token(
        self, token: str, token_type: str = "access"
    ) -> Dict[str, Any]:
        """驗證令牌"""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )

            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Invalid token type. Expected {token_type}",
                )

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    def refresh_access_token(self, refresh_token: str) -> str:
        """刷新訪問令牌"""
        payload = self.verify_token(refresh_token, "refresh")

        # 移除不需要的字段
        new_payload = {
            k: v for k, v in payload.items() if k not in ["exp", "iat", "type"]
        }

        return self.create_access_token(new_payload)


# ========================================
# 密碼處理
# ========================================
class PasswordHandler:
    """密碼處理器"""

    def __init__(self, config: SecurityConfig):
        self.config = config

    def hash_password(self, password: str) -> str:
        """哈希密碼"""
        return bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def verify_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        """驗證密碼"""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    def validate_password_strength(self, password: str) -> bool:
        """驗證密碼強度"""
        if len(password) < self.config.password_min_length:
            return False

        if self.config.password_require_special:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(char in special_chars for char in password):
                return False

            # 檢查是否包含數字和字母
            has_digit = any(char.isdigit() for char in password)
            has_alpha = any(char.isalpha() for char in password)

            if not (has_digit and has_alpha):
                return False

        return True

    def generate_secure_password(self, length: int = 12) -> str:
        """生成安全密碼"""
        import string

        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        password = "".join(secrets.choice(characters) for _ in range(length))

        # 確保包含所有必需的字符類型
        if not self.validate_password_strength(password):
            return self.generate_secure_password(length)

        return password


# ========================================
# 加密處理
# ========================================
class EncryptionHandler:
    """加密處理器"""

    def __init__(self, key: Optional[str] = None):
        if key:
            self.key = key.encode()
        else:
            self.key = Fernet.generate_key()

        # 使用 PBKDF2 派生密鑰
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"stable_salt",  # 在生產中應該使用隨機鹽
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.key))
        self.fernet = Fernet(key)

    def encrypt(self, data: str) -> str:
        """加密數據"""
        return self.fernet.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """解密數據"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()

    def generate_secure_token(self, length: int = 32) -> str:
        """生成安全令牌"""
        return secrets.token_urlsafe(length)


# ========================================
# 認證中間件
# ========================================
class SecurityBearer(HTTPBearer):
    """安全Bearer認證"""

    def __init__(self, jwt_handler: JWTHandler, auto_error: bool = True):
        super(SecurityBearer, self).__init__(auto_error=auto_error)
        self.jwt_handler = jwt_handler

    async def __call__(self, request: Request) -> Optional[Dict[str, Any]]:
        credentials: HTTPAuthorizationCredentials = await super(
            SecurityBearer, self
        ).__call__(request)

        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme.",
                )

            payload = self.jwt_handler.verify_token(credentials.credentials)
            return payload

        return None


# ========================================
# 權限檢查
# ========================================
class PermissionChecker:
    """權限檢查器"""

    def __init__(self):
        self.permissions = {}

    def add_permission(self, role: str, resource: str, actions: List[str]):
        """添加權限"""
        if role not in self.permissions:
            self.permissions[role] = {}
        self.permissions[role][resource] = actions

    def check_permission(
        self, user_role: str, resource: str, action: str
    ) -> bool:
        """檢查權限"""
        if user_role not in self.permissions:
            return False

        if resource not in self.permissions[user_role]:
            return False

        return action in self.permissions[user_role][resource]

    def require_permission(self, resource: str, action: str):
        """權限裝飾器"""

        def decorator(func):
            async def wrapper(*args, **kwargs):
                # 從請求中獲取用戶信息
                user_payload = kwargs.get("current_user")
                if not user_payload:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required",
                    )

                user_role = user_payload.get("role", "user")

                if not self.check_permission(user_role, resource, action):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions",
                    )

                return await func(*args, **kwargs)

            return wrapper

        return decorator


# ========================================
# 限流處理
# ========================================
class RateLimiter:
    """限流器"""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.requests = {}  # 在生產環境中應該使用 Redis

    def is_allowed(self, identifier: str) -> bool:
        """檢查是否允許請求"""
        if not self.config.rate_limit_enabled:
            return True

        current_time = int(time.time())
        minute_key = current_time // 60
        key = f"{identifier}:{minute_key}"

        if key not in self.requests:
            self.requests[key] = 0

        self.requests[key] += 1

        # 清理舊記錄
        self._cleanup_old_records(current_time)

        return self.requests[key] <= self.config.rate_limit_per_minute

    def _cleanup_old_records(self, current_time: int):
        """清理舊記錄"""
        current_minute = current_time // 60
        keys_to_delete = []

        for key in self.requests.keys():
            minute = int(key.split(":")[1])
            if current_minute - minute > 5:  # 保留 5 分鐘的記錄
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self.requests[key]


# ========================================
# 安全頭部中間件
# ========================================
class SecurityHeadersMiddleware:
    """安全頭部中間件"""

    def __init__(self, app, config: SecurityConfig):
        self.app = app
        self.config = config

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":

            async def send_wrapper(message):
                if (
                    message["type"] == "http.response.start"
                    and self.config.security_headers_enabled
                ):
                    headers = dict(message.get("headers", []))

                    # 添加安全頭部
                    security_headers = {
                        b"X-Content-Type-Options": b"nosniff",
                        b"X-Frame-Options": b"DENY",
                        b"X-XSS-Protection": b"1; mode=block",
                        b"Strict-Transport-Security": b"max-age=31536000; includeSubDomains",
                        b"Referrer-Policy": b"strict-origin-when-cross-origin",
                        b"Content-Security-Policy": b"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
                    }

                    headers.update(security_headers)
                    message["headers"] = list(headers.items())

                await send(message)

            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


# ========================================
# 審計日誌
# ========================================
class AuditLogger:
    """審計日誌記錄器"""

    def __init__(self):
        self.logger = logging.getLogger("audit")

    def log_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        ip_address: str,
        user_agent: str,
        success: bool,
        details: Optional[Dict[str, Any]] = None,
    ):
        """記錄用戶行為"""
        audit_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "details": details or {},
        }

        self.logger.info(f"AUDIT: {audit_data}")

    def log_security_event(
        self, event_type: str, details: Dict[str, Any], severity: str = "INFO"
    ):
        """記錄安全事件"""
        security_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "details": details,
        }

        if severity == "CRITICAL":
            self.logger.critical(f"SECURITY: {security_data}")
        elif severity == "WARNING":
            self.logger.warning(f"SECURITY: {security_data}")
        else:
            self.logger.info(f"SECURITY: {security_data}")


# ========================================
# 安全工具類
# ========================================
class SecurityUtils:
    """安全工具類"""

    @staticmethod
    def generate_csrf_token() -> str:
        """生成 CSRF 令牌"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def verify_csrf_token(token: str, expected_token: str) -> bool:
        """驗證 CSRF 令牌"""
        return hmac.compare_digest(token, expected_token)

    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """清理輸入"""
        # 移除潛在的惡意字符
        dangerous_chars = ["<", ">", '"', "'", "&", "script", "javascript"]
        sanitized = input_str

        for char in dangerous_chars:
            sanitized = sanitized.replace(char, "")

        return sanitized.strip()

    @staticmethod
    def generate_api_key() -> str:
        """生成 API 密鑰"""
        return f"ak_{secrets.token_urlsafe(32)}"

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """哈希 API 密鑰"""
        return hashlib.sha256(api_key.encode()).hexdigest()


# ========================================
# 統一安全管理器
# ========================================
class SecurityManager:
    """統一安全管理器"""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.jwt_handler = JWTHandler(config)
        self.password_handler = PasswordHandler(config)
        self.encryption_handler = EncryptionHandler()
        self.permission_checker = PermissionChecker()
        self.rate_limiter = RateLimiter(config)
        self.audit_logger = AuditLogger()

        # 設置默認權限
        self._setup_default_permissions()

    def _setup_default_permissions(self):
        """設置默認權限"""
        # 管理員權限
        self.permission_checker.add_permission(
            "admin", "users", ["create", "read", "update", "delete"]
        )
        self.permission_checker.add_permission(
            "admin", "services", ["create", "read", "update", "delete"]
        )
        self.permission_checker.add_permission(
            "admin", "system", ["create", "read", "update", "delete"]
        )

        # 用戶權限
        self.permission_checker.add_permission(
            "user", "profile", ["read", "update"]
        )
        self.permission_checker.add_permission(
            "user", "videos", ["create", "read", "update", "delete"]
        )
        self.permission_checker.add_permission(
            "user", "ai", ["create", "read"]
        )

        # 訪客權限
        self.permission_checker.add_permission("guest", "public", ["read"])

    def get_security_bearer(self) -> SecurityBearer:
        """獲取安全Bearer認證"""
        return SecurityBearer(self.jwt_handler)

    def get_current_user_dependency(self):
        """獲取當前用戶依賴"""
        security_bearer = self.get_security_bearer()

        async def get_current_user(
            payload: Dict[str, Any] = Depends(security_bearer),
        ) -> Dict[str, Any]:
            return payload

        return get_current_user

    def require_permission(self, resource: str, action: str):
        """權限要求裝飾器"""
        return self.permission_checker.require_permission(resource, action)


# ========================================
# 全局安全管理器實例
# ========================================
_security_manager: Optional[SecurityManager] = None


def get_security_manager(
    config: Optional[SecurityConfig] = None,
) -> SecurityManager:
    """獲取全局安全管理器實例"""
    global _security_manager

    if _security_manager is None:
        if config is None:
            # 使用默認配置
            config = SecurityConfig(
                jwt_secret_key=os.getenv(
                    "JWT_SECRET_KEY", "your-secret-key-change-in-production"
                ),
                jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
                jwt_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "30")),
                rate_limit_per_minute=int(
                    os.getenv("RATE_LIMIT_PER_MINUTE", "60")
                ),
            )

        _security_manager = SecurityManager(config)

    return _security_manager


# ========================================
# 便捷函數
# ========================================
def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """創建訪問令牌的便捷函數"""
    security_manager = get_security_manager()
    return security_manager.jwt_handler.create_access_token(
        data, expires_delta
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼的便捷函數"""
    security_manager = get_security_manager()
    return security_manager.password_handler.verify_password(
        plain_password, hashed_password
    )


def hash_password(password: str) -> str:
    """哈希密碼的便捷函數"""
    security_manager = get_security_manager()
    return security_manager.password_handler.hash_password(password)


def get_current_user():
    """獲取當前用戶的便捷函數"""
    security_manager = get_security_manager()
    return security_manager.get_current_user_dependency()
