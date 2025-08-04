"""
認證與授權相關的數據模型

提供用戶認證、授權、角色和權限的數據結構。
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Set
from enum import Enum
import uuid


class AuthStatus(Enum):
    """認證狀態"""
    SUCCESS = "success"
    FAILED = "failed"
    EXPIRED = "expired"
    INVALID = "invalid"
    DISABLED = "disabled"
    LOCKED = "locked"


class SessionStatus(Enum):
    """會話狀態"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    INVALID = "invalid"


class PermissionType(Enum):
    """權限類型"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"
    MANAGE = "manage"
    CREATE = "create"
    UPDATE = "update"
    EXPORT = "export"
    ANALYZE = "analyze"


class ResourceType(Enum):
    """資源類型"""
    SYSTEM = "system"
    USER = "user"
    CRAWLER = "crawler"
    TRENDS = "trends"
    LOGS = "logs"
    MODELS = "models"
    BEHAVIOR = "behavior"
    MONITORING = "monitoring"
    SECURITY = "security"
    TRACING = "tracing"
    CONFIG = "config"


@dataclass
class Permission:
    """權限數據類"""
    permission_id: str
    name: str
    resource_type: ResourceType
    permission_type: PermissionType
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.permission_id:
            self.permission_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "permission_id": self.permission_id,
            "name": self.name,
            "resource_type": self.resource_type.value,
            "permission_type": self.permission_type.value,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat()
        }
    
    def __str__(self):
        return f"{self.resource_type.value}:{self.permission_type.value}"


@dataclass
class Role:
    """角色數據類"""
    role_id: str
    name: str
    description: Optional[str] = None
    permissions: Set[str] = field(default_factory=set)
    is_active: bool = True
    is_system: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if not self.role_id:
            self.role_id = str(uuid.uuid4())
    
    def add_permission(self, permission_id: str):
        """添加權限"""
        self.permissions.add(permission_id)
        self.updated_at = datetime.utcnow()
    
    def remove_permission(self, permission_id: str):
        """移除權限"""
        self.permissions.discard(permission_id)
        self.updated_at = datetime.utcnow()
    
    def has_permission(self, permission_id: str) -> bool:
        """檢查是否有特定權限"""
        return permission_id in self.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role_id": self.role_id,
            "name": self.name,
            "description": self.description,
            "permissions": list(self.permissions),
            "is_active": self.is_active,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class UserSession:
    """用戶會話數據類"""
    session_id: str
    user_id: str
    username: str
    ip_address: str
    user_agent: str
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        if not self.expires_at:
            self.expires_at = self.created_at + timedelta(hours=24)
    
    def is_valid(self) -> bool:
        """檢查會話是否有效"""
        if self.status != SessionStatus.ACTIVE:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            self.status = SessionStatus.EXPIRED
            return False
        return True
    
    def refresh(self, duration_hours: int = 24):
        """刷新會話"""
        if self.is_valid():
            self.last_accessed_at = datetime.utcnow()
            self.expires_at = datetime.utcnow() + timedelta(hours=duration_hours)
    
    def revoke(self):
        """撤銷會話"""
        self.status = SessionStatus.REVOKED
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_accessed_at": self.last_accessed_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata
        }


@dataclass
class AuthAttempt:
    """認證嘗試記錄"""
    attempt_id: str
    username: str
    ip_address: str
    user_agent: str
    status: AuthStatus
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.attempt_id:
            self.attempt_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "error_message": self.error_message,
            "metadata": self.metadata
        }


@dataclass
class SecurityAlert:
    """安全警報"""
    alert_id: str
    alert_type: str
    severity: str  # low, medium, high, critical
    title: str
    description: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    is_resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.alert_id:
            self.alert_id = str(uuid.uuid4())
    
    def resolve(self):
        """解決警報"""
        self.is_resolved = True
        self.resolved_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "user_id": self.user_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "is_resolved": self.is_resolved,
            "metadata": self.metadata
        }


@dataclass
class PasswordPolicy:
    """密碼策略"""
    min_length: int = 8
    max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    forbidden_patterns: List[str] = field(default_factory=list)
    max_age_days: Optional[int] = 90
    prevent_reuse_count: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "min_length": self.min_length,
            "max_length": self.max_length,
            "require_uppercase": self.require_uppercase,
            "require_lowercase": self.require_lowercase,
            "require_numbers": self.require_numbers,
            "require_special_chars": self.require_special_chars,
            "forbidden_patterns": self.forbidden_patterns,
            "max_age_days": self.max_age_days,
            "prevent_reuse_count": self.prevent_reuse_count
        }


@dataclass
class LoginAttemptStats:
    """登錄嘗試統計"""
    ip_address: str
    username: Optional[str] = None
    success_count: int = 0
    failed_count: int = 0
    last_attempt_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    is_locked: bool = False
    locked_until: Optional[datetime] = None
    
    def add_attempt(self, success: bool):
        """添加嘗試記錄"""
        self.last_attempt_at = datetime.utcnow()
        if success:
            self.success_count += 1
            self.last_success_at = datetime.utcnow()
            self.failed_count = 0  # 重置失敗計數
        else:
            self.failed_count += 1
    
    def should_lock(self, max_failures: int = 5) -> bool:
        """是否應該鎖定"""
        return self.failed_count >= max_failures
    
    def lock(self, duration_minutes: int = 15):
        """鎖定"""
        self.is_locked = True
        self.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    
    def unlock(self):
        """解鎖"""
        self.is_locked = False
        self.locked_until = None
        self.failed_count = 0
    
    def is_locked_now(self) -> bool:
        """當前是否被鎖定"""
        if not self.is_locked:
            return False
        if self.locked_until and datetime.utcnow() > self.locked_until:
            self.unlock()
            return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ip_address": self.ip_address,
            "username": self.username,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "last_attempt_at": self.last_attempt_at.isoformat() if self.last_attempt_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "is_locked": self.is_locked,
            "locked_until": self.locked_until.isoformat() if self.locked_until else None
        }


# 預定義的系統權限
SYSTEM_PERMISSIONS = [
    # 系統管理權限
    Permission("system_admin", "系統管理", ResourceType.SYSTEM, PermissionType.ADMIN),
    Permission("system_read", "系統查看", ResourceType.SYSTEM, PermissionType.READ),
    Permission("system_config", "系統配置", ResourceType.SYSTEM, PermissionType.MANAGE),
    
    # 用戶管理權限
    Permission("user_read", "用戶查看", ResourceType.USER, PermissionType.READ),
    Permission("user_write", "用戶編輯", ResourceType.USER, PermissionType.WRITE),
    Permission("user_create", "用戶創建", ResourceType.USER, PermissionType.CREATE),
    Permission("user_delete", "用戶刪除", ResourceType.USER, PermissionType.DELETE),
    Permission("user_manage", "用戶管理", ResourceType.USER, PermissionType.MANAGE),
    
    # 爬蟲管理權限  
    Permission("crawler_read", "爬蟲查看", ResourceType.CRAWLER, PermissionType.READ),
    Permission("crawler_write", "爬蟲編輯", ResourceType.CRAWLER, PermissionType.WRITE),
    Permission("crawler_create", "爬蟲創建", ResourceType.CRAWLER, PermissionType.CREATE),
    Permission("crawler_delete", "爬蟲刪除", ResourceType.CRAWLER, PermissionType.DELETE),
    Permission("crawler_execute", "爬蟲執行", ResourceType.CRAWLER, PermissionType.EXECUTE),
    
    # 趨勢數據權限
    Permission("trends_read", "趨勢查看", ResourceType.TRENDS, PermissionType.READ),
    Permission("trends_write", "趨勢編輯", ResourceType.TRENDS, PermissionType.WRITE),
    Permission("trends_analyze", "趨勢分析", ResourceType.TRENDS, PermissionType.ANALYZE),
    Permission("trends_export", "趨勢導出", ResourceType.TRENDS, PermissionType.EXPORT),
    
    # 日誌管理權限
    Permission("logs_read", "日誌查看", ResourceType.LOGS, PermissionType.READ),
    Permission("logs_analyze", "日誌分析", ResourceType.LOGS, PermissionType.ANALYZE),
    Permission("logs_export", "日誌導出", ResourceType.LOGS, PermissionType.EXPORT),
    Permission("logs_manage", "日誌管理", ResourceType.LOGS, PermissionType.MANAGE),
    
    # 模型管理權限
    Permission("models_read", "模型查看", ResourceType.MODELS, PermissionType.READ),
    Permission("models_write", "模型編輯", ResourceType.MODELS, PermissionType.WRITE),
    Permission("models_create", "模型創建", ResourceType.MODELS, PermissionType.CREATE),
    Permission("models_delete", "模型刪除", ResourceType.MODELS, PermissionType.DELETE),
    Permission("models_execute", "模型執行", ResourceType.MODELS, PermissionType.EXECUTE),
    
    # 行為追蹤權限
    Permission("behavior_read", "行為查看", ResourceType.BEHAVIOR, PermissionType.READ),
    Permission("behavior_write", "行為編輯", ResourceType.BEHAVIOR, PermissionType.WRITE),
    Permission("behavior_analyze", "行為分析", ResourceType.BEHAVIOR, PermissionType.ANALYZE),
    Permission("behavior_export", "行為導出", ResourceType.BEHAVIOR, PermissionType.EXPORT),
    Permission("behavior_manage", "行為管理", ResourceType.BEHAVIOR, PermissionType.MANAGE),
    
    # 監控權限
    Permission("monitoring_read", "監控查看", ResourceType.MONITORING, PermissionType.READ),
    Permission("monitoring_manage", "監控管理", ResourceType.MONITORING, PermissionType.MANAGE),
    
    # 安全權限
    Permission("security_read", "安全查看", ResourceType.SECURITY, PermissionType.READ),
    Permission("security_manage", "安全管理", ResourceType.SECURITY, PermissionType.MANAGE),
    
    # 追蹤權限
    Permission("tracing_read", "追蹤查看", ResourceType.TRACING, PermissionType.READ),
    Permission("tracing_manage", "追蹤管理", ResourceType.TRACING, PermissionType.MANAGE),
    
    # 配置權限
    Permission("config_read", "配置查看", ResourceType.CONFIG, PermissionType.READ),
    Permission("config_write", "配置編輯", ResourceType.CONFIG, PermissionType.WRITE),
    Permission("config_manage", "配置管理", ResourceType.CONFIG, PermissionType.MANAGE),
]

# 預定義的系統角色
SYSTEM_ROLES = [
    Role(
        "super_admin",
        "超級管理員",
        "擁有所有系統權限的超級管理員",
        {p.permission_id for p in SYSTEM_PERMISSIONS},
        is_system=True
    ),
    Role(
        "admin",
        "管理員",
        "系統管理員，擁有大部分管理權限",
        {p.permission_id for p in SYSTEM_PERMISSIONS if p.permission_type != PermissionType.ADMIN},
        is_system=True
    ),
    Role(
        "operator",
        "操作員",
        "系統操作員，擁有執行和查看權限",
        {p.permission_id for p in SYSTEM_PERMISSIONS if p.permission_type in [PermissionType.READ, PermissionType.EXECUTE, PermissionType.ANALYZE]},
        is_system=True
    ),
    Role(
        "viewer",
        "查看者",
        "只讀用戶，只能查看系統信息",
        {p.permission_id for p in SYSTEM_PERMISSIONS if p.permission_type == PermissionType.READ},
        is_system=True
    )
]