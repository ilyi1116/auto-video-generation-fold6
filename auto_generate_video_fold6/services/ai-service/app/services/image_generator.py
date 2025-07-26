import asyncio
import time
import uuid
import io
import base64
from typing import Dict, List, Optional, Any
from PIL import Image
import httpx
import structlog
from ..config import settings

logger = structlog.get_logger()


class ImageGenerator:
    """AI-powered image generation service for video backgrounds and assets"""
    
    def __init__(self):
        self.stability_client = None
        self.openai_client = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize image generation services"""
        try:
            logger.info("Initializing Image Generator")
            
            # Initialize HTTP client for API calls
            self.http_client = httpx.AsyncClient(timeout=60.0)
            
            # Check API keys
            if settings.stability_api_key:
                logger.info("Stability AI client configured")
            
            if settings.openai_api_key:
                logger.info("OpenAI DALL-E client configured")
            
            self.initialized = True
            logger.info("Image Generator initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Image Generator", error=str(e))
            raise
    
    async def shutdown(self):
        """Shutdown image generation services"""
        if hasattr(self, 'http_client'):
            await self.http_client.aclose()
        self.initialized = False
        logger.info("Image Generator shutdown complete")
    
    def is_healthy(self) -> bool:
        """Check if image generation service is healthy"""
        return self.initialized and (settings.stability_api_key or settings.openai_api_key)
    
    async def generate_image(
        self,
        prompt: str,
        style: str = "modern",
        aspect_ratio: str = "9:16",
        resolution: str = "1080p",
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 50
    ) -> Dict[str, Any]:
        """Generate image based on text prompt"""
        try:
            start_time = time.time()
            image_id = str(uuid.uuid4())
            
            logger.info(
                "Generating image",
                image_id=image_id,
                prompt=prompt[:100],
                style=style,
                aspect_ratio=aspect_ratio
            )
            
            # Preprocess prompt with style
            enhanced_prompt = self._enhance_prompt(prompt, style)
            
            # Generate image using available service
            image_data = await self._generate_with_stability(
                prompt=enhanced_prompt,
                negative_prompt=negative_prompt or self._get_default_negative_prompt(),
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                seed=seed,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps
            )
            
            # Save image and get URL
            image_url = await self._save_image(image_data, image_id, "generated")
            
            generation_time = time.time() - start_time
            
            result = {
                "image_id": image_id,
                "image_url": image_url,
                "prompt": enhanced_prompt,
                "original_prompt": prompt,
                "style": style,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "generation_time": round(generation_time, 2),
                "status": "completed",
                "metadata": {
                    "negative_prompt": negative_prompt,
                    "seed": seed,
                    "guidance_scale": guidance_scale,
                    "num_inference_steps": num_inference_steps
                }
            }
            
            logger.info(
                "Image generated successfully",
                image_id=image_id,
                generation_time=generation_time,
                size_kb=len(image_data) // 1024
            )
            
            return result
            
        except Exception as e:
            logger.error("Image generation failed", prompt=prompt[:50], error=str(e))
            raise
    
    async def generate_variations(
        self,
        base_image_url: str,
        variation_prompt: Optional[str] = None,
        strength: float = 0.7,
        num_variations: int = 3
    ) -> Dict[str, Any]:
        """Generate variations of an existing image"""
        try:
            logger.info(
                "Generating image variations",
                base_image=base_image_url,
                num_variations=num_variations
            )
            
            # Download base image
            base_image = await self._download_image(base_image_url)
            
            variations = []
            for i in range(num_variations):
                variation_id = str(uuid.uuid4())
                
                # Generate variation
                variation_data = await self._generate_variation(
                    base_image=base_image,
                    prompt=variation_prompt,
                    strength=strength,
                    seed=i * 1000  # Different seed for each variation
                )
                
                # Save variation
                variation_url = await self._save_image(variation_data, variation_id, "variation")
                
                variations.append({
                    "variation_id": variation_id,
                    "image_url": variation_url,
                    "strength": strength,
                    "seed": i * 1000
                })
            
            result = {
                "base_image_url": base_image_url,
                "variation_prompt": variation_prompt,
                "variations": variations,
                "num_generated": len(variations),
                "parameters": {
                    "strength": strength,
                    "num_variations": num_variations
                }
            }
            
            logger.info("Image variations generated successfully", count=len(variations))
            return result
            
        except Exception as e:
            logger.error("Image variation generation failed", error=str(e))
            raise
    
    async def upscale_image(
        self,
        image_url: str,
        scale_factor: int = 2
    ) -> Dict[str, Any]:
        """Upscale image resolution using AI"""
        try:
            logger.info("Upscaling image", image_url=image_url, scale_factor=scale_factor)
            
            # Download original image
            original_image = await self._download_image(image_url)
            
            # Get original dimensions
            with Image.open(io.BytesIO(original_image)) as img:
                original_width, original_height = img.size
            
            new_width = original_width * scale_factor
            new_height = original_height * scale_factor
            
            # Upscale using Real-ESRGAN or similar service
            upscaled_data = await self._upscale_with_ai(original_image, scale_factor)
            
            # Save upscaled image
            upscale_id = str(uuid.uuid4())
            upscaled_url = await self._save_image(upscaled_data, upscale_id, "upscaled")
            
            result = {
                "upscale_id": upscale_id,
                "original_url": image_url,
                "upscaled_url": upscaled_url,
                "scale_factor": scale_factor,
                "original_dimensions": [original_width, original_height],
                "upscaled_dimensions": [new_width, new_height],
                "file_size_increase": round(len(upscaled_data) / len(original_image), 2)
            }
            
            logger.info("Image upscaling completed", scale_factor=scale_factor)
            return result
            
        except Exception as e:
            logger.error("Image upscaling failed", error=str(e))
            raise
    
    async def enhance_image(
        self,
        image_url: str,
        enhancement_type: str = "general"
    ) -> Dict[str, Any]:
        """Enhance image quality using AI"""
        try:
            logger.info("Enhancing image", image_url=image_url, type=enhancement_type)
            
            # Download original image
            original_image = await self._download_image(image_url)
            
            # Enhance based on type
            enhanced_data = await self._enhance_with_ai(original_image, enhancement_type)
            
            # Save enhanced image
            enhance_id = str(uuid.uuid4())
            enhanced_url = await self._save_image(enhanced_data, enhance_id, "enhanced")
            
            result = {
                "enhance_id": enhance_id,
                "original_url": image_url,
                "enhanced_url": enhanced_url,
                "enhancement_type": enhancement_type,
                "quality_improvement": self._calculate_quality_improvement(
                    original_image, enhanced_data
                )
            }
            
            logger.info("Image enhancement completed", type=enhancement_type)
            return result
            
        except Exception as e:
            logger.error("Image enhancement failed", error=str(e))
            raise
    
    async def _generate_with_stability(
        self,
        prompt: str,
        negative_prompt: str,
        aspect_ratio: str,
        resolution: str,
        seed: Optional[int],
        guidance_scale: float,
        num_inference_steps: int
    ) -> bytes:
        """Generate image using Stability AI"""
        if not settings.stability_api_key:
            raise Exception("Stability AI API key not configured")
        
        # Map aspect ratio to dimensions
        width, height = self._get_dimensions(aspect_ratio, resolution)
        
        # Prepare request
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        
        headers = {
            "Authorization": f"Bearer {settings.stability_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        data = {
            "text_prompts": [
                {"text": prompt, "weight": 1.0},
                {"text": negative_prompt, "weight": -1.0}
            ],
            "cfg_scale": guidance_scale,
            "height": height,
            "width": width,
            "steps": num_inference_steps,
            "samples": 1,
            "style_preset": self._get_stability_style_preset("modern")
        }
        
        if seed:
            data["seed"] = seed
        
        # Make request
        response = await self.http_client.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        # Extract image data
        result = response.json()
        image_b64 = result["artifacts"][0]["base64"]
        return base64.b64decode(image_b64)
    
    async def _generate_variation(
        self,
        base_image: bytes,
        prompt: Optional[str],
        strength: float,
        seed: int
    ) -> bytes:
        """Generate image variation using image-to-image"""
        if not settings.stability_api_key:
            raise Exception("Stability AI API key not configured")
        
        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/image-to-image"
        
        headers = {
            "Authorization": f"Bearer {settings.stability_api_key}",
            "Accept": "application/json"
        }
        
        # Prepare multipart form data
        files = {
            "init_image": base_image
        }
        
        data = {
            "init_image_mode": "IMAGE_STRENGTH",
            "image_strength": 1.0 - strength,
            "cfg_scale": 7,
            "samples": 1,
            "steps": 30,
            "seed": seed
        }
        
        if prompt:
            data["text_prompts[0][text]"] = prompt
            data["text_prompts[0][weight]"] = 1.0
        
        # Make request
        response = await self.http_client.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        
        # Extract image data
        result = response.json()
        image_b64 = result["artifacts"][0]["base64"]
        return base64.b64decode(image_b64)
    
    async def _upscale_with_ai(self, image_data: bytes, scale_factor: int) -> bytes:
        """Upscale image using AI service (placeholder implementation)"""
        # This would integrate with Real-ESRGAN or similar service
        # For now, use simple PIL upscaling as fallback
        with Image.open(io.BytesIO(image_data)) as img:
            new_size = (img.width * scale_factor, img.height * scale_factor)
            upscaled = img.resize(new_size, Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            upscaled.save(output, format='JPEG', quality=95)
            return output.getvalue()
    
    async def _enhance_with_ai(self, image_data: bytes, enhancement_type: str) -> bytes:
        """Enhance image using AI service (placeholder implementation)"""
        # This would integrate with specialized enhancement services
        # For now, apply basic PIL enhancements
        with Image.open(io.BytesIO(image_data)) as img:
            # Apply basic enhancements based on type
            if enhancement_type == "face":
                # Face-specific enhancements
                enhanced = img
            elif enhancement_type == "artifact_removal":
                # Artifact removal
                enhanced = img
            else:
                # General enhancement
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Sharpness(img)
                enhanced = enhancer.enhance(1.2)
                
                enhancer = ImageEnhance.Contrast(enhanced)
                enhanced = enhancer.enhance(1.1)
            
            output = io.BytesIO()
            enhanced.save(output, format='JPEG', quality=95)
            return output.getvalue()
    
    async def _download_image(self, image_url: str) -> bytes:
        """Download image from URL"""
        response = await self.http_client.get(image_url)
        response.raise_for_status()
        return response.content
    
    async def _save_image(self, image_data: bytes, image_id: str, category: str) -> str:
        """Save image to storage and return URL"""
        # This would integrate with your storage service (S3, MinIO, etc.)
        # For now, return a placeholder URL
        filename = f"{category}_{image_id}.jpg"
        storage_path = f"{settings.temp_storage_path}/{filename}"
        
        # Save to local storage (in production, use cloud storage)
        import os
        os.makedirs(settings.temp_storage_path, exist_ok=True)
        
        with open(storage_path, 'wb') as f:
            f.write(image_data)
        
        # Return URL (in production, this would be your CDN URL)
        return f"/storage/images/{filename}"
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """Enhance prompt with style-specific keywords"""
        style_enhancements = {
            "modern": "clean, minimalist, contemporary, sleek design, high quality",
            "vintage": "retro, nostalgic, classic, aged, warm tones",
            "minimalist": "simple, clean lines, negative space, uncluttered",
            "artistic": "creative, expressive, painterly, artistic interpretation",
            "photorealistic": "photorealistic, highly detailed, professional photography",
            "cartoon": "cartoon style, animated, colorful, stylized",
            "anime": "anime style, manga, japanese animation",
            "cyberpunk": "cyberpunk, neon, futuristic, dystopian, high tech"
        }
        
        enhancement = style_enhancements.get(style, "high quality, detailed")
        return f"{prompt}, {enhancement}"
    
    def _get_default_negative_prompt(self) -> str:
        """Get default negative prompt to avoid unwanted elements"""
        return ("blurry, low quality, distorted, deformed, duplicate, watermark, "
                "signature, text, worst quality, low res, jpeg artifacts, "
                "mutation, extra limbs, bad anatomy")
    
    def _get_dimensions(self, aspect_ratio: str, resolution: str) -> tuple:
        """Get width and height from aspect ratio and resolution"""
        resolution_map = {
            "720p": 720,
            "1080p": 1080,
            "4k": 2160
        }
        
        base_height = resolution_map.get(resolution, 1080)
        
        ratio_map = {
            "9:16": (9, 16),  # Vertical (TikTok, Instagram Stories)
            "16:9": (16, 9),  # Horizontal (YouTube)
            "1:1": (1, 1),    # Square (Instagram)
            "4:3": (4, 3)     # Traditional
        }
        
        width_ratio, height_ratio = ratio_map.get(aspect_ratio, (9, 16))
        
        # Calculate width based on aspect ratio
        width = int(base_height * width_ratio / height_ratio)
        
        # Ensure dimensions are multiples of 64 (required by some models)
        width = (width // 64) * 64
        height = (base_height // 64) * 64
        
        return width, height
    
    def _get_stability_style_preset(self, style: str) -> Optional[str]:
        """Map our style to Stability AI style presets"""
        style_map = {
            "modern": "enhance",
            "vintage": "analog-film",
            "minimalist": None,
            "artistic": "artistic",
            "photorealistic": "photographic",
            "cartoon": "comic-book",
            "anime": "anime",
            "cyberpunk": "neon-punk"
        }
        return style_map.get(style)
    
    def _calculate_quality_improvement(self, original: bytes, enhanced: bytes) -> float:
        """Calculate quality improvement score (placeholder)"""
        # This would use actual image quality metrics
        # For now, return a placeholder score
        return round((len(enhanced) / len(original)) * 1.2, 2)