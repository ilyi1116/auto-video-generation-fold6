from datetime import datetime, timedelta
from unittest.mock import patch

import pytest


def test_health_check(client):
    """測試健康檢查端點"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    """測試根端點"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Scheduler Service" in response.json()["message"]


@patch("app.auth.verify_token")
def test_schedule_post_success(
    mock_verify_token, client, sample_schedule_data, auth_headers
):
    """測試成功建立排程貼文"""
    mock_verify_token.return_value = {"user_id": "1"}

    # 設定未來時間
    future_time = (datetime.utcnow() + timedelta(hours=2)).isoformat() + "Z"
    sample_schedule_data["scheduled_time"] = future_time

    response = client.post(
        "/api/v1/schedule/posts",
        json=sample_schedule_data,
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == sample_schedule_data["video_id"]
    assert data["platform"] == sample_schedule_data["platform"]
    assert data["status"] == "pending"


@patch("app.auth.verify_token")
def test_schedule_post_past_time(
    mock_verify_token, client, sample_schedule_data, auth_headers
):
    """測試排程過去時間應該失敗"""
    mock_verify_token.return_value = {"user_id": "1"}

    # 設定過去時間
    past_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
    sample_schedule_data["scheduled_time"] = past_time

    response = client.post(
        "/api/v1/schedule/posts",
        json=sample_schedule_data,
        headers=auth_headers,
    )

    assert response.status_code == 400
    assert "future" in response.json()["detail"]


@patch("app.auth.verify_token")
def test_get_scheduled_posts(mock_verify_token, client, auth_headers):
    """測試獲取排程列表"""
    mock_verify_token.return_value = {"user_id": "1"}

    response = client.get("/api/v1/schedule/posts", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert "page" in data
    assert "page_size" in data


@patch("app.auth.verify_token")
def test_get_scheduled_posts_with_filters(
    mock_verify_token, client, auth_headers
):
    """測試帶篩選條件的排程列表"""
    mock_verify_token.return_value = {"user_id": "1"}

    response = client.get(
        "/api/v1/schedule/posts?status=pending&platform=tiktok&page=1&page_size=5",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 5


@patch("app.auth.verify_token")
def test_get_scheduled_post_not_found(mock_verify_token, client, auth_headers):
    """測試獲取不存在的排程貼文"""
    mock_verify_token.return_value = {"user_id": "1"}

    response = client.get("/api/v1/schedule/posts/999", headers=auth_headers)

    assert response.status_code == 404


@patch("app.auth.verify_token")
def test_cancel_scheduled_post_not_found(
    mock_verify_token, client, auth_headers
):
    """測試取消不存在的排程貼文"""
    mock_verify_token.return_value = {"user_id": "1"}

    response = client.delete(
        "/api/v1/schedule/posts/999", headers=auth_headers
    )

    assert response.status_code == 404


@patch("app.auth.verify_token")
def test_connect_platform_account(mock_verify_token, client, auth_headers):
    """測試連接平台帳號"""
    mock_verify_token.return_value = {"user_id": "1"}

    account_data = {
        "platform": "tiktok",
        "platform_user_id": "tiktok_user_123",
        "platform_username": "test_user",
        "access_token": "access_token_123",
        "refresh_token": "refresh_token_123",
    }

    response = client.post(
        "/api/v1/schedule/accounts", json=account_data, headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["platform"] == account_data["platform"]
    assert data["platform_user_id"] == account_data["platform_user_id"]
    assert data["is_active"] == True


@patch("app.auth.verify_token")
def test_get_platform_accounts(mock_verify_token, client, auth_headers):
    """測試獲取平台帳號列表"""
    mock_verify_token.return_value = {"user_id": "1"}

    response = client.get("/api/v1/schedule/accounts", headers=auth_headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@patch("app.auth.verify_token")
def test_disconnect_platform_account_not_found(
    mock_verify_token, client, auth_headers
):
    """測試斷開不存在的平台帳號"""
    mock_verify_token.return_value = {"user_id": "1"}

    response = client.delete(
        "/api/v1/schedule/accounts/999", headers=auth_headers
    )

    assert response.status_code == 404


@patch("app.tasks.publish_post.delay")
@patch("app.auth.verify_token")
def test_publish_now_not_found(
    mock_verify_token, mock_publish_task, client, auth_headers
):
    """測試立即發布不存在的貼文"""
    mock_verify_token.return_value = {"user_id": "1"}

    response = client.post(
        "/api/v1/schedule/posts/999/publish", headers=auth_headers
    )

    assert response.status_code == 404


def test_invalid_token(client):
    """測試無效的認證 token"""
    invalid_headers = {"Authorization": "Bearer invalid_token"}

    response = client.get("/api/v1/schedule/posts", headers=invalid_headers)

    assert response.status_code == 401


def test_missing_token(client):
    """測試缺少認證 token"""
    response = client.get("/api/v1/schedule/posts")
    assert response.status_code == 403  # FastAPI HTTPBearer 回傳 403


def test_invalid_platform_enum(client, auth_headers):
    """測試無效的平台類型"""
    with patch("app.auth.verify_token") as mock_verify_token:
        mock_verify_token.return_value = {"user_id": "1"}

        invalid_data = {
            "video_id": 1,
            "platform": "invalid_platform",
            "scheduled_time": (
                datetime.utcnow() + timedelta(hours=2)
            ).isoformat()
            + "Z",
        }

        response = client.post(
            "/api/v1/schedule/posts", json=invalid_data, headers=auth_headers
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_celery_task_exists():
    """測試 Celery 任務是否正確定義"""
    from app.tasks import (
        check_scheduled_posts,
        cleanup_old_posts,
        publish_post,
    )

    # 檢查任務函數存在
    assert publish_post is not None
    assert check_scheduled_posts is not None
    assert cleanup_old_posts is not None

    # 檢查任務名稱
    assert publish_post.name == "app.tasks.publish_post"
    assert check_scheduled_posts.name == "app.tasks.check_scheduled_posts"
    assert cleanup_old_posts.name == "app.tasks.cleanup_old_posts"
