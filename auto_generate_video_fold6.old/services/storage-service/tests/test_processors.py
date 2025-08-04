import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from app.processors import (
    AudioProcessor,
    ImageProcessor,
    ProcessorManager,
    VideoProcessor,
)
from PIL import Image

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))


class TestImageProcessor:
    """Test image processing functionality"""

    def setup_method(self):
        self.processor = ImageProcessor()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_test_image(self, size=(100, 100), format="JPEG"):
        """Create a test image file"""
        img = Image.new("RGB", size, color="red")
        img_path = os.path.join(self.temp_dir, f"test.{format.lower()}")
        img.save(img_path, format)
        return img_path

    @pytest.mark.asyncio
    async def test_process_image_basic(self):
        """Test basic image processing"""
        input_path = self.create_test_image()
        output_path = os.path.join(self.temp_dir, "output.jpg")

        result = await self.processor.process(input_path, output_path)

        assert result["width"] == 100
        assert result["height"] == 100
        assert result["processed"] is True
        assert os.path.exists(output_path)

    @pytest.mark.asyncio
    async def test_process_image_resize(self):
        """Test image resizing"""
        input_path = self.create_test_image(size=(2000, 1500))
        output_path = os.path.join(self.temp_dir, "output.jpg")

        result = await self.processor.process(
            input_path, output_path, max_dimension=800
        )

        # Should be resized to fit within 800px
        assert max(result["width"], result["height"]) <= 800
        assert result["processed"] is True

    @pytest.mark.asyncio
    async def test_process_image_with_thumbnail(self):
        """Test image processing with thumbnail generation"""
        input_path = self.create_test_image()
        output_path = os.path.join(self.temp_dir, "output.jpg")

        result = await self.processor.process(
            input_path,
            output_path,
            generate_thumbnail=True,
            thumbnail_size=150,
        )

        assert result["thumbnail_path"] is not None
        assert os.path.exists(result["thumbnail_path"])

    def test_get_metadata(self):
        """Test image metadata extraction"""
        input_path = self.create_test_image(size=(200, 150))

        metadata = self.processor.get_metadata(input_path)

        assert metadata["width"] == 200
        assert metadata["height"] == 150
        assert metadata["format"] == "JPEG"
        assert metadata["mode"] == "RGB"

    @pytest.mark.asyncio
    async def test_rgba_to_rgb_conversion(self):
        """Test RGBA to RGB conversion for JPEG"""
        # Create RGBA image
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        input_path = os.path.join(self.temp_dir, "test.png")
        img.save(input_path, "PNG")

        output_path = os.path.join(self.temp_dir, "output.jpg")

        result = await self.processor.process(input_path, output_path)

        # Should convert to RGB
        assert result["processed"] is True
        assert os.path.exists(output_path)


