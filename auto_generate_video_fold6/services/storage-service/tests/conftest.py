import pytest
import asyncio
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from app.main import app
from app.database import get_db
from app.models import Base
from app.config import settings


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def db_session():
    """Create a test database session"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_db():
    """Mock database dependency"""
    async def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_storage():
    """Mock storage manager"""
    from app.storage import storage_manager
    
    original_upload = storage_manager.upload_file
    original_download = storage_manager.download_file
    original_delete = storage_manager.delete_file
    original_validate = storage_manager.validate_file_type
    
    async def mock_upload_file(file_data, filename, content_type, user_id, file_type, category):
        return {
            "object_key": f"test/{user_id}/{filename}",
            "file_size": 1024,
            "content_type": content_type,
            "file_hash": "test_hash_123",
            "public_url": f"https://test.com/test/{user_id}/{filename}"
        }
    
    async def mock_download_file(object_key):
        return b"test file content"
    
    async def mock_delete_file(object_key):
        return True
    
    def mock_validate_file_type(mime_type, file_type):
        return True
    
    storage_manager.upload_file = mock_upload_file
    storage_manager.download_file = mock_download_file
    storage_manager.delete_file = mock_delete_file
    storage_manager.validate_file_type = mock_validate_file_type
    
    yield storage_manager
    
    # Restore original methods
    storage_manager.upload_file = original_upload
    storage_manager.download_file = original_download
    storage_manager.delete_file = original_delete
    storage_manager.validate_file_type = original_validate


@pytest.fixture
def mock_auth():
    """Mock authentication"""
    from app.auth import get_current_user
    
    async def mock_get_current_user():
        return {"id": "test_user_123", "email": "test@example.com"}
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(mock_db, mock_storage, mock_auth):
    """Test client with mocked dependencies"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def test_file():
    """Create a test file"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"This is a test file content")
        f.flush()
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def test_image():
    """Create a test image file"""
    from PIL import Image
    import io
    
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes


@pytest.fixture
def sample_file_data():
    """Sample file data for testing"""
    return {
        "original_filename": "test.jpg",
        "filename": "processed_test.jpg",
        "file_path": "test/user123/processed_test.jpg",
        "file_size": 1024,
        "mime_type": "image/jpeg",
        "file_hash": "abc123",
        "file_type": "image",
        "category": "uploaded",
        "storage_backend": "local",
        "bucket_name": None,
        "object_key": "test/user123/processed_test.jpg",
        "public_url": "https://test.com/test.jpg",
        "description": "Test image",
        "tags": ["test", "image"],
        "is_processed": False,
        "processing_status": "pending"
    }