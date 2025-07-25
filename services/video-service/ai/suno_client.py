"""
Suno.ai Pro API Client

This client handles voice synthesis and music generation using Suno.ai Pro API.
Provides high-quality voice cloning and background music generation.
"""

import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class VoiceGenerationRequest(BaseModel):
    text: str
    voice_type: str = "default"
    music_genre: str = "ambient"
    language: str = "en"
    speed: float = 1.0
    pitch: float = 1.0

class VoiceGenerationResponse(BaseModel):
    audio_url: str
    music_url: Optional[str]
    duration: float
    generation_id: str
    created_at: datetime

class SunoAIClient:
    """Suno.ai Pro API Client for voice synthesis and music generation"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.suno.ai/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "AutoVideoGeneration/1.0"
            }
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout
            )
        return self.session
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Suno.ai API health status"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    return {"status": "healthy", "service": "suno.ai"}
                else:
                    return {"status": "unhealthy", "service": "suno.ai", "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"status": "unhealthy", "service": "suno.ai", "error": str(e)}
    
    async def generate_voice(
        self,
        text: str,
        voice_type: str = "default",
        music_genre: str = "ambient",
        language: str = "en"
    ) -> VoiceGenerationResponse:
        """Generate voice narration and background music"""
        
        try:
            session = await self._get_session()
            
            # Prepare request payload
            payload = {
                "text": text,
                "voice_settings": {
                    "voice_type": voice_type,
                    "language": language,
                    "speed": 1.0,
                    "pitch": 1.0,
                    "emotion": "neutral"
                },
                "music_settings": {
                    "genre": music_genre,
                    "mood": "background",
                    "volume": 0.3,  # Lower volume for background music
                    "fade_in": True,
                    "fade_out": True
                },
                "output_format": "mp3",
                "quality": "high"
            }
            
            logger.info(f"Generating voice with Suno.ai: {len(text)} characters")
            
            # Submit generation request
            async with session.post(f"{self.base_url}/generate", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Suno.ai API error: {response.status} - {error_text}")
                
                result = await response.json()
                generation_id = result["generation_id"]
            
            # Poll for completion
            audio_url, music_url, duration = await self._wait_for_completion(generation_id)
            
            return VoiceGenerationResponse(
                audio_url=audio_url,
                music_url=music_url,
                duration=duration,
                generation_id=generation_id,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Voice generation failed: {str(e)}")
            raise Exception(f"Failed to generate voice: {str(e)}")
    
    async def _wait_for_completion(self, generation_id: str, max_wait: int = 300) -> tuple[str, Optional[str], float]:
        """Wait for voice generation to complete"""
        
        session = await self._get_session()
        start_time = datetime.utcnow()
        
        while True:
            try:
                async with session.get(f"{self.base_url}/generate/{generation_id}") as response:
                    if response.status != 200:
                        raise Exception(f"Failed to check generation status: {response.status}")
                    
                    result = await response.json()
                    status = result["status"]
                    
                    if status == "completed":
                        return (
                            result["audio_url"],
                            result.get("music_url"),
                            result["duration"]
                        )
                    elif status == "failed":
                        raise Exception(f"Voice generation failed: {result.get('error', 'Unknown error')}")
                    elif status in ["queued", "processing"]:
                        # Check timeout
                        elapsed = (datetime.utcnow() - start_time).total_seconds()
                        if elapsed > max_wait:
                            raise Exception(f"Voice generation timeout after {max_wait} seconds")
                        
                        logger.info(f"Voice generation in progress: {status}")
                        await asyncio.sleep(5)  # Wait 5 seconds before next check
                    else:
                        raise Exception(f"Unknown generation status: {status}")
                        
            except Exception as e:
                logger.error(f"Error checking generation status: {str(e)}")
                raise
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voice types"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/voices") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get voices: {response.status}")
                
                result = await response.json()
                return result["voices"]
                
        except Exception as e:
            logger.error(f"Failed to get available voices: {str(e)}")
            return []
    
    async def get_available_music_genres(self) -> List[str]:
        """Get list of available music genres"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/music/genres") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get music genres: {response.status}")
                
                result = await response.json()
                return result["genres"]
                
        except Exception as e:
            logger.error(f"Failed to get available music genres: {str(e)}")
            return ["ambient", "cinematic", "upbeat", "calm", "dramatic"]
    
    async def clone_voice(self, voice_sample_url: str, text: str) -> VoiceGenerationResponse:
        """Clone a voice from a sample and generate speech"""
        
        try:
            session = await self._get_session()
            
            payload = {
                "voice_sample_url": voice_sample_url,
                "text": text,
                "clone_settings": {
                    "similarity_boost": True,
                    "stability": 0.75,
                    "clarity": 0.75
                },
                "output_format": "mp3",
                "quality": "high"
            }
            
            logger.info(f"Cloning voice and generating speech: {len(text)} characters")
            
            async with session.post(f"{self.base_url}/clone", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Voice cloning API error: {response.status} - {error_text}")
                
                result = await response.json()
                generation_id = result["generation_id"]
            
            # Wait for completion
            audio_url, _, duration = await self._wait_for_completion(generation_id)
            
            return VoiceGenerationResponse(
                audio_url=audio_url,
                music_url=None,
                duration=duration,
                generation_id=generation_id,
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Voice cloning failed: {str(e)}")
            raise Exception(f"Failed to clone voice: {str(e)}")
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()