"""
統一配置管理基類
供所有微服務使用，確保配置載入的一致性
"""

import os
import sys
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


def load_env_file(env: Optional[str] = None) -> Optional[str]:
    """
    載入環境特定的配置檔案

    Args:
        env: 環境名稱 (development, testing, production)
             如果為 None，則從 ENVIRONMENT 環境變數讀取

    Returns:
        配置檔案路徑，如果找不到則返回 None
    """
    if env is None:
        env = os.getenv("ENVIRONMENT", "development")

    # 從項目根目錄開始查找配置
    current_dir = Path(__file__).parent
    while current_dir.parent != current_dir:  # 找到根目錄
        config_dir = current_dir / "config" / "environments"
        config_file = config_dir / f"{env}.env"

        if config_file.exists():
            return str(config_file)

        # 如果找不到特定環境配置，嘗試 development
        if env != "development":
            dev_config = config_dir / "development.env"
            if dev_config.exists():
                print(f"Warning: {env}.env not found, using development.env")
                return str(dev_config)

        current_dir = current_dir.parent

    return None


class BaseServiceSettings(BaseSettings):
    """
    微服務基礎配置類
    所有服務配置都應該繼承這個類
    """

    # 基礎配置
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "info")

    # 服務資訊
    service_name: str = "unknown-service"
    service_version: str = "1.0.0"

    # API 配置
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_reload: bool = os.getenv("API_RELOAD", "false").lower() == "true"
    api_workers: int = int(os.getenv("API_WORKERS", "1"))

    # 資料庫配置
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    database_pool_size: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    database_max_overflow: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))

    # Redis 配置
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # CORS 配置
    cors_origins: list[str] = []
    cors_credentials: bool = os.getenv("CORS_CREDENTIALS", "false").lower() == "true"

    # 監控配置
    prometheus_enabled: bool = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
    jaeger_enabled: bool = os.getenv("JAEGER_ENABLED", "false").lower() == "true"

    class Config:
        """Pydantic 配置"""

        env_file = load_env_file()
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        # 處理 CORS_ORIGINS 字符串轉換為列表
        cors_origins_str = os.getenv("CORS_ORIGINS", "")
        if cors_origins_str:
            self.cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

        super().__init__(**kwargs)

    @property
    def is_development(self) -> bool:
        """是否為開發環境"""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """是否為生產環境"""
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        """是否為測試環境"""
        return self.environment == "testing"


class APIGatewaySettings(BaseServiceSettings):
    """API Gateway 專用配置"""

    service_name: str = "api-gateway"
    api_port: int = int(os.getenv("API_PORT", "8000"))

    # Rate limiting
    rate_limit_requests: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    rate_limit_window: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))


class AuthServiceSettings(BaseServiceSettings):
    """認證服務專用配置"""

    service_name: str = "auth-service"
    api_port: int = int(os.getenv("API_PORT", "8001"))

    # JWT 配置
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    jwt_refresh_token_expire_days: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))


class VideoServiceSettings(BaseServiceSettings):
    """視頻服務專用配置"""

    service_name: str = "video-service"
    api_port: int = int(os.getenv("API_PORT", "8004"))

    # 上傳配置
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "104857600"))  # 100MB


class AIServiceSettings(BaseServiceSettings):
    """AI 服務專用配置"""

    service_name: str = "ai-service"
    api_port: int = int(os.getenv("API_PORT", "8005"))

    # AI 配置
    model_cache_dir: str = os.getenv("MODEL_CACHE_DIR", "./models")
    max_concurrent_requests: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))


class StorageServiceSettings(BaseServiceSettings):
    """存儲服務專用配置"""

    service_name: str = "storage-service"
    api_port: int = int(os.getenv("API_PORT", "8009"))

    # 存儲配置
    storage_backend: str = os.getenv("STORAGE_BACKEND", "local")
    s3_endpoint: str = os.getenv("S3_ENDPOINT", "http://localhost:9000")
    s3_access_key: str = os.getenv("S3_ACCESS_KEY", "")
    s3_secret_key: str = os.getenv("S3_SECRET_KEY", "")
    s3_bucket: str = os.getenv("S3_BUCKET", "auto-video-storage")


# 工廠函數，根據服務名稱返回對應的配置類
def get_service_settings(service_name: str) -> BaseServiceSettings:
    """
    根據服務名稱獲取對應的配置實例

    Args:
        service_name: 服務名稱

    Returns:
        對應的配置實例
    """
    settings_map = {
        "api-gateway": APIGatewaySettings,
        "auth-service": AuthServiceSettings,
        "video-service": VideoServiceSettings,
        "ai-service": AIServiceSettings,
        "storage-service": StorageServiceSettings,
    }

    settings_class = settings_map.get(service_name, BaseServiceSettings)
    return settings_class()
