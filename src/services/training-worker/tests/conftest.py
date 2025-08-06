"""
training-worker 服務測試配置
提供通用的測試 fixtures 和配置
"""

import asyncio
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# TODO: 導入應用相關模組
# from app.main import app
# from app.database import Base, get_db
# from app.config import settings

# 測試數據庫設置
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


@pytest.fixture(scope="session")
def event_loop():
    """創建事件循環 fixture"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_engine():
    """數據庫引擎 fixture"""
    # TODO: 創建測試表
    # Base.metadata.create_all(bind=engine)
    yield engine
    # TODO: 清理測試表
    # Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """數據庫會話 fixture"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """測試客戶端 fixture"""
    # TODO: 配置測試客戶端
    # with TestClient(app) as test_client:
    #     yield test_client
    pass


@pytest.fixture
def auth_headers():
    """認證頭部 fixture"""
    # TODO: 創建測試認證令牌
    token = "test_token_here"
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_user_data():
    """示例用戶數據 fixture"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    }


@pytest.fixture
def mock_external_service():
    """模擊外部服務 fixture"""
    mock_service = Mock()
    mock_service.call_api.return_value = {
        "status": "success",
        "data": "test_data",
    }
    return mock_service


@pytest.fixture(autouse=True)
def setup_test_environment():
    """自動運行的測試環境設置"""
    # TODO: 設置測試環境變量
    # os.environ["ENVIRONMENT"] = "testing"
    # os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    yield
    # TODO: 清理測試環境
    pass


# TODO: 添加更多通用 fixtures
# TODO: 添加測試數據工廠
# TODO: 添加性能測試配置
