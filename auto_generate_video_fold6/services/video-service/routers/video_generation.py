"""
Video Generation API Routes

Provides endpoints for complete video generation workflow including
status tracking, preview generation, and final rendering.
"""

from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..video.video_generator import (
    VideoGenerationRequest,
    VideoGenerationResult,
    video_generation_service,
)

router = APIRouter()
logger = structlog.get_logger()


class VideoGenerationResponse(BaseModel):
    """API response for video generation"""

    success: bool
    generation_id: str
    status: str
    message: str
    preview_url: Optional[str] = None
    estimated_completion: str


class VideoStatusResponse(BaseModel):
    """API response for generation status"""

    generation_id: str
    status: str
    progress: int
    current_step: str
    preview_url: Optional[str] = None
    final_video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: str
    estimated_completion: Optional[str] = None
    error_message: Optional[str] = None


class QuickVideoRequest(BaseModel):
    """Quick video generation request"""

    topic: str
    platform: str = "youtube"
    length: str = "short"
    voice_settings: Dict[str, Any] = {}
    include_music: bool = True
    image_style: str = "realistic"


class CustomVideoRequest(BaseModel):
    """Custom video generation with detailed parameters"""

    topic: str
    script_prompt: Optional[str] = None
    platform: str = "youtube"
    length: str = "medium"
    voice_settings: Dict[str, Any] = {}
    image_style: str = "realistic"
    music_style: str = "cinematic"
    include_music: bool = True
    include_captions: bool = True
    quality: str = "high"
    custom_scenes: Optional[List[Dict[str, Any]]] = None


@router.post("/generate/quick", response_model=VideoGenerationResponse)
async def generate_quick_video(
    request: QuickVideoRequest, current_user: dict = Depends(get_current_user)
):
    """Generate video with preset configurations for quick creation"""
    try:
        logger.info(
            "Quick video generation requested",
            user_id=current_user.get("id"),
            topic=request.topic,
            platform=request.platform,
        )

        # Convert to full generation request
        generation_request = VideoGenerationRequest(
            topic=request.topic,
            target_platform=request.platform,
            video_length=request.length,
            voice_settings=request.voice_settings,
            include_music=request.include_music,
            image_style=request.image_style,
            quality="medium",  # Fixed for quick generation
        )

        result = await video_generation_service.generate_video(
            generation_request, current_user.get("id")
        )

        return VideoGenerationResponse(
            success=True,
            generation_id=result.generation_id,
            status=result.status,
            message="Video generation started successfully",
            estimated_completion=result.estimated_completion.isoformat(),
        )

    except Exception as e:
        logger.error("Quick video generation failed", error=str(e), user_id=current_user.get("id"))
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


@router.post("/generate/custom", response_model=VideoGenerationResponse)
async def generate_custom_video(
    request: CustomVideoRequest, current_user: dict = Depends(get_current_user)
):
    """Generate video with custom parameters and advanced settings"""
    try:
        logger.info(
            "Custom video generation requested",
            user_id=current_user.get("id"),
            topic=request.topic,
            platform=request.platform,
            quality=request.quality,
        )

        # Build generation request
        generation_request = VideoGenerationRequest(
            topic=request.topic,
            target_platform=request.platform,
            video_length=request.length,
            voice_settings=request.voice_settings,
            include_music=request.include_music,
            include_captions=request.include_captions,
            image_style=request.image_style,
            quality=request.quality,
        )

        result = await video_generation_service.generate_video(
            generation_request, current_user.get("id")
        )

        return VideoGenerationResponse(
            success=True,
            generation_id=result.generation_id,
            status=result.status,
            message="Custom video generation started successfully",
            estimated_completion=result.estimated_completion.isoformat(),
        )

    except Exception as e:
        logger.error("Custom video generation failed", error=str(e), user_id=current_user.get("id"))
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


@router.get("/status/{generation_id}", response_model=VideoStatusResponse)
async def get_generation_status(generation_id: str, current_user: dict = Depends(get_current_user)):
    """Get current status of video generation"""
    try:
        status = await video_generation_service.get_generation_status(generation_id)

        return VideoStatusResponse(
            generation_id=generation_id,
            status=status["status"],
            progress=status["progress"],
            current_step=status["current_step"],
            preview_url=status.get("preview_url"),
            final_video_url=status.get("final_video_url"),
            thumbnail_url=status.get("thumbnail_url"),
            created_at=status["created_at"].isoformat(),
            estimated_completion=status.get("estimated_completion"),
            error_message=status.get("error_message"),
        )

    except Exception as e:
        logger.error("Failed to get generation status", error=str(e), generation_id=generation_id)
        raise HTTPException(status_code=404, detail="Generation not found")


