import io
from datetime import datetime
from typing import List, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..auth import get_current_user
from ..database import database, synthesis_jobs, voice_models
from ..services.synthesis_engine import synthesis_engine
from ..storage import s3_storage

logger = structlog.get_logger()
router = APIRouter()


class SynthesisRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="Text to synthesize")
    model_id: int = Field(..., description="Voice model ID to use")
    speed: Optional[float] = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    pitch: Optional[float] = Field(default=1.0, ge=0.5, le=2.0, description="Speech pitch")
    volume: Optional[float] = Field(default=1.0, ge=0.1, le=2.0, description="Speech volume")
    emotion: Optional[str] = Field(default="neutral", description="Emotion style")
    return_audio: bool = Field(default=False, description="Return audio data directly")


class BatchSynthesisRequest(BaseModel):
    texts: List[str] = Field(..., max_items=10, description="List of texts to synthesize")
    model_id: int = Field(..., description="Voice model ID to use")
    speed: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)
    pitch: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)
    volume: Optional[float] = Field(default=1.0, ge=0.1, le=2.0)
    emotion: Optional[str] = Field(default="neutral")


class SynthesisResponse(BaseModel):
    job_id: int
    status: str
    text: str
    model_id: int
    audio_url: Optional[str] = None
    audio_duration: Optional[float] = None
    processing_time: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


@router.post("/synthesize", response_model=SynthesisResponse)
async def synthesize_voice(
    request: SynthesisRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Synthesize voice from text"""

    # Validate model access
    model_query = voice_models.select().where(
        (voice_models.c.id == request.model_id)
        & (voice_models.c.user_id == current_user["id"])
        & (voice_models.c.status == "ready")
    )
    model_result = await database.fetch_one(model_query)

    if not model_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice model not found or not ready",
        )

    # Create synthesis job record
    job_insert = synthesis_jobs.insert().values(
        user_id=current_user["id"],
        model_id=request.model_id,
        text=request.text,
        status="pending",
        synthesis_params={
            "speed": request.speed,
            "pitch": request.pitch,
            "volume": request.volume,
            "emotion": request.emotion,
        },
    )
    job_id = await database.execute(job_insert)

    logger.info(
        "Synthesis job created",
        job_id=job_id,
        user_id=current_user["id"],
        text_length=len(request.text),
    )

    # If return_audio is True, process synchronously
    if request.return_audio:
        try:
            # Update job status
            await database.execute(
                synthesis_jobs.update()
                .where(synthesis_jobs.c.id == job_id)
                .values(status="processing")
            )

            # Perform synthesis
            model_config = {
                "model_path": model_result["model_path"],
                "config_data": model_result["config_data"],
            }

            synthesis_result = await synthesis_engine.synthesize_speech(
                text=request.text,
                model_id=request.model_id,
                model_config=model_config,
                synthesis_params={
                    "speed": request.speed,
                    "pitch": request.pitch,
                    "volume": request.volume,
                    "emotion": request.emotion,
                },
                user_id=current_user["id"],
            )

            # Upload audio to S3
            audio_key = f"synthesized/{current_user['id']}/{job_id}.wav"
            audio_url = await s3_storage.upload_audio(synthesis_result["audio_data"], audio_key)

            # Update job with results
            await database.execute(
                synthesis_jobs.update()
                .where(synthesis_jobs.c.id == job_id)
                .values(
                    status="completed",
                    audio_url=audio_url,
                    audio_duration=synthesis_result["audio_duration"],
                    processing_time=synthesis_result["processing_time"],
                    completed_at=datetime.utcnow(),
                )
            )

            return SynthesisResponse(
                job_id=job_id,
                status="completed",
                text=request.text,
                model_id=request.model_id,
                audio_url=audio_url,
                audio_duration=synthesis_result["audio_duration"],
                processing_time=synthesis_result["processing_time"],
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )

        except Exception as e:
            # Update job with error
            await database.execute(
                synthesis_jobs.update()
                .where(synthesis_jobs.c.id == job_id)
                .values(
                    status="failed",
                    error_message=str(e),
                    completed_at=datetime.utcnow(),
                )
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Synthesis failed: {str(e)}",
            )

    else:
        # Process asynchronously
        background_tasks.add_task(
            process_synthesis_job,
            job_id,
            request.model_id,
            model_result,
            request,
            current_user["id"],
        )

        return SynthesisResponse(
            job_id=job_id,
            status="pending",
            text=request.text,
            model_id=request.model_id,
            created_at=datetime.utcnow(),
        )


@router.post("/synthesize/batch")
async def batch_synthesize_voice(
    request: BatchSynthesisRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Batch synthesize multiple texts"""

    # Validate model access
    model_query = voice_models.select().where(
        (voice_models.c.id == request.model_id)
        & (voice_models.c.user_id == current_user["id"])
        & (voice_models.c.status == "ready")
    )
    model_result = await database.fetch_one(model_query)

    if not model_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice model not found or not ready",
        )

    # Create synthesis jobs for each text
    job_ids = []
    for text in request.texts:
        job_insert = synthesis_jobs.insert().values(
            user_id=current_user["id"],
            model_id=request.model_id,
            text=text,
            status="pending",
            synthesis_params={
                "speed": request.speed,
                "pitch": request.pitch,
                "volume": request.volume,
                "emotion": request.emotion,
            },
        )
        job_id = await database.execute(job_insert)
        job_ids.append(job_id)

    # Process batch asynchronously
    background_tasks.add_task(
        process_batch_synthesis,
        job_ids,
        request.model_id,
        model_result,
        request,
        current_user["id"],
    )

    return {
        "job_ids": job_ids,
        "status": "pending",
        "batch_size": len(request.texts),
    }


