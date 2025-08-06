"""
GraphQL Gateway Service
負責統一 GraphQL API 端點，減少前端過度獲取問題
"""

import time

import structlog
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, make_asgi_app
from strawberry.fastapi import GraphQLRouter

from .auth import get_current_user
from .config import get_settings
from .middleware import PrometheusMiddleware
from .schema import schema

# 設定日誌
logger = structlog.get_logger()

# Prometheus 指標
REQUEST_COUNT = Counter("graphql_requests_total", "總 GraphQL 請求數", ["operation"])
REQUEST_DURATION = Histogram("graphql_request_duration_seconds", "GraphQL 請求處理時間")


def create_app() -> FastAPI:
    """建立 FastAPI 應用程式"""
    settings = get_settings()

    app = FastAPI(
        title="GraphQL Gateway Service",
        description="統一 GraphQL API 閘道器，優化前端資料獲取",
        version="1.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # CORS 設定
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "X-Requested-With",
        ],
    )

    # Prometheus 監控中介軟體
    app.add_middleware(PrometheusMiddleware)

    # GraphQL 路由器
    graphql_app = GraphQLRouter(
        schema,
        path="/graphql",
        dependencies=[Depends(get_current_user)] if not settings.DEBUG else [],
    )

    app.include_router(graphql_app, prefix="/api/v1")

    # Prometheus 指標端點
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)

    @app.get("/health")
    async def health_check():
        """健康檢查端點"""
        return {
            "status": "healthy",
            "service": "graphql-gateway",
            "timestamp": time.time(),
        }

    @app.get("/")
    async def root():
        """根端點"""
        return {
            "message": "GraphQL Gateway Service",
            "graphql_endpoint": "/api/v1/graphql",
            "playground": "/api/v1/graphql" if settings.DEBUG else None,
        }

    logger.info("GraphQL Gateway Service 啟動完成")
    return app


# 建立應用程式實例
app = create_app()
