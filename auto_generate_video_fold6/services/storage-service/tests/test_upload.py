import pytest
import io
import json
from unittest.mock import patch, AsyncMock
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


class TestUploadAPI:
    """Test upload API endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "storage-service"

    def test_upload_file_success(self, client, test_image):
        """Test successful file upload"""
        files = {"file": ("test.jpg", test_image, "image/jpeg")}
        data = {"file_type": "image", "category": "uploaded", "description": "Test image upload"}

        response = client.post("/api/v1/upload", files=files, data=data)

        assert response.status_code == 200
        result = response.json()

        assert "file_id" in result
        assert result["filename"] is not None
        assert result["original_filename"] == "test.jpg"
        assert result["file_type"] == "image"
        assert result["mime_type"] == "image/jpeg"
        assert result["status"] == "uploaded"

    def test_upload_file_with_tags(self, client, test_image):
        """Test file upload with tags"""
        files = {"file": ("test.jpg", test_image, "image/jpeg")}
        data = {
            "file_type": "image",
            "category": "uploaded",
            "tags": "test, image, upload",
            "project_id": "project123",
        }

        response = client.post("/api/v1/upload", files=files, data=data)

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "uploaded"

    def test_upload_file_invalid_type(self, client):
        """Test upload with invalid file type"""
        # Create a text file and try to upload as image
        text_content = io.BytesIO(b"This is not an image")
        files = {"file": ("test.txt", text_content, "text/plain")}
        data = {"file_type": "image"}

        with patch("app.routers.upload.magic.from_buffer") as mock_magic:
            mock_magic.return_value = "text/plain"
            response = client.post("/api/v1/upload", files=files, data=data)

        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]

    @patch("app.routers.upload.settings.max_file_size_mb", 1)
    def test_upload_file_too_large(self, client):
        """Test upload with file too large"""
        # Create a large file (2MB when limit is 1MB)
        large_content = io.BytesIO(b"x" * (2 * 1024 * 1024))
        files = {"file": ("large.txt", large_content, "text/plain")}
        data = {"file_type": "document"}

        response = client.post("/api/v1/upload", files=files, data=data)

        assert response.status_code == 413
        assert "exceeds maximum" in response.json()["detail"]

    def test_upload_multiple_files(self, client, test_image):
        """Test multiple file upload"""
        # Create multiple test images
        files = [
            ("files", ("test1.jpg", test_image, "image/jpeg")),
            ("files", ("test2.jpg", test_image, "image/jpeg")),
        ]
        data = {"file_type": "image", "category": "batch"}

        response = client.post("/api/v1/upload-multiple", files=files, data=data)

        assert response.status_code == 200
        result = response.json()

        assert result["total_files"] == 2
        assert result["successful_uploads"] >= 0
        assert result["failed_uploads"] >= 0
        assert len(result["uploaded_files"]) + len(result["failed_files"]) == 2

    @patch("app.routers.upload.settings.max_upload_files", 1)
    def test_upload_too_many_files(self, client, test_image):
        """Test upload with too many files"""
        files = [
            ("files", ("test1.jpg", test_image, "image/jpeg")),
            ("files", ("test2.jpg", test_image, "image/jpeg")),
        ]
        data = {"file_type": "image"}

        response = client.post("/api/v1/upload-multiple", files=files, data=data)

        assert response.status_code == 400
        assert "Too many files" in response.json()["detail"]

    @patch("app.routers.upload.httpx.AsyncClient")
    def test_upload_from_url_success(self, mock_httpx, client):
        """Test upload from URL"""
        # Mock HTTP response
        mock_response = AsyncMock()
        mock_response.content = b"test file content"
        mock_response.raise_for_status = AsyncMock()

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx.return_value.__aenter__.return_value = mock_client

        data = {
            "url": "https://example.com/test.jpg",
            "file_type": "image",
            "filename": "downloaded.jpg",
        }

        with patch("app.routers.upload.magic.from_buffer") as mock_magic:
            mock_magic.return_value = "image/jpeg"
            response = client.post("/api/v1/upload-from-url", data=data)

        assert response.status_code == 200
        result = response.json()
        assert result["original_filename"] == "downloaded.jpg"
        assert result["status"] == "uploaded"

    @patch("app.routers.upload.httpx.AsyncClient")
    def test_upload_from_url_invalid_url(self, mock_httpx, client):
        """Test upload from invalid URL"""
        # Mock HTTP error
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection failed")
        mock_httpx.return_value.__aenter__.return_value = mock_client

        data = {"url": "https://invalid-url.com/test.jpg", "file_type": "image"}

        response = client.post("/api/v1/upload-from-url", data=data)

        assert response.status_code == 400
        assert "Failed to download" in response.json()["detail"]

    def test_get_upload_status(self, client):
        """Test getting upload status"""
        # This would require a real job ID from database
        # For now, test the endpoint structure
        response = client.get("/api/v1/upload-status/nonexistent-job")

        # Should return 404 for non-existent job
        assert response.status_code == 404
