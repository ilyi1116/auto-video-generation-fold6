from typing import List, Optional
from urllib.parse import quote

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel

from ..auth import get_current_user
from ..config import settings
from ..crud import DownloadCRUD, FileCRUD
from ..database import get_db
from ..storage import storage_manager

router = APIRouter()
logger = structlog.get_logger()


class FileResponse(BaseModel):
    file_id: str
    filename: str
    original_filename: str
    file_size: int
    file_type: str
    mime_type: str
    public_url: str
    created_at: str
    processing_status: str
    download_count: int


class FileListResponse(BaseModel):
    files: List[FileResponse]
    total_count: int
    page: int
    page_size: int
    has_next: bool


@router.get("/files", response_model=FileListResponse)
async def list_files(
    file_type: Optional[str] = None,
    category: Optional[str] = None,
    project_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """List user's files with filtering and pagination"""
    try:
        skip = (page - 1) * page_size

        if search:
            files = await FileCRUD.search_files(
                db, current_user.get("id"), search, file_type, skip, page_size
            )
        else:
            files = await FileCRUD.get_user_files(
                db,
                current_user.get("id"),
                file_type,
                category,
                project_id,
                skip,
                page_size,
            )

        # Get download counts for each file
        file_responses = []
        for file in files:
            download_stats = await DownloadCRUD.get_download_stats(db, file.id)

            file_responses.append(
                FileResponse(
                    file_id=file.id,
                    filename=file.filename,
                    original_filename=file.original_filename,
                    file_size=file.file_size,
                    file_type=file.file_type,
                    mime_type=file.mime_type,
                    public_url=file.public_url,
                    created_at=file.created_at.isoformat(),
                    processing_status=file.processing_status,
                    download_count=download_stats.get("total_downloads", 0),
                )
            )

        return FileListResponse(
            files=file_responses,
            total_count=len(file_responses),
            page=page,
            page_size=page_size,
            has_next=len(files) == page_size,
        )

    except Exception as e:
        logger.error(
            "Failed to list files",
            error=str(e),
            user_id=current_user.get("id"),
        )
        raise HTTPException(status_code=500, detail="Failed to list files")


@router.get("/files/{file_id}")
async def get_file_info(
    file_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Get detailed file information"""
    try:
        file = await FileCRUD.get_file_by_id(
            db, file_id, current_user.get("id")
        )
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        download_stats = await DownloadCRUD.get_download_stats(db, file.id)

        return {
            "file_id": file.id,
            "filename": file.filename,
            "original_filename": file.original_filename,
            "file_size": file.file_size,
            "file_type": file.file_type,
            "mime_type": file.mime_type,
            "category": file.category,
            "description": file.description,
            "tags": file.tags,
            "project_id": file.project_id,
            "public_url": file.public_url,
            "created_at": file.created_at.isoformat(),
            "updated_at": file.updated_at.isoformat(),
            "processing_status": file.processing_status,
            "processing_metadata": file.processing_metadata,
            "download_count": download_stats.get("total_downloads", 0),
            # Type-specific metadata
            "image_width": file.image_width,
            "image_height": file.image_height,
            "image_format": file.image_format,
            "has_thumbnail": file.has_thumbnail,
            "thumbnail_path": file.thumbnail_path,
            "audio_duration": file.audio_duration,
            "audio_bitrate": file.audio_bitrate,
            "audio_sample_rate": file.audio_sample_rate,
            "audio_channels": file.audio_channels,
            "video_duration": file.video_duration,
            "video_width": file.video_width,
            "video_height": file.video_height,
            "video_fps": file.video_fps,
            "video_bitrate": file.video_bitrate,
            "video_codec": file.video_codec,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get file info", error=str(e), file_id=file_id)
        raise HTTPException(status_code=500, detail="Failed to get file info")


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Download file by ID"""
    try:
        file = await FileCRUD.get_file_by_id(
            db, file_id, current_user.get("id")
        )
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        # Record download
        await DownloadCRUD.create_download_record(
            db,
            file_id=file.id,
            user_id=current_user.get("id"),
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            referer=request.headers.get("referer"),
        )

        # If using public URLs (S3), redirect to the URL
        if file.public_url and settings.storage_backend in ["s3", "minio"]:
            return RedirectResponse(url=file.public_url)

        # For local storage, stream the file
        try:
            file_data = await storage_manager.download_file(file.object_key)

            def generate():
                yield file_data

            headers = {
                "Content-Disposition": f'attachment; filename="{quote
                                                                (file.original_filename)}"',
                "Content-Type": file.mime_type,
                "Content-Length": str(file.file_size),
            }

            return StreamingResponse(
                generate(), media_type=file.mime_type, headers=headers
            )

        except Exception as e:
            logger.error(
                "Failed to retrieve file from storage",
                error=str(e),
                file_id=file_id,
            )
            raise HTTPException(
                status_code=500, detail="Failed to retrieve file"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Download failed", error=str(e), file_id=file_id)
        raise HTTPException(status_code=500, detail="Download failed")


@router.get("/serve/{file_id}")
async def serve_file(
    file_id: str,
    request: Request,
    thumbnail: bool = False,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Serve file for viewing (not downloading)"""
    try:
        file = await FileCRUD.get_file_by_id(
            db, file_id, current_user.get("id")
        )
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        # For thumbnails
        if thumbnail and file.has_thumbnail and file.thumbnail_path:
            try:
                thumbnail_data = await storage_manager.download_file(
                    file.thumbnail_path
                )

                def generate():
                    yield thumbnail_data

                return StreamingResponse(generate(), media_type="image/jpeg")
            except Exception:
                # Fallback to original file if thumbnail fails
                pass

        # Serve original file
        if file.public_url and settings.storage_backend in ["s3", "minio"]:
            return RedirectResponse(url=file.public_url)

        try:
            file_data = await storage_manager.download_file(file.object_key)

            def generate():
                yield file_data

            return StreamingResponse(generate(), media_type=file.mime_type)

        except Exception as e:
            logger.error("Failed to serve file", error=str(e), file_id=file_id)
            raise HTTPException(status_code=500, detail="Failed to serve file")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Serve failed", error=str(e), file_id=file_id)
        raise HTTPException(status_code=500, detail="Serve failed")


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Delete file"""
    try:
        file = await FileCRUD.get_file_by_id(
            db, file_id, current_user.get("id")
        )
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        # Delete from storage
        try:
            await storage_manager.delete_file(file.object_key)

            # Delete thumbnail if exists
            if file.has_thumbnail and file.thumbnail_path:
                try:
                    await storage_manager.delete_file(file.thumbnail_path)
                except Exception:
                    pass  # Continue even if thumbnail deletion fails

        except Exception as e:
            logger.warning(
                "Failed to delete file from storage",
                error=str(e),
                file_id=file_id,
            )

        # Delete from database
        success = await FileCRUD.delete_file(
            db, file_id, current_user.get("id")
        )
        if not success:
            raise HTTPException(status_code=404, detail="File not found")

        logger.info(
            "File deleted successfully",
            file_id=file_id,
            user_id=current_user.get("id"),
        )

        return {"message": "File deleted successfully", "file_id": file_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("File deletion failed", error=str(e), file_id=file_id)
        raise HTTPException(status_code=500, detail="File deletion failed")


@router.put("/files/{file_id}")
async def update_file(
    file_id: str,
    filename: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[str] = None,
    category: Optional[str] = None,
    project_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Update file metadata"""
    try:
        file = await FileCRUD.get_file_by_id(
            db, file_id, current_user.get("id")
        )
        if not file:
            raise HTTPException(status_code=404, detail="File not found")

        updates = {}
        if filename is not None:
            updates["filename"] = filename
        if description is not None:
            updates["description"] = description
        if tags is not None:
            tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            updates["tags"] = tag_list
        if category is not None:
            updates["category"] = category
        if project_id is not None:
            updates["project_id"] = project_id

        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")

        updated_file = await FileCRUD.update_file(
            db, file_id, current_user.get("id"), updates
        )
        if not updated_file:
            raise HTTPException(status_code=404, detail="File not found")

        return {
            "message": "File updated successfully",
            "file_id": file_id,
            "updates": updates,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("File update failed", error=str(e), file_id=file_id)
        raise HTTPException(status_code=500, detail="File update failed")


@router.post("/files/bulk-delete")
async def bulk_delete_files(
    file_ids: List[str],
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """Delete multiple files"""
    try:
        deleted_files = []
        failed_files = []

        for file_id in file_ids:
            try:
                file = await FileCRUD.get_file_by_id(
                    db, file_id, current_user.get("id")
                )
                if not file:
                    failed_files.append(
                        {"file_id": file_id, "error": "File not found"}
                    )
                    continue

                # Delete from storage
                try:
                    await storage_manager.delete_file(file.object_key)
                    if file.has_thumbnail and file.thumbnail_path:
                        try:
                            await storage_manager.delete_file(
                                file.thumbnail_path
                            )
                        except Exception:
                            pass
                except Exception as e:
                    logger.warning(
                        "Failed to delete file from storage",
                        error=str(e),
                        file_id=file_id,
                    )

                # Delete from database
                success = await FileCRUD.delete_file(
                    db, file_id, current_user.get("id")
                )
                if success:
                    deleted_files.append(file_id)
                else:
                    failed_files.append(
                        {
                            "file_id": file_id,
                            "error": "Database deletion failed",
                        }
                    )

            except Exception as e:
                failed_files.append({"file_id": file_id, "error": str(e)})

        return {
            "deleted_files": deleted_files,
            "failed_files": failed_files,
            "total_requested": len(file_ids),
            "total_deleted": len(deleted_files),
            "total_failed": len(failed_files),
        }

    except Exception as e:
        logger.error("Bulk delete failed", error=str(e))
        raise HTTPException(status_code=500, detail="Bulk delete failed")
