from unittest.mock import patch

import pytest
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_check():
    """測試健康檢查端點"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint():
    """測試根端點"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Social Service" in response.json()["message"]


def test_get_auth_url_tiktok():
    """測試獲取 TikTok 授權 URL"""
    response = client.get("/api/v1/platforms/auth/tiktok")

    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "tiktok"
    assert "auth_url" in data
    assert "tiktok" in data["auth_url"]


def test_get_auth_url_youtube():
    """測試獲取 YouTube 授權 URL"""
    response = client.get("/api/v1/platforms/auth/youtube")

    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "youtube"
    assert "auth_url" in data
    assert "google" in data["auth_url"]


def test_get_auth_url_instagram():
    """測試獲取 Instagram 授權 URL"""
    response = client.get("/api/v1/platforms/auth/instagram")

    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "instagram"
    assert "auth_url" in data
    assert "instagram" in data["auth_url"]


def test_get_auth_url_unsupported_platform():
    """測試不支援的平台"""
    response = client.get("/api/v1/platforms/auth/unsupported")

    assert response.status_code == 400
    assert "Unsupported platform" in response.json()["detail"]


@patch("app.platforms.tiktok.exchange_code_for_token")
@pytest.mark.asyncio
async def test_oauth_callback_tiktok_success(mock_exchange):
    """測試 TikTok OAuth 回調成功"""
    mock_exchange.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer",
    }

    callback_data = {"code": "test_authorization_code", "state": "test_state"}

    response = client.post(
        "/api/v1/platforms/auth/tiktok/callback", json=callback_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"] == "test_access_token"
    assert data["token_type"] == "Bearer"


@patch("app.platforms.tiktok.exchange_code_for_token")
@pytest.mark.asyncio
async def test_oauth_callback_tiktok_failure(mock_exchange):
    """測試 TikTok OAuth 回調失敗"""
    mock_exchange.side_effect = Exception("Token exchange failed")

    callback_data = {"code": "invalid_code"}

    response = client.post(
        "/api/v1/platforms/auth/tiktok/callback", json=callback_data
    )

    assert response.status_code == 400
    assert "Authentication failed" in response.json()["detail"]


@patch("app.platforms.tiktok.publish_video")
@pytest.mark.asyncio
async def test_publish_to_tiktok_success(mock_publish):
    """測試成功發布到 TikTok"""
    mock_publish.return_value = {
        "success": True,
        "post_id": "tiktok_post_123",
        "post_url": "https://www.tiktok.com/@user/video/123",
    }

    publish_data = {
        "video_id": 1,
        "access_token": "test_token",
        "title": "測試影片",
        "description": "這是一個測試影片",
        "tags": ["測試", "影片"],
        "settings": {"disable_comment": False},
    }

    response = client.post(
        "/api/v1/platforms/tiktok/publish", json=publish_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["post_id"] == "tiktok_post_123"


@patch("app.platforms.tiktok.publish_video")
@pytest.mark.asyncio
async def test_publish_to_tiktok_failure(mock_publish):
    """測試發布到 TikTok 失敗"""
    mock_publish.side_effect = Exception("Publish failed")

    publish_data = {
        "video_id": 1,
        "access_token": "test_token",
        "title": "測試影片",
    }

    response = client.post(
        "/api/v1/platforms/tiktok/publish", json=publish_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "Failed to publish to TikTok" in data["error"]


@patch("app.platforms.youtube.publish_video")
@pytest.mark.asyncio
async def test_publish_to_youtube_success(mock_publish):
    """測試成功發布到 YouTube"""
    mock_publish.return_value = {
        "success": True,
        "post_id": "youtube_video_456",
        "post_url": "https://www.youtube.com/watch?v=456",
    }

    publish_data = {
        "video_id": 1,
        "access_token": "test_token",
        "title": "測試 YouTube 影片",
        "description": "這是一個測試 YouTube 影片",
        "tags": ["教學", "測試"],
    }

    response = client.post(
        "/api/v1/platforms/youtube/publish", json=publish_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["post_id"] == "youtube_video_456"


@patch("app.platforms.instagram.publish_video")
@pytest.mark.asyncio
async def test_publish_to_instagram_success(mock_publish):
    """測試成功發布到 Instagram"""
    mock_publish.return_value = {
        "success": True,
        "post_id": "instagram_post_789",
        "post_url": "https://www.instagram.com/p/789/",
    }

    publish_data = {
        "video_id": 1,
        "access_token": "test_token",
        "title": "測試 Instagram 影片",
        "description": "這是一個測試 Instagram 影片",
        "tags": ["instagram", "測試"],
    }

    response = client.post(
        "/api/v1/platforms/instagram/publish", json=publish_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["post_id"] == "instagram_post_789"


@patch("app.platforms.tiktok.check_api_status")
@pytest.mark.asyncio
async def test_check_platform_status_tiktok(mock_status):
    """測試檢查 TikTok 平台狀態"""
    mock_status.return_value = "healthy"

    response = client.get("/api/v1/platforms/status/tiktok")

    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "tiktok"
    assert data["status"] == "healthy"


@patch("app.platforms.youtube.check_api_status")
@pytest.mark.asyncio
async def test_check_platform_status_error(mock_status):
    """測試平台狀態檢查錯誤"""
    mock_status.side_effect = Exception("API Error")

    response = client.get("/api/v1/platforms/status/youtube")

    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == "youtube"
    assert data["status"] == "error"
    assert "error" in data


def test_check_platform_status_unsupported():
    """測試不支援的平台狀態檢查"""
    response = client.get("/api/v1/platforms/status/unsupported")

    assert response.status_code == 400
    assert "Unsupported platform" in response.json()["detail"]


def test_oauth_callback_unsupported_platform():
    """測試不支援平台的 OAuth 回調"""
    callback_data = {"code": "test_code"}

    response = client.post(
        "/api/v1/platforms/auth/unsupported/callback", json=callback_data
    )

    assert response.status_code == 400
    assert "Unsupported platform" in response.json()["detail"]


def test_publish_request_validation():
    """測試發布請求的資料驗證"""
    # 缺少必要欄位
    invalid_data = {
        "access_token": "test_token"
        # 缺少 video_id
    }

    response = client.post(
        "/api/v1/platforms/tiktok/publish", json=invalid_data
    )

    assert response.status_code == 422  # Validation error


def test_oauth_callback_missing_code():
    """測試 OAuth 回調缺少授權碼"""
    callback_data = {}  # 缺少 code

    response = client.post(
        "/api/v1/platforms/auth/tiktok/callback", json=callback_data
    )

    assert response.status_code == 422  # Validation error
