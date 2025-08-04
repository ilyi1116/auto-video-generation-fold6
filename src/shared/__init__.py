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

__all__ = [
    "BaseServiceSettings",
    "APIGatewaySettings", 
    "AuthServiceSettings",
    "VideoServiceSettings",
    "AIServiceSettings",
    "StorageServiceSettings",
    "get_service_settings"
]

__version__ = "1.0.0"