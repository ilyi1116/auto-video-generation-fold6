from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "Trend Service"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql://auto_video_user:password@postgres:5432/auto_video_db"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # External APIs
    GOOGLE_TRENDS_API_KEY: str = ""
    SOCIAL_SERVICE_URL: str = "http://social-service:8006"

    # Third-party APIs
    GOOGLE_API_KEY: str = ""
    YOUTUBE_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
