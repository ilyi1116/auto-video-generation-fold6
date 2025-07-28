import json
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


class TestDownloadAPI:
    """Test download API endpoints"""

    def test_list_files_empty(self, client):
        """Test listing files when no files exist"""
        response = client.get("/api/v1/files")

        assert response.status_code == 200
        result = response.json()

        assert "files" in result
        assert "total_count" in result
        assert "page" in result
        assert "page_size" in result
        assert "has_next" in result
        assert result["total_count"] == 0
        assert len(result["files"]) == 0

    def test_list_files_with_filters(self, client):
        """Test listing files with filters"""
        response = client.get(
            "/api/v1/files",
            params={"file_type": "image", "category": "uploaded", "page": 1, "page_size": 10},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["page"] == 1
        assert result["page_size"] == 10

    def test_list_files_with_search(self, client):
        """Test listing files with search"""
        response = client.get("/api/v1/files", params={"search": "test", "file_type": "image"})

        assert response.status_code == 200
        result = response.json()
        assert "files" in result

    def test_get_file_info_not_found(self, client):
        """Test getting info for non-existent file"""
        response = client.get("/api/v1/files/nonexistent-file-id")

        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]

    def test_download_file_not_found(self, client):
        """Test downloading non-existent file"""
        response = client.get("/api/v1/download/nonexistent-file-id")

        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]

    def test_serve_file_not_found(self, client):
        """Test serving non-existent file"""
        response = client.get("/api/v1/serve/nonexistent-file-id")

        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]

    def test_serve_file_thumbnail(self, client):
        """Test serving file thumbnail"""
        response = client.get("/api/v1/serve/nonexistent-file-id", params={"thumbnail": True})

        assert response.status_code == 404

    def test_delete_file_not_found(self, client):
        """Test deleting non-existent file"""
        response = client.delete("/api/v1/files/nonexistent-file-id")

        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]

    def test_update_file_not_found(self, client):
        """Test updating non-existent file"""
        response = client.put(
            "/api/v1/files/nonexistent-file-id",
            json={"filename": "new_name.jpg", "description": "Updated description"},
        )

        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]

    def test_update_file_no_updates(self, client):
        """Test updating file with no changes"""
        # This would need a real file ID, but we can test the validation
        response = client.put("/api/v1/files/test-file-id")

        # Should fail because no updates provided
        assert response.status_code in [400, 404]  # 400 for no updates, 404 for not found

    def test_bulk_delete_files(self, client):
        """Test bulk delete files"""
        response = client.post(
            "/api/v1/files/bulk-delete", json={"file_ids": ["file1", "file2", "file3"]}
        )

        assert response.status_code == 200
        result = response.json()

        assert "deleted_files" in result
        assert "failed_files" in result
        assert "total_requested" in result
        assert "total_deleted" in result
        assert "total_failed" in result

        # All should fail because files don't exist
        assert result["total_requested"] == 3
        assert result["total_deleted"] == 0
        assert result["total_failed"] == 3


class TestDownloadAPIWithData:
    """Test download API with mock data"""

    @pytest.fixture
    def mock_file_crud(self):
        """Mock FileCRUD with sample data"""
        from datetime import datetime

        from app.crud import FileCRUD
        from app.models import StoredFile

        async def mock_get_file_by_id(db, file_id, user_id=None):
            if file_id == "existing-file":
                file = StoredFile()
                file.id = "existing-file"
                file.filename = "test.jpg"
                file.original_filename = "original_test.jpg"
                file.file_size = 1024
                file.file_type = "image"
                file.mime_type = "image/jpeg"
                file.category = "uploaded"
                file.description = "Test image"
                file.tags = ["test", "image"]
                file.project_id = None
                file.public_url = "https://test.com/test.jpg"
                file.object_key = "test/user/test.jpg"
                file.created_at = datetime.now()
                file.updated_at = datetime.now()
                file.processing_status = "completed"
                file.processing_metadata = {}
                file.image_width = 100
                file.image_height = 100
                file.image_format = "JPEG"
                file.has_thumbnail = True
                file.thumbnail_path = "test/user/test_thumb.jpg"
                file.user_id = "test_user_123"
                return file
            return None

        original_method = FileCRUD.get_file_by_id
        FileCRUD.get_file_by_id = mock_get_file_by_id

        yield

        FileCRUD.get_file_by_id = original_method

    @pytest.fixture
    def mock_download_crud(self):
        """Mock DownloadCRUD"""
        from app.crud import DownloadCRUD

        async def mock_get_download_stats(db, file_id):
            return {"total_downloads": 5}

        async def mock_create_download_record(db, **kwargs):
            from app.models import FileDownload

            download = FileDownload()
            download.id = "download123"
            return download

        original_stats = DownloadCRUD.get_download_stats
        original_create = DownloadCRUD.create_download_record

        DownloadCRUD.get_download_stats = mock_get_download_stats
        DownloadCRUD.create_download_record = mock_create_download_record

        yield

        DownloadCRUD.get_download_stats = original_stats
        DownloadCRUD.create_download_record = original_create

    def test_get_file_info_success(self, client, mock_file_crud, mock_download_crud):
        """Test getting file info successfully"""
        response = client.get("/api/v1/files/existing-file")

        assert response.status_code == 200
        result = response.json()

        assert result["file_id"] == "existing-file"
        assert result["filename"] == "test.jpg"
        assert result["original_filename"] == "original_test.jpg"
        assert result["file_type"] == "image"
        assert result["download_count"] == 5
        assert result["image_width"] == 100
        assert result["image_height"] == 100

    @patch("app.routers.download.settings.storage_backend", "local")
    def test_download_file_success_local(self, client, mock_file_crud, mock_download_crud):
        """Test downloading file from local storage"""
        response = client.get("/api/v1/download/existing-file")

        # Should attempt to stream the file
        assert response.status_code == 200

    @patch("app.routers.download.settings.storage_backend", "s3")
    def test_download_file_success_s3(self, client, mock_file_crud, mock_download_crud):
        """Test downloading file from S3 (redirect)"""
        response = client.get("/api/v1/download/existing-file", follow_redirects=False)

        # Should redirect to public URL
        assert response.status_code == 307  # Redirect
        assert "test.com" in response.headers.get("location", "")

    def test_serve_file_success(self, client, mock_file_crud, mock_download_crud):
        """Test serving file successfully"""
        with patch("app.routers.download.settings.storage_backend", "s3"):
            response = client.get("/api/v1/serve/existing-file", follow_redirects=False)

            # Should redirect to public URL for S3
            assert response.status_code == 307

    def test_serve_thumbnail_success(self, client, mock_file_crud, mock_download_crud):
        """Test serving thumbnail successfully"""
        response = client.get("/api/v1/serve/existing-file", params={"thumbnail": True})

        # Should attempt to serve thumbnail
        assert response.status_code == 200
