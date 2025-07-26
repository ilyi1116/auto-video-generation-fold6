import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://voiceclone_user:your_secure_password_here@postgres:5432/voiceclone_db",
    )

    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # S3 Storage
    s3_endpoint_url: str = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
    s3_access_key_id: str = os.getenv("S3_ACCESS_KEY_ID", "minioadmin")
    s3_secret_access_key: str = os.getenv("S3_SECRET_ACCESS_KEY", "minioadmin")
    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "voice-models")
    s3_region: str = os.getenv("S3_REGION", "us-east-1")

    # JWT
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")

    # Auth Service
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    # Model settings
    max_model_cache_size: int = int(os.getenv("MAX_MODEL_CACHE_SIZE", "3"))
    model_cache_ttl: int = int(os.getenv("MODEL_CACHE_TTL", "3600"))  # 1 hour

    # Synthesis settings
    max_text_length: int = int(os.getenv("MAX_TEXT_LENGTH", "1000"))
    max_audio_duration: int = int(os.getenv("MAX_AUDIO_DURATION", "300"))  # 5 minutes

    # Performance
    synthesis_timeout: int = int(os.getenv("SYNTHESIS_TIMEOUT", "60"))  # 60 seconds
    model_load_timeout: int = int(os.getenv("MODEL_LOAD_TIMEOUT", "120"))  # 2 minutes


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
