"""
End-to-End Video Generation Test Suite
Complete business workflow testing from user registration to video completion
"""

import asyncio

# Import test dependencies
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.shared.database import (
    AsyncSessionLocal,
    ProcessingTask,
    User,
    Video,
    VideoAsset,
)
from src.shared.services import (
    VideoEvents,
    get_service_registry,
    publish_video_event,
)

# from src.services.video_service.main import app as video_app


class E2ETestClient:
    """End-to-End Test Client for Video Generation Workflow"""

    def __init__(self):
        self.base_url = "http://localhost:8000"  # API Gateway
        self.auth_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def register_user(self, email: str, password: str) -> Dict[str, Any]:
        """Register a new user"""
        async with self.session.post(
            f"{self.base_url}/api/v1/auth/register",
            json={"email": email, "password": password, "full_name": "Test User"},
        ) as response:
            return await response.json()

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login and get authentication token"""
        async with self.session.post(
            f"{self.base_url}/api/v1/auth/login", json={"email": email, "password": password}
        ) as response:
            result = await response.json()
            if "access_token" in result:
                self.auth_token = result["access_token"]
                self.user_id = result.get("user_id")
            return result

    async def create_video_project(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new video generation project"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        async with self.session.post(
            f"{self.base_url}/api/v1/video/generate", json=video_data, headers=headers
        ) as response:
            return await response.json()

    async def get_video_status(self, project_id: int) -> Dict[str, Any]:
        """Get video project status"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        async with self.session.get(
            f"{self.base_url}/api/v1/video/projects/{project_id}", headers=headers
        ) as response:
            return await response.json()

    async def get_video_assets(self, project_id: int) -> Dict[str, Any]:
        """Get video project assets"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        async with self.session.get(
            f"{self.base_url}/api/v1/video/projects/{project_id}/assets", headers=headers
        ) as response:
            return await response.json()

    async def get_processing_tasks(self, project_id: int) -> Dict[str, Any]:
        """Get video processing tasks"""
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        async with self.session.get(
            f"{self.base_url}/api/v1/video/projects/{project_id}/tasks", headers=headers
        ) as response:
            return await response.json()

    async def wait_for_completion(self, project_id: int, timeout: int = 300) -> Dict[str, Any]:
        """Wait for video generation to complete"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status_response = await self.get_video_status(project_id)

            if status_response.get("status") == "completed":
                return status_response
            elif status_response.get("status") == "failed":
                raise Exception(f"Video generation failed: {status_response}")

            await asyncio.sleep(5)

        raise TimeoutError(f"Video generation timed out after {timeout} seconds")


@pytest.fixture
async def e2e_client():
    """Create E2E test client"""
    async with E2ETestClient() as client:
        yield client


@pytest.fixture
async def test_user_credentials():
    """Test user credentials"""
    return {"email": "test@example.com", "password": "testpassword123"}


@pytest.fixture
async def sample_video_request():
    """Sample video generation request"""
    return {
        "title": "Test Video Project",
        "description": "End-to-end test video",
        "theme": "technology innovation",
        "style": "modern",
        "duration": 30,
        "voice_type": "professional",
        "music_genre": "ambient",
        "include_captions": True,
        "target_platform": "youtube",
    }


