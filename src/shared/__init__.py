"""
共享庫模組
提供所有微服務通用的配置、工具和基礎類別
"""

from .config import (
    BaseServiceSettings,
    APIGatewaySettings,
    AuthServiceSettings,
    VideoServiceSettings,
    AIServiceSettings,
    StorageServiceSettings,
    get_service_settings
)

from .service_discovery import (
    ServiceDiscovery,
    ServiceInstance,
    ServiceStatus,
    LoadBalanceStrategy,
    get_service_discovery,
    register_service,
    get_service_url,
    get_service_instance
)

from .service_client import (
    ServiceClient,
    ServiceClientManager,
    RetryConfig,
    CircuitBreakerConfig,
    get_service_client,
    get_client_manager,
    ServiceUnavailableError,
    HTTPError
)

from .security import (
    SecurityConfig,
    SecurityManager,
    JWTHandler,
    PasswordHandler,
    EncryptionHandler,
    SecurityBearer,
    PermissionChecker,
    RateLimiter,
    SecurityHeadersMiddleware,
    AuditLogger,
    SecurityUtils,
    get_security_manager,
    create_access_token,
    verify_password,
    hash_password,
    get_current_user
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
    "get_current_user"
]

__version__ = "1.0.0"