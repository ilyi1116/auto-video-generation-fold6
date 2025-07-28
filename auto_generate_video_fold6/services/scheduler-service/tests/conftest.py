import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app.config import settings

# 使用內存資料庫進行測試
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """模擬認證標頭"""
    # 在實際測試中，這裡應該生成有效的 JWT token
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def sample_schedule_data():
    """範例排程數據"""
    return {
        "video_id": 1,
        "platform": "tiktok",
        "scheduled_time": "2024-12-31T20:00:00Z",
        "title": "測試影片標題",
        "description": "這是一個測試影片的描述",
        "tags": ["測試", "影片"],
        "platform_settings": {"disable_comment": False},
    }
