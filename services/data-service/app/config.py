from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = (
        "postgresql://voiceclone:voiceclone@postgres:5432/voiceclone"
    )

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # S3/MinIO Storage
    s3_endpoint: str = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "voice-data"
    s3_region: str = "us-east-1"

    # File upload settings
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_audio_formats: List[str] = ["wav", "mp3", "flac", "m4a", "ogg"]
    upload_dir: str = "/tmp/uploads"

    # Audio processing
    target_sample_rate: int = 22050
    target_channels: int = 1
    min_duration: float = 1.0  # seconds
    max_duration: float = 600.0  # 10 minutes

    # Service settings
    debug: bool = False
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    # Celery
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/0"

    class Config:
        env_file = ".env"


settings = Settings()
