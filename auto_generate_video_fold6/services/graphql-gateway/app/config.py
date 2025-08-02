"""
GraphQL Gateway 配置設定
"""

import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """應用程式設定"""

    # 基本設定
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # 服務端點
    AUTH_SERVICE_URL: str = os.getenv(
        "AUTH_SERVICE_URL", "http://auth-service:8000"
    )
    VIDEO_SERVICE_URL: str = os.getenv(
        "VIDEO_SERVICE_URL", "http://video-service:8000"
    )
    AI_SERVICE_URL: str = os.getenv("AI_SERVICE_URL", "http://ai-service:8000")
    TREND_SERVICE_URL: str = os.getenv(
        "TREND_SERVICE_URL", "http://trend-service:8000"
    )
    STORAGE_SERVICE_URL: str = os.getenv(
        "STORAGE_SERVICE_URL", "http://storage-service:8000"
    )

    # CORS 設定
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://app.autovideo.com",
    ]

    # 效能設定
    MAX_QUERY_DEPTH: int = 10
    MAX_QUERY_COMPLEXITY: int = 1000
    CACHE_TTL: int = 300  # 5 分鐘

    # Redis 快取設定
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # JWT 設定
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key")
    JWT_ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"
        case_sensitive = True


# 設定實例
_settings = None


def get_settings() -> Settings:
    """獲取設定實例（單例模式）"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
