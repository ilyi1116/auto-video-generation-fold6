import os
from pathlib import Path
from typing import BinaryIO

import aiofiles
import boto3
import structlog
from app.config import settings
from botocore.exceptions import ClientError

logger = structlog.get_logger(__name__)


class S3Storage:
    """S3-compatible storage client for MinIO/AWS S3"""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region,
        )
        self.bucket = settings.s3_bucket
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            self.client.head_bucket(Bucket=self.bucket)
            logger.info("S3 bucket exists", bucket=self.bucket)
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                try:
                    self.client.create_bucket(Bucket=self.bucket)
                    logger.info("Created S3 bucket", bucket=self.bucket)
                except ClientError as create_error:
                    logger.error(
                        "Failed to create S3 bucket",
                        bucket=self.bucket,
                        error=str(create_error),
                    )
                    raise
            else:
                logger.error(
                    "Error checking S3 bucket",
                    bucket=self.bucket,
                    error=str(e),
                )
                raise

    async def upload_file(self, file_path: str, s3_key: str) -> str:
        """Upload file to S3 storage"""
        try:
            # Upload file
            self.client.upload_file(file_path, self.bucket, s3_key)

            # Generate URL
            url = f"{settings.s3_endpoint}/{self.bucket}/{s3_key}"

            logger.info(
                "File uploaded to S3",
                file_path=file_path,
                s3_key=s3_key,
                url=url,
            )

            return url

        except ClientError as e:
            logger.error(
                "Failed to upload file to S3",
                file_path=file_path,
                s3_key=s3_key,
                error=str(e),
            )
            raise

    async def download_file(self, s3_key: str, local_path: str) -> str:
        """Download file from S3 storage"""
        try:
            # Ensure local directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # Download file
            self.client.download_file(self.bucket, s3_key, local_path)

            logger.info(
                "File downloaded from S3", s3_key=s3_key, local_path=local_path
            )

            return local_path

        except ClientError as e:
            logger.error(
                "Failed to download file from S3",
                s3_key=s3_key,
                local_path=local_path,
                error=str(e),
            )
            raise

    async def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3 storage"""
        try:
            self.client.delete_object(Bucket=self.bucket, Key=s3_key)

            logger.info("File deleted from S3", s3_key=s3_key)
            return True

        except ClientError as e:
            logger.error(
                "Failed to delete file from S3", s3_key=s3_key, error=str(e)
            )
            return False

    def file_exists(self, s3_key: str) -> bool:
        """Check if file exists in S3 storage"""
        try:
            self.client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError:
            return False


class LocalStorage:
    """Local file storage manager"""

    def __init__(self, base_path: str = settings.upload_dir):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, file_data: BinaryIO, filename: str) -> str:
        """Save uploaded file to local storage"""
        file_path = self.base_path / filename

        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, "wb") as f:
            content = file_data.read()
            await f.write(content)

        logger.info("File saved locally", file_path=str(file_path))
        return str(file_path)

    async def delete_file(self, file_path: str) -> bool:
        """Delete file from local storage"""
        try:
            os.remove(file_path)
            logger.info("File deleted locally", file_path=file_path)
            return True
        except OSError as e:
            logger.error(
                "Failed to delete local file",
                file_path=file_path,
                error=str(e),
            )
            return False

    def file_exists(self, file_path: str) -> bool:
        """Check if file exists locally"""
        return os.path.exists(file_path)


# Global storage instances
s3_storage = S3Storage()
local_storage = LocalStorage()
