"""
Stable Diffusion API Client

This client handles image generation using Stable Diffusion API for video
frames, thumbnails, and visual content creation with various styles and
aspect ratios.
"""

import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any, List, Tuple
from pydantic import BaseModel
from datetime import datetime
import base64
import io
from PIL import Image
import os

logger = logging.getLogger(__name__)


class ImageGenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    style: str = "modern"
    aspect_ratio: str = "16:9"
    quality: str = "high"
    steps: int = 50
    cfg_scale: float = 7.5
    seed: Optional[int] = None


class ImageGenerationResponse(BaseModel):
    url: str
    thumbnail_url: Optional[str]
    prompt: str
    style: str
    aspect_ratio: str
    generation_id: str
    seed: int
    created_at: datetime


class StableDiffusionClient:
    """Stable Diffusion API Client for image generation"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.stability.ai/v1"
        self.session: Optional[aiohttp.ClientSession] = None

        # Style presets for different video aesthetics
        self.style_presets = {
            "modern": {
                "style_preset": "photographic",
                "cfg_scale": 7.5,
                "negative_prompt": (
                    "blurry, low quality, distorted, ugly, bad anatomy"
                ),
            },
            "cinematic": {
                "style_preset": "cinematic",
                "cfg_scale": 8.0,
                "negative_prompt": (
                    "cartoon, anime, low quality, blurry, text, watermark"
                ),
            },
            "artistic": {
                "style_preset": "enhance",
                "cfg_scale": 7.0,
                "negative_prompt": (
                    "photorealistic, photograph, low quality, blurry"
                ),
            },
            "minimal": {
                "style_preset": "digital-art",
                "cfg_scale": 6.5,
                "negative_prompt": (
                    "cluttered, busy, complex, low quality, blurry"
                ),
            },
            "vibrant": {
                "style_preset": "fantasy-art",
                "cfg_scale": 8.5,
                "negative_prompt": (
                    "dull, muted, monochrome, low quality, blurry"
                ),
            },
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "AutoVideoGeneration/1.0",
            }
            timeout = aiohttp.ClientTimeout(total=180)  # 3 minutes timeout
            self.session = aiohttp.ClientSession(
                headers=headers, timeout=timeout
            )
        return self.session

    async def health_check(self) -> Dict[str, Any]:
        """Check Stable Diffusion API health status"""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/user/account"
            ) as response:
                if response.status == 200:
                    return {"status": "healthy", "service": "stable-diffusion"}
                else:
                    return {
                        "status": "unhealthy",
                        "service": "stable-diffusion",
                        "error": f"HTTP {response.status}",
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "stable-diffusion",
                "error": str(e),
            }

    async def generate_image(
        self,
        prompt: str,
        style: str = "modern",
        aspect_ratio: str = "16:9",
        negative_prompt: Optional[str] = None,
    ) -> ImageGenerationResponse:
        """Generate a single image based on prompt and style"""

        try:
            session = await self._get_session()

            # Get style configuration
            style_config = self.style_presets.get(
                style, self.style_presets["modern"]
            )

            # Convert aspect ratio to dimensions
            width, height = self._get_dimensions(aspect_ratio)

            # Enhance prompt with style keywords
            enhanced_prompt = self._enhance_prompt(prompt, style)

            # Combine negative prompts
            final_negative_prompt = style_config["negative_prompt"]
            if negative_prompt:
                final_negative_prompt += f", {negative_prompt}"

            payload = {
                "text_prompts": [
                    {"text": enhanced_prompt, "weight": 1.0},
                    {"text": final_negative_prompt, "weight": -1.0},
                ],
                "cfg_scale": style_config["cfg_scale"],
                "height": height,
                "width": width,
                "samples": 1,
                "steps": 50,
                "style_preset": style_config.get("style_preset"),
                "sampler": "K_DPM_2_ANCESTRAL",
            }

            logger.info(
                f"Generating image with Stable Diffusion: "
                f"{enhanced_prompt[:100]}..."
            )

            # Submit generation request
            url = (
                f"{self.base_url}/generation/"
                f"stable-diffusion-xl-1024-v1-0/text-to-image"
            )
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"Stable Diffusion API error: {response.status} - "
                        f"{error_text}"
                    )

                result = await response.json()

                if not result.get("artifacts"):
                    raise Exception("No image generated")

                # Process the first artifact
                artifact = result["artifacts"][0]
                image_data = base64.b64decode(artifact["base64"])

                # Save image and create thumbnail
                generation_id = f"sd_{datetime.utcnow().timestamp()}"
                image_url, thumbnail_url = await self._save_image(
                    image_data, generation_id
                )

                return ImageGenerationResponse(
                    url=image_url,
                    thumbnail_url=thumbnail_url,
                    prompt=enhanced_prompt,
                    style=style,
                    aspect_ratio=aspect_ratio,
                    generation_id=generation_id,
                    seed=artifact.get("seed", 0),
                    created_at=datetime.utcnow(),
                )

        except Exception as e:
            logger.error(f"Image generation failed: {str(e)}")
            raise Exception(f"Failed to generate image: {str(e)}")

    async def generate_image_batch(
        self,
        prompts: List[str],
        style: str = "modern",
        aspect_ratio: str = "16:9",
    ) -> List[ImageGenerationResponse]:
        """Generate multiple images in batch"""

        tasks = []
        for prompt in prompts:
            task = self.generate_image(prompt, style, aspect_ratio)
            tasks.append(task)

        logger.info(f"Generating {len(prompts)} images in batch")

        # Execute all tasks concurrently with some delay to avoid rate limits
        results = []
        for i in range(0, len(tasks), 3):  # Process 3 at a time
            batch = tasks[i:i + 3]
            batch_results = await asyncio.gather(
                *batch, return_exceptions=True
            )

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch image generation failed: {result}")
                    raise result
                results.append(result)

            # Rate limiting delay
            if i + 3 < len(tasks):
                await asyncio.sleep(2)

        return results

    def _get_dimensions(self, aspect_ratio: str) -> Tuple[int, int]:
        """Convert aspect ratio to pixel dimensions"""

        dimension_map = {
            "16:9": (1024, 576),  # YouTube/landscape
            "9:16": (576, 1024),  # TikTok/portrait
            "1:1": (1024, 1024),  # Instagram square
            "4:3": (1024, 768),  # Traditional
            "21:9": (1344, 576),  # Ultrawide
        }

        return dimension_map.get(aspect_ratio, (1024, 576))

    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """Enhance prompt with style-specific keywords"""

        style_keywords = {
            "modern": "modern, clean, professional, high-tech, sleek design",
            "cinematic": (
                "cinematic lighting, dramatic, film-like, movie scene, "
                "professional cinematography"
            ),
            "artistic": (
                "artistic, creative, expressive, painterly, "
                "artistic composition"
            ),
            "minimal": (
                "minimal, simple, clean lines, uncluttered, geometric"
            ),
            "vibrant": (
                "vibrant colors, dynamic, energetic, bold, striking"
            ),
        }

        keywords = style_keywords.get(style, "")
        if keywords:
            enhanced = (
                f"{prompt}, {keywords}, high quality, detailed, sharp focus"
            )
        else:
            enhanced = f"{prompt}, high quality, detailed, sharp focus"

        return enhanced

    async def _save_image(
        self, image_data: bytes, generation_id: str
    ) -> Tuple[str, str]:
        """Save image and create thumbnail, return URLs"""

        # Create directories if they don't exist
        os.makedirs("storage/images", exist_ok=True)
        os.makedirs("storage/thumbnails", exist_ok=True)

        # Save original image
        image_filename = f"{generation_id}.png"
        image_path = f"storage/images/{image_filename}"

        with open(image_path, "wb") as f:
            f.write(image_data)

        # Create thumbnail
        thumbnail_filename = f"{generation_id}_thumb.jpg"
        thumbnail_path = f"storage/thumbnails/{thumbnail_filename}"

        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # Create thumbnail (300x300 max, maintain aspect ratio)
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                img.convert("RGB").save(thumbnail_path, "JPEG", quality=85)
        except Exception as e:
            logger.error(f"Failed to create thumbnail: {e}")
            thumbnail_path = None

        # Return URLs (in production, these would be CDN URLs)
        base_url = os.getenv("MEDIA_BASE_URL", "http://localhost:8003")
        image_url = f"{base_url}/media/images/{image_filename}"
        thumbnail_url = (
            f"{base_url}/media/thumbnails/{thumbnail_filename}"
            if thumbnail_path
            else None
        )

        return image_url, thumbnail_url

    async def upscale_image(
        self, image_url: str, upscale_factor: int = 2
    ) -> ImageGenerationResponse:
        """Upscale an existing image using Stable Diffusion"""

        try:
            session = await self._get_session()

            # Download the original image
            async with session.get(image_url) as response:
                if response.status != 200:
                    raise Exception(
                        f"Failed to download image: {response.status}"
                    )

                image_data = await response.read()
                image_b64 = base64.b64encode(image_data).decode()

            payload = {
                "image": image_b64,
                "width": 2048 if upscale_factor >= 2 else 1024,
                "height": 2048 if upscale_factor >= 2 else 1024,
            }

            url = (
                f"{self.base_url}/generation/esrgan-v1-x2plus/"
                f"image-to-image/upscale"
            )
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(
                        f"Upscale API error: {response.status} - {error_text}"
                    )

                result = await response.json()
                artifact = result["artifacts"][0]
                upscaled_data = base64.b64decode(artifact["base64"])

                # Save upscaled image
                generation_id = f"upscale_{datetime.utcnow().timestamp()}"
                upscaled_url, thumbnail_url = await self._save_image(
                    upscaled_data, generation_id
                )

                return ImageGenerationResponse(
                    url=upscaled_url,
                    thumbnail_url=thumbnail_url,
                    prompt="upscaled_image",
                    style="upscaled",
                    aspect_ratio="original",
                    generation_id=generation_id,
                    seed=0,
                    created_at=datetime.utcnow(),
                )

        except Exception as e:
            logger.error(f"Image upscaling failed: {str(e)}")
            raise Exception(f"Failed to upscale image: {str(e)}")

    async def get_generation_styles(self) -> List[Dict[str, Any]]:
        """Get available generation styles"""
        return [
            {
                "name": "modern",
                "description": "Clean, professional, high-tech aesthetic",
                "suitable_for": ["corporate", "tech", "business"],
            },
            {
                "name": "cinematic",
                "description": "Film-like with dramatic lighting",
                "suitable_for": ["storytelling", "dramatic", "movie-style"],
            },
            {
                "name": "artistic",
                "description": "Creative and expressive visual style",
                "suitable_for": ["creative", "artistic", "expressive"],
            },
            {
                "name": "minimal",
                "description": "Simple, clean, uncluttered design",
                "suitable_for": ["minimal", "clean", "simple"],
            },
            {
                "name": "vibrant",
                "description": "Bold colors and dynamic composition",
                "suitable_for": ["energetic", "colorful", "dynamic"],
            },
        ]

    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