@router.get("/synthesize/audio/{job_id}")
async def get_synthesis_audio(job_id: int, current_user: dict = Depends(get_current_user)):
    """Get synthesized audio file"""

    # Get job details
    job_query = synthesis_jobs.select().where(
        (synthesis_jobs.c.id == job_id) & (synthesis_jobs.c.user_id == current_user["id"])
    )
    job = await database.fetch_one(job_query)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Synthesis job not found",
        )

    if job["status"] != "completed" or not job["audio_url"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio not ready or synthesis failed",
        )

    # Stream audio file
    try:
        # Extract S3 key from URL
        job["audio_url"].split("/")[-1]

        # For demonstration, return mock audio
        mock_audio = b"RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00" + b"\x00" * 1000

        return StreamingResponse(
            io.BytesIO(mock_audio),
            media_type="audio/wav",
            headers={"Content-Disposition": (f"attachment; filename=synthesis_{job_id}.wav")},
        )

    except Exception as e:
        logger.error("Failed to stream audio", job_id=job_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audio",
        )


@router.get("/jobs", response_model=List[SynthesisResponse])
async def get_synthesis_jobs(
    current_user: dict = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
):
    """Get user's synthesis jobs"""

    query = (
        synthesis_jobs.select()
        .where(synthesis_jobs.c.user_id == current_user["id"])
        .order_by(synthesis_jobs.c.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    jobs = await database.fetch_all(query)

    return [
        SynthesisResponse(
            job_id=job["id"],
            status=job["status"],
            text=job["text"],
            model_id=job["model_id"],
            audio_url=job["audio_url"],
            audio_duration=job["audio_duration"],
            processing_time=job["processing_time"],
            created_at=job["created_at"],
            completed_at=job["completed_at"],
        )
        for job in jobs
    ]


@router.get("/jobs/{job_id}", response_model=SynthesisResponse)
async def get_synthesis_job(job_id: int, current_user: dict = Depends(get_current_user)):
    """Get synthesis job details"""

    query = synthesis_jobs.select().where(
        (synthesis_jobs.c.id == job_id) & (synthesis_jobs.c.user_id == current_user["id"])
    )

    job = await database.fetch_one(query)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Synthesis job not found",
        )

    return SynthesisResponse(
        job_id=job["id"],
        status=job["status"],
        text=job["text"],
        model_id=job["model_id"],
        audio_url=job["audio_url"],
        audio_duration=job["audio_duration"],
        processing_time=job["processing_time"],
        created_at=job["created_at"],
        completed_at=job["completed_at"],
    )


async def process_synthesis_job(
    job_id: int,
    model_id: int,
    model_result,
    request: SynthesisRequest,
    user_id: int,
):
    """Background task to process synthesis job"""
    try:
        # Update job status
        await database.execute(
            synthesis_jobs.update().where(synthesis_jobs.c.id == job_id).values(status="processing")
        )

        # Perform synthesis
        model_config = {
            "model_path": model_result["model_path"],
            "config_data": model_result["config_data"],
        }

        synthesis_result = await synthesis_engine.synthesize_speech(
            text=request.text,
            model_id=model_id,
            model_config=model_config,
            synthesis_params={
                "speed": request.speed,
                "pitch": request.pitch,
                "volume": request.volume,
                "emotion": request.emotion,
            },
            user_id=user_id,
        )

        # Upload audio to S3
        audio_key = f"synthesized/{user_id}/{job_id}.wav"
        audio_url = await s3_storage.upload_audio(synthesis_result["audio_data"], audio_key)

        # Update job with results
        await database.execute(
            synthesis_jobs.update()
            .where(synthesis_jobs.c.id == job_id)
            .values(
                status="completed",
                audio_url=audio_url,
                audio_duration=synthesis_result["audio_duration"],
                processing_time=synthesis_result["processing_time"],
                completed_at=datetime.utcnow(),
            )
        )

        logger.info("Synthesis job completed", job_id=job_id)

    except Exception as e:
        # Update job with error
        await database.execute(
            synthesis_jobs.update()
            .where(synthesis_jobs.c.id == job_id)
            .values(
                status="failed",
                error_message=str(e),
                completed_at=datetime.utcnow(),
            )
        )
        logger.error("Synthesis job failed", job_id=job_id, error=str(e))


async def process_batch_synthesis(
    job_ids: List[int],
    model_id: int,
    model_result,
    request: BatchSynthesisRequest,
    user_id: int,
):
    """Background task to process batch synthesis"""
    logger.info("Starting batch synthesis", job_ids=job_ids, batch_size=len(job_ids))

    for i, job_id in enumerate(job_ids):
        try:
            await process_synthesis_job(
                job_id,
                model_id,
                model_result,
                SynthesisRequest(
                    text=request.texts[i],
                    model_id=model_id,
                    speed=request.speed,
                    pitch=request.pitch,
                    volume=request.volume,
                    emotion=request.emotion,
                ),
                user_id,
            )
        except Exception as e:
            logger.error("Batch synthesis item failed", job_id=job_id, error=str(e))
