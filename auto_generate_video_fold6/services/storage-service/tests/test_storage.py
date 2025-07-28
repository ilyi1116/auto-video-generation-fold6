import os
import sys
import tempfile
from unittest.mock import mock_open, patch

import pytest

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

from app.storage import LocalStorageBackend, S3StorageBackend, StorageManager


class TestLocalStorageBackend:
    """Test local storage backend"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.backend = LocalStorageBackend(base_path=self.temp_dir)

    def teardown_method(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_upload_file(self):
        """Test file upload to local storage"""
        import io

        file_data = io.BytesIO(b"test content")
        object_key = "test/file.txt"
        content_type = "text/plain"

        result = await self.backend.upload_file(file_data, object_key, content_type)

        assert result == object_key

        # Check file exists
        file_path = os.path.join(self.temp_dir, object_key)
        assert os.path.exists(file_path)

        # Check content
        with open(file_path, "rb") as f:
            assert f.read() == b"test content"

    @pytest.mark.asyncio
    async def test_download_file(self):
        """Test file download from local storage"""
        # Create test file
        object_key = "test/file.txt"
        file_path = os.path.join(self.temp_dir, object_key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(b"test content")

        # Download file
        result = await self.backend.download_file(object_key)
        assert result == b"test content"

    @pytest.mark.asyncio
    async def test_delete_file(self):
        """Test file deletion from local storage"""
        # Create test file
        object_key = "test/file.txt"
        file_path = os.path.join(self.temp_dir, object_key)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(b"test content")

        assert os.path.exists(file_path)

        # Delete file
        await self.backend.delete_file(object_key)
        assert not os.path.exists(file_path)

    def test_get_file_url(self):
        """Test getting file URL"""
        object_key = "test/file.txt"
        base_url = "https://example.com"

        url = self.backend.get_file_url(object_key, base_url)
        assert url == f"{base_url}/{object_key}"


class TestS3StorageBackend:
    """Test S3 storage backend"""

    def setup_method(self):
        self.backend = S3StorageBackend(
            access_key_id="test_key",
            secret_access_key="test_secret",
            bucket_name="test-bucket",
            region_name="us-east-1",
        )

    @pytest.mark.asyncio
    @patch("app.storage.boto3.client")
    async def test_upload_file(self, mock_boto_client):
        """Test file upload to S3"""
        import io

        # Mock S3 client
        mock_s3 = mock_boto_client.return_value

        file_data = io.BytesIO(b"test content")
        object_key = "test/file.txt"
        content_type = "text/plain"

        result = await self.backend.upload_file(file_data, object_key, content_type)

        assert result == object_key
        mock_s3.upload_fileobj.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.storage.boto3.client")
    async def test_download_file(self, mock_boto_client):
        """Test file download from S3"""
        # Mock S3 client
        mock_s3 = mock_boto_client.return_value
        mock_response = mock_s3.get_object.return_value
        mock_response["Body"].read.return_value = b"test content"

        object_key = "test/file.txt"

        result = await self.backend.download_file(object_key)

        assert result == b"test content"
        mock_s3.get_object.assert_called_once_with(Bucket="test-bucket", Key=object_key)

    @pytest.mark.asyncio
    @patch("app.storage.boto3.client")
    async def test_delete_file(self, mock_boto_client):
        """Test file deletion from S3"""
        mock_s3 = mock_boto_client.return_value

        object_key = "test/file.txt"

        await self.backend.delete_file(object_key)

        mock_s3.delete_object.assert_called_once_with(Bucket="test-bucket", Key=object_key)

    @patch("app.storage.boto3.client")
    def test_get_file_url(self, mock_boto_client):
        """Test getting presigned URL"""
        mock_s3 = mock_boto_client.return_value
        mock_s3.generate_presigned_url.return_value = "https://presigned.url"

        object_key = "test/file.txt"

        url = self.backend.get_file_url(object_key)

        assert url == "https://presigned.url"
        mock_s3.generate_presigned_url.assert_called_once()


class TestStorageManager:
    """Test storage manager"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = StorageManager(storage_type="local", base_path=self.temp_dir)

    def teardown_method(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    async def test_upload_file_with_hash(self):
        """Test file upload with hash calculation"""
        import io

        file_data = io.BytesIO(b"test content")
        filename = "test.txt"

        result = await self.manager.upload_file(
            file_data=file_data,
            filename=filename,
            content_type="text/plain",
            user_id="user123",
            file_type="document",
            category="uploaded",
        )

        assert "object_key" in result
        assert "file_size" in result
        assert "content_type" in result
        assert "file_hash" in result
        assert "public_url" in result

        assert result["file_size"] == 12  # len(b"test content")
        assert result["content_type"] == "text/plain"

    def test_validate_file_type_image(self):
        """Test image file type validation"""
        assert self.manager.validate_file_type("image/jpeg", "image")
        assert self.manager.validate_file_type("image/png", "image")
        assert not self.manager.validate_file_type("text/plain", "image")

    def test_validate_file_type_audio(self):
        """Test audio file type validation"""
        assert self.manager.validate_file_type("audio/mpeg", "audio")
        assert self.manager.validate_file_type("audio/wav", "audio")
        assert not self.manager.validate_file_type("image/jpeg", "audio")

    def test_validate_file_type_video(self):
        """Test video file type validation"""
        assert self.manager.validate_file_type("video/mp4", "video")
        assert self.manager.validate_file_type("video/avi", "video")
        assert not self.manager.validate_file_type("text/plain", "video")

    def test_generate_object_key(self):
        """Test object key generation"""
        key = self.manager._generate_object_key("user123", "test.txt", "document", "uploaded")

        assert "user123" in key
        assert "test.txt" in key
        assert key.startswith("uploaded/document/user123/")

    def test_calculate_file_hash(self):
        """Test file hash calculation"""
        import io

        file_data = io.BytesIO(b"test content")
        hash_value = self.manager._calculate_file_hash(file_data)

        # SHA-256 hash of "test content"
        expected_hash = "1eebdf4fdc9fc7bf283031b93f9aef3338de9052f68b773bc27161c0966e7dc6"
        assert hash_value == expected_hash
