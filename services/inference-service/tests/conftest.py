import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock

from app.main import app


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
    with patch('app.auth.get_current_user') as mock:
        mock.return_value = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com"
        }
        yield mock


@pytest.fixture
def mock_database():
    """Mock database operations"""
    with patch('app.database.database') as mock:
        mock.execute = AsyncMock(return_value=1)  # Return mock ID
        mock.fetch_one = AsyncMock()
        mock.fetch_all = AsyncMock(return_value=[])
        yield mock


@pytest.fixture
def mock_s3_storage():
    """Mock S3 storage operations"""
    with patch('app.storage.s3_storage') as mock:
        mock.upload_audio = AsyncMock(return_value="http://minio:9000/voice-models/test-audio.wav")
        mock.delete_file = AsyncMock(return_value=True)
        mock.file_exists = AsyncMock(return_value=True)
        yield mock


@pytest.fixture
def mock_model_manager():
    """Mock model manager operations"""
    with patch('app.services.model_manager.model_manager') as mock:
        mock_model = MagicMock()
        mock_model.synthesize = AsyncMock(return_value=b"fake audio data")
        mock.get_model = AsyncMock(return_value=mock_model)
        mock.get_cache_stats = AsyncMock(return_value={
            "cached_models": 1,
            "max_cache_size": 3,
            "cache_ttl": 3600,
            "model_ids": [1],
            "oldest_cache_age": 100.0
        })
        yield mock


@pytest.fixture
def sample_voice_model():
    """Sample voice model data for testing"""
    return {
        "id": 1,
        "user_id": 1,
        "name": "Test Voice Model",
        "description": "A test voice model",
        "model_type": "tacotron2",
        "language": "en",
        "status": "ready",
        "model_path": "models/test_model",
        "config_data": '{"sample_rate": 22050}',
        "training_data_size": 100,
        "training_duration": 3600.0,
        "quality_score": 0.95
    }


@pytest.fixture
def sample_synthesis_request():
    """Sample synthesis request data"""
    return {
        "text": "Hello, this is a test synthesis.",
        "model_id": 1,
        "speed": 1.0,
        "pitch": 1.0,
        "volume": 1.0,
        "emotion": "neutral",
        "return_audio": False
    }