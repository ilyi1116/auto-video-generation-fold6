from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog

from ..auth import get_current_user
from ..database import database, voice_models, model_usage_stats
from ..services.model_manager import model_manager

logger = structlog.get_logger()
router = APIRouter()


class VoiceModelResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    model_type: str
    language: str
    status: str
    training_data_size: int
    training_duration: Optional[float] = None
    quality_score: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class ModelUsageStats(BaseModel):
    model_id: int
    synthesis_count: int
    total_characters: int
    total_audio_duration: float
    last_used_at: Optional[datetime] = None


class ModelCacheStats(BaseModel):
    cached_models: int
    max_cache_size: int
    cache_ttl: int
    model_ids: List[int]
    oldest_cache_age: float


@router.get("/models", response_model=List[VoiceModelResponse])
async def get_user_models(
    current_user: dict = Depends(get_current_user),
    status_filter: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    """Get user's voice models"""

    query = voice_models.select().where(
        voice_models.c.user_id == current_user["id"]
    )

    if status_filter:
        query = query.where(voice_models.c.status == status_filter)

    query = (
        query.order_by(voice_models.c.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    models = await database.fetch_all(query)

    return [
        VoiceModelResponse(
            id=model["id"],
            name=model["name"],
            description=model["description"],
            model_type=model["model_type"],
            language=model["language"],
            status=model["status"],
            training_data_size=model["training_data_size"],
            training_duration=model["training_duration"],
            quality_score=model["quality_score"],
            created_at=model["created_at"],
            updated_at=model["updated_at"],
        )
        for model in models
    ]


@router.get("/models/{model_id}", response_model=VoiceModelResponse)
async def get_model_details(
    model_id: int, current_user: dict = Depends(get_current_user)
):
    """Get voice model details"""

    query = voice_models.select().where(
        (voice_models.c.id == model_id)
        & (voice_models.c.user_id == current_user["id"])
    )

    model = await database.fetch_one(query)

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice model not found",
        )

    return VoiceModelResponse(
        id=model["id"],
        name=model["name"],
        description=model["description"],
        model_type=model["model_type"],
        language=model["language"],
        status=model["status"],
        training_data_size=model["training_data_size"],
        training_duration=model["training_duration"],
        quality_score=model["quality_score"],
        created_at=model["created_at"],
        updated_at=model["updated_at"],
    )


@router.post("/models/{model_id}/preload")
async def preload_model(
    model_id: int, current_user: dict = Depends(get_current_user)
):
    """Preload model into cache"""

    # Verify model ownership and readiness
    query = voice_models.select().where(
        (voice_models.c.id == model_id)
        & (voice_models.c.user_id == current_user["id"])
        & (voice_models.c.status == "ready")
    )

    model_result = await database.fetch_one(query)

    if not model_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice model not found or not ready",
        )

    try:
        # Preload the model
        model_config = {
            "model_path": model_result["model_path"],
            "config_data": model_result["config_data"],
        }

        await model_manager.preload_model(model_id, model_config)

        logger.info(
            "Model preloaded successfully",
            model_id=model_id,
            user_id=current_user["id"],
        )

        return {
            "message": "Model preloaded successfully",
            "model_id": model_id,
            "status": "cached",
        }

    except Exception as e:
        logger.error(
            "Failed to preload model", model_id=model_id, error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preload model: {str(e)}",
        )


@router.get("/models/{model_id}/usage", response_model=ModelUsageStats)
async def get_model_usage_stats(
    model_id: int, current_user: dict = Depends(get_current_user)
):
    """Get model usage statistics"""

    # Verify model ownership
    model_query = voice_models.select().where(
        (voice_models.c.id == model_id)
        & (voice_models.c.user_id == current_user["id"])
    )

    model_result = await database.fetch_one(model_query)

    if not model_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice model not found",
        )

    # Get usage stats
    stats_query = model_usage_stats.select().where(
        (model_usage_stats.c.model_id == model_id)
        & (model_usage_stats.c.user_id == current_user["id"])
    )

    stats = await database.fetch_one(stats_query)

    if not stats:
        return ModelUsageStats(
            model_id=model_id,
            synthesis_count=0,
            total_characters=0,
            total_audio_duration=0.0,
            last_used_at=None,
        )

    return ModelUsageStats(
        model_id=stats["model_id"],
        synthesis_count=stats["synthesis_count"],
        total_characters=stats["total_characters"],
        total_audio_duration=stats["total_audio_duration"],
        last_used_at=stats["last_used_at"],
    )


@router.get("/models/ready", response_model=List[VoiceModelResponse])
async def get_ready_models(current_user: dict = Depends(get_current_user)):
    """Get user's ready-to-use voice models"""

    query = (
        voice_models.select()
        .where(
            (voice_models.c.user_id == current_user["id"])
            & (voice_models.c.status == "ready")
        )
        .order_by(voice_models.c.created_at.desc())
    )

    models = await database.fetch_all(query)

    return [
        VoiceModelResponse(
            id=model["id"],
            name=model["name"],
            description=model["description"],
            model_type=model["model_type"],
            language=model["language"],
            status=model["status"],
            training_data_size=model["training_data_size"],
            training_duration=model["training_duration"],
            quality_score=model["quality_score"],
            created_at=model["created_at"],
            updated_at=model["updated_at"],
        )
        for model in models
    ]


@router.get("/cache/stats", response_model=ModelCacheStats)
async def get_cache_stats(current_user: dict = Depends(get_current_user)):
    """Get model cache statistics"""

    try:
        stats = await model_manager.get_cache_stats()

        return ModelCacheStats(
            cached_models=stats["cached_models"],
            max_cache_size=stats["max_cache_size"],
            cache_ttl=stats["cache_ttl"],
            model_ids=stats["model_ids"],
            oldest_cache_age=stats["oldest_cache_age"],
        )

    except Exception as e:
        logger.error("Failed to get cache stats", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cache statistics",
        )


@router.post("/cache/clear")
async def clear_model_cache(current_user: dict = Depends(get_current_user)):
    """Clear all models from cache (admin only)"""

    # For now, this is available to all users
    # In production, you might want to restrict this to admin users

    try:
        # Get current cache stats
        stats_before = await model_manager.get_cache_stats()

        # Clear cache by recreating the model manager
        # This is a simple approach - in production you might want a more sophisticated method
        model_manager.model_cache.clear()
        model_manager.cache_timestamps.clear()

        stats_after = await model_manager.get_cache_stats()

        logger.info(
            "Model cache cleared",
            user_id=current_user["id"],
            models_cleared=stats_before["cached_models"],
        )

        return {
            "message": "Model cache cleared successfully",
            "models_cleared": stats_before["cached_models"],
            "cache_size_before": stats_before["cached_models"],
            "cache_size_after": stats_after["cached_models"],
        }

    except Exception as e:
        logger.error("Failed to clear cache", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear model cache",
        )
