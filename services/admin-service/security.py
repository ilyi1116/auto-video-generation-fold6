from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Union, Any
import os
from cryptography.fernet import Fernet

# 密碼加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 數據加密密鑰（用於加密 API Keys 等敏感信息）
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
if isinstance(ENCRYPTION_KEY, str):
    ENCRYPTION_KEY = ENCRYPTION_KEY.encode()
fernet = Fernet(ENCRYPTION_KEY)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """驗證密碼"""
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """加密密碼"""
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """創建訪問令牌"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """驗證令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None


def encrypt_data(data: str) -> str:
    """加密敏感數據"""
    if not data:
        return data
    return fernet.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """解密敏感數據"""
    if not encrypted_data:
        return encrypted_data
    try:
        return fernet.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return encrypted_data  # 如果解密失敗，返回原數據


class PermissionChecker:
    """權限檢查器"""
    
    # 定義權限常量
    PERMISSIONS = {
        # AI Provider 權限
        "ai_provider:read": "查看 AI Provider",
        "ai_provider:create": "創建 AI Provider",
        "ai_provider:update": "更新 AI Provider",
        "ai_provider:delete": "刪除 AI Provider",
        "ai_provider:test": "測試 AI Provider",
        
        # 爬蟲配置權限
        "crawler:read": "查看爬蟲配置",
        "crawler:create": "創建爬蟲配置",
        "crawler:update": "更新爬蟲配置",
        "crawler:delete": "刪除爬蟲配置",
        "crawler:run": "運行爬蟲",
        
        # 社交媒體趨勢權限
        "trends:read": "查看趨勢數據",
        "trends:create": "創建趨勢配置",
        "trends:update": "更新趨勢配置",
        "trends:delete": "刪除趨勢配置",
        
        # 日誌權限
        "logs:read": "查看系統日誌",
        "logs:export": "導出日誌",
        
        # 用戶管理權限
        "users:read": "查看用戶",
        "users:create": "創建用戶",
        "users:update": "更新用戶",
        "users:delete": "刪除用戶",
        
        # 系統管理權限
        "system:dashboard": "查看儀表板",
        "system:settings": "系統設置",
        "system:backup": "系統備份"
    }
    
    # 角色權限配置
    ROLE_PERMISSIONS = {
        "readonly": [
            "ai_provider:read",
            "crawler:read", 
            "trends:read",
            "logs:read",
            "system:dashboard"
        ],
        "admin": [
            "ai_provider:read", "ai_provider:create", "ai_provider:update", "ai_provider:test",
            "crawler:read", "crawler:create", "crawler:update", "crawler:run",
            "trends:read", "trends:create", "trends:update",
            "logs:read", "logs:export",
            "system:dashboard"
        ],
        "super_admin": list(PERMISSIONS.keys())  # 所有權限
    }
    
    @classmethod
    def check_permission(cls, user_role: str, user_permissions: Optional[dict], 
                        required_permission: str) -> bool:
        """檢查用戶是否有指定權限"""
        
        # 超級管理員擁有所有權限
        if user_role == "super_admin":
            return True
        
        # 檢查角色默認權限
        role_perms = cls.ROLE_PERMISSIONS.get(user_role, [])
        if required_permission in role_perms:
            return True
        
        # 檢查用戶自定義權限
        if user_permissions and user_permissions.get(required_permission):
            return True
        
        return False
    
    @classmethod
    def get_role_permissions(cls, role: str) -> list:
        """獲取角色權限列表"""
        return cls.ROLE_PERMISSIONS.get(role, [])
    
    @classmethod
    def get_all_permissions(cls) -> dict:
        """獲取所有權限定義"""
        return cls.PERMISSIONS


def require_permission(permission: str):
    """權限裝飾器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 這裡應該從請求上下文中獲取當前用戶信息
            # 暫時跳過權限檢查
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 審計日誌裝飾器
def audit_log(action: str, resource_type: str):
    """審計日誌裝飾器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                # 記錄成功的操作
                # 這裡應該調用日誌記錄函數
                return result
            except Exception as e:
                # 記錄失敗的操作
                # 這裡應該調用錯誤日誌記錄函數
                raise
        return wrapper
    return decorator