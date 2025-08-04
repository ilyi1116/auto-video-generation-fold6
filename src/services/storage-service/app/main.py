import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .config import settings
from .database import close_db, init_db
from .routers import download, upload

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
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
    logger.info("Starting Storage Service")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down Storage Service")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e))


# Create FastAPI app
app = FastAPI(
    title="Storage Service",
    description="File upload, storage, and management service for AI \
        video generation platform",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
)

# Add trusted host middleware for security
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts
    )


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all requests"""
    start_time = time.time()

    # Extract user info from headers (set by API Gateway)
    user_id = request.headers.get("x-user-id")
    user_role = request.headers.get("x-user-role")

    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        user_id=user_id,
        user_role=user_role,
        client_ip=request.client.host,
    )

    try:
        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=round(process_time, 4),
            user_id=user_id,
        )

        response.headers["X-Process-Time"] = str(process_time)
        return response

    except Exception as e:
        process_time = time.time() - start_time
        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=round(process_time, 4),
            user_id=user_id,
        )
        raise


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured logging"""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        method=request.method,
        url=str(request.url),
    )
    raise exc


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        method=request.method,
        url=str(request.url),
        exc_info=True,
    )
    raise HTTPException(status_code=500, detail="Internal server error")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "storage-service",
        "version": "1.0.0",
        "storage_backend": settings.storage_backend,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Storage Service API",
        "version": "1.0.0",
        "docs_url": "/docs" if settings.debug else None,
    }


# Include routers
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(download.router, prefix="/api/v1", tags=["download"])
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=settings.debug,
        log_level="info",
    )
