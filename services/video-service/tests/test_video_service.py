"""
Video Service Tests

Test suite for video generation service functionality
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient

from main import app
from models.video_project import VideoProject, VideoStatus
from ai.suno_client import SunoAIClient
from ai.gemini_client import (
    GeminiClient,
    ScriptGenerationResponse,
    ScriptScene,
)
from ai.stable_diffusion_client import (
    StableDiffusionClient,
    ImageGenerationResponse,
)

client = TestClient(app)


@pytest.fixture
def mock_db():
    """Mock database connection"""
    return Mock()


@pytest.fixture
def mock_auth_token():
    """Mock valid JWT token"""
    return "valid_jwt_token"


@pytest.fixture
def sample_video_request():
    """Sample video generation request"""
    return {
        "title": "Test Video",
        "description": "A test video for unit testing",
        "theme": "Technology trends in 2024",
        "style": "modern",
        "duration": 60,
        "voice_type": "default",
        "music_genre": "ambient",
        "include_captions": True,
        "target_platform": "youtube",
    }


@pytest.fixture
def sample_script_response():
    """Sample script generation response"""
    scenes = [
        ScriptScene(
            sequence=1,
            duration=20.0,
            narration_text="Welcome to our technology overview",
            visual_description="Modern office with computers and tech gadgets",
            scene_type="intro",
            keywords=["technology", "modern", "office"],
        ),
        ScriptScene(
            sequence=2,
            duration=25.0,
            narration_text="AI is transforming how we work",
            visual_description="AI robots working alongside humans",
            scene_type="main",
            keywords=["AI", "robots", "collaboration"],
        ),
        ScriptScene(
            sequence=3,
            duration=15.0,
            narration_text="Thank you for watching",
            visual_description="Call to action screen with subscribe button",
            scene_type="outro",
            keywords=["subscribe", "call-to-action"],
        ),
    ]

    return ScriptGenerationResponse(
        content="Full script content here...",
        scenes=scenes,
        narration_text=(
            "Welcome to our technology overview. "
            "AI is transforming how we work. "
            "Thank you for watching."
        ),
        total_duration=60.0,
        theme="Technology trends in 2024",
        style="modern",
        generation_id="script_123",
        created_at=datetime.utcnow(),
    )


class TestVideoServiceHealth:
    """Test health check endpoint"""

    def test_health_check(self):
        """Test health check returns correct status"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "video-generation"
        assert "timestamp" in data


