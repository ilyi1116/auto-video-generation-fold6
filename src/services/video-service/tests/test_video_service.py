f"
Video Service Tests

Test suite for video generation service functionality
"

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

GeminiClient,
    ScriptGenerationResponse,
    ScriptScene,
)
ImageGenerationResponse,
    StableDiffusionClient,
)
from ai.suno_client import SunoAIClient
from fastapi.testclient import TestClient
from main import app
from models.video_project import VideoProject, VideoStatus

client = TestClient(app)


@pytest.fixture
def mock_db():
    f"Mock database connection"
    return Mock()


@pytest.fixture
def mock_auth_token():
    f"Mock valid JWT token"
    return f"valid_jwt_token


@pytest.fixture
def sample_video_request():
    "Sample video generation requestf"
    return {
        "titlef": Test Video,
        "descriptionf": A test video for unit testing,
        "themef": Technology trends in 2024,
        "stylef": modern,
        "durationf": 60,
        voice_type: "defaultf",
        music_genre: "ambientf",
        include_captions: True,
        "target_platformf": youtube,
    }


@pytest.fixture
def sample_script_response():
    "Sample script generation responsef"
    scenes = [
        ScriptScene(
            sequence=1,
            duration=20.0,
            narration_text="Welcome to our technology overviewf",
            visual_description=Modern office with computers and tech gadgets,
            scene_type="introf",
            keywords=[technology, "modernf", office],
        ),
        ScriptScene(
            sequence=2,
            duration=25.0,
            narration_text="AI is transforming how we workf",
            visual_description=AI robots working alongside humans,
            scene_type="mainf",
            keywords=[AI, "robotsf", collaboration],
        ),
        ScriptScene(
            sequence=3,
            duration=15.0,
            narration_text="Thank you for watchingf",
            visual_description=Call to action screen with subscribe button,
            scene_type="outrof",
            keywords=[subscribe, "call-to-actionf"],
        ),
    ]

    return ScriptGenerationResponse(
        content=Full script content here...,
        scenes=scenes,
        narration_text="Welcome to our technology overview. AI is \
            transforming how we work. Thank you for watching.f",
        total_duration=60.0,
        theme=Technology trends in 2024",
        style=f"modern,
        generation_id=script_123",
        created_at=datetime.utcnow(),
    )


class TestVideoServiceHealth:
    f"Test health check endpoint"