class TestAudioProcessor:
    """Test audio processing functionality"""

    def setup_method(self):
        self.processor = AudioProcessor()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    @patch("app.processors.asyncio.create_subprocess_exec")
    async def test_process_audio_success(self, mock_subprocess):
        """Test successful audio processing"""
        # Mock ffmpeg subprocess
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))
        mock_subprocess.return_value = mock_process

        input_path = os.path.join(self.temp_dir, "input.wav")
        output_path = os.path.join(self.temp_dir, "output.mp3")

        # Create dummy input file
        with open(input_path, "wb") as f:
            f.write(b"dummy audio data")

        with patch.object(self.processor, "get_metadata") as mock_metadata:
            mock_metadata.return_value = {
                "duration": 120.0,
                "bitrate": 128000,
                "sample_rate": 44100,
                "channels": 2,
            }

            result = await self.processor.process(input_path, output_path)

        assert result["duration"] == 120.0
        assert result["bitrate"] == 128000
        assert result["processed"] is True

    @pytest.mark.asyncio
    @patch("app.processors.asyncio.create_subprocess_exec")
    async def test_process_audio_failure(self, mock_subprocess):
        """Test audio processing failure"""
        # Mock failed ffmpeg subprocess
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(
            return_value=(b"", b"Error processing audio")
        )
        mock_subprocess.return_value = mock_process

        input_path = os.path.join(self.temp_dir, "input.wav")
        output_path = os.path.join(self.temp_dir, "output.mp3")

        with pytest.raises(Exception, match="Audio processing failed"):
            await self.processor.process(input_path, output_path)

    @patch("app.processors.subprocess.run")
    def test_get_metadata_success(self, mock_subprocess):
        """Test audio metadata extraction"""
        # Mock ffprobe output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
        {
            "streams": [
                {
                    "codec_type": "audio",
                    "codec_name": "mp3",
                    "sample_rate": "44100",
                    "channels": 2
                }
            ],
            "format": {
                "duration": "120.5",
                "bit_rate": "128000",
                "format_name": "mp3"
            }
        }
        """
        mock_subprocess.return_value = mock_result

        input_path = os.path.join(self.temp_dir, "test.mp3")
        metadata = self.processor.get_metadata(input_path)

        assert metadata["duration"] == 120.5
        assert metadata["bitrate"] == 128000
        assert metadata["sample_rate"] == 44100
        assert metadata["channels"] == 2
        assert metadata["codec"] == "mp3"


class TestVideoProcessor:
    """Test video processing functionality"""

    def setup_method(self):
        self.processor = VideoProcessor()
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    @pytest.mark.asyncio
    @patch("app.processors.asyncio.create_subprocess_exec")
    async def test_process_video_success(self, mock_subprocess):
        """Test successful video processing"""
        # Mock ffmpeg subprocess
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))
        mock_subprocess.return_value = mock_process

        input_path = os.path.join(self.temp_dir, "input.mp4")
        output_path = os.path.join(self.temp_dir, "output.mp4")

        with patch.object(self.processor, "get_metadata") as mock_metadata:
            mock_metadata.return_value = {
                "duration": 60.0,
                "width": 1920,
                "height": 1080,
                "fps": 30.0,
                "bitrate": 2000000,
                "codec": "h264",
            }

            with patch.object(
                self.processor, "_generate_video_thumbnail"
            ) as mock_thumb:
                mock_thumb.return_value = "thumbnail.jpg"

                result = await self.processor.process(input_path, output_path)

        assert result["duration"] == 60.0
        assert result["width"] == 1920
        assert result["height"] == 1080
        assert result["thumbnail_path"] == "thumbnail.jpg"
        assert result["processed"] is True

    @pytest.mark.asyncio
    @patch("app.processors.asyncio.create_subprocess_exec")
    async def test_generate_video_thumbnail(self, mock_subprocess):
        """Test video thumbnail generation"""
        # Mock ffmpeg subprocess for thumbnail
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"", b""))
        mock_subprocess.return_value = mock_process

        input_path = os.path.join(self.temp_dir, "input.mp4")
        output_path = os.path.join(self.temp_dir, "output.mp4")

        result = await self.processor._generate_video_thumbnail(
            input_path, output_path
        )

        assert result is not None
        assert "thumb.jpg" in result

    @patch("app.processors.subprocess.run")
    def test_get_metadata_success(self, mock_subprocess):
        """Test video metadata extraction"""
        # Mock ffprobe output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = """
        {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "30/1",
                    "bit_rate": "2000000"
                },
                {
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "sample_rate": "44100",
                    "channels": 2,
                    "bit_rate": "128000"
                }
            ],
            "format": {
                "duration": "90.5",
                "format_name": "mp4"
            }
        }
        """
        mock_subprocess.return_value = mock_result

        input_path = os.path.join(self.temp_dir, "test.mp4")
        metadata = self.processor.get_metadata(input_path)

        assert metadata["duration"] == 90.5
        assert metadata["width"] == 1920
        assert metadata["height"] == 1080
        assert metadata["fps"] == 30.0
        assert metadata["video_codec"] == "h264"
        assert metadata["audio_codec"] == "aac"


class TestProcessorManager:
    """Test processor manager"""

    def setup_method(self):
        self.manager = ProcessorManager()

    def test_get_processor(self):
        """Test getting processors by type"""
        image_processor = self.manager.get_processor("image")
        audio_processor = self.manager.get_processor("audio")
        video_processor = self.manager.get_processor("video")
        invalid_processor = self.manager.get_processor("invalid")

        assert isinstance(image_processor, ImageProcessor)
        assert isinstance(audio_processor, AudioProcessor)
        assert isinstance(video_processor, VideoProcessor)
        assert invalid_processor is None

    @pytest.mark.asyncio
    async def test_process_file_invalid_type(self):
        """Test processing file with invalid type"""
        with pytest.raises(ValueError, match="No processor available"):
            await self.manager.process_file("/path/to/file", "invalid_type")

    @pytest.mark.asyncio
    async def test_process_file_auto_output_path(self):
        """Test processing file with auto-generated output path"""
        with patch.object(self.manager, "get_processor") as mock_get:
            mock_processor = MagicMock()
            mock_processor.process = AsyncMock(
                return_value={"processed": True}
            )
            mock_get.return_value = mock_processor

            result = await self.manager.process_file(
                "/path/to/input.jpg", "image"
            )

            # Check that processor was called with auto-generated output path
            mock_processor.process.assert_called_once()
            args = mock_processor.process.call_args[0]
            assert args[0] == "/path/to/input.jpg"
            assert args[1] == "/path/to/input_processed.jpg"

    def test_get_metadata_invalid_type(self):
        """Test getting metadata for invalid file type"""
        result = self.manager.get_metadata("/path/to/file", "invalid_type")
        assert result == {}
