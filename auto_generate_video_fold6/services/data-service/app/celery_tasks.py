import asyncio
import os
from datetime import datetime
from typing import Any, Dict

import librosa
import soundfile as sf
import structlog
from app.celery_app import app
from app.config import settings
from app.storage import local_storage, s3_storage

logger = structlog.get_logger(__name__)


@app.task(bind=True)
def start_preprocessing_task(
    self, job_id: int, file_id: int, s3_key: str, preprocessing_params: Dict[str, Any]
):
    """Celery task for audio preprocessing"""

    # Update job status to running
    asyncio.run(update_job_status(job_id, "running", 0))

    try:
        logger.info("Starting audio preprocessing", job_id=job_id, file_id=file_id, s3_key=s3_key)

        # Download file from S3
        local_filename = f"temp_{job_id}_{file_id}.wav"
        local_path = f"/tmp/{local_filename}"

        asyncio.run(s3_storage.download_file(s3_key, local_path))
        asyncio.run(update_job_status(job_id, "running", 20))

        # Load audio
        y, sr = librosa.load(local_path, sr=None)
        asyncio.run(update_job_status(job_id, "running", 40))

        # Apply preprocessing steps
        processed_audio = y
        target_sr = preprocessing_params.get("target_sample_rate", settings.target_sample_rate)
        target_channels = preprocessing_params.get("target_channels", settings.target_channels)
        steps = preprocessing_params.get("preprocessing_steps", [])

        step_progress = 40
        progress_per_step = 40 // max(len(steps), 1)

        for step in steps:
            if step == "resample" and sr != target_sr:
                processed_audio = librosa.resample(processed_audio, orig_sr=sr, target_sr=target_sr)
                sr = target_sr
                logger.info("Audio resampled", job_id=job_id, target_sr=target_sr)

            elif step == "channel_conversion":
                if processed_audio.ndim > 1 and target_channels == 1:
                    processed_audio = librosa.to_mono(processed_audio)
                logger.info("Converted to mono", job_id=job_id)

            elif step == "silence_removal":
                # Trim silence from beginning and end
                processed_audio, _ = librosa.effects.trim(processed_audio, top_db=20)
                logger.info("Silence trimmed", job_id=job_id)

            elif step == "normalize":
                # Normalize audio
                processed_audio = librosa.util.normalize(processed_audio)
                logger.info("Audio normalized", job_id=job_id)

            step_progress += progress_per_step
            asyncio.run(update_job_status(job_id, "running", step_progress))

        # Save processed audio
        processed_filename = f"processed_{job_id}_{file_id}.wav"
        processed_path = f"/tmp/{processed_filename}"
        sf.write(processed_path, processed_audio, sr)

        # Upload processed file to S3
        processed_s3_key = s3_key.replace(".wav", "_processed.wav").replace(
            ".mp3", "_processed.wav"
        )
        processed_s3_key = processed_s3_key.replace(
            os.path.splitext(processed_s3_key)[1], "_processed.wav"
        )

        asyncio.run(s3_storage.upload_file(processed_path, processed_s3_key))
        asyncio.run(update_job_status(job_id, "running", 90))

        # Cleanup temp files
        os.remove(local_path)
        os.remove(processed_path)

        # Prepare result data
        result_data = {
            "processed_s3_key": processed_s3_key,
            "original_sample_rate": sr,
            "processed_sample_rate": target_sr,
            "processing_steps_applied": steps,
            "processed_duration": len(processed_audio) / sr,
            "processing_completed_at": datetime.utcnow().isoformat(),
        }

        # Update job as completed
        asyncio.run(update_job_status(job_id, "completed", 100, result_data))

        logger.info(
            "Audio preprocessing completed successfully",
            job_id=job_id,
            file_id=file_id,
            processed_s3_key=processed_s3_key,
        )

        return result_data

    except Exception as e:
        error_message = str(e)
        logger.error(
            "Audio preprocessing failed", job_id=job_id, file_id=file_id, error=error_message
        )

        # Update job as failed
        asyncio.run(update_job_status(job_id, "failed", 0, None, error_message))

        # Cleanup temp files if they exist
        try:
            if "local_path" in locals() and os.path.exists(local_path):
                os.remove(local_path)
            if "processed_path" in locals() and os.path.exists(processed_path):
                os.remove(processed_path)
        except:
            pass

        raise


async def update_job_status(
    job_id: int,
    status: str,
    progress: int,
    result_data: Dict[str, Any] = None,
    error_message: str = None,
):
    """Update processing job status in database"""
    try:
        # Import here to avoid circular imports
        from app.database import database, processing_jobs

        update_data = {"status": status, "progress": progress, "updated_at": datetime.utcnow()}

        if status == "running" and progress == 0:
            update_data["started_at"] = datetime.utcnow()

        if status in ["completed", "failed"]:
            update_data["completed_at"] = datetime.utcnow()

        if result_data:
            update_data["result_data"] = result_data

        if error_message:
            update_data["error_message"] = error_message

        query = processing_jobs.update().where(processing_jobs.c.id == job_id).values(**update_data)

        await database.execute(query)

    except Exception as e:
        logger.error("Failed to update job status", job_id=job_id, status=status, error=str(e))
