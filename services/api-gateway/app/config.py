from pydantic_settings import BaseSettings
from typing import List, Dict


class Settings(BaseSettings):
    # API Gateway
    project_name: str = "Voice Cloning API Gateway"
    api_v1_str: str = "/api/v1"
    debug: bool = True
    
    # CORS
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Logging
    log_level: str = "INFO"
    structured_logging: bool = True
    
    # Redis for rate limiting and caching
    redis_url: str = "redis://redis:6379/0"
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # Service URLs
    auth_service_url: str = "http://auth-service:8001"
    data_service_url: str = "http://data-service:8002"
    inference_service_url: str = "http://inference-service:8003"
    
    # JWT
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    
    # Request timeout
    service_timeout: int = 30
    
    # File upload limits
    max_upload_size_mb: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()