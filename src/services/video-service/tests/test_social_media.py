import os
import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from main import app
from social.platforms import PublishRequest, PublishResult, SocialMediaManager

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestSocialMediaAPI:
    """Test social media API endpoints"""

    @pytest.fixture
    def client(self):
        """Test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_auth(self):
        """Mock authentication"""
        with patch("main.verify_token") as mock_verify:
            mock_verify.return_value = "test_user_123"
            yield mock_verify

    @pytest.fixture
    def mock_social_manager(self):
        """Mock social media manager"""
        with patch("routers.social_media.social_manager") as mock_manager:
            # Mock available platforms
            mock_manager.get_available_platforms.return_value = [
                "youtube",
                "tiktok",
                "instagram",
            ]

            # Mock publish results
            mock_results = [
                PublishResult(
                    platform="youtube",
                    success=True,
                    platform_id="yt_12345",
                    url="https://youtube.com/watch?v=12345",
                    published_at=datetime.utcnow(),
                ),
                PublishResult(
                    platform="tiktok",
                    success=True,
                    platform_id="tt_67890",
                    url="https://tiktok.com/@user/video/67890",
                    published_at=datetime.utcnow(),
                ),
            ]

            mock_manager.publish_to_all = AsyncMock(return_value=mock_results)
            mock_manager.get_platform_stats = AsyncMock(
                return_value={"views": 1000, "likes": 50, "comments": 10}
            )
            mock_manager.health_check_all = AsyncMock(
                return_value={
                    "youtube": {"status": "healthy"},
                    "tiktok": {"status": "healthy"},
                }
            )
            mock_manager.delete_from_platform = AsyncMock(return_value=True)

            yield mock_manager

    def test_get_available_platforms(
        self, client, mock_auth, mock_social_manager
    ):
        """Test getting available platforms"""
        response = client.get(
            "/api/v1/social/platforms",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "platforms" in data
        assert data["total"] == 3

        # Check platform structure
        platform = data["platforms"][0]
        assert "id" in platform
        assert "name" in platform
        assert "connected" in platform

    def test_publish_to_social_media(
        self, client, mock_auth, mock_social_manager
    ):
        """Test publishing to social media platforms"""
        request_data = {
            "video_url": "https://example.com/video.mp4",
            "platforms": ["youtube", "tiktok"],
            "title": "Test Video",
            "description": "This is a test video",
            "tags": ["test", "video"],
            "privacy": "public",
        }

        response = client.post(
            "/api/v1/social/publish",
            json=request_data,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_platforms"] == 2
        assert data["successful_publishes"] == 2
        assert data["failed_publishes"] == 0
        assert len(data["results"]) == 2

        # Check result structure
        result = data["results"][0]
        assert "platform" in result
        assert "success" in result
        assert "platform_id" in result
        assert "url" in result

    def test_publish_invalid_platforms(
        self, client, mock_auth, mock_social_manager
    ):
        """Test publishing to invalid platforms"""
        request_data = {
            "video_url": "https://example.com/video.mp4",
            "platforms": ["invalid_platform"],
            "title": "Test Video",
        }

        response = client.post(
            "/api/v1/social/publish",
            json=request_data,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 400
        assert "Invalid platforms" in response.json()["detail"]

    def test_scheduled_publishing(
        self, client, mock_auth, mock_social_manager
    ):
        """Test scheduled publishing"""
        future_time = datetime.utcnow() + timedelta(hours=1)

        request_data = {
            "video_url": "https://example.com/video.mp4",
            "platforms": ["youtube"],
            "title": "Scheduled Video",
            "scheduled_time": future_time.isoformat(),
        }

        response = client.post(
            "/api/v1/social/publish",
            json=request_data,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "scheduled" in data["message"].lower()

    def test_get_video_stats(self, client, mock_auth, mock_social_manager):
        """Test getting video statistics"""
        response = client.get(
            "/api/v1/social/stats/youtube/yt_12345",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["platform"] == "youtube"
        assert data["platform_id"] == "yt_12345"
        assert "stats" in data
        assert "views" in data["stats"]
        assert "likes" in data["stats"]

    def test_platform_health_check(
        self, client, mock_auth, mock_social_manager
    ):
        """Test platform health check"""
        response = client.get(
            "/api/v1/social/platforms/health",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "connections" in data
        assert "total_platforms" in data
        assert "healthy_platforms" in data

        # Check connection structure
        if data["connections"]:
            connection = data["connections"][0]
            assert "platform" in connection
            assert "connected" in connection
            assert "last_check" in connection

    def test_delete_video(self, client, mock_auth, mock_social_manager):
        """Test deleting video from platform"""
        response = client.delete(
            "/api/v1/social/videos/youtube/yt_12345",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"]
        assert data["platform"] == "youtube"
        assert data["platform_id"] == "yt_12345"

    def test_get_platform_templates(self, client, mock_auth):
        """Test getting platform templates"""
        response = client.get(
            "/api/v1/social/templates/youtube",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "video_templates" in data
        assert "best_practices" in data

        # Check template structure
        template = data["video_templates"][0]
        assert "name" in template
        assert "description" in template
        assert "structure" in template
        assert "recommended_length" in template

    def test_get_invalid_platform_templates(self, client, mock_auth):
        """Test getting templates for invalid platform"""
        response = client.get(
            "/api/v1/social/templates/invalid_platform",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 404

    def test_schedule_publication(self, client, mock_auth):
        """Test scheduling publication"""
        future_time = datetime.utcnow() + timedelta(hours=2)

        request_data = {
            "video_url": "https://example.com/video.mp4",
            "platforms": ["youtube"],
            "title": "Scheduled Video",
            "scheduled_time": future_time.isoformat(),
        }

        response = client.post(
            "/api/v1/social/schedule",
            json=request_data,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "scheduled successfully" in data["message"]
        assert data["platforms"] == ["youtube"]

    def test_schedule_publication_past_time(self, client, mock_auth):
        """Test scheduling publication with past time"""
        past_time = datetime.utcnow() - timedelta(hours=1)

        request_data = {
            "video_url": "https://example.com/video.mp4",
            "platforms": ["youtube"],
            "title": "Invalid Scheduled Video",
            "scheduled_time": past_time.isoformat(),
        }

        response = client.post(
            "/api/v1/social/schedule",
            json=request_data,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 400
        assert "must be in the future" in response.json()["detail"]


class TestSocialMediaPlatforms:
    """Test social media platform integrations"""

    @pytest.mark.asyncio
    async def test_youtube_client_initialization(self):
        """Test YouTube client initialization"""
        from social.platforms import YouTubeClient

        client = YouTubeClient("test_api_key", "test_oauth_token")
        assert client.api_key == "test_api_key"
        assert client.oauth_token == "test_oauth_token"
        assert client.base_url == "https://www.googleapis.com/youtube/v3"

    @pytest.mark.asyncio
    async def test_tiktok_client_initialization(self):
        """Test TikTok client initialization"""
        from social.platforms import TikTokClient

        client = TikTokClient(
            "test_api_key", "test_client_id", "test_client_secret"
        )
        assert client.api_key == "test_api_key"
        assert client.client_id == "test_client_id"
        assert client.client_secret == "test_client_secret"

    @pytest.mark.asyncio
    async def test_instagram_client_initialization(self):
        """Test Instagram client initialization"""
        from social.platforms import InstagramClient

        client = InstagramClient("test_api_key", "test_business_id")
        assert client.api_key == "test_api_key"
        assert client.business_account_id == "test_business_id"

    @pytest.mark.asyncio
    async def test_social_media_manager(self):
        """Test social media manager"""
        with patch.dict(
            os.environ,
            {
                "YOUTUBE_API_KEY": "test_yt_key",
                "YOUTUBE_OAUTH_TOKEN": "test_yt_token",
                "TIKTOK_API_KEY": "test_tt_key",
                "TIKTOK_CLIENT_ID": "test_tt_id",
                "TIKTOK_CLIENT_SECRET": "test_tt_secret",
            },
        ):
            manager = SocialMediaManager()

            # Should initialize platforms based on env vars
            available = manager.get_available_platforms()
            assert "youtube" in available
            assert "tiktok" in available

    @pytest.mark.asyncio
    async def test_publish_to_platform_not_configured(self):
        """Test publishing to unconfigured platform"""
        manager = SocialMediaManager()

        request = PublishRequest(
            video_url="https://example.com/video.mp4", title="Test Video"
        )

        result = await manager.publish_to_platform(
            "unconfigured_platform", request
        )

        assert result.success is False
        assert "not configured" in result.error_message
        assert result.platform == "unconfigured_platform"

    @pytest.mark.asyncio
    async def test_publish_to_all_platforms(self):
        """Test publishing to all platforms"""
        with patch.dict(
            os.environ,
            {
                "YOUTUBE_API_KEY": "test_key",
                "YOUTUBE_OAUTH_TOKEN": "test_token",
            },
        ):
            manager = SocialMediaManager()

            # Mock the platform client
            mock_client = AsyncMock()
            mock_result = PublishResult(
                platform="youtube",
                success=True,
                platform_id="test_id",
                published_at=datetime.utcnow(),
            )
            mock_client.publish_video.return_value = mock_result
            manager.platforms["youtube"] = mock_client

            request = PublishRequest(
                video_url="https://example.com/video.mp4", title="Test Video"
            )

            results = await manager.publish_to_all(request, ["youtube"])

            assert len(results) == 1
            assert results[0].success is True
            assert results[0].platform == "youtube"

    @pytest.mark.asyncio
    async def test_platform_stats_not_configured(self):
        """Test getting stats from unconfigured platform"""
        manager = SocialMediaManager()

        stats = await manager.get_platform_stats(
            "unconfigured_platform", "test_id"
        )

        assert "error" in stats
        assert "not configured" in stats["error"]

    @pytest.mark.asyncio
    async def test_delete_from_platform_not_configured(self):
        """Test deleting from unconfigured platform"""
        manager = SocialMediaManager()

        result = await manager.delete_from_platform(
            "unconfigured_platform", "test_id"
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_health_check_all_platforms(self):
        """Test health check for all platforms"""
        with patch.dict(
            os.environ,
            {
                "YOUTUBE_API_KEY": "test_key",
                "YOUTUBE_OAUTH_TOKEN": "test_token",
            },
        ):
            manager = SocialMediaManager()

            # Mock platform client
            mock_client = AsyncMock()
            mock_client.health_check.return_value = {"status": "healthy"}
            manager.platforms["youtube"] = mock_client

            health_results = await manager.health_check_all()

            assert "youtube" in health_results
            assert health_results["youtube"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_close_all_platforms(self):
        """Test closing all platform connections"""
        manager = SocialMediaManager()

        # Mock platform client
        mock_client = AsyncMock()
        manager.platforms["test_platform"] = mock_client

        await manager.close_all()

        mock_client.close.assert_called_once()
