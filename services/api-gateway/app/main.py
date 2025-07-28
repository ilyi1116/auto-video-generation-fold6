from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog
from slowapi.errors import RateLimitExceeded

from .config import settings
from .middleware import LoggingMiddleware, SecurityHeadersMiddleware
from .rate_limiter import limiter, custom_rate_limit_exceeded_handler
from .routers import auth_router, data_router, inference_router, admin_router


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
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)

# Add middleware
app.add_middleware(SecurityHeadersMiddleware)
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

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