class TestVideoGeneration:
    """Test video generation functionality"""

    @patch("main.verify_token")
    @patch("main.get_db_connection")
    def test_create_video_project_success(
        self, mock_db, mock_verify_token, sample_video_request
    ):
        """Test successful video project creation"""

        # Mock authentication
        mock_verify_token.return_value = "user123"
        mock_db.return_value = Mock()

        # Mock headers
        headers = {"Authorization": "Bearer valid_token"}

        response = client.post(
            "/api/v1/video/generate",
            json=sample_video_request,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "project_id" in data
        assert data["title"] == sample_video_request["title"]
        assert data["status"] == VideoStatus.INITIALIZING
        assert data["progress"] == 0

    def test_create_video_project_unauthorized(self, sample_video_request):
        """Test video project creation without authentication"""

        response = client.post(
            "/api/v1/video/generate", json=sample_video_request
        )
        assert response.status_code == 403  # Missing Authorization header

    @patch("main.verify_token")
    @patch("main.get_db_connection")
    def test_get_video_project(self, mock_db, mock_verify_token):
        """Test retrieving video project details"""

        # Mock authentication
        mock_verify_token.return_value = "user123"

        # Mock database response
        mock_project = VideoProject(
            id="project123",
            user_id="user123",
            title="Test Video",
            theme="Test theme",
            status=VideoStatus.COMPLETED,
            progress=100,
            created_at=datetime.utcnow(),
        )

        with patch(
            "models.video_project.VideoProject.get_by_id",
            return_value=mock_project,
        ):
            headers = {"Authorization": "Bearer valid_token"}
            response = client.get(
                "/api/v1/video/projects/project123", headers=headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data["project_id"] == "project123"
            assert data["status"] == VideoStatus.COMPLETED


class TestAIIntegration:
    """Test AI service integration"""

    @pytest.mark.asyncio
    async def test_suno_client_health_check(self):
        """Test Suno.ai client health check"""

        client = SunoAIClient("test_api_key")

        with patch.object(client, "_get_session") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.return_value.get.return_value.__aenter__.return_value = (
                mock_response
            )

            health = await client.health_check()
            assert health["status"] == "healthy"
            assert health["service"] == "suno.ai"

    @pytest.mark.asyncio
    async def test_gemini_script_generation(self, sample_script_response):
        """Test Gemini script generation"""

        client = GeminiClient("test_api_key")

        with patch.object(client, "_generate_content") as mock_generate:
            mock_generate.return_value = (
                '{"full_script": "test script", "scenes": []}'
            )

            with patch.object(
                client,
                "_parse_script_response",
                return_value={
                    "full_script": "test script",
                    "scenes": [
                        {
                            "type": "intro",
                            "duration": 20.0,
                            "narration": "Test narration",
                            "visual": "Test visual",
                            "keywords": ["test"],
                        }
                    ],
                },
            ):
                result = await client.generate_script(
                    theme="Test theme", duration=60, style="modern"
                )

                assert isinstance(result, ScriptGenerationResponse)
                assert result.theme == "Test theme"
                assert len(result.scenes) > 0

    @pytest.mark.asyncio
    async def test_stable_diffusion_image_generation(self):
        """Test Stable Diffusion image generation"""

        client = StableDiffusionClient("test_api_key")

        with patch.object(client, "_get_session") as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "artifacts": [
                    {
                        "base64": "test_base64_data",
                        "seed": 12345,
                    }
                ]
            }
            mock_session.return_value.post.return_value.__aenter__.return_value = (
                mock_response
            )

            with patch.object(
                client,
                "_save_image",
                return_value=(
                    "http://test.com/image.png",
                    "http://test.com/thumb.jpg",
                ),
            ):
                result = await client.generate_image(
                    prompt="A modern office scene",
                    style="modern",
                    aspect_ratio="16:9",
                )

                assert isinstance(result, ImageGenerationResponse)
                assert result.url == "http://test.com/image.png"
                assert result.style == "modern"


class TestVideoComposition:
    """Test video composition and rendering"""

    @pytest.mark.asyncio
    async def test_video_composer_creation(self, sample_script_response):
        """Test video composition creation"""

        from video.composer import VideoComposer, CompositionResult

        composer = VideoComposer()

        with patch.object(composer, "_download_media") as mock_download:
            mock_download.side_effect = [
                "/tmp/voice.mp3",  # voice file
                "/tmp/music.mp3",  # music file
                "/tmp/img1.png",  # image files
                "/tmp/img2.png",
                "/tmp/img3.png",
            ]

            with patch.object(
                composer, "_create_preview", return_value="/tmp/preview.mp4"
            ):
                with patch.object(
                    composer,
                    "_upload_media",
                    return_value="http://test.com/preview.mp4",
                ):
                    result = await composer.create_video(
                        script_scenes=sample_script_response.scenes,
                        voice_url="http://test.com/voice.mp3",
                        music_url="http://test.com/music.mp3",
                        image_urls=[
                            "http://test.com/img1.png",
                            "http://test.com/img2.png",
                            "http://test.com/img3.png",
                        ],
                        include_captions=True,
                        target_platform="youtube",
                    )

                    assert isinstance(result, CompositionResult)
                    assert result.preview_url == "http://test.com/preview.mp4"
                    assert result.status == "ready_for_render"


class TestSocialMediaIntegration:
    """Test social media platform integration"""

    @pytest.mark.asyncio
    async def test_social_media_manager_publish(self):
        """Test social media publishing"""

        from social.platforms import (
            SocialMediaManager,
            PublishRequest,
            PublishResult,
        )

        manager = SocialMediaManager()

        request = PublishRequest(
            video_url="http://test.com/video.mp4",
            title="Test Video",
            description="Test description",
            tags=["test", "video"],
            privacy="public",
        )

        # Mock successful publication
        with patch.object(manager, "publish_to_platform") as mock_publish:
            mock_result = PublishResult(
                platform="tiktok",
                success=True,
                platform_id="tiktok123",
                url="https://tiktok.com/video/123",
                published_at=datetime.utcnow(),
            )
            mock_publish.return_value = mock_result

            result = await manager.publish_to_platform("tiktok", request)

            assert result.success is True
            assert result.platform == "tiktok"
            assert result.platform_id == "tiktok123"


class TestDatabase:
    """Test database operations"""

    @pytest.mark.asyncio
    async def test_video_project_save(self):
        """Test saving video project to database"""

        mock_db = Mock()

        project = VideoProject(
            id="test123",
            user_id="user123",
            title="Test Video",
            theme="Test theme",
            created_at=datetime.utcnow(),
        )

        with patch.object(project, "_insert_project") as mock_insert:
            await project.save(mock_db)
            mock_insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_video_project_update_status(self):
        """Test updating video project status"""

        mock_db = Mock()

        project = VideoProject(
            id="test123",
            user_id="user123",
            title="Test Video",
            theme="Test theme",
            created_at=datetime.utcnow(),
        )

        with patch.object(project, "save") as mock_save:
            await project.update_status(
                mock_db, VideoStatus.GENERATING_SCRIPT, 25, None
            )

            assert project.status == VideoStatus.GENERATING_SCRIPT
            assert project.progress == 25
            mock_save.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