class TestVideoGenerationE2E:
    """End-to-End Video Generation Test Cases"""

    @pytest.mark.asyncio
    async def test_complete_video_generation_workflow(
        self, e2e_client: E2ETestClient, test_user_credentials: Dict, sample_video_request: Dict
    ):
        """Test complete video generation workflow from registration to completion"""

        # Step 1: User Registration
        register_response = await e2e_client.register_user(
            email=test_user_credentials["email"], password=test_user_credentials["password"]
        )
        assert "user_id" in register_response

        # Step 2: User Login
        login_response = await e2e_client.login(
            email=test_user_credentials["email"], password=test_user_credentials["password"]
        )
        assert "access_token" in login_response
        assert e2e_client.auth_token is not None

        # Step 3: Create Video Project
        project_response = await e2e_client.create_video_project(sample_video_request)
        assert "project_id" in project_response
        assert project_response["status"] == "initializing"
        assert project_response["progress"] == 0

        project_id = project_response["project_id"]

        # Step 4: Wait for Processing to Complete (with mocked AI services)
        with patch_ai_services():
            completion_response = await e2e_client.wait_for_completion(project_id)

            assert completion_response["status"] == "completed"
            assert completion_response["progress"] == 100
            assert completion_response["final_url"] is not None
            assert completion_response["thumbnail_url"] is not None

        # Step 5: Verify Assets Creation
        assets_response = await e2e_client.get_video_assets(project_id)
        assets = assets_response["assets"]

        assert len(assets) >= 3  # At least voice, images, and final video
        asset_types = {asset["asset_type"] for asset in assets}
        assert "audio" in asset_types
        assert "image" in asset_types

        # Step 6: Verify Processing Tasks
        tasks_response = await e2e_client.get_processing_tasks(project_id)
        tasks = tasks_response["tasks"]

        assert len(tasks) >= 1
        completed_tasks = [task for task in tasks if task["status"] == "completed"]
        assert len(completed_tasks) >= 1

    @pytest.mark.asyncio
    async def test_video_generation_with_different_platforms(
        self, e2e_client: E2ETestClient, test_user_credentials: Dict
    ):
        """Test video generation for different target platforms"""

        # Setup user
        await e2e_client.register_user(**test_user_credentials)
        await e2e_client.login(**test_user_credentials)

        platforms = ["youtube", "tiktok", "instagram"]
        project_ids = []

        for platform in platforms:
            video_request = {
                "title": f"Test Video for {platform.title()}",
                "theme": "social media trends",
                "target_platform": platform,
                "duration": 15 if platform in ["tiktok", "instagram"] else 60,
            }

            project_response = await e2e_client.create_video_project(video_request)
            project_ids.append(project_response["project_id"])

        # Verify all projects are created
        assert len(project_ids) == len(platforms)

        # Check project status for each platform
        for i, project_id in enumerate(project_ids):
            status_response = await e2e_client.get_video_status(project_id)
            assert status_response["project_id"] == project_id
            assert platforms[i] in status_response["title"].lower()

    @pytest.mark.asyncio
    async def test_concurrent_video_generation(
        self, e2e_client: E2ETestClient, test_user_credentials: Dict
    ):
        """Test concurrent video generation projects"""

        # Setup user
        await e2e_client.register_user(**test_user_credentials)
        await e2e_client.login(**test_user_credentials)

        # Create multiple concurrent projects
        concurrent_projects = []
        for i in range(3):
            video_request = {
                "title": f"Concurrent Video {i+1}",
                "theme": f"topic_{i+1}",
                "duration": 20,
            }
            project_response = await e2e_client.create_video_project(video_request)
            concurrent_projects.append(project_response["project_id"])

        # Verify all projects are in processing
        for project_id in concurrent_projects:
            status_response = await e2e_client.get_video_status(project_id)
            assert status_response["status"] in [
                "initializing",
                "generating_script",
                "generating_voice",
            ]

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(
        self, e2e_client: E2ETestClient, test_user_credentials: Dict
    ):
        """Test error handling and recovery mechanisms"""

        # Setup user
        await e2e_client.register_user(**test_user_credentials)
        await e2e_client.login(**test_user_credentials)

        # Test invalid video request
        invalid_request = {
            "title": "",  # Invalid empty title
            "theme": "test",
            "duration": 1000,  # Invalid duration
        }

        try:
            await e2e_client.create_video_project(invalid_request)
            assert False, "Should have raised validation error"
        except Exception:
            # Expected validation error
            pass

        # Test valid request after error
        valid_request = {
            "title": "Recovery Test Video",
            "theme": "recovery testing",
            "duration": 30,
        }

        project_response = await e2e_client.create_video_project(valid_request)
        assert "project_id" in project_response


class TestMessageQueueIntegration:
    """Test message queue integration in video generation workflow"""

    @pytest.mark.asyncio
    async def test_video_events_publication(self):
        """Test that video events are properly published during workflow"""

        # Mock message queue
        mock_queue = AsyncMock()

        with patch("src.shared.services.message_queue.get_message_queue", return_value=mock_queue):
            # Simulate video creation event
            await publish_video_event(
                VideoEvents.VIDEO_CREATED,
                video_id=123,
                user_id=456,
                title="Test Video",
                description="Test Description",
            )

            # Verify event was published
            mock_queue.publish_event.assert_called_once()
            call_args = mock_queue.publish_event.call_args

            assert call_args[1]["topic"] == VideoEvents.VIDEO_CREATED
            assert call_args[1]["payload"]["video_id"] == 123
            assert call_args[1]["payload"]["user_id"] == 456

    @pytest.mark.asyncio
    async def test_processing_events_sequence(self):
        """Test that processing events are published in correct sequence"""

        mock_queue = AsyncMock()
        expected_events = [
            VideoEvents.VIDEO_CREATED,
            VideoEvents.VIDEO_PROCESSING_STARTED,
            VideoEvents.VIDEO_PROCESSING_COMPLETED,
        ]

        with patch("src.shared.services.message_queue.get_message_queue", return_value=mock_queue):
            # Simulate event sequence
            for event in expected_events:
                await publish_video_event(event, video_id=123, user_id=456)

            # Verify all events were published
            assert mock_queue.publish_event.call_count == len(expected_events)


