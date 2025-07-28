from typing import Any, Dict, List, Optional

import structlog
from sqlalchemy import and_, delete, desc, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import FileDownload, FileProcessingJob, StoredFile

logger = structlog.get_logger()


class FileCRUD:
    """CRUD operations for stored files"""

    @staticmethod
    async def create_file(db: AsyncSession, user_id: str, file_data: Dict[str, Any]) -> StoredFile:
        """Create a new stored file record"""
        try:
            stored_file = StoredFile(user_id=user_id, **file_data)
            db.add(stored_file)
            await db.commit()
            await db.refresh(stored_file)
            return stored_file
        except Exception as e:
            await db.rollback()
            logger.error("Failed to create file record", error=str(e), user_id=user_id)
            raise

    @staticmethod
    async def get_file_by_id(
        db: AsyncSession, file_id: str, user_id: str = None
    ) -> Optional[StoredFile]:
        """Get file by ID"""
        try:
            query = select(StoredFile).where(StoredFile.id == file_id)
            if user_id:
                query = query.where(StoredFile.user_id == user_id)

            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Failed to get file by ID", error=str(e), file_id=file_id)
            raise

    @staticmethod
    async def get_file_by_hash(
        db: AsyncSession, file_hash: str, user_id: str = None
    ) -> Optional[StoredFile]:
        """Get file by hash (for deduplication)"""
        try:
            query = select(StoredFile).where(StoredFile.file_hash == file_hash)
            if user_id:
                query = query.where(StoredFile.user_id == user_id)

            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Failed to get file by hash", error=str(e), file_hash=file_hash)
            raise

    @staticmethod
    async def get_user_files(
        db: AsyncSession,
        user_id: str,
        file_type: str = None,
        category: str = None,
        project_id: str = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StoredFile]:
        """Get user's files with filtering"""
        try:
            query = select(StoredFile).where(StoredFile.user_id == user_id)

            if file_type:
                query = query.where(StoredFile.file_type == file_type)

            if category:
                query = query.where(StoredFile.category == category)

            if project_id:
                query = query.where(StoredFile.project_id == project_id)

            query = query.order_by(desc(StoredFile.created_at)).offset(skip).limit(limit)

            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error("Failed to get user files", error=str(e), user_id=user_id)
            raise

    @staticmethod
    async def update_file(
        db: AsyncSession, file_id: str, user_id: str, updates: Dict[str, Any]
    ) -> Optional[StoredFile]:
        """Update file record"""
        try:
            query = (
                update(StoredFile)
                .where(and_(StoredFile.id == file_id, StoredFile.user_id == user_id))
                .values(**updates)
                .returning(StoredFile)
            )

            result = await db.execute(query)
            await db.commit()
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            logger.error("Failed to update file", error=str(e), file_id=file_id)
            raise

    @staticmethod
    async def delete_file(db: AsyncSession, file_id: str, user_id: str) -> bool:
        """Delete file record"""
        try:
            query = delete(StoredFile).where(
                and_(StoredFile.id == file_id, StoredFile.user_id == user_id)
            )

            result = await db.execute(query)
            await db.commit()
            return result.rowcount > 0
        except Exception as e:
            await db.rollback()
            logger.error("Failed to delete file", error=str(e), file_id=file_id)
            raise

    @staticmethod
    async def get_files_by_project(
        db: AsyncSession, project_id: str, user_id: str
    ) -> List[StoredFile]:
        """Get all files for a project"""
        try:
            query = (
                select(StoredFile)
                .where(and_(StoredFile.project_id == project_id, StoredFile.user_id == user_id))
                .order_by(desc(StoredFile.created_at))
            )

            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error("Failed to get project files", error=str(e), project_id=project_id)
            raise

    @staticmethod
    async def search_files(
        db: AsyncSession,
        user_id: str,
        search_term: str,
        file_type: str = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[StoredFile]:
        """Search files by filename or description"""
        try:
            query = select(StoredFile).where(StoredFile.user_id == user_id)

            # Search in filename, original_filename, and description
            search_conditions = [
                StoredFile.filename.ilike(f"%{search_term}%"),
                StoredFile.original_filename.ilike(f"%{search_term}%"),
                StoredFile.description.ilike(f"%{search_term}%"),
            ]
            query = query.where(or_(*search_conditions))

            if file_type:
                query = query.where(StoredFile.file_type == file_type)

            query = query.order_by(desc(StoredFile.created_at)).offset(skip).limit(limit)

            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error("Failed to search files", error=str(e), user_id=user_id)
            raise


class ProcessingJobCRUD:
    """CRUD operations for file processing jobs"""

    @staticmethod
    async def create_job(db: AsyncSession, job_data: Dict[str, Any]) -> FileProcessingJob:
        """Create a new processing job"""
        try:
            job = FileProcessingJob(**job_data)
            db.add(job)
            await db.commit()
            await db.refresh(job)
            return job
        except Exception as e:
            await db.rollback()
            logger.error("Failed to create processing job", error=str(e))
            raise

    @staticmethod
    async def get_job_by_id(db: AsyncSession, job_id: str) -> Optional[FileProcessingJob]:
        """Get processing job by ID"""
        try:
            query = select(FileProcessingJob).where(FileProcessingJob.id == job_id)
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error("Failed to get processing job", error=str(e), job_id=job_id)
            raise

    @staticmethod
    async def get_pending_jobs(db: AsyncSession, limit: int = 10) -> List[FileProcessingJob]:
        """Get pending processing jobs"""
        try:
            query = (
                select(FileProcessingJob)
                .where(FileProcessingJob.status == "pending")
                .order_by(FileProcessingJob.priority, FileProcessingJob.created_at)
                .limit(limit)
            )

            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error("Failed to get pending jobs", error=str(e))
            raise

    @staticmethod
    async def update_job_status(
        db: AsyncSession, job_id: str, status: str, progress: int = None, error_message: str = None
    ) -> Optional[FileProcessingJob]:
        """Update job status and progress"""
        try:
            updates = {"status": status}
            if progress is not None:
                updates["progress_percentage"] = progress
            if error_message:
                updates["error_message"] = error_message

            query = (
                update(FileProcessingJob)
                .where(FileProcessingJob.id == job_id)
                .values(**updates)
                .returning(FileProcessingJob)
            )

            result = await db.execute(query)
            await db.commit()
            return result.scalar_one_or_none()
        except Exception as e:
            await db.rollback()
            logger.error("Failed to update job status", error=str(e), job_id=job_id)
            raise


class DownloadCRUD:
    """CRUD operations for file downloads"""

    @staticmethod
    async def create_download_record(
        db: AsyncSession,
        file_id: str,
        user_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        referer: str = None,
    ) -> FileDownload:
        """Create download record"""
        try:
            download = FileDownload(
                file_id=file_id,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                referer=referer,
            )
            db.add(download)
            await db.commit()
            await db.refresh(download)
            return download
        except Exception as e:
            await db.rollback()
            logger.error("Failed to create download record", error=str(e))
            raise

    @staticmethod
    async def get_download_stats(db: AsyncSession, file_id: str) -> Dict[str, Any]:
        """Get download statistics for a file"""
        try:
            from sqlalchemy import func

            query = select(func.count(FileDownload.id)).where(FileDownload.file_id == file_id)
            result = await db.execute(query)
            total_downloads = result.scalar() or 0

            return {"total_downloads": total_downloads}
        except Exception as e:
            logger.error("Failed to get download stats", error=str(e), file_id=file_id)
            raise
