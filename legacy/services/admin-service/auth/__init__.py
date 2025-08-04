"""
用戶認證與授權管理系統

提供用戶認證、授權、角色管理和權限控制功能。
"""

from .auth_manager import auth_manager, init_auth_system
from .jwt_handler import jwt_handler
from .password_manager import password_manager
from .role_manager import role_manager
from .permission_manager import permission_manager
from .session_manager import session_manager
from .middleware import AuthMiddleware
from .models import Role, Permission, UserSession

# 初始化認證系統的便捷函數
def init_auth_system(config=None):
    """初始化整個認證與授權系統"""
    init_auth_system(config)

__all__ = [
    'auth_manager',
    'jwt_handler',
    'password_manager',
    'role_manager',
    'permission_manager',
    'session_manager',
    'AuthMiddleware',
    'Role',
    'Permission',
    'UserSession',
    'init_auth_system'
]