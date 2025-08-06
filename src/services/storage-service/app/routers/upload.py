import asyncio
import os
import tempfile
from typing import Dict, List, Optional

import magic
import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ..auth import get_current_user
from ..config import settings
from ..crud import FileCRUD, ProcessingJobCRUD
from ..database import get_db
from ..processors import processor_manager
from ..storage import storage_manager

router = APIRouter()
logger = structlog.get_logger()


class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    mime_type: str
    public_url: str
    status: str
    processing_job_id: Optional[str] = None


class BulkUploadResponse(BaseModel):
    uploaded_files: List[FileUploadResponse]
    failed_files: List[Dict[str, str]]
    total_files: int
    successful_uploads: int
    failed_uploads: int


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    category: str = Form("uploaded"),
    project_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    auto_process: bool = Form(True),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Upload a single file"""
    try:
        logger.info(
            "Starting file upload",
            user_id=current_user.get("id"),
            filename=file.filename,
            file_type=file_type,
            size=file.size,
        )

        # Validate file size
        if file.size > settings.max_file_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail="File size exceeds maximum allowed size of "
                f"{settings.max_file_size_mb}MB",
            )

        # Read file content
        file_content = await file.read()

        # Detect MIME type
        mime_type = magic.from_buffer(file_content, mime=True)

        # Validate file type
        if not storage_manager.validate_file_type(mime_type, file_type):
            raise HTTPException(
                status_code=400,
                detail=f"File type {mime_type} not allowed for "
                f"{file_type} files",
            )

        # Upload to storage
        file.file.seek(0)
        upload_result = await storage_manager.upload_file(
            file_data=file.file,
            filename=file.filename,
            content_type=mime_type,
            user_id=current_user.get("id"),
            file_type=file_type,
            category=category,
        )

        # Parse tags
        tag_list = []
        if tags:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Create database record
        file_data = {
            "original_filename": file.filename,
            "filename": os.path.basename(upload_result["object_key"]),
            "file_path": upload_result["object_key"],
            "file_size": upload_result["file_size"],
            "mime_type": upload_result["content_type"],
            "file_hash": upload_result["file_hash"],
            "file_type": file_type,
            "category": category,
            "storage_backend": settings.storage_backend,
            "bucket_name": settings.s3_bucket_name,
            "object_key": upload_result["object_key"],
            "public_url": upload_result["public_url"],
            "project_id": project_id,
            "description": description,
            "tags": tag_list,
            "is_processed": False,
            "processing_status": "pending" if auto_process else "skipped",
        }

        stored_file = await FileCRUD.create_file(
            db, current_user.get("id"), file_data
        )

        # Queue processing job if auto_process is enabled
        processing_job_id = None
        if auto_process and file_type in ["image", "audio", "video"]:
            job_data = {
                "file_id": stored_file.id,
                "user_id": current_user.get("id"),
                "job_type": "process",
                "input_parameters": {
                    "file_type": file_type,
                    "auto_thumbnail": True,
                    "optimize": True,
                },
                "priority": 5,
            }

            processing_job = await ProcessingJobCRUD.create_job(db, job_data)
            processing_job_id = processing_job.id

            # Trigger async processing
            asyncio.create_task(
                process_file_async(stored_file.id, processing_job.id)
            )

        response = FileUploadResponse(
            file_id=stored_file.id,
            filename=stored_file.filename,
            original_filename=stored_file.original_filename,
            file_size=stored_file.file_size,
            file_type=stored_file.file_type,
            mime_type=stored_file.mime_type,
            public_url=stored_file.public_url,
            status="uploaded",
            processing_job_id=processing_job_id,
        )

        logger.info(
            "File upload completed",
            user_id=current_user.get("id"),
            file_id=stored_file.id,
            processing_job_id=processing_job_id,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "File upload failed", error=str(e), filename=file.filename
        )
        raise HTTPException(status_code=500, detail="File upload failed")


@router.post("/upload-multiple", response_model=BulkUploadResponse)
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    file_type: str = Form(...),
    category: str = Form("uploaded"),
    project_id: Optional[str] = Form(None),
    auto_process: bool = Form(True),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Upload multiple files"""
    try:
        if len(files) > settings.max_upload_files:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files. Maximum allowed: {settings.max_upload_files}",
            )

        uploaded_files = []
        failed_files = []

        for file in files:
            try:
                # Process each file individually
                result = await upload_file(
                    file=file,
                    file_type=file_type,
                    category=category,
                    project_id=project_id,
                    auto_process=auto_process,
                    current_user=current_user,
                    db=db,
                )
                uploaded_files.append(result)

            except Exception as e:
                failed_files.append(
                    {"filename": file.filename, "error": str(e)}
                )

        return BulkUploadResponse(
            uploaded_files=uploaded_files,
            failed_files=failed_files,
            total_files=len(files),
            successful_uploads=len(uploaded_files),
            failed_uploads=len(failed_files),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Bulk upload failed", error=str(e))
        raise HTTPException(status_code=500, detail="Bulk upload failed")


@router.post("/upload-from-url")
async def upload_from_url(
    url: str = Form(...),
    filename: Optional[str] = Form(None),
    file_type: str = Form(...),
    category: str = Form("downloaded"),
    project_id: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Upload file from URL"""
    try:
        from urllib.parse import urlparse

        import httpx

        logger.info(
            "Uploading file from URL", url=url, user_id=current_user.get("id")
        )

        # Download file from URL
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=60.0)
            response.raise_for_status()

            file_content = response.content

            # Determine filename
            if not filename:
                parsed_url = urlparse(url)
                filename = (
                    os.path.basename(parsed_url.path) or "downloaded_file"
                )

            # Detect MIME type
            mime_type = magic.from_buffer(file_content, mime=True)

            # Validate file type
            if not storage_manager.validate_file_type(mime_type, file_type):
                raise HTTPException(
                    status_code=400,
                    detail=f"File type {mime_type} not allowed for "
                    f"{file_type} files",
                )

            # Validate file size
            if len(file_content) > settings.max_file_size_mb * 1024 * 1024:
                raise HTTPException(
                    status_code=413,
                    detail="File size exceeds maximum allowed size",
                )

            # Create temporary file-like object
            import io

            file_obj = io.BytesIO(file_content)

            # Upload to storage
            upload_result = await storage_manager.upload_file(
                file_data=file_obj,
                filename=filename,
                content_type=mime_type,
                user_id=current_user.get("id"),
                file_type=file_type,
                category=category,
            )

            # Create database record
            file_data = {
                "original_filename": filename,
                "filename": os.path.basename(upload_result["object_key"]),
                "file_path": upload_result["object_key"],
                "file_size": upload_result["file_size"],
                "mime_type": upload_result["content_type"],
                "file_hash": upload_result["file_hash"],
                "file_type": file_type,
                "category": category,
                "storage_backend": settings.storage_backend,
                "bucket_name": settings.s3_bucket_name,
                "object_key": upload_result["object_key"],
                "public_url": upload_result["public_url"],
                "project_id": project_id,
                "description": f"Downloaded from: {url}",
                "is_processed": False,
                "processing_status": "pending",
            }

            stored_file = await FileCRUD.create_file(
                db, current_user.get("id"), file_data
            )

            return FileUploadResponse(
                file_id=stored_file.id,
                filename=stored_file.filename,
                original_filename=stored_file.original_filename,
                file_size=stored_file.file_size,
                file_type=stored_file.file_type,
                mime_type=stored_file.mime_type,
                public_url=stored_file.public_url,
                status="uploaded",
            )

    except httpx.RequestError as e:
        logger.error("Failed to download file from URL", error=str(e), url=url)
        raise HTTPException(
            status_code=400, detail="Failed to download file from URL"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("URL upload failed", error=str(e), url=url)
        raise HTTPException(status_code=500, detail="URL upload failed")


async def process_file_async(file_id: str, job_id: str):
    """Async file processing task"""
    try:
        pass

        from ..database import AsyncSessionLocal

        async with AsyncSessionLocal() as db:
            # Get file and job records
            file_record = await FileCRUD.get_file_by_id(db, file_id)
            if not file_record:
                return

            # Update job status to processing
            await ProcessingJobCRUD.update_job_status(
                db, job_id, "processing", 0
            )

            # Download file for processing
            file_data = await storage_manager.download_file(
                file_record.object_key
            )

            # Create temporary file
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f".{file_record.file_type}"
            ) as temp_file:
                temp_file.write(file_data)
                temp_file_path = temp_file.name

            try:
                # Process file
                output_path = temp_file_path.replace(
                    f".{file_record.file_type}",
                    f"_processed.{file_record.file_type}",
                )
                processing_result = await processor_manager.process_file(
                    temp_file_path, file_record.file_type, output_path
                )

                # Update file record with processing results
                updates = {
                    "is_processed": True,
                    "processing_status": "completed",
                    "processing_metadata": processing_result,
                }

                # Add type-specific metadata
                if file_record.file_type == "image":
                    updates.update(
                        {
                            "image_width": processing_result.get("width"),
                            "image_height": processing_result.get("height"),
                            "image_format": processing_result.get("format"),
                            "has_thumbnail": processing_result.get(
                                "thumbnail_path"
                            )
                            is not None,
                            "thumbnail_path": processing_result.get(
                                "thumbnail_path"
                            ),
                        }
                    )
                elif file_record.file_type == "audio":
                    updates.update(
                        {
                            "audio_duration": processing_result.get(
                                "duration"
                            ),
                            "audio_bitrate": processing_result.get("bitrate"),
                            "audio_sample_rate": processing_result.get(
                                "sample_rate"
                            ),
                            "audio_channels": processing_result.get(
                                "channels"
                            ),
                        }
                    )
                elif file_record.file_type == "video":
                    updates.update(
                        {
                            "video_duration": processing_result.get(
                                "duration"
                            ),
                            "video_width": processing_result.get("width"),
                            "video_height": processing_result.get("height"),
                            "video_fps": processing_result.get("fps"),
                            "video_bitrate": processing_result.get("bitrate"),
                            "video_codec": processing_result.get("codec"),
                        }
                    )

                await FileCRUD.update_file(
                    db, file_id, file_record.user_id, updates
                )

                # Update job status to completed
                await ProcessingJobCRUD.update_job_status(
                    db, job_id, "completed", 100
                )

                logger.info(
                    "File processing completed", file_id=file_id, job_id=job_id
                )

            except Exception as e:
                # Update job status to failed
                await ProcessingJobCRUD.update_job_status(
                    db, job_id, "failed", 0, str(e)
                )

                # Update file processing status
                await FileCRUD.update_file(
                    db,
                    file_id,
                    file_record.user_id,
                    {"processing_status": "failed"},
                )

                logger.error(
                    "File processing failed", error=str(e), file_id=file_id
                )

            finally:
                # Clean up temporary files
                try:
                    os.unlink(temp_file_path)
                    if os.path.exists(output_path):
                        os.unlink(output_path)
                except Exception:
                    pass

    except Exception as e:
        logger.error(
            "Async file processing failed", error=str(e), file_id=file_id
        )


@router.get("/upload-status/{job_id}")
async def get_upload_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get upload/processing status"""
    try:
        job = await ProcessingJobCRUD.get_job_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.user_id != current_user.get("id"):
            raise HTTPException(status_code=403, detail="Access denied")

        return {
            "job_id": job.id,
            "status": job.status,
            "progress": job.progress_percentage,
            "current_step": job.current_step,
            "error_message": job.error_message,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get upload status", error=str(e), job_id=job_id
        )
        raise HTTPException(
            status_code=500, detail="Failed to get upload status"
        )
