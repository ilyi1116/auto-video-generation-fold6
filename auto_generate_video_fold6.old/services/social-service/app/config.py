from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Social Service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "RS256"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # External Services
    VIDEO_SERVICE_URL: str = "http://video-service:8004"

    # Social Media APIs
    TIKTOK_CLIENT_ID: str = ""
    TIKTOK_CLIENT_SECRET: str = ""

    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""

    INSTAGRAM_CLIENT_ID: str = ""
    INSTAGRAM_CLIENT_SECRET: str = ""

    # API Endpoints
    TIKTOK_API_BASE: str = "https://open-api.tiktok.com"
    YOUTUBE_API_BASE: str = "https://www.googleapis.com/youtube/v3"
    INSTAGRAM_API_BASE: str = "https://graph.instagram.com"

    class Config:
        env_file = ".env"


settings = Settings()
