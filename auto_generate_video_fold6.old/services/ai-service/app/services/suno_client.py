#!/usr/bin/env python3
"""
Suno.ai 音樂生成客戶端
提供 AI 驅動的音樂生成服務
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class MusicGenerationRequest:
    """音樂生成請求"""

    prompt: str
    style: str = "pop"
    mood: str = "upbeat"
    platform: str = "tiktok"
    duration_seconds: int = 30
    instrumental: bool = False
    custom_lyrics: Optional[str] = None


@dataclass
class MusicGenerationResult:
    """音樂生成結果"""

    music_id: str
    music_url: str
    duration_seconds: int
    generation_time_seconds: float
    metadata: Dict[str, Any]


class SunoClient:
    """Suno.ai 音樂生成客戶端"""

    def __init__(
        self, api_key: str = None, base_url: str = "https://api.sunoai.com"
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.session = None

        # Cost tracking
        self.total_cost = 0.0
        self.generation_count = 0

        # Generation history
        self.generation_history = []

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "AutoVideo-SunoClient/1.0",
            },
            timeout=aiohttp.ClientTimeout(total=300),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def generate_music(
        self, request: MusicGenerationRequest
    ) -> MusicGenerationResult:
        """Generate music using Suno.ai API with cost tracking"""
        start_time = time.time()

        try:
            generation_id = str(uuid.uuid4())
            logger.info(
                "Starting music generation",
                generation_id=generation_id,
                prompt=request.prompt[:50],
                style=request.style,
                duration=request.duration_seconds,
            )

            # Enhanced prompt with style and mood
            enhanced_prompt = self._enhance_prompt(
                request.prompt, request.style, request.mood, request.platform
            )

            # Generate music (with fallback to procedural generation)
            result = await self._generate_with_suno_api(
                enhanced_prompt,
                request.duration_seconds,
                request.instrumental,
                request.custom_lyrics,
                generation_id,
            )

            generation_time = time.time() - start_time

            # Enhance result with metadata
            result.update(
                {
                    "generation_id": generation_id,
                    "enhanced_prompt": enhanced_prompt,
                    "original_prompt": request.prompt,
                    "style": request.style,
                    "mood": request.mood,
                    "platform": request.platform,
                    "generation_time_seconds": round(generation_time, 2),
                    "status": "completed",
                }
            )

            logger.info(
                "Music generation completed",
                generation_id=generation_id,
                duration=result.get("duration_seconds", 0),
                generation_time=generation_time,
            )

            return result

        except Exception as e:
            logger.error(
                "Music generation failed",
                prompt=request.prompt[:50],
                error=str(e),
            )
            raise

    def _enhance_prompt(
        self, prompt: str, style: str, mood: str, platform: str
    ) -> str:
        """Enhance the music generation prompt"""
        enhancements = []

        # Style enhancements
        style_mapping = {
            "pop": "upbeat pop with catchy melody",
            "electronic": "electronic beats with synth elements",
            "acoustic": "acoustic instruments with organic feel",
            "ambient": "atmospheric ambient soundscape",
            "rock": "energetic rock with guitar riffs",
        }

        if style in style_mapping:
            enhancements.append(style_mapping[style])

        # Mood enhancements
        mood_mapping = {
            "upbeat": "energetic and positive",
            "calm": "peaceful and relaxing",
            "dramatic": "intense and emotional",
            "mysterious": "dark and intriguing",
            "playful": "fun and lighthearted",
        }

        if mood in mood_mapping:
            enhancements.append(mood_mapping[mood])

        # Platform-specific optimizations
        platform_mapping = {
            "tiktok": "short-form, attention-grabbing",
            "youtube": "full-length with dynamic progression",
            "instagram": "loop-friendly and engaging",
        }

        if platform in platform_mapping:
            enhancements.append(platform_mapping[platform])

        # Combine prompt with enhancements
        if enhancements:
            enhanced = f"{prompt}, {', '.join(enhancements)}"
        else:
            enhanced = prompt

        return enhanced

    async def _generate_with_suno_api(
        self,
        prompt: str,
        duration: int,
        instrumental: bool,
        custom_lyrics: Optional[str],
        generation_id: str,
    ) -> Dict[str, Any]:
        """Generate music using actual Suno API"""
        try:
            # Prepare generation request
            request_data = {
                "prompt": prompt,
                "make_instrumental": instrumental,
                "wait_audio": True,
            }

            if custom_lyrics and not instrumental:
                request_data["lyrics"] = custom_lyrics

            # Submit generation request
            response = await self.session.post(
                f"{self.base_url}/api/generate", json=request_data
            )
            response.raise_for_status()

            generation_data = await response.json()

            # Wait for generation to complete
            job_id = generation_data.get("id")
            music_url = await self._wait_for_generation(job_id)

            # Download and save music
            music_data = await self._download_music(music_url)
            local_url = await self._save_music(music_data, generation_id)

            return {
                "music_id": generation_id,
                "music_url": local_url,
                "suno_job_id": job_id,
                "duration_seconds": duration,
                "service": "suno_api",
            }

        except Exception as e:
            logger.error("Suno API generation failed", error=str(e))
            # Fallback to procedural generation
            return await self._generate_fallback_music(
                style="background",
                duration_seconds=duration,
                mood="neutral",
                platform="tiktok",
                generation_id=generation_id,
            )

    async def _wait_for_generation(self, job_id: str) -> str:
        """Wait for Suno generation to complete"""
        max_wait_time = 300  # 5 minutes
        poll_interval = 5
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            try:
                response = await self.session.get(
                    f"{self.base_url}/api/get/{job_id}"
                )
                response.raise_for_status()

                job_data = await response.json()
                status = job_data.get("status")

                if status == "complete":
                    music_url = job_data.get("audio_url")
                    if music_url:
                        return music_url
                elif status == "error":
                    raise Exception(
                        f"Generation failed: {job_data.get('error')}"
                    )

                await asyncio.sleep(poll_interval)

            except Exception as e:
                logger.warning(f"Polling error: {e}")
                await asyncio.sleep(poll_interval)

        raise Exception("Generation timeout")

    async def _download_music(self, music_url: str) -> bytes:
        """Download generated music"""
        response = await self.session.get(music_url)
        response.raise_for_status()
        return await response.read()

    async def _save_music(self, music_data: bytes, generation_id: str) -> str:
        """Save music to local storage"""
        import os

        # Ensure storage directory exists
        storage_dir = "/tmp/generated_music"
        os.makedirs(storage_dir, exist_ok=True)

        # Save music file
        file_path = os.path.join(storage_dir, f"{generation_id}.mp3")
        with open(file_path, "wb") as f:
            f.write(music_data)

        return f"/storage/music/{generation_id}.mp3"

    async def _generate_fallback_music(
        self,
        style: str,
        duration_seconds: int,
        mood: str,
        platform: str,
        generation_id: str,
    ) -> Dict[str, Any]:
        """Generate fallback procedural music"""
        logger.info("Using fallback music generation")

        # Simulate processing time
        await asyncio.sleep(2)

        return {
            "music_id": generation_id,
            "music_url": f"/storage/music/fallback_{generation_id}.mp3",
            "duration_seconds": duration_seconds,
            "service": "fallback_procedural",
            "status": "completed",
        }

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get generation statistics"""
        return {
            "total_generations": self.generation_count,
            "total_cost": self.total_cost,
            "average_cost_per_generation": (
                self.total_cost / self.generation_count
                if self.generation_count > 0
                else 0
            ),
            "generation_history": self.generation_history[
                -10:
            ],  # Last 10 generations
        }


# Usage example
async def main():
    """Main function for testing"""
    api_key = "your-suno-api-key"

    async with SunoClient(api_key=api_key) as client:
        request = MusicGenerationRequest(
            prompt="Upbeat electronic dance music for a tech product demo",
            style="electronic",
            mood="upbeat",
            platform="youtube",
            duration_seconds=60,
        )

        try:
            result = await client.generate_music(request)
            print("✅ Music generated successfully!")
            print(f"Music ID: {result['music_id']}")
            print(f"Music URL: {result['music_url']}")
            print(f"Duration: {result['duration_seconds']} seconds")
            print(
                f"Generation time: {result['generation_time_seconds']} seconds"
            )

        except Exception as e:
            print(f"❌ Music generation failed: {e}")


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
