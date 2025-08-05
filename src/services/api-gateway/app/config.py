import os
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """API Gateway 配置"""

    service_name: str = "api-gateway"
    
    # 基本設定
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "info")
    
    # API 設定
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # 資料庫設定
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    
    # JWT 設定 (legacy, use the new one below)
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    # API Configuration
    project_name: str = os.getenv("PROJECT_NAME", "Auto Video Generation API Gateway")
    api_v1_str: str = "/api/v1"

    # CORS Configuration (繼承自基類，但可以擴展)
    allowed_hosts: List[str] = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

    # Logging (繼承自基類)
    structured_logging: bool = os.getenv("STRUCTURED_LOGGING", "true").lower() == "true"

    # Rate Limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    rate_limit_burst: int = int(os.getenv("RATE_LIMIT_BURST", "10"))

    # Service URLs
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001")
    data_service_url: str = os.getenv("DATA_SERVICE_URL", "http://data-service:8002")
    inference_service_url: str = os.getenv("INFERENCE_SERVICE_URL", "http://inference-service:8003")
    video_service_url: str = os.getenv("VIDEO_SERVICE_URL", "http://video-service:8004")
    ai_service_url: str = os.getenv("AI_SERVICE_URL", "http://ai-service:8005")
    social_service_url: str = os.getenv("SOCIAL_SERVICE_URL", "http://social-service:8006")
    trend_service_url: str = os.getenv("TREND_SERVICE_URL", "http://trend-service:8007")
    scheduler_service_url: str = os.getenv("SCHEDULER_SERVICE_URL", "http://scheduler-service:8008")

    # JWT Configuration (for token verification)
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "development-jwt-secret-key-change-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")

    # Request Configuration
    service_timeout: int = int(os.getenv("SERVICE_TIMEOUT", "30"))

    # File Upload Limits
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "100"))
    allowed_file_extensions: List[str] = os.getenv(
        "ALLOWED_FILE_EXTENSIONS", "mp3,wav,m4a,flac"
    ).split(",")

    # Security Headers
    security_headers_enabled: bool = os.getenv("SECURITY_HEADERS_ENABLED", "true").lower() == "true"
    hsts_max_age: int = int(os.getenv("HSTS_MAX_AGE", "31536000"))
    csp_policy: str = os.getenv(
        "CSP_POLICY",
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'",
    )

    # SSL Configuration
    ssl_enabled: bool = os.getenv("SSL_ENABLED", "false").lower() == "true"
    ssl_cert_path: str = os.getenv("SSL_CERT_PATH", "")
    ssl_key_path: str = os.getenv("SSL_KEY_PATH", "")

    # Monitoring
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    prometheus_enabled: bool = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
    metrics_port: int = int(os.getenv("METRICS_PORT", "9090"))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Validate required settings - only in production
        if self.environment == "production" and not os.getenv("JWT_SECRET_KEY"):
            raise ValueError("JWT_SECRET_KEY environment variable is required in production")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
