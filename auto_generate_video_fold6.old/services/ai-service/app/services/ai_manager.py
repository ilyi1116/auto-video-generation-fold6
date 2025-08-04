import asyncio
import time
import uuid
from typing import Any, Dict, Optional

import structlog

from ..config import settings
from .audio_processor import AudioProcessor
from .image_generator import ImageGenerator
from .suno_client import SunoClient
from .text_generator import TextGenerator

logger = structlog.get_logger()


class AIManager:
    """Central AI service manager for coordinating all AI operations"""

    def __init__(self):
        self.text_generator: Optional[TextGenerator] = None
        self.image_generator: Optional[ImageGenerator] = None
        self.audio_processor: Optional[AudioProcessor] = None
        self.suno_client: Optional[SunoClient] = None
        self.initialized = False

        # Service health tracking
        self.service_health = {
            "text_generation": False,
            "image_generation": False,
            "audio_processing": False,
            "music_generation": False,
        }

    async def initialize(self):
        """Initialize all AI services"""
        try:
            logger.info("Initializing AI Manager")
            start_time = time.time()

            # Initialize all services concurrently
            initialization_tasks = [
                self._initialize_text_generator(),
                self._initialize_image_generator(),
                self._initialize_audio_processor(),
                self._initialize_suno_client(),
            ]

            await asyncio.gather(*initialization_tasks, return_exceptions=True)

            # Update health status
            await self._update_health_status()

            initialization_time = time.time() - start_time
            self.initialized = True

            logger.info(
                "AI Manager initialized successfully",
                initialization_time=round(initialization_time, 2),
                healthy_services=sum(self.service_health.values()),
            )

        except Exception as e:
            logger.error("Failed to initialize AI Manager", error=str(e))
            raise

    async def shutdown(self):
        """Shutdown all AI services"""
        try:
            logger.info("Shutting down AI Manager")

            # Shutdown all services concurrently
            shutdown_tasks = []

            if self.text_generator:
                shutdown_tasks.append(self.text_generator.shutdown())

            if self.image_generator:
                shutdown_tasks.append(self.image_generator.shutdown())

            if self.audio_processor:
                shutdown_tasks.append(self.audio_processor.shutdown())

            if self.suno_client:
                shutdown_tasks.append(self.suno_client.shutdown())

            if shutdown_tasks:
                await asyncio.gather(*shutdown_tasks, return_exceptions=True)

            self.initialized = False
            logger.info("AI Manager shutdown complete")

        except Exception as e:
            logger.error("Error during AI Manager shutdown", error=str(e))

    async def _initialize_text_generator(self):
        """Initialize text generation service"""
        try:
            self.text_generator = TextGenerator()
            await self.text_generator.initialize()
            logger.info("Text generator initialized")
        except Exception as e:
            logger.error("Failed to initialize text generator", error=str(e))

    async def _initialize_image_generator(self):
        """Initialize image generation service"""
        try:
            self.image_generator = ImageGenerator()
            await self.image_generator.initialize()
            logger.info("Image generator initialized")
        except Exception as e:
            logger.error("Failed to initialize image generator", error=str(e))

    async def _initialize_audio_processor(self):
        """Initialize audio processing service"""
        try:
            self.audio_processor = AudioProcessor()
            await self.audio_processor.initialize()
            logger.info("Audio processor initialized")
        except Exception as e:
            logger.error("Failed to initialize audio processor", error=str(e))

    async def _initialize_suno_client(self):
        """Initialize music generation service"""
        try:
            self.suno_client = SunoClient()
            await self.suno_client.initialize()
            logger.info("Suno client initialized")
        except Exception as e:
            logger.error("Failed to initialize Suno client", error=str(e))

    async def _update_health_status(self):
        """Update health status for all services"""
        self.service_health = {
            "text_generation": (
                self.text_generator.is_healthy()
                if self.text_generator
                else False
            ),
            "image_generation": (
                self.image_generator.is_healthy()
                if self.image_generator
                else False
            ),
            "audio_processing": (
                self.audio_processor.is_healthy()
                if self.audio_processor
                else False
            ),
            "music_generation": (
                self.suno_client.is_healthy() if self.suno_client else False
            ),
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        healthy_count = sum(self.service_health.values())
        total_count = len(self.service_health)

        return {
            "overall_status": (
                "healthy" if healthy_count >= total_count // 2 else "degraded"
            ),
            "healthy_services": healthy_count,
            "total_services": total_count,
            "services": self.service_health,
            "initialized": self.initialized,
            "api_keys_configured": {
                "openai": bool(settings.openai_api_key),
                "google": bool(settings.google_api_key),
                "stability": bool(settings.stability_api_key),
                "elevenlabs": bool(settings.elevenlabs_api_key),
                "suno": bool(settings.suno_api_key),
            },
        }

    def is_healthy(self) -> bool:
        """Check if AI Manager is healthy"""
        return self.initialized and sum(self.service_health.values()) > 0

    # Content Generation Workflows

    async def generate_video_content(
        self,
        script_topic: str,
        video_style: str = "modern",
        duration_seconds: int = 60,
        platform: str = "tiktok",
        include_music: bool = True,
        include_voice: bool = True,
    ) -> Dict[str, Any]:
        """Generate complete video content (script, images, voice, music)"""
        try:
            logger.info(
                "Generating complete video content",
                topic=script_topic,
                style=video_style,
                duration=duration_seconds,
                platform=platform,
            )

            project_id = str(uuid.uuid4())
            start_time = time.time()

            # Step 1: Generate script
            if not self.text_generator or not self.text_generator.is_healthy():
                raise Exception("Text generation service not available")

            script_result = await self.text_generator.generate_script(
                topic=script_topic,
                style="engaging",
                duration_seconds=duration_seconds,
            )

            # Step 2: Generate titles
            titles_result = await self.text_generator.generate_titles(
                script_content=script_result["content"],
                style="catchy",
                max_length=100,
            )

            # Parallel generation of media assets
            media_tasks = []

            # Step 3: Generate images (if available)
            if self.image_generator and self.image_generator.is_healthy():
                image_task = self.image_generator.generate_image(
                    prompt=f"Visual representation of: {script_topic}",
                    style=video_style,
                    aspect_ratio="9:16" if platform == "tiktok" else "16:9",
                    resolution="1080p",
                )
                media_tasks.append(("image", image_task))

            # Step 4: Generate voice (if requested and available)
            if (
                include_voice
                and self.audio_processor
                and self.audio_processor.is_healthy()
            ):
                voice_task = self.audio_processor.synthesize_voice(
                    text=script_result["content"],
                    voice_style="natural",
                    language="en",
                    emotion="neutral",
                )
                media_tasks.append(("voice", voice_task))

            # Step 5: Generate music (if requested and available)
            if (
                include_music
                and self.suno_client
                and self.suno_client.is_healthy()
            ):
                music_task = self.suno_client.generate_music(
                    prompt=f"Background music for {script_topic}",
                    style="background",
                    duration_seconds=duration_seconds,
                    platform=platform,
                    instrumental=True,
                )
                media_tasks.append(("music", music_task))

            # Execute media generation tasks
            media_results = {}
            if media_tasks:
                task_results = await asyncio.gather(
                    *[task[1] for task in media_tasks], return_exceptions=True
                )

                for i, (media_type, _) in enumerate(media_tasks):
                    result = task_results[i]
                    if not isinstance(result, Exception):
                        media_results[media_type] = result
                    else:
                        logger.warning(
                            f"Failed to generate {media_type}",
                            error=str(result),
                        )

            generation_time = time.time() - start_time

            # Compile final result
            video_content = {
                "project_id": project_id,
                "script": script_result,
                "titles": titles_result,
                "media": media_results,
                "metadata": {
                    "topic": script_topic,
                    "style": video_style,
                    "duration_seconds": duration_seconds,
                    "platform": platform,
                    "generation_time_seconds": round(generation_time, 2),
                    "assets_generated": list(media_results.keys()),
                    "status": "completed",
                },
            }

            logger.info(
                "Video content generation completed",
                project_id=project_id,
                assets_count=len(media_results),
                generation_time=generation_time,
            )

            return video_content

        except Exception as e:
            logger.error("Video content generation failed", error=str(e))
            raise

    def get_service_capabilities(self) -> Dict[str, Any]:
        """Get capabilities of all available services"""
        capabilities = {
            "text_generation": {
                "available": self.service_health["text_generation"],
                "features": (
                    [
                        "script_generation",
                        "title_generation",
                        "content_optimization",
                    ]
                    if self.text_generator
                    else []
                ),
                "supported_languages": (
                    ["en", "zh", "ja", "ko", "es", "fr", "de"]
                    if self.text_generator
                    else []
                ),
            },
            "image_generation": {
                "available": self.service_health["image_generation"],
                "features": (
                    [
                        "image_generation",
                        "style_transfer",
                        "upscaling",
                        "variations",
                    ]
                    if self.image_generator
                    else []
                ),
                "supported_styles": (
                    ["photorealistic", "artistic", "cartoon", "anime"]
                    if self.image_generator
                    else []
                ),
            },
            "audio_processing": {
                "available": self.service_health["audio_processing"],
                "features": (
                    ["voice_synthesis", "voice_cloning", "audio_enhancement"]
                    if self.audio_processor
                    else []
                ),
                "supported_voices": (
                    ["natural", "professional", "energetic"]
                    if self.audio_processor
                    else []
                ),
            },
            "music_generation": {
                "available": self.service_health["music_generation"],
                "features": (
                    ["music_generation", "variations", "extension"]
                    if self.suno_client
                    else []
                ),
                "supported_styles": (
                    ["background", "energetic", "cinematic"]
                    if self.suno_client
                    else []
                ),
            },
        }

        return {
            "capabilities": capabilities,
            "overall_health": self.get_health_status(),
        }
