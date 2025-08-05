from contextlib import asynccontextmanager

import structlog
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .auth import get_current_user
from .config import settings
from .routers import (
    audio_processing,
    image_generation,
    music_generation,
    text_generation,
)
from .services.ai_manager import AIManager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
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
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-domain.com",
        "https://app.autovideo.com",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
# Include routers
app.include_router(
    text_generation.router,
    prefix=f"{settings.api_v1_str}/text",
    tags=["text-generation"],
)

app.include_router(
    image_generation.router,
    prefix=f"{settings.api_v1_str}/images",
    tags=["image-generation"],
)

app.include_router(
    audio_processing.router,
    prefix=f"{settings.api_v1_str}/audio",
    tags=["audio-processing"],
)

app.include_router(
    music_generation.router,
    prefix=f"{settings.api_v1_str}/music",
    tags=["music-generation"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    ai_manager = app.state.ai_manager
    health_status = ai_manager.get_health_status()

    return {
        "status": health_status["overall_status"],
        "service": "ai-service",
        "details": health_status,
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Auto Video Generation AI Service",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "text": f"{settings.api_v1_str}/text",
            "images": f"{settings.api_v1_str}/images",
            "audio": f"{settings.api_v1_str}/audio",
            "music": f"{settings.api_v1_str}/music",
            "video": f"{settings.api_v1_str}/video",
        },
    }


@app.get(f"{settings.api_v1_str}/capabilities")
async def get_capabilities():
    """Get AI service capabilities"""
    ai_manager = app.state.ai_manager
    return ai_manager.get_service_capabilities()


# Comprehensive video generation endpoint
class VideoContentRequest(BaseModel):
    script_topic: str
    video_style: str = "modern"
    duration_seconds: int = 60
    platform: str = "tiktok"
    include_music: bool = True
    include_voice: bool = True


@app.post(f"{settings.api_v1_str}/video/generate")
async def generate_video_content(
    request: VideoContentRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate complete video content with all AI services"""
    try:
        logger.info(
            "Generating video content",
            user_id=current_user.get("id"),
            topic=request.script_topic,
            platform=request.platform,
        )

        ai_manager = app.state.ai_manager
        result = await ai_manager.generate_video_content(
            script_topic=request.script_topic,
            video_style=request.video_style,
            duration_seconds=request.duration_seconds,
            platform=request.platform,
            include_music=request.include_music,
            include_voice=request.include_voice,
        )

        return result

    except Exception as e:
        logger.error("Video content generation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Video content generation failed")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error("Unhandled exception", error=str(exc), path=request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
