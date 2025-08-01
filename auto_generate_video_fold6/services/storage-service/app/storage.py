import hashlib
import mimetypes
import os
import uuid
from abc import ABC, abstractmethod
from typing import Any, BinaryIO, Dict

import aiofiles
import boto3
import structlog
from botocore.exceptions import ClientError

from .config import settings

logger = structlog.get_logger()


class StorageBackend(ABC):
    """Abstract base class for storage backends"""

    @abstractmethod
    async def upload_file(
        self, file_data: BinaryIO, object_key: str, content_type: str = None
    ) -> str:
        """Upload file and return public URL"""

    @abstractmethod
    async def download_file(self, object_key: str) -> bytes:
        """Download file content"""

    @abstractmethod
    async def delete_file(self, object_key: str) -> bool:
        """Delete file"""

    @abstractmethod
    async def file_exists(self, object_key: str) -> bool:
        """Check if file exists"""

    @abstractmethod
    async def get_file_info(self, object_key: str) -> Dict[str, Any]:
        """Get file metadata"""

    @abstractmethod
    async def generate_presigned_url(
        self, object_key: str, expiration: int = 3600
    ) -> str:
        """Generate presigned URL for file access"""


class S3StorageBackend(StorageBackend):
    """AWS S3 storage backend"""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
            endpoint_url=(
                settings.s3_endpoint_url
                if settings.storage_backend == "minio"
                else None
            ),
        )
        self.bucket_name = settings.s3_bucket_name

        # Create bucket if it doesn't exist
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Ensure the bucket exists"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                try:
                    self.client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration=(
                            {"LocationConstraint": settings.s3_region}
                            if settings.s3_region != "us-east-1"
                            else {}
                        ),
                    )
                    logger.info(
                        "Created storage bucket", bucket=self.bucket_name
                    )
                except ClientError as create_error:
                    logger.error(
                        "Failed to create bucket", error=str(create_error)
                    )
                    raise
            else:
                logger.error("Failed to check bucket", error=str(e))
                raise

    async def upload_file(
        self, file_data: BinaryIO, object_key: str, content_type: str = None
    ) -> str:
        """Upload file to S3"""
        try:
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            self.client.upload_fileobj(
                file_data, self.bucket_name, object_key, ExtraArgs=extra_args
            )

            if settings.use_cdn and settings.cdn_url:
                return f"{settings.cdn_url}/{object_key}"
            else:
                return (
                    f"{settings.s3_public_url}/{self.bucket_name}/{object_key}"
                )

        except ClientError as e:
            logger.error(
                "Failed to upload file to S3",
                error=str(e),
                object_key=object_key,
            )
            raise

    async def download_file(self, object_key: str) -> bytes:
        """Download file from S3"""
        try:
            response = self.client.get_object(
                Bucket=self.bucket_name, Key=object_key
            )
            return response["Body"].read()
        except ClientError as e:
            logger.error(
                "Failed to download file from S3",
                error=str(e),
                object_key=object_key,
            )
            raise

    async def delete_file(self, object_key: str) -> bool:
        """Delete file from S3"""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError as e:
            logger.error(
                "Failed to delete file from S3",
                error=str(e),
                object_key=object_key,
            )
            return False

    async def file_exists(self, object_key: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError:
            return False

    async def get_file_info(self, object_key: str) -> Dict[str, Any]:
        """Get file metadata from S3"""
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name, Key=object_key
            )
            return {
                "size": response["ContentLength"],
                "last_modified": response["LastModified"],
                "content_type": response.get("ContentType"),
                "etag": response["ETag"],
            }
        except ClientError as e:
            logger.error(
                "Failed to get file info from S3",
                error=str(e),
                object_key=object_key,
            )
            raise

    async def generate_presigned_url(
        self, object_key: str, expiration: int = 3600
    ) -> str:
        """Generate presigned URL for file access"""
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=expiration,
            )
            return url
        except ClientError as e:
            logger.error(
                "Failed to generate presigned URL",
                error=str(e),
                object_key=object_key,
            )
            raise


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend"""

    def __init__(self):
        self.storage_path = settings.local_storage_path
        os.makedirs(self.storage_path, exist_ok=True)

    def _get_full_path(self, object_key: str) -> str:
        """Get full local path for object key"""
        return os.path.join(self.storage_path, object_key.lstrip("/"))

    async def upload_file(
        self, file_data: BinaryIO, object_key: str, content_type: str = None
    ) -> str:
        """Upload file to local storage"""
        try:
            full_path = self._get_full_path(object_key)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            async with aiofiles.open(full_path, "wb") as f:
                content = file_data.read()
                if isinstance(content, str):
                    content = content.encode("utf-8")
                await f.write(content)

            # Return public URL
            # (in production, this would be served by a web server)
            return f"/storage/{object_key}"

        except Exception as e:
            logger.error(
                "Failed to upload file to local storage",
                error=str(e),
                object_key=object_key,
            )
            raise

    async def download_file(self, object_key: str) -> bytes:
        """Download file from local storage"""
        try:
            full_path = self._get_full_path(object_key)
            async with aiofiles.open(full_path, "rb") as f:
                return await f.read()
        except Exception as e:
            logger.error(
                "Failed to download file from local storage",
                error=str(e),
                object_key=object_key,
            )
            raise

    async def delete_file(self, object_key: str) -> bool:
        """Delete file from local storage"""
        try:
            full_path = self._get_full_path(object_key)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception as e:
            logger.error(
                "Failed to delete file from local storage",
                error=str(e),
                object_key=object_key,
            )
            return False

    async def file_exists(self, object_key: str) -> bool:
        """Check if file exists in local storage"""
        full_path = self._get_full_path(object_key)
        return os.path.exists(full_path)

    async def get_file_info(self, object_key: str) -> Dict[str, Any]:
        """Get file metadata from local storage"""
        try:
            full_path = self._get_full_path(object_key)
            stat = os.stat(full_path)
            content_type, _ = mimetypes.guess_type(full_path)

            return {
                "size": stat.st_size,
                "last_modified": stat.st_mtime,
                "content_type": content_type,
                "path": full_path,
            }
        except Exception as e:
            logger.error(
                "Failed to get file info from local storage",
                error=str(e),
                object_key=object_key,
            )
            raise

    async def generate_presigned_url(
        self, object_key: str, expiration: int = 3600
    ) -> str:
        """Generate presigned URL for file access (not applicable for \
            local storage)"""
        return f"/storage/{object_key}"


class StorageManager:
    """Main storage manager that handles file operations"""

    def __init__(self):
        self.backend = self._get_storage_backend()

    def _get_storage_backend(self) -> StorageBackend:
        """Get the configured storage backend"""
        if settings.storage_backend == "s3":
            return S3StorageBackend()
        elif settings.storage_backend == "minio":
            return S3StorageBackend()  # MinIO uses S3-compatible API
        elif settings.storage_backend == "local":
            return LocalStorageBackend()
        else:
            raise ValueError(
                f"Unsupported storage backend: {settings.storage_backend}"
            )

    def generate_object_key(
        self, user_id: str, file_type: str, filename: str = None
    ) -> str:
        """Generate unique object key for file storage"""
        if not filename:
            filename = str(uuid.uuid4())

        # Remove any path traversal attempts
        safe_filename = os.path.basename(filename)

        # Create hierarchical structure: user_id/file_type/year/month/filename
        from datetime import datetime

        now = datetime.utcnow()

        object_key = f"{user_id}/{file_type}/{now.year:04d}/{now.month:02d}/{
            safe_filename
        }"
        return object_key

    def calculate_file_hash(self, file_data: bytes) -> str:
        """Calculate SHA-256 hash of file data"""
        return hashlib.sha256(file_data).hexdigest()

    def validate_file_type(self, content_type: str, file_type: str) -> bool:
        """Validate if content type is allowed for file type"""
        allowed_types = {
            "image": settings.allowed_image_types,
            "audio": settings.allowed_audio_types,
            "video": settings.allowed_video_types,
            "document": settings.allowed_document_types,
        }

        return content_type in allowed_types.get(file_type, [])

    def validate_file_size(self, file_size: int) -> bool:
        """Validate file size"""
        max_size_bytes = settings.max_file_size_mb * 1024 * 1024
        return file_size <= max_size_bytes

    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: str,
        user_id: str,
        file_type: str,
        category: str = "uploaded",
    ) -> Dict[str, Any]:
        """Upload file with validation and metadata"""

        # Validation
        if not self.validate_file_type(content_type, file_type):
            raise ValueError(
                f"File type {content_type} not allowed for {file_type}"
            )

        # Read file data for validation and hashing
        file_data.seek(0)
        file_content = file_data.read()
        file_size = len(file_content)

        if not self.validate_file_size(file_size):
            raise ValueError(
                f"File size {file_size} exceeds maximum allowed size"
            )

        # Calculate hash for deduplication
        file_hash = self.calculate_file_hash(file_content)

        # Generate unique object key
        object_key = self.generate_object_key(user_id, file_type, filename)

        # Upload to storage backend
        file_data.seek(0)
        public_url = await self.backend.upload_file(
            file_data, object_key, content_type
        )

        return {
            "object_key": object_key,
            "public_url": public_url,
            "file_size": file_size,
            "file_hash": file_hash,
            "content_type": content_type,
        }

    async def download_file(self, object_key: str) -> bytes:
        """Download file from storage"""
        return await self.backend.download_file(object_key)

    async def delete_file(self, object_key: str) -> bool:
        """Delete file from storage"""
        return await self.backend.delete_file(object_key)

    async def file_exists(self, object_key: str) -> bool:
        """Check if file exists"""
        return await self.backend.file_exists(object_key)

    async def get_file_info(self, object_key: str) -> Dict[str, Any]:
        """Get file metadata"""
        return await self.backend.get_file_info(object_key)

    async def generate_download_url(
        self, object_key: str, expiration: int = 3600
    ) -> str:
        """Generate download URL for file"""
        return await self.backend.generate_presigned_url(
            object_key, expiration
        )


# Global storage manager instance
storage_manager = StorageManager()
