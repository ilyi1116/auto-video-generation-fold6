import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database Configuration
    database_url: str = os.getenv("DATABASE_URL")
    database_read_url: str = os.getenv("DATABASE_READ_URL")  # Read replica URL
    database_pool_size: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    database_max_overflow: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    database_pool_timeout: int = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
    database_pool_recycle: int = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))

    # JWT Configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "RS256")
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    jwt_refresh_token_expire_days: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))

    # API Configuration
    api_v1_str: str = "/api/v1"
    project_name: str = os.getenv("PROJECT_NAME", "Auto Video Generation Auth Service")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # CORS Configuration
    allowed_hosts: List[str] = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    cors_origins: List[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
    ).split(",")

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
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        if not self.jwt_secret_key:
            raise ValueError("JWT_SECRET_KEY environment variable is required")
        if len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
