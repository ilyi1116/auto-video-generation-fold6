import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://auto_video_user:your_secure_password_here@postgres:5432/auto_video_db")
    
    # JWT Configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    jwt_refresh_token_expire_days: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    
    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = os.getenv("PROJECT_NAME", "Auto Video Generation Auth Service")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # CORS Configuration
    allowed_hosts: List[str] = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
    
    # Security
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    rate_limit_burst: int = int(os.getenv("RATE_LIMIT_BURST", "10"))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    structured_logging: bool = os.getenv("STRUCTURED_LOGGING", "true").lower() == "true"
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # Email Configuration
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_tls: bool = os.getenv("SMTP_TLS", "true").lower() == "true"
    
    # Monitoring
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    prometheus_enabled: bool = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate required settings
        if not self.jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable is required")
        if len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()