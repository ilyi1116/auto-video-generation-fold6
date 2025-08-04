"""
角色管理器

提供用戶角色的創建、管理、分配和權限控制功能。
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List, Set, Any
from collections import defaultdict

from .models import Role, Permission, SYSTEM_ROLES, SYSTEM_PERMISSIONS

logger = logging.getLogger(__name__)


class RoleManager:
    """角色管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 角色存儲
        self.roles: Dict[str, Role] = {}
        
        # 權限存儲
        self.permissions: Dict[str, Permission] = {}
        
        # 用戶角色映射
        self.user_roles: Dict[str, Set[str]] = defaultdict(set)
        
        # 初始化系統權限和角色
        self._initialize_system_permissions()
        self._initialize_system_roles()
        
        logger.info("角色管理器初始化完成")
    
    def _initialize_system_permissions(self):
        """初始化系統權限"""
        for permission in SYSTEM_PERMISSIONS:
            self.permissions[permission.permission_id] = permission
        
        logger.info(f"初始化了 {len(SYSTEM_PERMISSIONS)} 個系統權限")
    
    def _initialize_system_roles(self):
        """初始化系統角色"""
        for role in SYSTEM_ROLES:
            self.roles[role.role_id] = role
        
        logger.info(f"初始化了 {len(SYSTEM_ROLES)} 個系統角色")
    
    def create_role(self, 
                   name: str, 
                   description: Optional[str] = None,
                   permissions: Optional[List[str]] = None) -> Role:
        """
        創建新角色
        
        Args:
            name: 角色名稱
            description: 角色描述
            permissions: 權限ID列表
            
        Returns:
            創建的角色
        """
        # 檢查角色名是否已存在
        for role in self.roles.values():
            if role.name == name:
                raise ValueError(f"角色名稱 '{name}' 已存在")
        
        # 創建角色
        role = Role(
            role_id="",  # 會在 __post_init__ 中生成
            name=name,
            description=description,
            permissions=set(permissions or []),
            is_system=False
        )
        
        # 驗證權限是否存在
        for permission_id in role.permissions:
            if permission_id not in self.permissions:
                logger.warning(f"權限 {permission_id} 不存在，已忽略")
                role.permissions.discard(permission_id)
        
        self.roles[role.role_id] = role
        
        logger.info(f"創建角色: {name} ({role.role_id})")
        return role
    
    def get_role(self, role_id: str) -> Optional[Role]:
        """
        獲取角色
        
        Args:
            role_id: 角色ID
            
        Returns:
            角色對象
        """
        return self.roles.get(role_id)
    
    def get_role_by_name(self, name: str) -> Optional[Role]:
        """
        根據名稱獲取角色
        
        Args:
            name: 角色名稱
            
        Returns:
            角色對象
        """
        for role in self.roles.values():
            if role.name == name:
                return role
        return None
    
    def update_role(self, 
                   role_id: str, 
                   name: Optional[str] = None,
                   description: Optional[str] = None,
                   permissions: Optional[List[str]] = None) -> bool:
        """
        更新角色
        
        Args:
            role_id: 角色ID
            name: 新角色名稱
            description: 新角色描述
            permissions: 新權限列表
            
        Returns:
            是否更新成功
        """
        role = self.roles.get(role_id)
        if not role:
            return False
        
        # 檢查是否為系統角色
        if role.is_system:
            logger.warning(f"無法修改系統角色: {role.name}")
            return False
        
        # 更新角色信息
        if name is not None:
            # 檢查新名稱是否已存在
            for existing_role in self.roles.values():
                if existing_role.role_id != role_id and existing_role.name == name:
                    raise ValueError(f"角色名稱 '{name}' 已存在")
            role.name = name
        
        if description is not None:
            role.description = description
        
        if permissions is not None:
            # 驗證權限是否存在
            valid_permissions = set()
            for permission_id in permissions:
                if permission_id in self.permissions:
                    valid_permissions.add(permission_id)
                else:
                    logger.warning(f"權限 {permission_id} 不存在，已忽略")
            
            role.permissions = valid_permissions
        
        role.updated_at = datetime.utcnow()
        
        logger.info(f"更新角色: {role.name} ({role_id})")
        return True
    
    def delete_role(self, role_id: str) -> bool:
        """
        刪除角色
        
        Args:
            role_id: 角色ID
            
        Returns:
            是否刪除成功
        """
        role = self.roles.get(role_id)
        if not role:
            return False
        
        # 檢查是否為系統角色
        if role.is_system:
            logger.warning(f"無法刪除系統角色: {role.name}")
            return False
        
        # 檢查是否有用戶正在使用此角色
        users_with_role = [
            user_id for user_id, roles in self.user_roles.items()
            if role_id in roles
        ]
        
        if users_with_role:
            logger.warning(f"角色 {role.name} 正被 {len(users_with_role)} 個用戶使用，無法刪除")
            return False
        
        del self.roles[role_id]
        
        logger.info(f"刪除角色: {role.name} ({role_id})")
        return True
    
    def assign_role_to_user(self, user_id: str, role_id: str) -> bool:
        """
        為用戶分配角色
        
        Args:
            user_id: 用戶ID
            role_id: 角色ID
            
        Returns:
            是否分配成功
        """
        if role_id not in self.roles:
            logger.warning(f"角色 {role_id} 不存在")
            return False
        
        self.user_roles[user_id].add(role_id)
        
        role_name = self.roles[role_id].name
        logger.info(f"為用戶 {user_id} 分配角色: {role_name}")
        return True
    
    def remove_role_from_user(self, user_id: str, role_id: str) -> bool:
        """
        移除用戶的角色
        
        Args:
            user_id: 用戶ID
            role_id: 角色ID
            
        Returns:
            是否移除成功
        """
        if user_id not in self.user_roles:
            return False
        
        if role_id in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role_id)
            
            role_name = self.roles.get(role_id, {}).name if role_id in self.roles else role_id
            logger.info(f"移除用戶 {user_id} 的角色: {role_name}")
            return True
        
        return False
    
    def get_user_roles(self, user_id: str) -> List[Role]:
        """
        獲取用戶的所有角色
        
        Args:
            user_id: 用戶ID
            
        Returns:
            角色列表
        """
        role_ids = self.user_roles.get(user_id, set())
        return [self.roles[role_id] for role_id in role_ids if role_id in self.roles]
    
    def get_user_permissions(self, user_id: str) -> Set[str]:
        """
        獲取用戶的所有權限
        
        Args:
            user_id: 用戶ID
            
        Returns:
            權限ID集合
        """
        permissions = set()
        
        user_roles = self.get_user_roles(user_id)
        for role in user_roles:
            if role.is_active:
                permissions.update(role.permissions)
        
        return permissions
    
    def user_has_permission(self, user_id: str, permission_id: str) -> bool:
        """
        檢查用戶是否具有特定權限
        
        Args:
            user_id: 用戶ID
            permission_id: 權限ID
            
        Returns:
            是否具有權限
        """
        user_permissions = self.get_user_permissions(user_id)
        return permission_id in user_permissions
    
    def user_has_role(self, user_id: str, role_name: str) -> bool:
        """
        檢查用戶是否具有特定角色
        
        Args:
            user_id: 用戶ID
            role_name: 角色名稱
            
        Returns:
            是否具有角色
        """
        user_roles = self.get_user_roles(user_id)
        return any(role.name == role_name for role in user_roles)
    
    def list_roles(self, include_system: bool = True) -> List[Role]:
        """
        列出所有角色
        
        Args:
            include_system: 是否包含系統角色
            
        Returns:
            角色列表
        """
        roles = list(self.roles.values())
        
        if not include_system:
            roles = [role for role in roles if not role.is_system]
        
        return sorted(roles, key=lambda r: r.created_at)
    
    def create_permission(self, 
                         name: str,
                         resource_type: str,
                         permission_type: str,
                         description: Optional[str] = None) -> Permission:
        """
        創建新權限
        
        Args:
            name: 權限名稱
            resource_type: 資源類型
            permission_type: 權限類型
            description: 權限描述
            
        Returns:
            創建的權限
        """
        from .models import ResourceType, PermissionType
        
        # 轉換枚舉
        try:
            resource_enum = ResourceType(resource_type)
            permission_enum = PermissionType(permission_type)
        except ValueError as e:
            raise ValueError(f"無效的資源類型或權限類型: {e}")
        
        permission = Permission(
            permission_id="",  # 會在 __post_init__ 中生成
            name=name,
            resource_type=resource_enum,
            permission_type=permission_enum,
            description=description
        )
        
        self.permissions[permission.permission_id] = permission
        
        logger.info(f"創建權限: {name} ({permission.permission_id})")
        return permission
    
    def get_permission(self, permission_id: str) -> Optional[Permission]:
        """
        獲取權限
        
        Args:
            permission_id: 權限ID
            
        Returns:
            權限對象
        """
        return self.permissions.get(permission_id)
    
    def list_permissions(self) -> List[Permission]:
        """
        列出所有權限
        
        Returns:
            權限列表
        """
        return sorted(self.permissions.values(), key=lambda p: p.created_at)
    
    def get_role_usage_stats(self) -> Dict[str, Any]:
        """獲取角色使用統計"""
        role_usage = defaultdict(int)
        
        for user_id, roles in self.user_roles.items():
            for role_id in roles:
                role_usage[role_id] += 1
        
        stats = {}
        for role_id, role in self.roles.items():
            stats[role.name] = {
                "role_id": role_id,
                "user_count": role_usage[role_id],
                "is_system": role.is_system,
                "permission_count": len(role.permissions)
            }
        
        return stats
    
    def cleanup_orphaned_roles(self):
        """清理孤立的角色分配"""
        # 清理不存在的角色分配
        for user_id, roles in list(self.user_roles.items()):
            valid_roles = {role_id for role_id in roles if role_id in self.roles}
            invalid_roles = roles - valid_roles
            
            if invalid_roles:
                self.user_roles[user_id] = valid_roles
                logger.info(f"清理用戶 {user_id} 的無效角色: {invalid_roles}")
    
    def export_roles(self) -> Dict[str, Any]:
        """導出角色配置"""
        return {
            "roles": {
                role_id: role.to_dict() 
                for role_id, role in self.roles.items()
                if not role.is_system
            },
            "permissions": {
                perm_id: perm.to_dict()
                for perm_id, perm in self.permissions.items()
            },
            "user_roles": {
                user_id: list(roles)
                for user_id, roles in self.user_roles.items()
            }
        }
    
    def import_roles(self, data: Dict[str, Any]):
        """導入角色配置"""
        # 導入自定義角色
        for role_id, role_data in data.get("roles", {}).items():
            if role_id not in self.roles:
                role = Role(
                    role_id=role_id,
                    name=role_data["name"],
                    description=role_data.get("description"),
                    permissions=set(role_data.get("permissions", [])),
                    is_system=False
                )
                self.roles[role_id] = role
        
        # 導入用戶角色分配
        for user_id, roles in data.get("user_roles", {}).items():
            self.user_roles[user_id] = set(roles)
        
        logger.info("角色配置導入完成")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取角色管理統計"""
        return {
            "total_roles": len(self.roles),
            "system_roles": sum(1 for role in self.roles.values() if role.is_system),
            "custom_roles": sum(1 for role in self.roles.values() if not role.is_system),
            "total_permissions": len(self.permissions),
            "total_users_with_roles": len(self.user_roles),
            "role_usage": self.get_role_usage_stats()
        }


# 全局角色管理器實例
role_manager = RoleManager()


def init_role_manager(config: Optional[Dict[str, Any]] = None) -> RoleManager:
    """初始化角色管理器"""
    global role_manager
    role_manager = RoleManager(config)
    return role_manager