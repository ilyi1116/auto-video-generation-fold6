
from pydantic import BaseSettings


class Settings(BaseSettings):
    # 基本設置
    DEBUG: bool = False
    API_BASE_URL: str = "http://localhost:8000"

    # 數據庫設置
    DATABASE_URL: str = "sqlite:///./app.db"

    # Redis 設置
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT 設置
    JWT_SECRET_KEY: str = "your-secret-key"
    JWT_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # 服務端口
    API_GATEWAY_PORT: int = 8000
    AUTH_SERVICE_PORT: int = 8001
    VIDEO_SERVICE_PORT: int = 8004
    AI_SERVICE_PORT: int = 8005
    SOCIAL_SERVICE_PORT: int = 8006
    TREND_SERVICE_PORT: int = 8007
    SCHEDULER_SERVICE_PORT: int = 8008

    class Config:
        env_file = ".env"


settings = Settings()
