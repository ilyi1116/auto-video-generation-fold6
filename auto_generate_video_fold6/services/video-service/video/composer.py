"""
Video Composer

This module handles video composition, combining generated audio, images, and captions
into final video content with proper timing, transitions, and effects.
"""

import asyncio
import json
import logging
import os
import shutil
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SceneComposition(BaseModel):
    """Individual scene composition data"""

    sequence: int
    start_time: float
    duration: float
    image_url: str
    narration_text: str
    visual_effects: List[str] = []
    transition_type: str = "fade"


class CompositionRequest(BaseModel):
    """Video composition request parameters"""

    project_id: str
    scenes: List[SceneComposition]
    voice_url: str
    music_url: Optional[str] = None
    include_captions: bool = True
    target_platform: str = "youtube"
    quality: str = "high"


class CompositionResult(BaseModel):
    """Video composition result"""

    composition_id: str
    preview_url: str
    status: str
    created_at: datetime
    estimated_render_time: int  # seconds


class FinalRenderResult(BaseModel):
    """Final video render result"""

    video_url: str
    thumbnail_url: str
    duration: float
    file_size: int  # bytes
    resolution: str
    format: str


class VideoComposer:
    """Video composition and rendering engine"""

    def __init__(self):
        self.temp_dir = tempfile.mkdtemp(prefix="video_composer_")
        self.output_dir = "storage/videos"
        self.preview_dir = "storage/previews"

        # Ensure output directories exist
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.preview_dir, exist_ok=True)

        # Platform-specific settings
        self.platform_settings = {
            "youtube": {
                "resolution": "1920x1080",
                "fps": 30,
                "bitrate": "5000k",
                "audio_bitrate": "192k",
                "format": "mp4",
            },
            "tiktok": {
                "resolution": "1080x1920",
                "fps": 30,
                "bitrate": "3000k",
                "audio_bitrate": "128k",
                "format": "mp4",
            },
            "instagram": {
                "resolution": "1080x1080",
                "fps": 30,
                "bitrate": "3500k",
                "audio_bitrate": "160k",
                "format": "mp4",
            },
        }

    async def create_video(
        self,
        script_scenes: List[Any],  # ScriptScene objects from Gemini
        voice_url: str,
        music_url: Optional[str],
        image_urls: List[str],
        include_captions: bool = True,
        target_platform: str = "youtube",
    ) -> CompositionResult:
        """Create video composition from components"""

        try:
            composition_id = f"comp_{datetime.utcnow().timestamp()}"
            logger.info(f"Starting video composition: {composition_id}")

            # Download all media assets
            voice_path = await self._download_media(
                voice_url, f"{composition_id}_voice.mp3"
            )
            music_path = (
                await self._download_media(
                    music_url, f"{composition_id}_music.mp3"
                )
                if music_url
                else None
            )

            image_paths = []
            for i, image_url in enumerate(image_urls):
                image_path = await self._download_media(
                    image_url, f"{composition_id}_img_{i}.png"
                )
                image_paths.append(image_path)

            # Create scene compositions
            scenes = []
            current_time = 0.0

            for i, (script_scene, image_path) in enumerate(
                zip(script_scenes, image_paths)
            ):
                scene = SceneComposition(
                    sequence=i,
                    start_time=current_time,
                    duration=script_scene.duration,
                    image_url=image_path,
                    narration_text=script_scene.narration_text,
                    visual_effects=self._get_scene_effects(
                        script_scene.scene_type
                    ),
                    transition_type=self._get_transition_type(
                        i, len(script_scenes)
                    ),
                )
                scenes.append(scene)
                current_time += script_scene.duration

            # Generate preview video
            preview_path = await self._create_preview(
                composition_id,
                scenes,
                voice_path,
                music_path,
                target_platform,
                include_captions,
            )

            # Upload preview and get URL
            preview_url = await self._upload_media(preview_path, "previews")

            logger.info(f"Video composition created: {composition_id}")

            return CompositionResult(
                composition_id=composition_id,
                preview_url=preview_url,
                status="ready_for_render",
                created_at=datetime.utcnow(),
                estimated_render_time=int(current_time * 2),  # Rough estimate
            )

        except Exception as e:
            logger.error(f"Video composition failed: {str(e)}")
            raise Exception(f"Failed to create video composition: {str(e)}")

    async def render_final(
        self, composition_id: str, quality: str = "high"
    ) -> FinalRenderResult:
        """Render final high-quality video"""

        try:
            logger.info(f"Starting final render: {composition_id}")

            # Load composition data
            # (in real implementation, this would be from database)
            composition_data = await self._load_composition_data(
                composition_id
            )

            if not composition_data:
                raise Exception(f"Composition {composition_id} not found")

            # Render final video
            final_video_path = await self._render_final_video(
                composition_id, composition_data, quality
            )

            # Generate thumbnail
            thumbnail_path = await self._generate_thumbnail(
                final_video_path, composition_id
            )

            # Get video metadata
            metadata = await self._get_video_metadata(final_video_path)

            # Upload final video and thumbnail
            video_url = await self._upload_media(final_video_path, "videos")
            thumbnail_url = await self._upload_media(
                thumbnail_path, "thumbnails"
            )

            logger.info(f"Final render completed: {composition_id}")

            return FinalRenderResult(
                video_url=video_url,
                thumbnail_url=thumbnail_url,
                duration=metadata["duration"],
                file_size=metadata["file_size"],
                resolution=metadata["resolution"],
                format=metadata["format"],
            )

        except Exception as e:
            logger.error(f"Final render failed: {str(e)}")
            raise Exception(f"Failed to render final video: {str(e)}")

    async def _download_media(self, url: str, filename: str) -> str:
        """Download media file from URL"""

        if url.startswith("http"):
            # Download from remote URL
            import aiohttp

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise Exception(
                            f"Failed to download media: {response.status}"
                        )

                    file_path = os.path.join(self.temp_dir, filename)
                    with open(file_path, "wb") as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)

                    return file_path
        else:
            # Local file path
            return url

    async def _create_preview(
        self,
        composition_id: str,
        scenes: List[SceneComposition],
        voice_path: str,
        music_path: Optional[str],
        target_platform: str,
        include_captions: bool,
    ) -> str:
        """Create preview video with lower quality for quick review"""

        settings = self.platform_settings[target_platform]
        preview_path = os.path.join(
            self.temp_dir, f"{composition_id}_preview.mp4"
        )

        # Create FFmpeg filter complex for preview
        filter_complex = await self._build_filter_complex(
            scenes,
            voice_path,
            music_path,
            settings,
            include_captions,
            preview=True,
        )

        # Build FFmpeg command for preview
        cmd = ["ffmpeg", "-y", "-i", voice_path]

        # Add music input if available
        if music_path:
            cmd.extend(["-i", music_path])

        # Add image inputs
        for scene in scenes:
            cmd.extend(["-i", scene.image_url])

        # Add filter complex and output settings
        cmd.extend(
            [
                "-filter_complex",
                filter_complex,
                "-c:v",
                "libx264",
                "-preset",
                "fast",  # Fast preset for preview
                "-crf",
                "28",  # Lower quality for preview
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-r",
                "24",  # Lower fps for preview
                "-t",
                str(sum(scene.duration for scene in scenes)),
                preview_path,
            ]
        )

        # Run FFmpeg
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
            raise Exception(f"FFmpeg preview generation failed: {error_msg}")

        return preview_path

    async def _render_final_video(
        self,
        composition_id: str,
        composition_data: Dict[str, Any],
        quality: str,
    ) -> str:
        """Render final high-quality video"""

        final_path = os.path.join(
            self.output_dir, f"{composition_id}_final.mp4"
        )

        # Quality settings
        quality_settings = {
            "low": {"crf": "28", "preset": "fast"},
            "medium": {"crf": "23", "preset": "medium"},
            "high": {"crf": "18", "preset": "slow"},
            "ultra": {"crf": "15", "preset": "veryslow"},
        }

        settings = quality_settings.get(quality, quality_settings["high"])
        platform_settings = self.platform_settings[
            composition_data["target_platform"]
        ]

        # Build comprehensive FFmpeg command for final render
        cmd = ["ffmpeg", "-y", "-i", composition_data["voice_path"]]

        if composition_data.get("music_path"):
            cmd.extend(["-i", composition_data["music_path"]])

        # Add all image inputs
        for scene in composition_data["scenes"]:
            cmd.extend(["-i", scene["image_url"]])

        # Complex filter for final render
        filter_complex = await self._build_filter_complex(
            composition_data["scenes"],
            composition_data["voice_path"],
            composition_data.get("music_path"),
            platform_settings,
            composition_data.get("include_captions", True),
            preview=False,
        )

        cmd.extend(
            [
                "-filter_complex",
                filter_complex,
                "-c:v",
                "libx264",
                "-preset",
                settings["preset"],
                "-crf",
                settings["crf"],
                "-c:a",
                "aac",
                "-b:a",
                platform_settings["audio_bitrate"],
                "-r",
                str(platform_settings["fps"]),
                "-s",
                platform_settings["resolution"],
                final_path,
            ]
        )

        # Run final render
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown FFmpeg error"
            raise Exception(f"FFmpeg final render failed: {error_msg}")

        return final_path

    async def _build_filter_complex(
        self,
        scenes: List[Any],
        voice_path: str,
        music_path: Optional[str],
        settings: Dict[str, Any],
        include_captions: bool,
        preview: bool = False,
    ) -> str:
        """Build FFmpeg filter complex for video composition"""

        # This is a simplified version - real implementation would be much more
        # complex
        filter_parts = []

        # Scale and process images
        for i, scene in enumerate(scenes):
            input_idx = i + (
                2 if music_path else 1
            )  # Account for audio inputs
            filter_parts.append(
                f"[{input_idx}:v]scale={settings['resolution']}:force_original_aspect_ratio=increase,"
                f"crop={settings['resolution']},setsar=1[img{i}]"
            )

        # Concatenate video segments
        concat_inputs = "".join(f"[img{i}]" for i in range(len(scenes)))
        filter_parts.append(
            f"{concat_inputs}concat=n={len(scenes)}:v=1:a=0[video]"
        )

        # Audio mixing
        if music_path:
            filter_parts.append(
                "[0:a][1:a]amix=inputs=2:duration=first[audio]"
            )
            audio_output = "[audio]"
        else:
            audio_output = "[0:a]"

        return ";".join(filter_parts)

    def _get_scene_effects(self, scene_type: str) -> List[str]:
        """Get visual effects based on scene type"""

        effects_map = {
            "intro": ["fade_in", "zoom_in"],
            "main": ["pan", "zoom"],
            "transition": ["crossfade"],
            "outro": ["fade_out", "zoom_out"],
        }

        return effects_map.get(scene_type, [])

    def _get_transition_type(self, scene_index: int, total_scenes: int) -> str:
        """Determine transition type for scene"""

        if scene_index == 0:
            return "fade_in"
        elif scene_index == total_scenes - 1:
            return "fade_out"
        else:
            return "crossfade"

    async def _generate_thumbnail(
        self, video_path: str, composition_id: str
    ) -> str:
        """Generate thumbnail from video"""

        thumbnail_path = os.path.join(
            self.temp_dir, f"{composition_id}_thumb.jpg"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-ss",
            "00:00:03",  # 3 seconds into video
            "-vframes",
            "1",
            "-vf",
            "scale=1280:720",
            thumbnail_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        await process.communicate()

        if process.returncode != 0:
            logger.warning(f"Thumbnail generation failed for {composition_id}")
            return None

        return thumbnail_path

    async def _get_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """Get video file metadata"""

        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            video_path,
        ]

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, _ = await process.communicate()

        if process.returncode != 0:
            return {
                "duration": 0,
                "file_size": 0,
                "resolution": "unknown",
                "format": "mp4",
            }

        metadata = json.loads(stdout.decode())

        # Extract relevant information
        format_info = metadata.get("format", {})
        video_stream = next(
            (
                s
                for s in metadata.get("streams", [])
                if s["codec_type"] == "video"
            ),
            {},
        )

        return {
            "duration": float(format_info.get("duration", 0)),
            "file_size": int(format_info.get("size", 0)),
            "resolution": f"{video_stream.get('width', 0
                                              )}x{video_stream.get('height', 0)}",
            "format": format_info.get("format_name", "mp4").split(",")[0],
        }

    async def _upload_media(self, file_path: str, media_type: str) -> str:
        """Upload media file and return URL"""

        # In production, this would upload to cloud storage (S3, GCS, etc.)
        # For now, we'll just move to local storage

        filename = os.path.basename(file_path)
        destination_dir = f"storage/{media_type}"
        os.makedirs(destination_dir, exist_ok=True)

        destination_path = os.path.join(destination_dir, filename)
        shutil.copy2(file_path, destination_path)

        # Return URL
        base_url = os.getenv("MEDIA_BASE_URL", "http://localhost:8003")
        return f"{base_url}/media/{media_type}/{filename}"

    async def _load_composition_data(
        self, composition_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load composition data (placeholder - would be from database)"""

        # This is a placeholder - in real implementation,
        # this would load from database or cache
        return {
            "composition_id": composition_id,
            "target_platform": "youtube",
            "scenes": [],
            "voice_path": "",
            "music_path": None,
            "include_captions": True,
        }

    def cleanup(self):
        """Clean up temporary files"""

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")

    def __del__(self):
        """Cleanup on destruction"""
        self.cleanup()
