import os
from typing import Optional

import aiofiles
import boto3
import structlog
from botocore.exceptions import BotoCoreError, ClientError

from .config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class S3Storage:
    """S3-compatible storage for model files and generated audio"""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
            region_name=settings.s3_region,
        )
        self.bucket_name = settings.s3_bucket_name

    async def upload_audio(
        self, audio_data: bytes, key: str, content_type: str = "audio/wav"
    ) -> str:
        """Upload generated audio to S3"""
        try:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=audio_data,
                ContentType=content_type,
                CacheControl="max-age=3600",
            )

            # Generate URL
            url = f"{settings.s3_endpoint_url}/{self.bucket_name}/{key}"
            logger.info("Audio uploaded to S3", key=key, size=len(audio_data))
            return url

        except (ClientError, BotoCoreError) as e:
            logger.error("Failed to upload audio to S3", key=key, error=str(e))
            raise RuntimeError(f"S3 upload failed: {str(e)}")

    async def download_model(self, key: str, local_path: str) -> bool:
        """Download model file from S3"""
        try:
            self.client.download_file(
                Bucket=self.bucket_name, Key=key, Filename=local_path
            )
            logger.info(
                "Model downloaded from S3", key=key, local_path=local_path
            )
            return True

        except (ClientError, BotoCoreError) as e:
            logger.error(
                "Failed to download model from S3", key=key, error=str(e)
            )
            return False

    async def file_exists(self, key: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False

    async def delete_file(self, key: str) -> bool:
        """Delete file from S3"""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info("File deleted from S3", key=key)
            return True
        except (ClientError, BotoCoreError) as e:
            logger.error(
                "Failed to delete file from S3", key=key, error=str(e)
            )
            return False

    async def list_model_files(self, prefix: str) -> list[str]:
        """List model files with given prefix"""
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )

            files = []
            if "Contents" in response:
                files = [obj["Key"] for obj in response["Contents"]]

            return files

        except (ClientError, BotoCoreError) as e:
            logger.error(
                "Failed to list model files", prefix=prefix, error=str(e)
            )
            return []


class LocalStorage:
    """Local storage for temporary files"""

    def __init__(self, base_path: str = "/tmp/voice_inference"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    async def save_temp_audio(self, audio_data: bytes, filename: str) -> str:
        """Save audio to temporary file"""
        try:
            file_path = os.path.join(self.base_path, filename)

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(audio_data)

            logger.debug(
                "Temp audio saved", file_path=file_path, size=len(audio_data)
            )
            return file_path

        except Exception as e:
            logger.error(
                "Failed to save temp audio", filename=filename, error=str(e)
            )
            raise RuntimeError(f"Failed to save temporary audio: {str(e)}")

    async def read_temp_file(self, file_path: str) -> Optional[bytes]:
        """Read temporary file"""
        try:
            if not os.path.exists(file_path):
                return None

            async with aiofiles.open(file_path, "rb") as f:
                data = await f.read()

            return data

        except Exception as e:
            logger.error(
                "Failed to read temp file", file_path=file_path, error=str(e)
            )
            return None

    async def cleanup_temp_file(self, file_path: str) -> bool:
        """Delete temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug("Temp file cleaned up", file_path=file_path)
            return True
        except Exception as e:
            logger.error(
                "Failed to cleanup temp file",
                file_path=file_path,
                error=str(e),
            )
            return False


# Global storage instances
s3_storage = S3Storage()
local_storage = LocalStorage()
