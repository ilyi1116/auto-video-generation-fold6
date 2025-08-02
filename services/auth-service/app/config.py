from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = (
        "postgresql://voiceclone_user:password@postgres:5432/voiceclone_db"
    )

    # JWT
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # API
    api_v1_str: str = "/api/v1"
    project_name: str = "Voice Cloning Auth Service"
    debug: bool = True

    # CORS
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # Logging
    log_level: str = "INFO"
    structured_logging: bool = True

    # Redis
    redis_url: str = "redis://redis:6379/0"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
