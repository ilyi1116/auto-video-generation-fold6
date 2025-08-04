from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..services.text_generator import TextGenerator

router = APIRouter()
logger = structlog.get_logger()


class ScriptGenerationRequest(BaseModel):
    topic: str
    style: str = "engaging"  # engaging, informative, humorous, professional
    duration_seconds: int = 60
    target_audience: str = "general"
    keywords: Optional[List[str]] = None
    tone: str = "casual"  # casual, formal, enthusiastic, educational


class ScriptGenerationResponse(BaseModel):
    script_id: str
    content: str
    word_count: int
    estimated_duration: int
    style: str
    status: str


class TitleGenerationRequest(BaseModel):
    script_content: str
    style: str = "catchy"
    max_length: int = 100
    target_keywords: Optional[List[str]] = None


class TitleGenerationResponse(BaseModel):
    titles: List[str]
    recommended_title: str


@router.post("/generate-script", response_model=ScriptGenerationResponse)
async def generate_script(
    request: ScriptGenerationRequest,
    current_user: dict = Depends(get_current_user),
) -> ScriptGenerationResponse:
    """Generate script content based on topic and parameters"""
    try:
        logger.info(
            "Generating script",
            user_id=current_user.get("id"),
            topic=request.topic,
            style=request.style,
            duration=request.duration_seconds,
        )

        text_generator = TextGenerator()
        result = await text_generator.generate_script(
            topic=request.topic,
            style=request.style,
            duration_seconds=request.duration_seconds,
            target_audience=request.target_audience,
            keywords=request.keywords or [],
            tone=request.tone,
        )

        return ScriptGenerationResponse(**result)

    except Exception as e:
        logger.error("Script generation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Script generation failed")


@router.post("/generate-titles", response_model=TitleGenerationResponse)
async def generate_titles(
    request: TitleGenerationRequest,
    current_user: dict = Depends(get_current_user),
) -> TitleGenerationResponse:
    """Generate catchy titles based on script content"""
    try:
        logger.info(
            "Generating titles",
            user_id=current_user.get("id"),
            style=request.style,
        )

        text_generator = TextGenerator()
        result = await text_generator.generate_titles(
            script_content=request.script_content,
            style=request.style,
            max_length=request.max_length,
            target_keywords=request.target_keywords or [],
        )

        return TitleGenerationResponse(**result)

    except Exception as e:
        logger.error("Title generation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Title generation failed")


@router.post("/optimize-script")
async def optimize_script(
    script_content: str,
    target_duration: int,
    current_user: dict = Depends(get_current_user),
):
    """Optimize script for specific duration and engagement"""
    try:
        logger.info(
            "Optimizing script",
            user_id=current_user.get("id"),
            target_duration=target_duration,
        )

        text_generator = TextGenerator()
        result = await text_generator.optimize_script(
            script_content=script_content, target_duration=target_duration
        )

        return result

    except Exception as e:
        logger.error("Script optimization failed", error=str(e))
        raise HTTPException(
            status_code=500, detail="Script optimization failed"
        )


@router.get("/supported-styles")
async def get_supported_styles():
    """Get list of supported text generation styles"""
    return {
        "script_styles": [
            {
                "name": "engaging",
                "description": "Engaging and captivating content",
            },
            {
                "name": "informative",
                "description": "Educational and fact-based content",
            },
            {
                "name": "humorous",
                "description": "Funny and entertaining content",
            },
            {
                "name": "professional",
                "description": "Formal and business-oriented content",
            },
        ],
        "title_styles": [
            {"name": "catchy", "description": "Attention-grabbing titles"},
            {
                "name": "descriptive",
                "description": "Clear and informative titles",
            },
            {"name": "clickbait", "description": "High-engagement titles"},
            {
                "name": "professional",
                "description": "Formal and straightforward titles",
            },
        ],
    }
