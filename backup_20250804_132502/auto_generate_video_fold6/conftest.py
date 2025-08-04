"""
全局測試配置檔案
為所有後端服務提供共用的測試設定和 fixtures
"""

import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 設定測試環境變數
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
os.environ["AWS_ACCESS_KEY_ID"] = "test"
os.environ["AWS_SECRET_ACCESS_KEY"] = "test"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """創建事件循環供整個測試會話使用"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """創建測試用的異步資料庫引擎"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
        echo=True,
    )
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """創建測試用的資料庫會話"""
    async with test_engine.begin() as conn:
        async_session = sessionmaker(
            conn, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            yield session


@pytest.fixture
def mock_redis():
    """Mock Redis 客戶端"""
    redis_mock = MagicMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=1)
    redis_mock.exists = AsyncMock(return_value=False)
    redis_mock.expire = AsyncMock(return_value=True)
    redis_mock.keys = AsyncMock(return_value=[])
    redis_mock.hget = AsyncMock(return_value=None)
    redis_mock.hset = AsyncMock(return_value=True)
    redis_mock.hgetall = AsyncMock(return_value={})
    return redis_mock


@pytest.fixture
def mock_s3():
    """Mock S3 客戶端"""
    s3_mock = MagicMock()
    s3_mock.upload_file = MagicMock(return_value=True)
    s3_mock.download_file = MagicMock(return_value=True)
    s3_mock.delete_object = MagicMock(return_value=True)
    s3_mock.generate_presigned_url = MagicMock(
        return_value="https://test-bucket.s3.amazonaws.com/test-file"
    )
    return s3_mock


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """創建異步 HTTP 客戶端供測試使用"""
    async with AsyncClient(
        base_url="http://testserver", timeout=30.0
    ) as client:
        yield client


@pytest.fixture
def sample_user_data():
    """提供測試用戶資料"""
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "is_active": True,
        "is_verified": True,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_project_data():
    """提供測試專案資料"""
    return {
        "id": 1,
        "title": "Test Project",
        "description": "A test project for automated testing",
        "status": "draft",
        "user_id": 1,
        "settings": {
            "platform": "youtube",
            "duration": "short",
            "tone": "professional",
        },
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def sample_script_data():
    """提供測試腳本資料"""
    return {
        "id": 1,
        "title": "Test Script",
        "content": "This is a test script content for automated testing.",
        "scenes": [
            {
                "id": 1,
                "text": "Welcome to our test video",
                "duration": 3,
                "type": "intro",
            },
            {
                "id": 2,
                "text": "This is the main content of our test",
                "duration": 8,
                "type": "content",
            },
            {
                "id": 3,
                "text": "Thank you for watching",
                "duration": 2,
                "type": "outro",
            },
        ],
        "metadata": {
            "duration": 13,
            "word_count": 85,
            "reading_time": "13 seconds",
        },
        "project_id": 1,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def mock_ai_service():
    """Mock AI 服務客戶端"""
    ai_mock = MagicMock()

    # Mock 文本生成
    ai_mock.generate_script = AsyncMock(
        return_value={
            "title": "Generated Test Script",
            "content": "This is AI generated content for testing.",
            "scenes": [
                {
                    "id": 1,
                    "text": "Generated intro",
                    "duration": 3,
                    "type": "intro",
                },
                {
                    "id": 2,
                    "text": "Generated content",
                    "duration": 8,
                    "type": "content",
                },
                {
                    "id": 3,
                    "text": "Generated outro",
                    "duration": 2,
                    "type": "outro",
                },
            ],
            "metadata": {
                "duration": 13,
                "word_count": 67,
                "reading_time": "13 seconds",
            },
        }
    )

    # Mock 圖像生成
    ai_mock.generate_image = AsyncMock(
        return_value={
            "image_url": "https://test-bucket.s3.amazonaws.com/generated-image.jpg",
            "width": 1920,
            "height": 1080,
            "format": "jpg",
        }
    )

    # Mock 語音合成
    ai_mock.synthesize_speech = AsyncMock(
        return_value={
            "audio_url": "https://test-bucket.s3.amazonaws.com/synthesized-audio.wav",
            "duration": 13.5,
            "format": "wav",
            "sample_rate": 44100,
        }
    )

    return ai_mock


@pytest.fixture
def mock_celery():
    """Mock Celery 任務隊列"""
    celery_mock = MagicMock()

    # Mock 任務狀態
    task_result_mock = MagicMock()
    task_result_mock.id = "test-task-id"
    task_result_mock.status = "SUCCESS"
    task_result_mock.result = {"status": "completed", "output": "test-output"}
    task_result_mock.ready = MagicMock(return_value=True)
    task_result_mock.successful = MagicMock(return_value=True)
    task_result_mock.get = MagicMock(return_value={"status": "completed"})

    celery_mock.send_task = MagicMock(return_value=task_result_mock)
    celery_mock.AsyncResult = MagicMock(return_value=task_result_mock)

    return celery_mock


@pytest.fixture
def auth_headers(sample_user_data):
    """提供認證標頭"""
    # 在實際實現中，這裡會生成真實的 JWT token
    fake_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"
    return {
        "Authorization": f"Bearer {fake_token}",
        "Content-Type": "application/json",
    }


# 測試標記設定
pytest_plugins = []


# Pytest 配置
def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line(
        "markers", "requires_db: marks tests that require database"
    )
    config.addinivalue_line(
        "markers", "requires_redis: marks tests that require Redis"
    )
    config.addinivalue_line(
        "markers", "requires_s3: marks tests that require S3"
    )


# 自動使用 fixtures
@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """自動設定測試環境"""
    # 設定環境變數
    monkeypatch.setenv("TESTING", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    # 禁用外部服務調用
    monkeypatch.setenv("DISABLE_EXTERNAL_APIS", "true")


# 清理函數
@pytest.fixture(autouse=True)
async def cleanup_after_test():
    """每個測試後的清理"""
    yield
    # 這裡可以添加清理邏輯，例如清理臨時檔案、重置狀態等
