"""
Complete Video Generation Service

This module orchestrates the entire video generation process by integrating
all AI services (
    script generation, image generation, voice synthesis, music generation)
and the video composition engine.
"""

import asyncio
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
import structlog
from pydantic import BaseModel

from .composer import VideoComposer

logger = structlog.get_logger()


class VideoGenerationRequest(BaseModel):
    """Complete video generation request"""

    topic: str
    target_platform: str = "youtube"
    voice_settings: Dict[str, Any] = {}
    include_music: bool = True
    include_captions: bool = True
    image_style: str = "realistic"
    video_length: str = "short"  # short, medium, long
    quality: str = "high"


class VideoGenerationResult(BaseModel):
    """Video generation result"""

    generation_id: str
    status: str
    preview_url: Optional[str] = None
    final_video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime
    estimated_completion: datetime
    metadata: Dict[str, Any] = {}


class VideoGenerationService:
    """Complete video generation orchestration service"""

    def __init__(self):
        self.composer = VideoComposer()

        # AI Service endpoints
        self.ai_service_base = os.getenv("AI_SERVICE_URL", "http://ai-service:8002")
        self.storage_service_base = os.getenv("STORAGE_SERVICE_URL", "http://storage-service:8003")

        # Generation status tracking
        self.generation_status = {}

    async def generate_video(
        self, request: VideoGenerationRequest, user_id: str
    ) -> VideoGenerationResult:
        """Generate complete video from topic"""

        generation_id = str(uuid.uuid4())

        try:
            logger.info(
                "Starting video generation",
                generation_id=generation_id,
                user_id=user_id,
                topic=request.topic,
                platform=request.target_platform,
            )

            # Initialize generation tracking
            self.generation_status[generation_id] = {
                "status": "initializing",
                "progress": 0,
                "current_step": "Starting generation",
                "created_at": datetime.utcnow(),
            }

            # Start async generation process
            asyncio.create_task(self._generate_video_async(generation_id, request, user_id))

            return VideoGenerationResult(
                generation_id=generation_id,
                status="processing",
                created_at=datetime.utcnow(),
                estimated_completion=datetime.utcnow().replace(microsecond=0).replace(second=0)
                + self._estimate_completion_time(request),
                metadata={
                    "topic": request.topic,
                    "platform": request.target_platform,
                    "user_id": user_id,
                },
            )

        except Exception as e:
            logger.error(
                "Failed to initialize video generation",
                error=str(e),
                generation_id=generation_id,
                user_id=user_id,
            )
            raise Exception(f"Failed to start video generation: {str(e)}")

    async def get_generation_status(self, generation_id: str) -> Dict[str, Any]:
        """Get current generation status"""

        status = self.generation_status.get(generation_id)
        if not status:
            raise Exception("Generation not found")

        return status

    async def _generate_video_async(
        self, generation_id: str, request: VideoGenerationRequest, user_id: str
    ):
        """Async video generation process"""

        try:
            # Step 1: Generate script
            await self._update_status(
                generation_id,
                "generating_script",
                10,
                "Generating video script",
            )

            script_data = await self._generate_script(
                request.topic, request.target_platform, request.video_length
            )

            # Step 2: Generate images
            await self._update_status(
                generation_id,
                "generating_images",
                30,
                "Creating visual content",
            )

            image_urls = await self._generate_images(script_data["scenes"], request.image_style)

            # Step 3: Generate voice narration
            await self._update_status(
                generation_id,
                "generating_voice",
                50,
                "Synthesizing voice narration",
            )

            voice_url = await self._generate_voice(
                script_data["full_script"], request.voice_settings
            )

            # Step 4: Generate background music (if requested)
            music_url = None
            if request.include_music:
                await self._update_status(
                    generation_id,
                    "generating_music",
                    60,
                    "Creating background music",
                )

                music_url = await self._generate_music(request.topic, script_data["mood"])

            # Step 5: Create video composition
            await self._update_status(
                generation_id,
                "composing_video",
                70,
                "Composing video elements",
            )

            composition_result = await self.composer.create_video(
                script_scenes=script_data["scenes"],
                voice_url=voice_url,
                music_url=music_url,
                image_urls=image_urls,
                include_captions=request.include_captions,
                target_platform=request.target_platform,
            )

            # Step 6: Generate preview
            await self._update_status(
                generation_id,
                "generating_preview",
                80,
                "Creating preview video",
            )

            # Step 7: Render final video
            await self._update_status(generation_id, "rendering_final", 90, "Rendering final video")

            final_result = await self.composer.render_final(
                composition_result.composition_id, request.quality
            )

            # Step 8: Complete
            await self._update_status(
                generation_id,
                "completed",
                100,
                "Video generation completed",
                {
                    "preview_url": composition_result.preview_url,
                    "final_video_url": final_result.video_url,
                    "thumbnail_url": final_result.thumbnail_url,
                    "duration": final_result.duration,
                    "file_size": final_result.file_size,
                    "resolution": final_result.resolution,
                },
            )

            logger.info(
                "Video generation completed successfully",
                generation_id=generation_id,
                user_id=user_id,
                duration=final_result.duration,
            )

        except Exception as e:
            logger.error(
                "Video generation failed",
                error=str(e),
                generation_id=generation_id,
                user_id=user_id,
            )

            await self._update_status(generation_id, "failed", 0, f"Generation failed: {str(e)}")

    async def _generate_script(self, topic: str, platform: str, length: str) -> Dict[str, Any]:
        """Generate video script using AI service"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.ai_service_base}/api/v1/script/generate",
                json={
                    "topic": topic,
                    "platform": platform,
                    "length": length,
                    "include_scenes": True,
                    "include_timing": True,
                },
            )

            if response.status_code != 200:
                raise Exception(f"Script generation failed: {response.text}")

            return response.json()

    async def _generate_images(self, scenes: List[Dict], style: str) -> List[str]:
        """Generate images for each scene"""

        image_urls = []

        async with httpx.AsyncClient(timeout=60.0) as client:
            for i, scene in enumerate(scenes):
                try:
                    response = await client.post(
                        f"{self.ai_service_base}/api/v1/image/generate",
                        json={
                            "prompt": scene["visual_description"],
                            "style": style,
                            "aspect_ratio": "16:9",
                            "quality": "high",
                        },
                    )

                    if response.status_code == 200:
                        result = response.json()
                        image_urls.append(result["image_url"])
                    else:
                        logger.warning(
                            f"Image generation failed for scene {i}: \
                                {response.text}"
                        )
                        # Use a placeholder or default image
                        image_urls.append(self._get_placeholder_image())

                except Exception as e:
                    logger.warning(f"Image generation error for scene {i}: {str(e)}")
                    image_urls.append(self._get_placeholder_image())

        return image_urls

    async def _generate_voice(self, script_text: str, voice_settings: Dict[str, Any]) -> str:
        """Generate voice narration using AI service"""

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.ai_service_base}/api/v1/voice/synthesize",
                json={
                    "text": script_text,
                    "voice_id": voice_settings.get("voice_id", "alloy"),
                    "speed": voice_settings.get("speed", 1.0),
                    "language": voice_settings.get("language", "en"),
                    "emotion": voice_settings.get("emotion", "neutral"),
                },
            )

            if response.status_code != 200:
                raise Exception(f"Voice synthesis failed: {response.text}")

            result = response.json()
            return result["audio_url"]

    async def _generate_music(self, topic: str, mood: str) -> str:
        """Generate background music using AI service"""

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{self.ai_service_base}/api/v1/music/generate",
                json={
                    "prompt": f"Background music for {topic}",
                    "mood": mood,
                    "duration": 60,  # Will be adjusted during composition
                    "genre": "cinematic",
                    "instrumental": True,
                },
            )

            if response.status_code != 200:
                logger.warning(f"Music generation failed: {response.text}")
                return None

            result = response.json()
            return result["audio_url"]

    async def _update_status(
        self,
        generation_id: str,
        status: str,
        progress: int,
        current_step: str,
        additional_data: Dict[str, Any] = None,
    ):
        """Update generation status"""

        if generation_id not in self.generation_status:
            return

        self.generation_status[generation_id].update(
            {
                "status": status,
                "progress": progress,
                "current_step": current_step,
                "updated_at": datetime.utcnow(),
            }
        )

        if additional_data:
            self.generation_status[generation_id].update(additional_data)

        logger.info(
            "Generation status updated",
            generation_id=generation_id,
            status=status,
            progress=progress,
            step=current_step,
        )

    def _estimate_completion_time(self, request: VideoGenerationRequest) -> datetime:
        """Estimate completion time based on request parameters"""

        base_minutes = 5  # Base processing time

        # Adjust based on video length
        length_multipliers = {"short": 1.0, "medium": 1.5, "long": 2.0}

        multiplier = length_multipliers.get(request.video_length, 1.0)

        # Adjust based on quality
        if request.quality == "ultra":
            multiplier *= 1.5
        elif request.quality == "high":
            multiplier *= 1.2

        # Adjust based on music inclusion
        if request.include_music:
            multiplier *= 1.2

        estimated_minutes = int(base_minutes * multiplier)

        from datetime import timedelta

        return timedelta(minutes=estimated_minutes)

    def _get_placeholder_image(self) -> str:
        """Get placeholder image URL when generation fails"""
        return f"{self.storage_service_base}/static/placeholder.jpg"

    async def cleanup_generation(self, generation_id: str):
        """Clean up generation data"""

        if generation_id in self.generation_status:
            del self.generation_status[generation_id]

        # Clean up temporary files
        self.composer.cleanup()


# Global service instance
video_generation_service = VideoGenerationService()
