"""
權限管理器

提供權限檢查、控制和動態權限管理功能。
"""

import logging
from collections import defaultdict
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set

from .models import PermissionType, ResourceType

logger = logging.getLogger(__name__)


class PermissionManager:
    """權限管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

        # 權限檢查器註冊表
        self.permission_checkers: Dict[str, Callable] = {}

        # 動態權限規則
        self.dynamic_rules: List[Callable] = []

        # 權限依賴關係
        self.permission_dependencies: Dict[str, Set[str]] = {}

        # 權限組
        self.permission_groups: Dict[str, Set[str]] = {}

        # 初始化基本權限組
        self._initialize_permission_groups()

        logger.info("權限管理器初始化完成")

    def _initialize_permission_groups(self):
        """初始化基本權限組"""
        # 系統管理權限組
        self.permission_groups["system_admin"] = {"system:admin", "system:read", "system:config"}

        # 用戶管理權限組
        self.permission_groups["user_manager"] = {
            "user:read",
            "user:write",
            "user:create",
            "user:delete",
            "user:manage",
        }

        # 內容管理權限組
        self.permission_groups["content_manager"] = {
            "crawler:read",
            "crawler:write",
            "crawler:create",
            "crawler:execute",
            "trends:read",
            "trends:write",
            "trends:analyze",
        }

        # 分析師權限組
        self.permission_groups["analyst"] = {
            "logs:read",
            "logs:analyze",
            "behavior:read",
            "behavior:analyze",
            "trends:read",
            "trends:analyze",
            "monitoring:read",
        }

        # 只讀用戶權限組
        self.permission_groups["readonly"] = {
            "system:read",
            "user:read",
            "crawler:read",
            "trends:read",
            "logs:read",
            "models:read",
            "behavior:read",
            "monitoring:read",
        }

    def register_permission_checker(self, permission: str, checker: Callable) -> None:
        """
        註冊權限檢查器

        Args:
            permission: 權限標識
            checker: 檢查函數，應接受 (user_id, resource_id, context) 參數
        """
        self.permission_checkers[permission] = checker
        logger.debug(f"註冊權限檢查器: {permission}")

    def add_dynamic_rule(self, rule: Callable) -> None:
        """
        添加動態權限規則

        Args:
            rule: 規則函數，應接受 (user_id, permission, resource_id, context) 參數並返回布爾值
        """
        self.dynamic_rules.append(rule)
        logger.debug("添加動態權限規則")

    def set_permission_dependency(self, permission: str, dependencies: List[str]) -> None:
        """
        設置權限依賴關係

        Args:
            permission: 權限標識
            dependencies: 依賴的權限列表
        """
        self.permission_dependencies[permission] = set(dependencies)
        logger.debug(f"設置權限依賴: {permission} -> {dependencies}")

    def create_permission_group(self, group_name: str, permissions: List[str]) -> None:
        """
        創建權限組

        Args:
            group_name: 權限組名稱
            permissions: 權限列表
        """
        self.permission_groups[group_name] = set(permissions)
        logger.info(f"創建權限組: {group_name}")

    def check_permission(
        self,
        user_id: str,
        permission: str,
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        檢查用戶權限

        Args:
            user_id: 用戶ID
            permission: 權限標識
            resource_id: 資源ID
            context: 上下文信息

        Returns:
            是否有權限
        """
        context = context or {}

        # 首先檢查基本權限（從角色管理器獲取）
        from .role_manager import role_manager

        if not role_manager.user_has_permission(user_id, permission):
            logger.debug(f"用戶 {user_id} 沒有基本權限: {permission}")
            return False

        # 檢查權限依賴
        if permission in self.permission_dependencies:
            for dep_permission in self.permission_dependencies[permission]:
                if not role_manager.user_has_permission(user_id, dep_permission):
                    logger.debug(f"用戶 {user_id} 缺少依賴權限: {dep_permission}")
                    return False

        # 檢查自定義權限檢查器
        if permission in self.permission_checkers:
            try:
                checker_result = self.permission_checkers[permission](user_id, resource_id, context)
                if not checker_result:
                    logger.debug(f"用戶 {user_id} 未通過自定義權限檢查: {permission}")
                    return False
            except Exception as e:
                logger.error(f"權限檢查器執行失敗: {permission}, 錯誤: {e}")
                return False

        # 檢查動態規則
        for rule in self.dynamic_rules:
            try:
                if not rule(user_id, permission, resource_id, context):
                    logger.debug(f"用戶 {user_id} 未通過動態權限規則: {permission}")
                    return False
            except Exception as e:
                logger.error(f"動態權限規則執行失敗: {e}")
                return False

        return True

    def check_any_permission(
        self,
        user_id: str,
        permissions: List[str],
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        檢查用戶是否擁有任一權限

        Args:
            user_id: 用戶ID
            permissions: 權限列表
            resource_id: 資源ID
            context: 上下文信息

        Returns:
            是否有任一權限
        """
        for permission in permissions:
            if self.check_permission(user_id, permission, resource_id, context):
                return True
        return False

    def check_all_permissions(
        self,
        user_id: str,
        permissions: List[str],
        resource_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        檢查用戶是否擁有所有權限

        Args:
            user_id: 用戶ID
            permissions: 權限列表
            resource_id: 資源ID
            context: 上下文信息

        Returns:
            是否有所有權限
        """
        for permission in permissions:
            if not self.check_permission(user_id, permission, resource_id, context):
                return False
        return True

    def get_user_permissions_for_resource(self, user_id: str, resource_type: str) -> Set[str]:
        """
        獲取用戶對特定資源類型的所有權限

        Args:
            user_id: 用戶ID
            resource_type: 資源類型

        Returns:
            權限集合
        """
        from .role_manager import role_manager

        all_permissions = role_manager.get_user_permissions(user_id)
        resource_permissions = set()

        for permission in all_permissions:
            if permission.startswith(f"{resource_type}:"):
                resource_permissions.add(permission)

        return resource_permissions

    def get_accessible_resources(
        self, user_id: str, resource_type: str, resource_ids: List[str]
    ) -> List[str]:
        """
        獲取用戶可訪問的資源列表

        Args:
            user_id: 用戶ID
            resource_type: 資源類型
            resource_ids: 資源ID列表

        Returns:
            可訪問的資源ID列表
        """
        accessible = []
        read_permission = f"{resource_type}:read"

        for resource_id in resource_ids:
            if self.check_permission(user_id, read_permission, resource_id):
                accessible.append(resource_id)

        return accessible

    def filter_by_permission(
        self,
        user_id: str,
        items: List[Dict[str, Any]],
        permission: str,
        resource_id_field: str = "id",
    ) -> List[Dict[str, Any]]:
        """
        根據權限過濾項目列表

        Args:
            user_id: 用戶ID
            items: 項目列表
            permission: 需要的權限
            resource_id_field: 資源ID字段名

        Returns:
            過濾後的項目列表
        """
        filtered = []

        for item in items:
            resource_id = item.get(resource_id_field)
            if self.check_permission(user_id, permission, resource_id, {"item": item}):
                filtered.append(item)

        return filtered

    def get_permission_matrix(self, user_id: str) -> Dict[str, Dict[str, bool]]:
        """
        獲取用戶的權限矩陣

        Args:
            user_id: 用戶ID

        Returns:
            權限矩陣 {resource_type: {permission_type: bool}}
        """
        from .role_manager import role_manager

        user_permissions = role_manager.get_user_permissions(user_id)
        matrix = defaultdict(dict)

        for permission in user_permissions:
            if ":" in permission:
                resource_type, permission_type = permission.split(":", 1)
                matrix[resource_type][permission_type] = True

        return dict(matrix)

    def require_permission(self, permission: str, resource_id_param: Optional[str] = None):
        """
        權限檢查裝飾器

        Args:
            permission: 需要的權限
            resource_id_param: 資源ID參數名

        Returns:
            裝飾器函數
        """

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # 從參數中獲取用戶ID（假設是 current_user）
                current_user = kwargs.get("current_user")
                if not current_user:
                    raise PermissionError("未找到當前用戶信息")

                user_id = getattr(current_user, "id", None) or getattr(
                    current_user, "user_id", None
                )
                if not user_id:
                    raise PermissionError("無法獲取用戶ID")

                # 獲取資源ID
                resource_id = None
                if resource_id_param:
                    resource_id = kwargs.get(resource_id_param)

                # 檢查權限
                if not self.check_permission(user_id, permission, resource_id):
                    raise PermissionError(f"用戶沒有權限: {permission}")

                return func(*args, **kwargs)

            return wrapper

        return decorator

    def validate_permission_format(self, permission: str) -> bool:
        """
        驗證權限格式

        Args:
            permission: 權限字符串

        Returns:
            是否為有效格式
        """
        if not permission or ":" not in permission:
            return False

        parts = permission.split(":")
        if len(parts) != 2:
            return False

        resource_type, permission_type = parts

        try:
            ResourceType(resource_type)
            PermissionType(permission_type)
            return True
        except ValueError:
            return False

    def explain_permission_denial(
        self, user_id: str, permission: str, resource_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        解釋權限拒絕的原因

        Args:
            user_id: 用戶ID
            permission: 權限標識
            resource_id: 資源ID

        Returns:
            拒絕原因的詳細信息
        """
        from .role_manager import role_manager

        explanation = {
            "permission": permission,
            "user_id": user_id,
            "resource_id": resource_id,
            "has_basic_permission": False,
            "missing_dependencies": [],
            "failed_custom_checks": [],
            "failed_dynamic_rules": [],
        }

        # 檢查基本權限
        if role_manager.user_has_permission(user_id, permission):
            explanation["has_basic_permission"] = True
        else:
            return explanation

        # 檢查權限依賴
        if permission in self.permission_dependencies:
            for dep_permission in self.permission_dependencies[permission]:
                if not role_manager.user_has_permission(user_id, dep_permission):
                    explanation["missing_dependencies"].append(dep_permission)

        # 檢查自定義檢查器
        if permission in self.permission_checkers:
            try:
                checker_result = self.permission_checkers[permission](user_id, resource_id, {})
                if not checker_result:
                    explanation["failed_custom_checks"].append(permission)
            except Exception as e:
                explanation["failed_custom_checks"].append(f"{permission}: {str(e)}")

        # 檢查動態規則
        for i, rule in enumerate(self.dynamic_rules):
            try:
                if not rule(user_id, permission, resource_id, {}):
                    explanation["failed_dynamic_rules"].append(f"rule_{i}")
            except Exception as e:
                explanation["failed_dynamic_rules"].append(f"rule_{i}: {str(e)}")

        return explanation

    def get_stats(self) -> Dict[str, Any]:
        """獲取權限管理統計"""
        return {
            "registered_checkers": len(self.permission_checkers),
            "dynamic_rules": len(self.dynamic_rules),
            "permission_dependencies": len(self.permission_dependencies),
            "permission_groups": len(self.permission_groups),
            "total_grouped_permissions": sum(
                len(perms) for perms in self.permission_groups.values()
            ),
        }


# 全局權限管理器實例
permission_manager = PermissionManager()


def init_permission_manager(config: Optional[Dict[str, Any]] = None) -> PermissionManager:
    """初始化權限管理器"""
    global permission_manager
    permission_manager = PermissionManager(config)
    return permission_manager


def require_permission(permission: str, resource_id_param: Optional[str] = None):
    """權限檢查裝飾器的快捷方式"""
    return permission_manager.require_permission(permission, resource_id_param)
