"""
Voice Enhancement Service
提供進階語音合成、情感表達和語音克隆功能
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
from prometheus_client import make_asgi_app
import time

from .config import get_settings
from .routers import synthesis, emotions, cloning, enhancement
from .middleware import PrometheusMiddleware

# 設定日誌
logger = structlog.get_logger()


def create_app() -> FastAPI:
    """建立 FastAPI 應用程式"""
    settings = get_settings()

    app = FastAPI(
        title="Voice Enhancement Service",
        description="進階語音合成、情感表達和語音克隆服務",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # CORS 設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Prometheus 監控中介軟體
    app.add_middleware(PrometheusMiddleware)

    # 路由器
    app.include_router(
        synthesis.router, prefix="/api/v1/synthesis", tags=["synthesis"]
    )
    app.include_router(
        emotions.router, prefix="/api/v1/emotions", tags=["emotions"]
    )
    app.include_router(
        cloning.router, prefix="/api/v1/cloning", tags=["cloning"]
    )
    app.include_router(
        enhancement.router, prefix="/api/v1/enhancement", tags=["enhancement"]
    )

    # Prometheus 指標端點
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    @app.get("/health")
    async def health_check():
        """健康檢查端點"""
        return {
            "status": "healthy",
            "service": "voice-enhancement",
            "timestamp": time.time(),
            "features": {
                "emotion_synthesis": True,
                "voice_cloning": True,
                "multi_language": True,
                "real_time_processing": True,
            },
        }

    @app.get("/")
    async def root():
        """根端點"""
        return {
            "message": "Voice Enhancement Service",
            "version": "1.0.0",
            "endpoints": {
                "synthesis": "/api/v1/synthesis",
                "emotions": "/api/v1/emotions",
                "cloning": "/api/v1/cloning",
                "enhancement": "/api/v1/enhancement",
            },
        }

    logger.info("Voice Enhancement Service 啟動完成")
    return app


# 建立應用程式實例
app = create_app()