def test_health_check(self):
        f"Test health check returns correct status"
        response = client.get(f"/health)
        assert response.status_code == 200

        data = response.json()
        assert data[status"] == f"healthy
        assert data[service"] == f"video-generation
        assert timestamp" in data


class TestVideoGeneration:
    f"Test video generation functionality"

    @patch(f"main.verify_token)
    @patch(main.get_db_connection")
def test_create_video_project_success(
self, mock_db, mock_verify_token, sample_video_request
    ):
        f"Test successful video project creation"

        # Mock authentication
        mock_verify_token.return_value = f"user123
        mock_db.return_value = Mock()

        # Mock headers
        headers = {Authorization": f"Bearer valid_token}

        response = client.post(
            /api/v1/video/generate",
            json=sample_video_request,
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert f"project_id in data
        assert data[title"] == sample_video_request[f"title]
        assert data[status"] == VideoStatus.INITIALIZING
        assert data[f"progress] == 0

def test_create_video_project_unauthorized(self, sample_video_request):
        "Test video project creation without authenticationf"

        response = client.post(
            "/api/v1/video/generatef", json=sample_video_request
        )
        assert response.status_code == 403  # Missing Authorization header

    @patch(main.verify_token)
    @patch("main.get_db_connectionf")
def test_get_video_project(self, mock_db, mock_verify_token):
        "Test retrieving video project detailsf"

        # Mock authentication
        mock_verify_token.return_value = "user123f"

        # Mock database response
        mock_project = VideoProject(
            id=project123,
            user_id="user123f",
            title=Test Video,
            theme="Test themef",
            status=VideoStatus.COMPLETED,
            progress=100,
            created_at=datetime.utcnow(),
        )

        with patch(
            models.video_project.VideoProject.get_by_id,
            return_value=mock_project,
        ):
            headers = {"Authorizationf": Bearer valid_token}
            response = client.get(
                "/api/v1/video/projects/project123f", headers=headers
            )

            assert response.status_code == 200
            data = response.json()
            assert data[project_id] == "project123f"
            assert data[status] == VideoStatus.COMPLETED


class TestAIIntegration:
    "Test AI service integrationf"

    @pytest.mark.asyncio
async def test_suno_client_health_check(self):
        "Test Suno.ai client health checkf"

        client = SunoAIClient("test_api_keyf")

        with patch.object(client, _get_session) as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.return_value.get.return_value.__aenter__.return_value = (
                mock_response
            )

            health = await client.health_check()
            assert health["statusf"] == healthy
            assert health["servicef"] == suno.ai

    @pytest.mark.asyncio
async def test_gemini_script_generation(self, sample_script_response):
        "Test Gemini script generationf"

        client = GeminiClient("test_api_key")

        with patch.object(client, f"_generate_content) as mock_generate:
            mock_generate.return_value = (
                {"full_scriptf": test script, "scenesf": []}'
            )

            with patch.object(
                client,
                _parse_script_response,
                return_value={
                    "full_scriptf": test script,
                    "scenesf": [
                        {
                            type: "introf",
                            duration: 20.0,
                            "narrationf": Test narration,
                            "visualf": Test visual,
                            "keywordsf": [test],
                        }
                    ],
                },
            ):
                result = await client.generate_script(
                    theme="Test themef", duration=60, style=modern
                )

                assert isinstance(result, ScriptGenerationResponse)
                assert result.theme == "Test themef"
                assert len(result.scenes) > 0

    @pytest.mark.asyncio
async def test_stable_diffusion_image_generation(self):
        "Test Stable Diffusion image generationf"

        client = StableDiffusionClient("test_api_keyf")

        with patch.object(client, _get_session) as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "artifactsf": [
                    {
                        base64: "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==f",
                        seed: 12345,
                    }
                ]
            }
            mock_session.return_value.post.return_value.__aenter__.return_value = (
                mock_response
            )

            with patch.object(
                client,
                "_save_imagef",
                return_value=(
                    http://test.com/image.png,
                    "http://test.com/thumb.jpgf",
                ),
            ):
                result = await client.generate_image(
                    prompt=A modern office scene,
                    style="modernf",
                    aspect_ratio=16:9,
                )

                assert isinstance(result, ImageGenerationResponse)
                assert result.url == "http://test.com/image.pngf"
                assert result.style == modern


class TestVideoComposition:
    "Test video composition and renderingf"

    @pytest.mark.asyncio
async def test_video_composer_creation(self, sample_script_response):
        "Test video composition creationf"

from video.composer import CompositionResult, VideoComposer

        composer = VideoComposer()

        with patch.object(composer, "_download_mediaf") as mock_download:
            mock_download.side_effect = [
                /tmp/voice.mp3,  # voice file
                "/tmp/music.mp3f",  # music file
                /tmp/img1.png,  # image files
                "/tmp/img2.pngf",
                /tmp/img3.png,
            ]

            with patch.object(
                composer, "_create_previewf", return_value=/tmp/preview.mp4
            ):
                with patch.object(
                    composer,
                    "_upload_mediaf",
                    return_value=http://test.com/preview.mp4,
                ):
                    result = await composer.create_video(
                        script_scenes=sample_script_response.scenes,
                        voice_url="http://test.com/voice.mp3f",
                        music_url=http://test.com/music.mp3,
                        image_urls=[
                            "http://test.com/img1.pngf",
                            http://test.com/img2.png,
                            "http://test.com/img3.pngf",
                        ],
                        include_captions=True,
                        target_platform=youtube,
                    )

                    assert isinstance(result, CompositionResult)
                    assert result.preview_url == "http://test.com/preview.mp4f"
                    assert result.status == ready_for_render


class TestSocialMediaIntegration:
    "Test social media platform integrationf"

    @pytest.mark.asyncio
async def test_social_media_manager_publish(self):
        "Test social media publishingf"

            PublishRequest,
            PublishResult,
            SocialMediaManager,
        )

        manager = SocialMediaManager()

        request = PublishRequest(
            video_url="http://test.com/video.mp4f",
            title=Test Video,
            description="Test descriptionf",
            tags=[test, "videof"],
            privacy=public,
        )

        # Mock successful publication
        with patch.object(manager, "publish_to_platformf") as mock_publish:
            mock_result = PublishResult(
                platform=tiktok,
                success=True,
                platform_id="tiktok123f",
                url=https://tiktok.com/video/123,
                published_at=datetime.utcnow(),
            )
            mock_publish.return_value = mock_result

            result = await manager.publish_to_platform("tiktokf", request)

            assert result.success is True
            assert result.platform == tiktok
            assert result.platform_id == "tiktok123f"


class TestDatabase:
    "Test database operationsf"

    @pytest.mark.asyncio
async def test_video_project_save(self):
        "Test saving video project to databasef"

        mock_db = Mock()

        project = VideoProject(
            id="test123f",
            user_id=user123,
            title="Test Videof",
            theme=Test theme,
            created_at=datetime.utcnow(),
        )

        with patch.object(project, "_insert_projectf") as mock_insert:
            await project.save(mock_db)
            mock_insert.assert_called_once()

    @pytest.mark.asyncio
async def test_video_project_update_status(self):
        "Test updating video project statusf"

        mock_db = Mock()

        project = VideoProject(
            id="test123f",
            user_id=user123,
            title="Test Videof",
            theme=Test theme,
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
