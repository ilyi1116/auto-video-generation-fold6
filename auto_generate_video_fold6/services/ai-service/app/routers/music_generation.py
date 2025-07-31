from typing import Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..services.suno_client import SunoClient

router = APIRouter()
logger = structlog.get_logger()


class MusicGenerationRequest(BaseModel):
    prompt: str
    style: str = "background"  # background, energetic, cinematic, acoustic, corporate, hip_hop, jazz
    duration_seconds: int = 30  # 15-300 seconds
    instrumental: bool = True
    mood: str = "neutral"  # upbeat, calm, dramatic, energetic, peaceful
    platform: str = "tiktok"  # tiktok, youtube, instagram, podcast
    custom_lyrics: Optional[str] = None
    tempo: Optional[str] = None  # slow, medium, fast


class MusicGenerationResponse(BaseModel):
    generation_id: str
    music_id: str
    music_url: str
    enhanced_prompt: str
    original_prompt: str
    style: str
    mood: str
    platform: str
    duration_seconds: int
    generation_time_seconds: float
    status: str


class MusicVariationRequest(BaseModel):
    base_music_id: str
    variation_count: int = 3
    variation_strength: float = 0.5  # 0.1-1.0


class MusicExtensionRequest(BaseModel):
    music_id: str
    additional_duration: int
    maintain_style: bool = True


@router.post("/generate", response_model=MusicGenerationResponse)
async def generate_music(
    request: MusicGenerationRequest,
    current_user: dict = Depends(get_current_user),
) -> MusicGenerationResponse:
    """Generate background music using AI"""
    try:
        logger.info(
            "Generating music",
            user_id=current_user.get("id"),
            style=request.style,
            duration=request.duration_seconds,
            platform=request.platform,
        )

        suno_client = SunoClient()
        await suno_client.initialize()

        result = await suno_client.generate_music(
            prompt=request.prompt,
            style=request.style,
            duration_seconds=request.duration_seconds,
            instrumental=request.instrumental,
            mood=request.mood,
            platform=request.platform,
            custom_lyrics=request.custom_lyrics,
            tempo=request.tempo,
        )

        await suno_client.shutdown()
        return MusicGenerationResponse(**result)

    except Exception as e:
        logger.error("Music generation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Music generation failed")


@router.post("/variations")
async def generate_variations(
    request: MusicVariationRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate variations of existing music"""
    try:
        logger.info(
            "Generating music variations",
            user_id=current_user.get("id"),
            base_music_id=request.base_music_id,
            count=request.variation_count,
        )

        suno_client = SunoClient()
        await suno_client.initialize()

        result = await suno_client.generate_variations(
            base_music_id=request.base_music_id,
            variation_count=request.variation_count,
            variation_strength=request.variation_strength,
        )

        await suno_client.shutdown()
        return result

    except Exception as e:
        logger.error("Music variation generation failed", error=str(e))
        raise HTTPException(
            status_code=500, detail="Music variation generation failed"
        )


@router.post("/extend")
async def extend_music(
    request: MusicExtensionRequest,
    current_user: dict = Depends(get_current_user),
):
    """Extend existing music to longer duration"""
    try:
        logger.info(
            "Extending music",
            user_id=current_user.get("id"),
            music_id=request.music_id,
            additional_duration=request.additional_duration,
        )

        suno_client = SunoClient()
        await suno_client.initialize()

        result = await suno_client.extend_music(
            music_id=request.music_id,
            additional_duration=request.additional_duration,
            maintain_style=request.maintain_style,
        )

        await suno_client.shutdown()
        return result

    except Exception as e:
        logger.error("Music extension failed", error=str(e))
        raise HTTPException(status_code=500, detail="Music extension failed")


@router.get("/supported-styles")
async def get_supported_styles():
    """Get list of supported music styles and platforms"""
    suno_client = SunoClient()
    return suno_client.get_supported_styles()


@router.get("/platform-specs")
async def get_platform_specifications():
    """Get platform-specific audio requirements"""
    return {
        "platforms": {
            "tiktok": {
                "duration_range": [15, 60],
                "optimal_duration": 30,
                "audio_format": "mp3",
                "sample_rate": 44100,
                "bitrate": "128k",
                "volume_level": "normalized",
                "fade_in_out": True,
            },
            "youtube": {
                "duration_range": [30, 300],
                "optimal_duration": 180,
                "audio_format": "mp3",
                "sample_rate": 44100,
                "bitrate": "320k",
                "volume_level": "normalized",
                "fade_in_out": False,
            },
            "instagram": {
                "duration_range": [15, 90],
                "optimal_duration": 60,
                "audio_format": "mp3",
                "sample_rate": 44100,
                "bitrate": "256k",
                "volume_level": "normalized",
                "fade_in_out": True,
            },
            "podcast": {
                "duration_range": [60, 600],
                "optimal_duration": 300,
                "audio_format": "mp3",
                "sample_rate": 44100,
                "bitrate": "320k",
                "volume_level": "consistent",
                "fade_in_out": False,
            },
        }
    }
