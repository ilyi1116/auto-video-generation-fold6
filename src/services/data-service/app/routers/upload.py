import json
import uuid
from typing import Optional

import structlog
from app.audio_validator import audio_validator
from app.auth import get_current_user
from app.database import database, voice_files
from app.schemas import FileValidationError, UploadResponse, VoiceFileCreate
from app.storage import local_storage, s3_storage
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = structlog.get_logger(__name__)
router = APIRouter()
security = HTTPBearer()


@router.post("/upload", response_model=UploadResponse)
async def upload_voice_file(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Upload and validate voice file"""

    # Get current user (verify JWT token)
    user_id = await get_current_user(credentials.credentials)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Generate unique filename
    file_extension = (
        file.filename.split(".")[-1] if "." in file.filename else ""
    )
    unique_filename = f"{uuid.uuid4()}.{file_extension}"

    try:
        # Save file temporarily
        temp_file_path = await local_storage.save_upload(
            file.file, unique_filename
        )

        logger.info(
            "File upload started",
            user_id=user_id,
            original_filename=file.filename,
            unique_filename=unique_filename,
            content_type=file.content_type,
        )

        # Validate file
        try:
            metadata = await audio_validator.validate_file_upload(
                temp_file_path, file.filename
            )
        except FileValidationError as e:
            # Clean up temp file
            await local_storage.delete_file(temp_file_path)

            logger.warning(
                "File validation failed",
                user_id=user_id,
                filename=file.filename,
                error=e.error,
                details=e.details,
            )

            raise HTTPException(
                status_code=400,
                detail=f"File validation failed: {e.error}",
                headers={"X-Validation-Details": json.dumps(e.details)},
            )

        # Create S3 key
        s3_key = f"users/{user_id}/voice-files/{unique_filename}"

        # Upload to S3
        try:
            await s3_storage.upload_file(temp_file_path, s3_key)
        except Exception as e:
            # Clean up temp file
            await local_storage.delete_file(temp_file_path)

            logger.error(
                "S3 upload failed",
                user_id=user_id,
                filename=file.filename,
                error=str(e),
            )

            raise HTTPException(
                status_code=500, detail="Failed to upload file to storage"
            )

        # Save file record to database
        file_data = VoiceFileCreate(
            user_id=user_id,
            filename=unique_filename,
            original_filename=file.filename,
            file_path=temp_file_path,
            s3_key=s3_key,
            file_size=metadata["file_size"],
            mime_type=metadata["mime_type"],
            duration=metadata.get("duration"),
            sample_rate=metadata.get("sample_rate"),
            channels=metadata.get("channels"),
            metadata=metadata,
        )

        query = voice_files.insert().values(**file_data.dict())
        file_id = await database.execute(query)

        # Clean up temp file
        await local_storage.delete_file(temp_file_path)

        logger.info(
            "File upload completed successfully",
            user_id=user_id,
            file_id=file_id,
            filename=file.filename,
            s3_key=s3_key,
            duration=metadata.get("duration"),
        )

        return UploadResponse(
            message="File uploaded successfully",
            file_id=file_id,
            filename=file.filename,
            size=metadata["file_size"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during file upload",
            user_id=user_id,
            filename=file.filename,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail="Internal server error during file upload"
        )


@router.get("/files")
async def list_user_files(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    skip: int = 0,
    limit: int = 10,
):
    """List user's uploaded files"""

    user_id = await get_current_user(credentials.credentials)

    query = (
        voice_files.select()
        .where(voice_files.c.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .order_by(voice_files.c.created_at.desc())
    )

    files = await database.fetch_all(query)

    return {
        "files": [dict(file) for file in files],
        "total": len(files),
        "skip": skip,
        "limit": limit,
    }


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int, credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete user's uploaded file"""

    user_id = await get_current_user(credentials.credentials)

    # Check if file exists and belongs to user
    query = voice_files.select().where(
        (voice_files.c.id == file_id) & (voice_files.c.user_id == user_id)
    )
    file_record = await database.fetch_one(query)

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete from S3
    if file_record.s3_key:
        await s3_storage.delete_file(file_record.s3_key)

    # Delete local file if it exists
    if file_record.file_path and local_storage.file_exists(
        file_record.file_path
    ):
        await local_storage.delete_file(file_record.file_path)

    # Delete from database
    delete_query = voice_files.delete().where(voice_files.c.id == file_id)
    await database.execute(delete_query)

    logger.info(
        "File deleted successfully",
        user_id=user_id,
        file_id=file_id,
        filename=file_record.filename,
    )

    return {"message": "File deleted successfully"}
