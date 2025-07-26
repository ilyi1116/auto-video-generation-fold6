import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = os.getenv("PROJECT_NAME", "Auto Video Generation AI Service")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL", "postgresql://auto_video_user:password@postgres:5432/auto_video_db")
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # JWT Configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    # AI Service API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    stability_api_key: str = os.getenv("STABILITY_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Service Configuration
    max_concurrent_requests: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "60"))
    
    # File Processing
    temp_storage_path: str = os.getenv("TEMP_STORAGE_PATH", "/tmp/ai_processing")
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    structured_logging: bool = os.getenv("STRUCTURED_LOGGING", "true").lower() == "true"
    
    # Monitoring
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    prometheus_enabled: bool = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
    
    # Celery Configuration
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")
    celery_result_backend: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/2")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create temp directory if it doesn't exist
        os.makedirs(self.temp_storage_path, exist_ok=True)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()