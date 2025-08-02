"""
影片生成服務測試
測試影片創建、編輯和處理功能
"""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from main import app
    from video.video_generator import (
        VideoGenerationRequest,
        video_generation_service,
    )
except ImportError:
    # Fallback for testing without actual services
    app = MagicMock()
    VideoGenerationRequest = MagicMock
    video_generation_service = MagicMock()


class TestVideoGenerationAPI:
    """Test video generation API endpoints"""

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
    def mock_video_service(self):
        """Mock video generation service"""
        with patch(
            "routers.video_generation.video_generation_service"
        ) as mock_service:
            # Mock generate_video method
            mock_result = MagicMock()
            mock_result.generation_id = "gen_123"
            mock_result.status = "processing"
            mock_result.created_at = "2024-01-01T12:00:00Z"
            mock_result.estimated_completion = "2024-01-01T12:10:00Z"

            mock_service.generate_video = AsyncMock(return_value=mock_result)
            mock_service.get_generation_status = AsyncMock(
                return_value={
                    "status": "processing",
                    "progress": 50,
                    "current_step": "Generating images",
                    "created_at": "2024-01-01T12:00:00Z",
                }
            )

            yield mock_service

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "video-generation"

    def test_quick_video_generation(
        self, client, mock_auth, mock_video_service
    ):
        """Test quick video generation endpoint"""
        request_data = {
            "topic": "AI and Machine Learning",
            "platform": "youtube",
            "length": "short",
            "voice_settings": {"voice_id": "alloy"},
            "include_music": True,
            "image_style": "realistic",
        }

        response = client.post(
            "/api/v1/video/generate/quick",
            json=request_data,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "generation_id" in data
        assert data["status"] == "processing"
        assert "estimated_completion" in data

    def test_custom_video_generation(
        self, client, mock_auth, mock_video_service
    ):
        """Test custom video generation endpoint"""
        request_data = {
            "topic": "Future of Technology",
            "platform": "youtube",
            "length": "medium",
            "voice_settings": {
                "voice_id": "nova",
                "speed": 1.0,
                "emotion": "professional",
            },
            "image_style": "futuristic",
            "music_style": "cinematic",
            "include_music": True,
            "include_captions": True,
            "quality": "high",
        }

        response = client.post(
            "/api/v1/video/generate/custom",
            json=request_data,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "generation_id" in data

    def test_generation_status(self, client, mock_auth, mock_video_service):
        """Test getting generation status"""
        response = client.get(
            "/api/v1/video/status/gen_123",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["generation_id"] == "gen_123"
        assert data["status"] == "processing"
        assert data["progress"] == 50
        assert data["current_step"] == "Generating images"

    def test_cancel_generation(self, client, mock_auth, mock_video_service):
        """Test cancelling generation"""
        mock_video_service.cleanup_generation = AsyncMock()

        response = client.post(
            "/api/v1/video/cancel/gen_123",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "cancelled" in data["message"].lower()
        assert data["generation_id"] == "gen_123"

    def test_get_templates(self, client, mock_auth):
        """Test getting video templates"""
        response = client.get(
            "/api/v1/video/templates",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert "youtube" in data["templates"]
        assert "tiktok" in data["templates"]
        assert "instagram" in data["templates"]

    def test_get_templates_by_platform(self, client, mock_auth):
        """Test getting templates for specific platform"""
        response = client.get(
            "/api/v1/video/templates?platform=youtube",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "templates" in data
        assert len(data["templates"]) >= 1

        # Check template structure
        template = data["templates"][0]
        assert "id" in template
        assert "name" in template
        assert "description" in template
        assert "duration" in template

    def test_get_presets(self, client, mock_auth):
        """Test getting generation presets"""
        response = client.get(
            "/api/v1/video/presets",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        assert "educational" in data["presets"]
        assert "entertainment" in data["presets"]
        assert "business" in data["presets"]
        assert "storytelling" in data["presets"]

        # Check preset structure
        educational = data["presets"]["educational"]
        assert "voice_settings" in educational
        assert "image_style" in educational
        assert "include_music" in educational

    def test_get_history(self, client, mock_auth):
        """Test getting generation history"""
        response = client.get(
            "/api/v1/video/history",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "total" in data

    def test_cleanup_generation(self, client, mock_auth, mock_video_service):
        """Test cleanup generation"""
        response = client.delete(
            "/api/v1/video/cleanup/gen_123",
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "cleanup" in data["message"].lower()
        assert data["generation_id"] == "gen_123"

    def test_unauthorized_access(self, client):
        """Test unauthorized access"""
        response = client.post(
            "/api/v1/video/generate/quick", json={"topic": "Test"}
        )

        assert response.status_code == 403  # Expecting auth error

    def test_invalid_quick_generation_request(self, client, mock_auth):
        """Test invalid quick generation request"""
        request_data = {
            # Missing required topic field
            "platform": "youtube"
        }

        response = client.post(
            "/api/v1/video/generate/quick",
            json=request_data,
            headers={"Authorization": "Bearer test_token"},
        )

        assert response.status_code == 422  # Validation error


class TestVideoGenerationService:
    """Test video generation service logic"""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for AI service calls"""
        with patch("video.video_generator.httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "full_script": "Test script content",
                "scenes": [
                    {
                        "sequence": 0,
                        "narration_text": "Scene 1 narration",
                        "visual_description": "A futuristic cityscape",
                        "duration": 5.0,
                        "scene_type": "intro",
                    }
                ],
                "mood": "professional",
            }

            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = (
                mock_client_instance
            )

            yield mock_client_instance

    @pytest.fixture
    def mock_composer(self):
        """Mock video composer"""
        with patch(
            "video.video_generator.VideoComposer"
        ) as mock_composer_class:
            mock_composer = AsyncMock()

            # Mock composition result
            mock_comp_result = MagicMock()
            mock_comp_result.composition_id = "comp_123"
            mock_comp_result.preview_url = "https://example.com/preview.mp4"
            mock_comp_result.status = "ready_for_render"

            # Mock final result
            mock_final_result = MagicMock()
            mock_final_result.video_url = "https://example.com/final.mp4"
            mock_final_result.thumbnail_url = "https://example.com/thumb.jpg"
            mock_final_result.duration = 60.0
            mock_final_result.file_size = 1024000
            mock_final_result.resolution = "1920x1080"

            mock_composer.create_video.return_value = mock_comp_result
            mock_composer.render_final.return_value = mock_final_result

            mock_composer_class.return_value = mock_composer
            yield mock_composer

    @pytest.mark.asyncio
    async def test_video_generation_process(
        self, mock_http_client, mock_composer
    ):
        """Test complete video generation process"""
        request = VideoGenerationRequest(
            topic="AI Technology",
            target_platform="youtube",
            video_length="short",
            include_music=True,
        )

        result = await video_generation_service.generate_video(
            request, "user_123"
        )

        assert result.status == "processing"
        assert "generation_id" in result.generation_id
        assert result.metadata["topic"] == "AI Technology"
        assert result.metadata["platform"] == "youtube"

    @pytest.mark.asyncio
    async def test_script_generation(self, mock_http_client):
        """Test script generation step"""
        script_data = await video_generation_service._generate_script(
            "AI Technology", "youtube", "short"
        )

        assert "full_script" in script_data
        assert "scenes" in script_data
        assert len(script_data["scenes"]) > 0

    @pytest.mark.asyncio
    async def test_image_generation(self, mock_http_client):
        """Test image generation step"""
        scenes = [
            {"visual_description": "A futuristic cityscape"},
            {"visual_description": "Robots working in a lab"},
        ]

        # Mock image generation response
        mock_http_client.post.return_value.json.return_value = {
            "image_url": "https://example.com/image.jpg"
        }

        image_urls = await video_generation_service._generate_images(
            scenes, "realistic"
        )

        assert len(image_urls) == 2
        assert all(url.startswith("http") for url in image_urls)

    @pytest.mark.asyncio
    async def test_voice_generation(self, mock_http_client):
        """Test voice generation step"""
        # Mock voice generation response
        mock_http_client.post.return_value.json.return_value = {
            "audio_url": "https://example.com/voice.mp3"
        }

        voice_url = await video_generation_service._generate_voice(
            "Test script text", {"voice_id": "alloy", "speed": 1.0}
        )

        assert voice_url == "https://example.com/voice.mp3"

    @pytest.mark.asyncio
    async def test_music_generation(self, mock_http_client):
        """Test music generation step"""
        # Mock music generation response
        mock_http_client.post.return_value.json.return_value = {
            "audio_url": "https://example.com/music.mp3"
        }

        music_url = await video_generation_service._generate_music(
            "AI Technology", "professional"
        )

        assert music_url == "https://example.com/music.mp3"

    def test_completion_time_estimation(self):
        """Test completion time estimation"""
        request = VideoGenerationRequest(
            topic="Test",
            video_length="long",
            quality="ultra",
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
        """Test generation status tracking"""
        generation_id = "test_gen_123"

        # Update status
        await video_generation_service._update_status(
            generation_id, "processing", 50, "Generating images"
        )

        # Get status
        status = await video_generation_service.get_generation_status(
            generation_id
        )

        assert status["status"] == "processing"
        assert status["progress"] == 50
        assert status["current_step"] == "Generating images"

    @pytest.mark.asyncio
    async def test_generation_cleanup(self):
        """Test generation cleanup"""
        generation_id = "test_gen_456"

        # Add to status tracking
        video_generation_service.generation_status[generation_id] = {
            "status": "completed"
        }

        # Cleanup
        await video_generation_service.cleanup_generation(generation_id)

        # Should be removed from tracking
        assert generation_id not in video_generation_service.generation_status