@router.post("/cancel/{generation_id}")
async def cancel_generation(generation_id: str, current_user: dict = Depends(get_current_user)):
    """Cancel ongoing video generation"""
    try:
        # In a real implementation, this would stop the generation process
        await video_generation_service.cleanup_generation(generation_id)

        logger.info(
            "Video generation cancelled",
            generation_id=generation_id,
            user_id=current_user.get("id"),
        )

        return {"message": "Generation cancelled successfully", "generation_id": generation_id}

    except Exception as e:
        logger.error("Failed to cancel generation", error=str(e), generation_id=generation_id)
        raise HTTPException(status_code=500, detail="Failed to cancel generation")


@router.get("/templates")
async def get_video_templates(
    platform: Optional[str] = None, current_user: dict = Depends(get_current_user)
):
    """Get available video templates for different platforms"""

    templates = {
        "youtube": [
            {
                "id": "youtube_explainer",
                "name": "Explainer Video",
                "description": "Educational content with clear explanations",
                "duration": "3-5 minutes",
                "style": "professional",
                "recommended_for": ["education", "business", "tutorials"],
            },
            {
                "id": "youtube_entertainment",
                "name": "Entertainment Video",
                "description": "Engaging content for entertainment",
                "duration": "5-10 minutes",
                "style": "dynamic",
                "recommended_for": ["entertainment", "lifestyle", "vlogs"],
            },
        ],
        "tiktok": [
            {
                "id": "tiktok_viral",
                "name": "Viral Content",
                "description": "Short, catchy content designed to go viral",
                "duration": "15-30 seconds",
                "style": "trendy",
                "recommended_for": ["trends", "challenges", "entertainment"],
            },
            {
                "id": "tiktok_educational",
                "name": "Quick Tips",
                "description": "Fast-paced educational content",
                "duration": "30-60 seconds",
                "style": "informative",
                "recommended_for": ["tips", "tutorials", "facts"],
            },
        ],
        "instagram": [
            {
                "id": "instagram_story",
                "name": "Story Format",
                "description": "Vertical content for Instagram Stories",
                "duration": "15-30 seconds",
                "style": "casual",
                "recommended_for": ["behind-the-scenes", "daily updates", "quick announcements"],
            },
            {
                "id": "instagram_reel",
                "name": "Reel Format",
                "description": "Engaging short-form content",
                "duration": "30-90 seconds",
                "style": "creative",
                "recommended_for": ["showcases", "tutorials", "entertainment"],
            },
        ],
    }

    if platform:
        return {"templates": templates.get(platform, [])}

    return {"templates": templates}


@router.get("/presets")
async def get_generation_presets(current_user: dict = Depends(get_current_user)):
    """Get preset configurations for different video types"""

    presets = {
        "educational": {
            "voice_settings": {"voice_id": "echo", "speed": 0.9, "emotion": "professional"},
            "image_style": "clean",
            "include_music": True,
            "music_style": "ambient",
            "include_captions": True,
        },
        "entertainment": {
            "voice_settings": {"voice_id": "alloy", "speed": 1.1, "emotion": "enthusiastic"},
            "image_style": "vibrant",
            "include_music": True,
            "music_style": "upbeat",
            "include_captions": True,
        },
        "business": {
            "voice_settings": {"voice_id": "nova", "speed": 1.0, "emotion": "confident"},
            "image_style": "professional",
            "include_music": True,
            "music_style": "corporate",
            "include_captions": True,
        },
        "storytelling": {
            "voice_settings": {"voice_id": "shimmer", "speed": 0.95, "emotion": "narrative"},
            "image_style": "artistic",
            "include_music": True,
            "music_style": "cinematic",
            "include_captions": False,
        },
    }

    return {"presets": presets}


@router.get("/history")
async def get_generation_history(limit: int = 20, current_user: dict = Depends(get_current_user)):
    """Get user's video generation history"""

    # In a real implementation, this would query the database
    # For now, return placeholder data

    history = [
        {
            "generation_id": "gen_123",
            "topic": "AI and the Future",
            "status": "completed",
            "created_at": "2024-01-15T10:30:00Z",
            "platform": "youtube",
            "video_url": "https://example.com/video1.mp4",
            "thumbnail_url": "https://example.com/thumb1.jpg",
        }
    ]

    return {"history": history, "total": len(history)}


@router.delete("/cleanup/{generation_id}")
async def cleanup_generation(
    generation_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Clean up generation data and temporary files"""

    background_tasks.add_task(video_generation_service.cleanup_generation, generation_id)

    return {"message": "Cleanup initiated", "generation_id": generation_id}
