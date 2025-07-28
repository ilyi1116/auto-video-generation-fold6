import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Create a test client"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_auth_service():
    """Mock authentication service responses"""
    with patch("app.auth.get_current_user") as mock:
        mock.return_value = 1  # Return user ID 1
        yield mock


@pytest.fixture
def mock_s3_storage():
    """Mock S3 storage operations"""
    with patch("app.storage.s3_storage") as mock:
        mock.upload_file = AsyncMock(return_value="http://minio:9000/voice-data/test-file.wav")
        mock.delete_file = AsyncMock(return_value=True)
        mock.file_exists = AsyncMock(return_value=True)
        yield mock


@pytest.fixture
def mock_database():
    """Mock database operations"""
    with patch("app.database.database") as mock:
        mock.execute = AsyncMock(return_value=1)  # Return mock ID
        mock.fetch_one = AsyncMock()
        mock.fetch_all = AsyncMock(return_value=[])
        yield mock


@pytest.fixture
def sample_audio_file():
    """Sample audio file data for testing"""
    return {
        "filename": "test_audio.wav",
        "content": b"fake audio content",
        "content_type": "audio/wav",
        "size": 1024,
    }
