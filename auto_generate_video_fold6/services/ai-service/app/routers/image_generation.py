from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..services.image_generator import ImageGenerator

router = APIRouter()
logger = structlog.get_logger()


class ImageGenerationRequest(BaseModel):
    prompt: str
    style: str = "modern"  # modern, vintage, minimalist, artistic, photorealistic
    aspect_ratio: str = "9:16"  # 9:16, 16:9, 1:1, 4:3
    resolution: str = "1080p"  # 720p, 1080p, 4k
    negative_prompt: Optional[str] = None
    seed: Optional[int] = None
    guidance_scale: float = 7.5
    num_inference_steps: int = 50


class ImageGenerationResponse(BaseModel):
    image_id: str
    image_url: str
    prompt: str
    style: str
    aspect_ratio: str
    resolution: str
    generation_time: float
    status: str


class ImageVariationRequest(BaseModel):
    base_image_url: str
    variation_prompt: Optional[str] = None
    strength: float = 0.7
    num_variations: int = 3


@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(
    request: ImageGenerationRequest, current_user: dict = Depends(get_current_user)
) -> ImageGenerationResponse:
    """Generate image based on text prompt"""
    try:
        logger.info(
            "Generating image",
            user_id=current_user.get("id"),
            prompt=request.prompt[:100],  # Log first 100 chars
            style=request.style,
            aspect_ratio=request.aspect_ratio,
        )

        image_generator = ImageGenerator()
        result = await image_generator.generate_image(
            prompt=request.prompt,
            style=request.style,
            aspect_ratio=request.aspect_ratio,
            resolution=request.resolution,
            negative_prompt=request.negative_prompt,
            seed=request.seed,
            guidance_scale=request.guidance_scale,
            num_inference_steps=request.num_inference_steps,
        )

        return ImageGenerationResponse(**result)

    except Exception as e:
        logger.error("Image generation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Image generation failed")


@router.post("/generate-variations")
async def generate_variations(
    request: ImageVariationRequest, current_user: dict = Depends(get_current_user)
):
    """Generate variations of an existing image"""
    try:
        logger.info(
            "Generating image variations",
            user_id=current_user.get("id"),
            base_image=request.base_image_url,
            num_variations=request.num_variations,
        )

        image_generator = ImageGenerator()
        result = await image_generator.generate_variations(
            base_image_url=request.base_image_url,
            variation_prompt=request.variation_prompt,
            strength=request.strength,
            num_variations=request.num_variations,
        )

        return result

    except Exception as e:
        logger.error("Image variation generation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Image variation generation failed")


@router.post("/upscale")
async def upscale_image(
    image_url: str, scale_factor: int = 2, current_user: dict = Depends(get_current_user)
):
    """Upscale image resolution"""
    try:
        logger.info(
            "Upscaling image",
            user_id=current_user.get("id"),
            image_url=image_url,
            scale_factor=scale_factor,
        )

        image_generator = ImageGenerator()
        result = await image_generator.upscale_image(image_url=image_url, scale_factor=scale_factor)

        return result

    except Exception as e:
        logger.error("Image upscaling failed", error=str(e))
        raise HTTPException(status_code=500, detail="Image upscaling failed")


@router.post("/enhance")
async def enhance_image(
    image_url: str,
    enhancement_type: str = "general",  # general, face, artifact_removal
    current_user: dict = Depends(get_current_user),
):
    """Enhance image quality using AI"""
    try:
        logger.info(
            "Enhancing image",
            user_id=current_user.get("id"),
            image_url=image_url,
            enhancement_type=enhancement_type,
        )

        image_generator = ImageGenerator()
        result = await image_generator.enhance_image(
            image_url=image_url, enhancement_type=enhancement_type
        )

        return result

    except Exception as e:
        logger.error("Image enhancement failed", error=str(e))
        raise HTTPException(status_code=500, detail="Image enhancement failed")


@router.get("/supported-styles")
async def get_supported_styles():
    """Get list of supported image generation styles"""
    return {
        "styles": [
            {"name": "modern", "description": "Clean, contemporary aesthetic"},
            {"name": "vintage", "description": "Retro and nostalgic feel"},
            {"name": "minimalist", "description": "Simple and uncluttered"},
            {"name": "artistic", "description": "Creative and expressive"},
            {"name": "photorealistic", "description": "Realistic photography style"},
            {"name": "cartoon", "description": "Animated cartoon style"},
            {"name": "anime", "description": "Japanese animation style"},
            {"name": "cyberpunk", "description": "Futuristic sci-fi aesthetic"},
        ],
        "aspect_ratios": [
            {"ratio": "9:16", "description": "Vertical (Mobile/TikTok)"},
            {"ratio": "16:9", "description": "Horizontal (YouTube)"},
            {"ratio": "1:1", "description": "Square (Instagram)"},
            {"ratio": "4:3", "description": "Traditional (Facebook)"},
        ],
        "resolutions": [
            {"name": "720p", "dimensions": "1280x720"},
            {"name": "1080p", "dimensions": "1920x1080"},
            {"name": "4k", "dimensions": "3840x2160"},
        ],
    }
