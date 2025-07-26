from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from contextlib import asynccontextmanager

from .config import settings
from .routers import text_generation, image_generation, audio_processing
from .services.ai_manager import AIManager


# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(int(settings.log_level.upper())),
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting AI Service", version="1.0.0")
    
    # Initialize AI Manager
    ai_manager = AIManager()
    app.state.ai_manager = ai_manager
    await ai_manager.initialize()
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Service")
    await ai_manager.shutdown()


app = FastAPI(
    title=settings.project_name,
    description="AI Integration Service for Auto Video Generation System",
    version="1.0.0",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(
    text_generation.router,
    prefix=f"{settings.api_v1_str}/text",
    tags=["text-generation"]
)

app.include_router(
    image_generation.router,
    prefix=f"{settings.api_v1_str}/images",
    tags=["image-generation"]
)

app.include_router(
    audio_processing.router,
    prefix=f"{settings.api_v1_str}/audio",
    tags=["audio-processing"]
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ai-service"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Auto Video Generation AI Service",
        "version": "1.0.0",
        "status": "active"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )