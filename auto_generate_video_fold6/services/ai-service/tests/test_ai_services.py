import os
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest
from services.audio_processor import AudioProcessor
from services.image_generator import ImageGenerator
from services.suno_client import SunoClient
from services.text_generator import TextGenerator

from config import settings

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


class TestAIServices:
    """Comprehensive test suite for all AI services"""

    @pytest.mark.asyncio
    async def test_text_generator_basic(self):
        """Test TextGenerator basic functionality"""
        generator = TextGenerator()
        await generator.initialize()

        # Test health check
        with patch.object(settings, "openai_api_key", "test_key"):
            assert generator.is_healthy()

        await generator.shutdown()

    @pytest.mark.asyncio
    async def test_image_generator_basic(self):
        """Test ImageGenerator basic functionality"""
        generator = ImageGenerator()
        await generator.initialize()

        # Test health check
        with patch.object(settings, "stability_api_key", "test_key"):
            assert generator.is_healthy()

        await generator.shutdown()

    @pytest.mark.asyncio
    async def test_audio_processor_basic(self):
        """Test AudioProcessor basic functionality"""
        processor = AudioProcessor()
        await processor.initialize()

        # Test health check
        with patch.object(settings, "elevenlabs_api_key", "test_key"):
            assert processor.is_healthy()

        await processor.shutdown()

    @pytest.mark.asyncio
    async def test_suno_client_basic(self):
        """Test SunoClient basic functionality"""
        client = SunoClient()
        await client.initialize()

        # Test health check
        assert client.is_healthy()

        await client.shutdown()

    @pytest.mark.asyncio
    @patch("services.text_generator.openai.AsyncOpenAI")
    async def test_text_generation_integration(self, mock_openai):
        """Test text generation with mocked API"""
        # Setup mock
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[
            0
        ].message.content = "Generated test script content"

        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client

        generator = TextGenerator()
        await generator.initialize()
        generator.openai_client = mock_client

        result = await generator.generate_script(
            topic="Test topic", style="engaging", duration_seconds=30
        )

        assert "script_id" in result
        assert "content" in result
        assert result["status"] == "generated"

        await generator.shutdown()

    @pytest.mark.asyncio
    async def test_image_generation_fallback(self):
        """Test image generation with fallback when no API key"""
        generator = ImageGenerator()
        await generator.initialize()

        # No API keys available
        generator.openai_client = None
        generator.stability_client = None

        with (
            patch.object(settings, "stability_api_key", ""),
            patch.object(settings, "openai_api_key", ""),
        ):
            with pytest.raises(
                Exception, match="No image generation service available"
            ):
                await generator.generate_image(
                    prompt="Test image", style="realistic"
                )

        await generator.shutdown()

    @pytest.mark.asyncio
    async def test_music_generation_fallback(self):
        """Test music generation with procedural fallback"""
        client = SunoClient()
        await client.initialize()

        # Disable Suno API to test fallback
        client.api_key = ""
        client.http_client = None

        with patch.object(
            client, "_save_music", return_value="/storage/music/test.mp3"
        ):
            result = await client.generate_music(
                prompt="Test music", style="background", duration_seconds=10
            )

            assert "generation_id" in result
            assert "music_id" in result
            assert result["service"] == "procedural_fallback"

        await client.shutdown()

    def test_all_services_configuration(self):
        """Test that all services have proper configuration"""
        # Test that settings are accessible
        assert hasattr(settings, "openai_api_key")
        assert hasattr(settings, "google_api_key")
        assert hasattr(settings, "stability_api_key")
        assert hasattr(settings, "elevenlabs_api_key")
        assert hasattr(settings, "suno_api_key")

        # Test temp storage path
        assert hasattr(settings, "temp_storage_path")
        assert os.path.exists(settings.temp_storage_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
