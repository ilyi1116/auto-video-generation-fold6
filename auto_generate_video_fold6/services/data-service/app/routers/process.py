from typing import Any, Dict

import structlog
from app.audio_validator import audio_validator
from app.auth import get_current_user
from app.celery_tasks import start_preprocessing_task
from app.database import database, processing_jobs, voice_files
from app.schemas import JobStatus, JobType, ProcessingJobCreate, ProcessingResponse
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = structlog.get_logger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.post("/process/{file_id}", response_model=ProcessingResponse)
async def start_processing(
    file_id: int, job_type: JobType, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Start processing job for uploaded file"""

    user_id = await get_current_user(credentials.credentials)

    # Check if file exists and belongs to user
    query = voice_files.select().where(
        (voice_files.c.id == file_id) & (voice_files.c.user_id == user_id)
    )
    file_record = await database.fetch_one(query)

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    if file_record.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"File is not ready for processing. Current status: {file_record.status}",
        )

    # Check for existing processing job
    existing_job_query = processing_jobs.select().where(
        (processing_jobs.c.voice_file_id == file_id)
        & (processing_jobs.c.job_type == job_type)
        & (processing_jobs.c.status.in_(["pending", "running"]))
    )
    existing_job = await database.fetch_one(existing_job_query)

    if existing_job:
        return ProcessingResponse(
            message="Processing job already exists",
            job_id=existing_job.id,
            status=JobStatus(existing_job.status),
        )

    try:
        # Create processing job record
        job_data = ProcessingJobCreate(user_id=user_id, voice_file_id=file_id, job_type=job_type)

        insert_query = processing_jobs.insert().values(**job_data.dict())
        job_id = await database.execute(insert_query)

        # Start appropriate processing task
        if job_type == JobType.PREPROCESSING:
            # Get preprocessing parameters
            metadata = file_record.metadata or {}
            preprocessing_params = await audio_validator.get_optimal_preprocessing_params(metadata)

            # Start Celery task
            task = start_preprocessing_task.delay(
                job_id=job_id,
                file_id=file_id,
                s3_key=file_record.s3_key,
                preprocessing_params=preprocessing_params,
            )

            # Update job with task ID
            update_query = (
                processing_jobs.update()
                .where(processing_jobs.c.id == job_id)
                .values(celery_task_id=task.id, status="running")
            )
            await database.execute(update_query)

            logger.info(
                "Preprocessing job started",
                user_id=user_id,
                job_id=job_id,
                file_id=file_id,
                task_id=task.id,
            )

        elif job_type == JobType.TRAINING:
            # Training logic will be implemented in Phase 3
            raise HTTPException(status_code=501, detail="Training jobs not yet implemented")

        elif job_type == JobType.INFERENCE:
            # Inference logic will be implemented in Phase 2
            raise HTTPException(status_code=501, detail="Inference jobs not yet implemented")

        return ProcessingResponse(
            message=f"{job_type.value} job started successfully",
            job_id=job_id,
            status=JobStatus.RUNNING,
        )

    except Exception as e:
        logger.error(
            "Failed to start processing job",
            user_id=user_id,
            file_id=file_id,
            job_type=job_type,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail="Failed to start processing job")


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Get processing job status"""

    user_id = await get_current_user(credentials.credentials)

    query = processing_jobs.select().where(
        (processing_jobs.c.id == job_id) & (processing_jobs.c.user_id == user_id)
    )
    job = await database.fetch_one(query)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return dict(job)


@router.get("/jobs")
async def list_user_jobs(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    skip: int = 0,
    limit: int = 10,
    job_type: JobType = None,
    status: JobStatus = None,
):
    """List user's processing jobs"""

    user_id = await get_current_user(credentials.credentials)

    query = processing_jobs.select().where(processing_jobs.c.user_id == user_id)

    if job_type:
        query = query.where(processing_jobs.c.job_type == job_type)

    if status:
        query = query.where(processing_jobs.c.status == status)

    query = query.offset(skip).limit(limit).order_by(processing_jobs.c.created_at.desc())

    jobs = await database.fetch_all(query)

    return {"jobs": [dict(job) for job in jobs], "total": len(jobs), "skip": skip, "limit": limit}


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Cancel processing job"""

    user_id = await get_current_user(credentials.credentials)

    # Check if job exists and belongs to user
    query = processing_jobs.select().where(
        (processing_jobs.c.id == job_id) & (processing_jobs.c.user_id == user_id)
    )
    job = await database.fetch_one(query)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job with status: {job.status}")

    # Cancel Celery task if it exists
    if job.celery_task_id:
        from app.celery_app import app as celery_app

        celery_app.control.revoke(job.celery_task_id, terminate=True)

    # Update job status
    update_query = (
        processing_jobs.update()
        .where(processing_jobs.c.id == job_id)
        .values(status="failed", error_message="Job cancelled by user")
    )
    await database.execute(update_query)

    logger.info(
        "Processing job cancelled", user_id=user_id, job_id=job_id, task_id=job.celery_task_id
    )

    return {"message": "Job cancelled successfully"}
