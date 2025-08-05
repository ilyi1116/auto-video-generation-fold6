from unittest.mock import patch

import pytest
from app.database import Base, get_db
from app.main import app
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 測試資料庫設定
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
    return {"Authorization": "Bearer test_token"}


def test_health_check(client):
    """測試健康檢查端點"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    """測試根端點"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Trend Service" in response.json()["message"]


@patch("app.auth.verify_token")
def test_get_trending_topics(mock_verify_token, client, auth_headers):
    """測試獲取趨勢主題"""
    mock_verify_token.return_value = {"user_id": "1"}

    response = client.get("/api/v1/trends/trending", headers=auth_headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@patch("app.auth.verify_token")
def test_get_trending_topics_with_filters(mock_verify_token, client, auth_headers):
    """測試帶篩選條件的趨勢主題"""
    mock_verify_token.return_value = {"user_id": "1"}

    response = client.get(
        "/api/v1/trends/trending?platform=youtube&category=tech&limit=10",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@patch("app.auth.verify_token")
def test_get_viral_content(mock_verify_token, client, auth_headers):
    """測試獲取病毒式內容"""
    mock_verify_token.return_value = {"user_id": "1"}

    response = client.get("/api/v1/trends/viral", headers=auth_headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@patch("app.auth.verify_token")
def test_get_viral_content_with_filters(mock_verify_token, client, auth_headers):
    """測試帶篩選條件的病毒式內容"""
    mock_verify_token.return_value = {"user_id": "1"}

    response = client.get(
        "/api/v1/trends/viral?platform=tiktok&days=3&min_viral_score=80",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@patch("app.services.trend_analyzer.generate_trend_suggestions")
@patch("app.auth.verify_token")
@pytest.mark.asyncio
async def test_get_trend_suggestions(mock_verify_token, mock_suggestions, client, auth_headers):
    """測試獲取趨勢建議"""
    mock_verify_token.return_value = {"user_id": "1"}
    mock_suggestions.return_value = [
        {
            "keyword": "AI 教學",
            "trend_score": 85.2,
            "search_volume": 45000,
            "competition": "medium",
            "opportunity_score": 78.5,
            "platforms": ["youtube", "tiktok"],
            "hashtags": ["#AI教學", "#人工智慧"],
            "estimated_reach": 120000,
        }
    ]

    response = client.get("/api/v1/trends/suggestions", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "keyword" in data[0]
        assert "trend_score" in data[0]


@patch("app.services.trend_analyzer.fetch_realtime_trends")
@patch("app.auth.verify_token")
@pytest.mark.asyncio
async def test_get_realtime_trends(mock_verify_token, mock_fetch, client, auth_headers):
    """測試獲取實時趨勢"""
    mock_verify_token.return_value = {"user_id": "1"}
    mock_fetch.return_value = [{"keyword": "世界盃", "rank": 1, "growth": "+150%"}]

    response = client.get("/api/v1/trends/realtime/google", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "google"
    assert "trends" in data
    assert "last_updated" in data


@patch("app.auth.verify_token")
def test_get_trend_categories(mock_verify_token, client, auth_headers):
    """測試獲取趨勢分類"""
    mock_verify_token.return_value = {"user_id": "1"}

    response = client.get("/api/v1/trends/categories", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert isinstance(data["categories"], list)


@patch("app.services.trend_analyzer.get_trending_hashtags")
@patch("app.auth.verify_token")
@pytest.mark.asyncio
async def test_get_trending_hashtags(mock_verify_token, mock_hashtags, client, auth_headers):
    """測試獲取熱門標籤"""
    mock_verify_token.return_value = {"user_id": "1"}
    mock_hashtags.return_value = [{"tag": "#fyp", "posts": 1500000, "growth": "+25%"}]

    response = client.get("/api/v1/trends/hashtags/tiktok", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "tiktok"
    assert "hashtags" in data


@patch("app.services.trend_analyzer.refresh_platform_data")
@patch("app.auth.verify_token")
@pytest.mark.asyncio
async def test_refresh_platform_trends(mock_verify_token, mock_refresh, client, auth_headers):
    """測試刷新平台趨勢"""
    mock_verify_token.return_value = {"user_id": "1"}
    mock_refresh.return_value = {"updated_count": 15, "new_count": 8}

    response = client.post("/api/v1/trends/refresh/youtube", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "updated_count" in data
    assert "new_count" in data


@patch("app.services.trend_analyzer.get_keyword_performance_history")
@patch("app.auth.verify_token")
@pytest.mark.asyncio
async def test_get_keyword_performance(mock_verify_token, mock_performance, client, auth_headers):
    """測試獲取關鍵字表現"""
    mock_verify_token.return_value = {"user_id": "1"}
    mock_performance.return_value = {
        "keyword": "AI",
        "period": "30 days",
        "platforms": {"google": []},
        "summary": {"average_volume": 25000},
    }

    response = client.get(
        "/api/v1/trends/performance/AI?platforms=google&days=30",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "keyword" in data
    assert "period" in data


# 關鍵字路由測試
@patch("app.services.keyword_analyzer.analyze_keyword")
@patch("app.auth.verify_token")
@pytest.mark.asyncio
async def test_research_keyword(mock_verify_token, mock_analyze, client, auth_headers):
    """測試關鍵字研究"""
    mock_verify_token.return_value = {"user_id": "1"}
    mock_analyze.return_value = {
        "monthly_searches": 25000,
        "competition_level": "medium",
        "difficulty_score": 65.5,
        "opportunity_score": 72.8,
        "related_keywords": ["AI 教學", "AI 攻略"],
        "long_tail_keywords": ["AI 初學者指南"],
        "youtube_results": 150000,
        "tiktok_hashtag_views": 8500000,
        "instagram_posts": 45000,
    }

    research_data = {
        "keyword": "AI",
        "platforms": ["google", "youtube"],
        "region": "TW",
    }

    response = client.post("/api/v1/keywords/research", json=research_data, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["keyword"] == "AI"
    assert "monthly_searches" in data
    assert "difficulty_score" in data


@patch("app.services.keyword_analyzer.get_keyword_suggestions")
@patch("app.auth.verify_token")
@pytest.mark.asyncio
async def test_get_keyword_suggestions(mock_verify_token, mock_suggestions, client, auth_headers):
    """測試獲取關鍵字建議"""
    mock_verify_token.return_value = {"user_id": "1"}
    mock_suggestions.return_value = {
        "keywords": ["AI 教學", "AI 攻略"],
        "questions": ["如何學習 AI？"],
        "long_tail": ["AI 完整指南 2024"],
    }

    response = client.get("/api/v1/keywords/suggestions/AI?limit=10", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["seed_keyword"] == "AI"
    assert "suggestions" in data
    assert isinstance(data["suggestions"], list)


def test_unauthorized_access(client):
    """測試未授權存取"""
    response = client.get("/api/v1/trends/trending")
    assert response.status_code == 403


def test_invalid_token(client):
    """測試無效 token"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/trends/trending", headers=headers)
    assert response.status_code == 401


def test_invalid_platform_enum(client, auth_headers):
    """測試無效平台類型"""
    with patch("app.auth.verify_token") as mock_verify_token:
        mock_verify_token.return_value = {"user_id": "1"}

        response = client.get(
            "/api/v1/trends/trending?platform=invalid_platform",
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error


def test_pagination_limits(client, auth_headers):
    """測試分頁限制"""
    with patch("app.auth.verify_token") as mock_verify_token:
        mock_verify_token.return_value = {"user_id": "1"}

        # 測試超過限制的 limit 值
        response = client.get("/api/v1/trends/trending?limit=1000", headers=auth_headers)

        assert response.status_code == 422  # Validation error
