"""
Voice Enhancement Service 配置設定
"""

import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """應用程式設定"""

    # 基本設定
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # CORS 設定
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://app.autovideo.com",
    ]

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
