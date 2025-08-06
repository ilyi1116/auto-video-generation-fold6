"""
Test Configuration and Fixtures
Shared test fixtures and configuration for all test suites
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test environment setup
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Use test database


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_database():
    """Setup test database"""
    from src.shared.database import Base, engine

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    """Create a test database session"""
    from src.shared.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
def mock_ai_services():
    """Mock AI services for testing"""

    # Mock Gemini Client
    mock_gemini = AsyncMock()
    mock_gemini.generate_script.return_value = type(
        "ScriptResponse",
        (),
        {
            "content": "Test script content",
            "scenes": [
                type(
                    "Scene",
                    (),
                    {"visual_description": "Test scene description", "narration": "Test narration"},
                )()
            ],
            "narration_text": "Complete test narration",
        },
    )()
    mock_gemini.health_check.return_value = {"status": "healthy"}

    # Mock Suno Client
    mock_suno = AsyncMock()
    mock_suno.generate_voice.return_value = type(
        "VoiceResponse",
        (),
        {"audio_url": "https://test.com/audio.mp3", "music_url": "https://test.com/music.mp3"},
    )()
    mock_suno.health_check.return_value = {"status": "healthy"}

    # Mock Stable Diffusion Client
    mock_sd = AsyncMock()
    mock_sd.generate_image.return_value = type(
        "ImageResponse", (), {"url": "https://test.com/image.jpg"}
    )()
    mock_sd.health_check.return_value = {"status": "healthy"}

    # Mock Video Composer
    mock_composer = AsyncMock()
    mock_composer.create_video.return_value = type(
        "CompositionResult",
        (),
        {"composition_id": "test_comp_123", "preview_url": "https://test.com/preview.jpg"},
    )()
    mock_composer.render_final.return_value = type(
        "FinalResult",
        (),
        {
            "video_url": "https://test.com/final.mp4",
            "thumbnail_url": "https://test.com/thumb.jpg",
            "duration": 30,
            "file_size": 10485760,
        },
    )()

    return {
        "gemini_client": mock_gemini,
        "suno_client": mock_suno,
        "stable_diffusion_client": mock_sd,
        "video_composer": mock_composer,
    }


@pytest.fixture
def mock_redis():
    """Mock Redis for testing"""
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True
    mock_redis.lpush.return_value = 1
    mock_redis.rpop.return_value = None
    mock_redis.zadd.return_value = 1
    mock_redis.zrangebyscore.return_value = []
    mock_redis.llen.return_value = 0
    mock_redis.zcard.return_value = 0
    mock_redis.ltrim.return_value = True
    mock_redis.zrem.return_value = 1
    return mock_redis


@pytest.fixture
def mock_service_registry():
    """Mock service registry for testing"""
    from src.shared.services import (
        ServiceInstance,
        ServiceRegistry,
        ServiceStatus,
    )

    registry = ServiceRegistry()

    # Register test services
    test_services = [
        ServiceInstance("auth-service", "localhost", 8001, status=ServiceStatus.HEALTHY),
        ServiceInstance("video-service", "localhost", 8003, status=ServiceStatus.HEALTHY),
        ServiceInstance("ai-service", "localhost", 8004, status=ServiceStatus.HEALTHY),
        ServiceInstance("user-service", "localhost", 8002, status=ServiceStatus.HEALTHY),
        ServiceInstance("storage-service", "localhost", 8009, status=ServiceStatus.HEALTHY),
    ]

    for service in test_services:
        registry.register_service(service)

    return registry


@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User",
        "subscription_tier": "pro",
    }


@pytest.fixture
def test_video_data():
    """Test video generation data"""
    return {
        "title": "Test Video",
        "description": "Test video description",
        "theme": "technology",
        "style": "modern",
        "duration": 30,
        "voice_type": "professional",
        "music_genre": "ambient",
        "include_captions": True,
        "target_platform": "youtube",
    }


@pytest.fixture
def temp_directory():
    """Create temporary directory for test files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_file_storage():
    """Mock file storage for testing"""
    mock_storage = AsyncMock()
    mock_storage.upload_file.return_value = "https://test.com/uploaded_file.mp4"
    mock_storage.delete_file.return_value = True
    mock_storage.get_file_url.return_value = "https://test.com/file.mp4"
    return mock_storage


@pytest.fixture
async def test_message_queue():
    """Setup test message queue"""
    from src.shared.services import MessageQueue

    # Use in-memory queue for testing
    queue = MessageQueue("redis://localhost:6379/15")

    with patch("src.shared.services.message_queue.get_message_queue", return_value=queue):
        try:
            await queue.start()
            yield queue
        finally:
            await queue.stop()


@pytest.fixture
def authenticated_headers():
    """Headers with authentication token"""
    return {"Authorization": "Bearer test_jwt_token", "Content-Type": "application/json"}


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token verification"""
    with patch("src.services.video_service.auth.verify_token") as mock_verify:
        mock_verify.return_value = 123  # Test user ID
        yield mock_verify


# Test data factories
class TestDataFactory:
    """Factory for creating test data"""

    @staticmethod
    def create_user_data(**overrides):
        """Create user data with optional overrides"""
        default_data = {
            "email": "test@example.com",
            "password": "password123",
            "full_name": "Test User",
            "subscription_tier": "free",
        }
        default_data.update(overrides)
        return default_data

    @staticmethod
    def create_video_data(**overrides):
        """Create video data with optional overrides"""
        default_data = {
            "title": "Test Video",
            "description": "Test video description",
            "theme": "technology",
            "style": "modern",
            "duration": 30,
            "voice_type": "professional",
            "music_genre": "ambient",
            "include_captions": True,
            "target_platform": "youtube",
        }
        default_data.update(overrides)
        return default_data


@pytest.fixture
def test_data_factory():
    """Test data factory fixture"""
    return TestDataFactory


# Custom markers for different test types
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "requires_redis: Tests that require Redis")
    config.addinivalue_line("markers", "requires_db: Tests that require database")


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify collected test items"""
    # Add markers based on test location
    for item in items:
        # Add markers based on file path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)

        # Add database marker for tests that use db fixtures
        if any(fixture in item.fixturenames for fixture in ["db_session", "test_database"]):
            item.add_marker(pytest.mark.requires_db)

        # Add Redis marker for tests that use Redis fixtures
        if any(fixture in item.fixturenames for fixture in ["mock_redis", "test_message_queue"]):
            item.add_marker(pytest.mark.requires_redis)


# Test reporting hooks
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    """Custom test protocol for reporting"""
    # Add test metadata
    item.user_properties.append(("test_type", getattr(item, "_pytest_mark_name", "unknown")))
    return None
