import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = os.getenv("PROJECT_NAME", "Auto Video Generation Storage Service")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "postgresql://auto_video_user:password@postgres:5432/auto_video_db")
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # JWT Configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    # Storage Configuration
    storage_backend: str = os.getenv("STORAGE_BACKEND", "s3")  # s3, minio, local
    
    # S3/MinIO Configuration
    s3_access_key_id: str = os.getenv("S3_ACCESS_KEY_ID", "")
    s3_secret_access_key: str = os.getenv("S3_SECRET_ACCESS_KEY", "")
    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "auto-video-storage")
    s3_region: str = os.getenv("S3_REGION", "us-east-1")
    s3_endpoint_url: str = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
    s3_public_url: str = os.getenv("S3_PUBLIC_URL", "http://localhost:9000")
    
    # Local Storage Configuration
    local_storage_path: str = os.getenv("LOCAL_STORAGE_PATH", "/app/storage")
    temp_storage_path: str = os.getenv("TEMP_STORAGE_PATH", "/app/storage/temp")
    
    # File Processing Configuration
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    max_upload_files: int = int(os.getenv("MAX_UPLOAD_FILES", "10"))
    
    # Allowed file types
    allowed_image_types: List[str] = ["image/jpeg", "image/png", "image/webp", "image/gif"]
    allowed_audio_types: List[str] = ["audio/mpeg", "audio/wav", "audio/ogg", "audio/m4a"]
    allowed_video_types: List[str] = ["video/mp4", "video/avi", "video/mov", "video/webm"]
    allowed_document_types: List[str] = ["application/pdf", "text/plain", "application/json"]
    
    # Image Processing
    max_image_dimension: int = int(os.getenv("MAX_IMAGE_DIMENSION", "4096"))
    image_quality: int = int(os.getenv("IMAGE_QUALITY", "95"))
    thumbnail_size: int = int(os.getenv("THUMBNAIL_SIZE", "300"))
    
    # Audio Processing
    max_audio_duration_seconds: int = int(os.getenv("MAX_AUDIO_DURATION_SECONDS", "600"))
    audio_sample_rate: int = int(os.getenv("AUDIO_SAMPLE_RATE", "44100"))
    
    # Video Processing
    max_video_duration_seconds: int = int(os.getenv("MAX_VIDEO_DURATION_SECONDS", "600"))
    video_quality: str = os.getenv("VIDEO_QUALITY", "high")
    
    # CDN Configuration
    cdn_url: str = os.getenv("CDN_URL", "")
    use_cdn: bool = os.getenv("USE_CDN", "false").lower() == "true"
    
    # Security Configuration
    virus_scan_enabled: bool = os.getenv("VIRUS_SCAN_ENABLED", "false").lower() == "true"
    content_moderation_enabled: bool = os.getenv("CONTENT_MODERATION_ENABLED", "false").lower() == "true"
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    structured_logging: bool = os.getenv("STRUCTURED_LOGGING", "true").lower() == "true"
    
    # Monitoring
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    prometheus_enabled: bool = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create storage directories if using local storage
        if self.storage_backend == "local":
            os.makedirs(self.local_storage_path, exist_ok=True)
            os.makedirs(self.temp_storage_path, exist_ok=True)
            os.makedirs(f"{self.local_storage_path}/images", exist_ok=True)
            os.makedirs(f"{self.local_storage_path}/audio", exist_ok=True)
            os.makedirs(f"{self.local_storage_path}/video", exist_ok=True)
            os.makedirs(f"{self.local_storage_path}/documents", exist_ok=True)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()