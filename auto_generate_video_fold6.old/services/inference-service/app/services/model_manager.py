import asyncio
import time
from typing import Any, Dict

import numpy as np
import structlog
import torch

from ..config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class MockVoiceModel:
    """Mock voice synthesis model for demonstration"""

    def __init__(self, model_id: int, model_path: str, config: Dict[str, Any]):
        self.model_id = model_id
        self.model_path = model_path
        self.config = config
        self.loaded_at = time.time()

    async def synthesize(self, text: str, **kwargs) -> bytes:
        """Synthesize speech from text - mock implementation"""
        # Simulate processing time
        processing_time = len(text) * 0.01  # 10ms per character
        await asyncio.sleep(min(processing_time, 2.0))  # Cap at 2 seconds

        # Generate mock audio data (simple sine wave)
        sample_rate = 22050
        duration = max(len(text) * 0.1, 1.0)  # Minimum 1 second
        t = np.linspace(0, duration, int(sample_rate * duration))

        # Create a simple sine wave with varying frequency
        frequency = 440 + (
            hash(text) % 200
        )  # Base frequency with text-based variation
        audio = np.sin(2 * np.pi * frequency * t) * 0.3

        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)

        # Convert to WAV format bytes (simplified)
        import io
        import wave

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())

        return buffer.getvalue()


class ModelManager:
    """Manages loading and caching of voice models"""

    def __init__(self):
        self.model_cache: Dict[int, MockVoiceModel] = {}
        self.cache_timestamps: Dict[int, float] = {}
        self.loading_locks: Dict[int, asyncio.Lock] = {}

    async def initialize(self):
        """Initialize the model manager"""
        logger.info(
            "Initializing model manager",
            max_cache_size=settings.max_model_cache_size,
        )

    async def get_model(
        self, model_id: int, model_config: Dict[str, Any]
    ) -> MockVoiceModel:
        """Get a model from cache or load it"""

        # Check if model is already cached and not expired
        if model_id in self.model_cache:
            cache_age = time.time() - self.cache_timestamps[model_id]
            if cache_age < settings.model_cache_ttl:
                logger.debug(
                    "Model cache hit", model_id=model_id, cache_age=cache_age
                )
                return self.model_cache[model_id]
            else:
                logger.debug(
                    "Model cache expired",
                    model_id=model_id,
                    cache_age=cache_age,
                )
                await self._unload_model(model_id)

        # Get or create loading lock for this model
        if model_id not in self.loading_locks:
            self.loading_locks[model_id] = asyncio.Lock()

        async with self.loading_locks[model_id]:
            # Double-check after acquiring lock
            if model_id in self.model_cache:
                return self.model_cache[model_id]

            # Load the model
            logger.info("Loading voice model", model_id=model_id)
            model = await self._load_model(model_id, model_config)

            # Manage cache size
            await self._manage_cache_size()

            # Cache the model
            self.model_cache[model_id] = model
            self.cache_timestamps[model_id] = time.time()

            logger.info(
                "Model loaded successfully",
                model_id=model_id,
                cache_size=len(self.model_cache),
            )

            return model

    async def _load_model(
        self, model_id: int, model_config: Dict[str, Any]
    ) -> MockVoiceModel:
        """Load a model from storage"""
        try:
            model_path = model_config.get(
                "model_path", f"models/model_{model_id}"
            )

            # Simulate model loading time
            await asyncio.sleep(0.5)

            # Create mock model
            model = MockVoiceModel(model_id, model_path, model_config)

            return model

        except Exception as e:
            logger.error(
                "Failed to load model", model_id=model_id, error=str(e)
            )
            raise RuntimeError(f"Failed to load model {model_id}: {str(e)}")

    async def _unload_model(self, model_id: int):
        """Unload a model from cache"""
        if model_id in self.model_cache:
            logger.debug("Unloading model from cache", model_id=model_id)
            del self.model_cache[model_id]
            del self.cache_timestamps[model_id]

            # Clean up GPU memory if using CUDA
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    async def _manage_cache_size(self):
        """Ensure cache doesn't exceed maximum size"""
        while len(self.model_cache) >= settings.max_model_cache_size:
            # Find oldest model to evict
            oldest_model_id = min(
                self.cache_timestamps.keys(),
                key=lambda k: self.cache_timestamps[k],
            )
            await self._unload_model(oldest_model_id)
            logger.debug("Evicted model from cache", model_id=oldest_model_id)

    async def preload_model(self, model_id: int, model_config: Dict[str, Any]):
        """Preload a model into cache"""
        try:
            await self.get_model(model_id, model_config)
            logger.info("Model preloaded", model_id=model_id)
        except Exception as e:
            logger.error(
                "Failed to preload model", model_id=model_id, error=str(e)
            )

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cached_models": len(self.model_cache),
            "max_cache_size": settings.max_model_cache_size,
            "cache_ttl": settings.model_cache_ttl,
            "model_ids": list(self.model_cache.keys()),
            "oldest_cache_age": (
                time.time() - min(self.cache_timestamps.values())
                if self.cache_timestamps
                else 0
            ),
        }


# Global model manager instance
model_manager = ModelManager()
