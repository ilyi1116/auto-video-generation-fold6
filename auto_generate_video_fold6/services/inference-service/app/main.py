import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import database, engine, metadata
from .routers import models, synthesis

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
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
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting voice inference service", service="inference-service")

    # Create database tables
    metadata.create_all(bind=engine)

    # Connect to database
    await database.connect()

    # Initialize model cache
    from .services.model_manager import model_manager

    await model_manager.initialize()

    logger.info("Inference service started successfully")

    yield

    # Cleanup
    await database.disconnect()
    logger.info("Inference service shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Voice Cloning - Inference Service",
    description="Real-time voice synthesis and model management service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(synthesis.router, prefix="/api/v1", tags=["synthesis"])
app.include_router(models.router, prefix="/api/v1", tags=["models"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "inference-service"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"service": "voice-cloning-inference", "version": "1.0.0", "status": "running"}
