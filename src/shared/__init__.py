"""
共享庫模組
提供所有微服務通用的配置、工具和基礎類別
"""

from .config import (
    AIServiceSettings,
    APIGatewaySettings,
    AuthServiceSettings,
    BaseServiceSettings,
    StorageServiceSettings,
    VideoServiceSettings,
    get_service_settings,
)
from .security import (
    AuditLogger,
    EncryptionHandler,
    JWTHandler,
    PasswordHandler,
    PermissionChecker,
    RateLimiter,
    SecurityBearer,
    SecurityConfig,
    SecurityHeadersMiddleware,
    SecurityManager,
    SecurityUtils,
    create_access_token,
    get_current_user,
    get_security_manager,
    hash_password,
    verify_password,
)
from .service_client import (
    CircuitBreakerConfig,
    HTTPError,
    RetryConfig,
    ServiceClient,
    ServiceClientManager,
    ServiceUnavailableError,
    get_client_manager,
    get_service_client,
)
from .service_discovery import (
    LoadBalanceStrategy,
    ServiceDiscovery,
    ServiceInstance,
    ServiceStatus,
    get_service_discovery,
    get_service_instance,
    get_service_url,
    register_service,
)

__all__ = [
    # Configuration
    "BaseServiceSettings",
    "APIGatewaySettings",
    "AuthServiceSettings",
    "VideoServiceSettings",
    "AIServiceSettings",
    "StorageServiceSettings",
    "get_service_settings",
    # Service Discovery
    "ServiceDiscovery",
    "ServiceInstance",
    "ServiceStatus",
    "LoadBalanceStrategy",
    "get_service_discovery",
    "register_service",
    "get_service_url",
    "get_service_instance",
    # Service Client
    "ServiceClient",
    "ServiceClientManager",
    "RetryConfig",
    "CircuitBreakerConfig",
    "get_service_client",
    "get_client_manager",
    "ServiceUnavailableError",
    "HTTPError",
    # Security
    "SecurityConfig",
    "SecurityManager",
    "JWTHandler",
    "PasswordHandler",
    "EncryptionHandler",
    "SecurityBearer",
    "PermissionChecker",
    "RateLimiter",
    "SecurityHeadersMiddleware",
    "AuditLogger",
    "SecurityUtils",
    "get_security_manager",
    "create_access_token",
    "verify_password",
    "hash_password",
    "get_current_user",
]

__version__ = "1.0.0"
