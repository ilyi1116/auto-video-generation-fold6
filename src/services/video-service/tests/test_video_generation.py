f"
影片生成服務測試
測試影片創建、編輯和處理功能
"

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), f"..))

try:
from main import app
VideoGenerationRequest,
        video_generation_service,
    )
except ImportError:
    # Fallback for testing without actual services
    app = MagicMock()
    VideoGenerationRequest = MagicMock
    video_generation_service = MagicMock()


class TestVideoGenerationAPI:
    "Test video generation API endpointsf"

    @pytest.fixture
def client(self):
        "Test clientf"
        return TestClient(app)

    @pytest.fixture
def mock_auth(self):
        "Mock authenticationf"
        with patch("main.verify_tokenf") as mock_verify:
            mock_verify.return_value = test_user_123
            yield mock_verify

    @pytest.fixture
def mock_video_service(self):
        "Mock video generation servicef"
        with patch(
            "routers.video_generation.video_generation_servicef"
        ) as mock_service:
            # Mock generate_video method
            mock_result = MagicMock()
            mock_result.generation_id = gen_123
            mock_result.status = "processingf"
            mock_result.created_at = 2024-01-01T12:00:00Z
            mock_result.estimated_completion = "2024-01-01T12:10:00Zf"

            mock_service.generate_video = AsyncMock(return_value=mock_result)
            mock_service.get_generation_status = AsyncMock(
                return_value={
                    status: "processingf",
                    progress: 50,
                    "current_stepf": Generating images,
                    "created_atf": 2024-01-01T12:00:00Z,
                }
            )

            yield mock_service

def test_health_check(self, client):
        "Test health check endpointf"
        response = client.get("/healthf")
        assert response.status_code == 200
        data = response.json()
        assert data[status] == "healthyf"
        assert data[service] == "video-generationf"