class TestServiceCommunication:
    """Test service communication during video generation"""

    @pytest.mark.asyncio
    async def test_service_registry_integration(self):
        """Test service registry integration"""

        registry = get_service_registry()

        # Verify essential services are registered
        essential_services = [
            "video-service",
            "ai-service",
            "auth-service",
            "user-service",
            "storage-service",
        ]

        for service_name in essential_services:
            instances = registry.get_service_instances(service_name)
            assert len(instances) >= 1, f"Service {service_name} not registered"

    @pytest.mark.asyncio
    async def test_load_balancing_strategies(self):
        """Test different load balancing strategies"""

        from src.shared.services.service_discovery import LoadBalancingStrategy

        registry = get_service_registry()

        strategies = [
            LoadBalancingStrategy.ROUND_ROBIN,
            LoadBalancingStrategy.RANDOM,
            LoadBalancingStrategy.LEAST_CONNECTIONS,
            LoadBalancingStrategy.HEALTH_BASED,
        ]

        for strategy in strategies:
            instance = registry.select_instance("video-service", strategy)
            assert instance is not None, f"Failed to select instance with {strategy}"


class TestDatabaseIntegration:
    """Test database integration during video generation"""

    @pytest.mark.asyncio
    async def test_video_model_lifecycle(self):
        """Test complete video model lifecycle"""

        async with AsyncSessionLocal() as db:
            # Create test user
            user = User(
                email="test@example.com", password_hash="hashed_password", full_name="Test User"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            # Create video project
            video = Video(
                user_id=user.id,
                title="Test Video",
                description="Test Description",
                script_content="Test script",
                status="initializing",
                progress_percentage=0,
            )
            db.add(video)
            await db.commit()
            await db.refresh(video)

            # Create processing task
            task = ProcessingTask(
                video_id=video.id,
                task_type="script_generation",
                task_name="Generate Script",
                status="completed",
                progress_percentage=100,
            )
            db.add(task)

            # Create video asset
            asset = VideoAsset(
                video_id=video.id,
                asset_type="audio",
                asset_name="Voice Narration",
                file_url="https://example.com/audio.mp3",
            )
            db.add(asset)

            await db.commit()

            # Verify relationships
            await db.refresh(video)
            assert len(video.processing_tasks) == 1
            assert len(video.assets) == 1
            assert video.processing_tasks[0].task_type == "script_generation"
            assert video.assets[0].asset_type == "audio"


def patch_ai_services():
    """Patch AI services for testing"""

    def mock_generate_script(*args, **kwargs):
        return AsyncMock(
            return_value=type(
                "ScriptResponse",
                (),
                {
                    "content": "Test script content",
                    "scenes": [
                        type(
                            "Scene",
                            (),
                            {"visual_description": "Test scene 1", "narration": "Test narration 1"},
                        )(),
                        type(
                            "Scene",
                            (),
                            {"visual_description": "Test scene 2", "narration": "Test narration 2"},
                        )(),
                    ],
                    "narration_text": "Complete narration text",
                },
            )()
        )

    def mock_generate_voice(*args, **kwargs):
        return AsyncMock(
            return_value=type(
                "VoiceResponse",
                (),
                {
                    "audio_url": "https://example.com/voice.mp3",
                    "music_url": "https://example.com/music.mp3",
                },
            )()
        )

    def mock_generate_image(*args, **kwargs):
        return AsyncMock(
            return_value=type("ImageResponse", (), {"url": "https://example.com/image.jpg"})()
        )

    def mock_create_video(*args, **kwargs):
        return AsyncMock(
            return_value=type(
                "CompositionResult",
                (),
                {
                    "composition_id": "test_composition_123",
                    "preview_url": "https://example.com/preview.jpg",
                },
            )()
        )

    def mock_render_final(*args, **kwargs):
        return AsyncMock(
            return_value=type(
                "FinalResult",
                (),
                {
                    "video_url": "https://example.com/final_video.mp4",
                    "thumbnail_url": "https://example.com/thumbnail.jpg",
                    "duration": 30,
                    "file_size": 10485760,
                },
            )()
        )

    return patch.multiple(
        "src.services.video_service.main",
        gemini_client=AsyncMock(generate_script=mock_generate_script()),
        suno_client=AsyncMock(generate_voice=mock_generate_voice()),
        stable_diffusion_client=AsyncMock(generate_image=mock_generate_image()),
        video_composer=AsyncMock(
            create_video=mock_create_video(), render_final=mock_render_final()
        ),
    )


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__, "-v"])
