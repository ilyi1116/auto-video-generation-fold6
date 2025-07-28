from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from .config import settings
from .middleware import LoggingMiddleware
from .rate_limiter import custom_rate_limit_exceeded_handler, limiter
from .routers import admin_router, auth_router, data_router, inference_router
from .security import (
    SecurityHeadersMiddleware,
    TrustedProxyMiddleware,
    get_ssl_context,
    validate_ssl_config,
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting API Gateway", service="api-gateway")

    # Validate SSL configuration
    try:
        validate_ssl_config()
    except Exception as e:
        logger.error("SSL configuration validation failed", error=str(e))
        if settings.ssl_enabled:
            raise

    yield

    # Shutdown
    logger.info("Shutting down API Gateway")


app = FastAPI(
    title=settings.project_name,
    version="1.0.0",
    description="API Gateway for voice cloning system",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    lifespan=lifespan,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded, custom_rate_limit_exceeded_handler
)

# Add middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    TrustedProxyMiddleware,
    trusted_proxies=[
        "127.0.0.1",
        "::1",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
    ],
)
app.add_middleware(LoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "api-gateway", "version": "1.0.0"}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Voice Cloning API Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# Include routers
app.include_router(
    auth_router,
    prefix=settings.api_v1_str,
)

app.include_router(
    data_router,
    prefix=settings.api_v1_str,
)

app.include_router(
    inference_router,
    prefix=settings.api_v1_str,
)

app.include_router(
    admin_router,
    prefix=settings.api_v1_str,
)


if __name__ == "__main__":
    import uvicorn

    ssl_context = get_ssl_context() if settings.ssl_enabled else None

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        ssl_certfile=settings.ssl_cert_path if settings.ssl_enabled else None,
        ssl_keyfile=settings.ssl_key_path if settings.ssl_enabled else None,
        ssl_ca_certs=None,
        ssl_ciphers="ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS",
    )