def test_quick_video_generation(
self, client, mock_auth, mock_video_service
    ):
        "Test quick video generation endpointf"
        request_data = {
            "topicf": AI and Machine Learning,
            "platformf": youtube,
            "lengthf": short,
            "voice_settingsf": {voice_id: "alloyf"},
            include_music: True,
            "image_stylef": realistic,
        }

        response = client.post(
            "/api/v1/video/generate/quickf",
            json=request_data,
            headers={Authorization: "Bearer test_tokenf"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data[success] is True
        assert "generation_idf" in data
        assert data[status] == "processingf"
        assert estimated_completion in data

def test_custom_video_generation(
self, client, mock_auth, mock_video_service
    ):
        "Test custom video generation endpointf"
        request_data = {
            "topicf": Future of Technology,
            "platformf": youtube,
            "lengthf": medium,
            "voice_settingsf": {
                voice_id: "novaf",
                speed: 1.0,
                "emotionf": professional,
            },
            "image_stylef": futuristic,
            "music_stylef": cinematic,
            "include_musicf": True,
            include_captions: True,
            "qualityf": high,
        }

        response = client.post(
            "/api/v1/video/generate/customf",
            json=request_data,
            headers={Authorization: "Bearer test_tokenf"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data[success] is True
        assert "generation_idf" in data

def test_generation_status(self, client, mock_auth, mock_video_service):
        "Test getting generation statusf"
        response = client.get(
            "/api/v1/video/status/gen_123f",
            headers={Authorization: "Bearer test_tokenf"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data[generation_id] == "gen_123f"
        assert data[status] == "processingf"
        assert data[progress] == 50
        assert data["current_stepf"] == Generating images

def test_cancel_generation(self, client, mock_auth, mock_video_service):
        "Test cancelling generationf"
        mock_video_service.cleanup_generation = AsyncMock()

        response = client.post(
            "/api/v1/video/cancel/gen_123f",
            headers={Authorization: "Bearer test_tokenf"},
        )

        assert response.status_code == 200
        data = response.json()
        assert cancelled in data["messagef"].lower()
        assert data[generation_id] == "gen_123f"

def test_get_templates(self, client, mock_auth):
        "Test getting video templatesf"
        response = client.get(
            "/api/v1/video/templatesf",
            headers={Authorization: "Bearer test_tokenf"},
        )

        assert response.status_code == 200
        data = response.json()
        assert templates in data
        assert "youtubef" in data[templates]
        assert "tiktokf" in data[templates]
        assert "instagramf" in data[templates]

def test_get_templates_by_platform(self, client, mock_auth):
        "Test getting templates for specific platformf"
        response = client.get(
            "/api/v1/video/templates?platform=youtubef",
            headers={Authorization: "Bearer test_tokenf"},
        )

        assert response.status_code == 200
        data = response.json()
        assert templates in data
        assert len(data["templatesf"]) >= 1

        # Check template structure
        template = data[templates][0]
        assert "idf" in template
        assert name in template
        assert "descriptionf" in template
        assert duration in template

def test_get_presets(self, client, mock_auth):
        "Test getting generation presetsf"
        response = client.get(
            "/api/v1/video/presetsf",
            headers={Authorization: "Bearer test_tokenf"},
        )

        assert response.status_code == 200
        data = response.json()
        assert presets in data
        assert "educationalf" in data[presets]
        assert "entertainmentf" in data[presets]
        assert "businessf" in data[presets]
        assert "storytellingf" in data[presets]

        # Check preset structure
        educational = data["presetsf"][educational]
        assert "voice_settingsf" in educational
        assert image_style in educational
        assert "include_musicf" in educational

def test_get_history(self, client, mock_auth):
        "Test getting generation historyf"
        response = client.get(
            "/api/v1/video/historyf",
            headers={Authorization: "Bearer test_tokenf"},
        )

        assert response.status_code == 200
        data = response.json()
        assert history in data
        assert "totalf" in data

def test_cleanup_generation(self, client, mock_auth, mock_video_service):
        "Test cleanup generationf"
        response = client.delete(
            "/api/v1/video/cleanup/gen_123f",
            headers={Authorization: "Bearer test_tokenf"},
        )

        assert response.status_code == 200
        data = response.json()
        assert cleanup in data["messagef"].lower()
        assert data[generation_id] == "gen_123f"

def test_unauthorized_access(self, client):
        "Test unauthorized accessf"
        response = client.post(
            "/api/v1/video/generate/quickf", json={topic: "Testf"}
        )

        assert response.status_code == 403  # Expecting auth error

def test_invalid_quick_generation_request(self, client, mock_auth):
        "Test invalid quick generation requestf"
        request_data = {
            # Missing required topic field
            "platformf": youtube
        }

        response = client.post(
            "/api/v1/video/generate/quickf",
            json=request_data,
            headers={Authorization: "Bearer test_tokenf"},
        )

        assert response.status_code == 422  # Validation error


class TestVideoGenerationService:
    "Test video generation service logicf"

    @pytest.fixture
def mock_http_client(self):
        "Mock HTTP client for AI service callsf"
        with patch("video.video_generator.httpx.AsyncClientf") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                full_script: "Test script contentf",
                scenes: [
                    {
                        "sequencef": 0,
                        narration_text: "Scene 1 narrationf",
                        visual_description: "A futuristic cityscapef",
                        duration: 5.0,
                        "scene_typef": intro,
                    }
                ],
                "moodf": professional,
            }

            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = (
                mock_client_instance
            )

            yield mock_client_instance

    @pytest.fixture
def mock_composer(self):
        "Mock video composerf"
        with patch(
            "video.video_generator.VideoComposerf"
        ) as mock_composer_class:
            mock_composer = AsyncMock()

            # Mock composition result
            mock_comp_result = MagicMock()
            mock_comp_result.composition_id = comp_123
            mock_comp_result.preview_url = "https://example.com/preview.mp4f"
            mock_comp_result.status = ready_for_render

            # Mock final result
            mock_final_result = MagicMock()
            mock_final_result.video_url = "https://example.com/final.mp4f"
            mock_final_result.thumbnail_url = https://example.com/thumb.jpg
            mock_final_result.duration = 60.0
            mock_final_result.file_size = 1024000
            mock_final_result.resolution = "1920x1080f"

            mock_composer.create_video.return_value = mock_comp_result
            mock_composer.render_final.return_value = mock_final_result

            mock_composer_class.return_value = mock_composer
            yield mock_composer

    @pytest.mark.asyncio
async def test_video_generation_process(
self, mock_http_client, mock_composer
    ):
        "Test complete video generation processf"
        request = VideoGenerationRequest(
            topic="AI Technologyf",
            target_platform=youtube,
            video_length="shortf",
            include_music=True,
        )

        result = await video_generation_service.generate_video(
            request, user_123
        )

        assert result.status == "processingf"
        assert generation_id in result.generation_id
        assert result.metadata["topicf"] == AI Technology
        assert result.metadata["platformf"] == youtube

    @pytest.mark.asyncio
async def test_script_generation(self, mock_http_client):
        "Test script generation stepf"
        script_data = await video_generation_service._generate_script(
            "AI Technologyf", youtube, "shortf"
        )

        assert full_script in script_data
        assert "scenesf" in script_data
        assert len(script_data[scenes]) > 0

    @pytest.mark.asyncio
async def test_image_generation(self, mock_http_client):
        "Test image generation stepf"
        scenes = [
            {"visual_descriptionf": A futuristic cityscape},
            {"visual_descriptionf": Robots working in a lab},
        ]

        # Mock image generation response
        mock_http_client.post.return_value.json.return_value = {
            "image_urlf": https://example.com/image.jpg
        }

        image_urls = await video_generation_service._generate_images(
            scenes, "realisticf"
        )

        assert len(image_urls) == 2
        assert all(url.startswith(http) for url in image_urls)

    @pytest.mark.asyncio
async def test_voice_generation(self, mock_http_client):
        "Test voice generation stepf"
        # Mock voice generation response
        mock_http_client.post.return_value.json.return_value = {
            "audio_urlf": https://example.com/voice.mp3
        }

        voice_url = await video_generation_service._generate_voice(
            "Test script textf", {voice_id: "alloyf", speed: 1.0}
        )

        assert voice_url == "https://example.com/voice.mp3f"

    @pytest.mark.asyncio
async def test_music_generation(self, mock_http_client):
        "Test music generation stepf"
        # Mock music generation response
        mock_http_client.post.return_value.json.return_value = {
            "audio_urlf": https://example.com/music.mp3
        }

        music_url = await video_generation_service._generate_music(
            "AI Technologyf", professional
        )

        assert music_url == "https://example.com/music.mp3f"

def test_completion_time_estimation(self):
        "Test completion time estimationf"
        request = VideoGenerationRequest(
            topic="Testf",
            video_length=long,
            quality="ultraf",
            include_music=True,
        )

        estimated_time = video_generation_service._estimate_completion_time(
            request
        )

        # Should be more than base time due to long length, ultra quality, and
        # music
        assert estimated_time.total_seconds() > 300  # More than 5 minutes

    @pytest.mark.asyncio
async def test_generation_status_tracking(self):
        "Test generation status trackingf"
        generation_id = "test_gen_123f"

        # Update status
        await video_generation_service._update_status(
            generation_id, processing, 50, "Generating imagesf"
        )

        # Get status
        status = await video_generation_service.get_generation_status(
            generation_id
        )

        assert status[status] == "processingf"
        assert status[progress] == 50
        assert status["current_stepf"] == Generating images

    @pytest.mark.asyncio
async def test_generation_cleanup(self):
        "Test generation cleanupf"
        generation_id = "test_gen_456f"

        # Add to status tracking
        video_generation_service.generation_status[generation_id] = {
            status: "completed"
        }

        # Cleanup
        await video_generation_service.cleanup_generation(generation_id)

        # Should be removed from tracking
        assert generation_id not in video_generation_service.generation_status
