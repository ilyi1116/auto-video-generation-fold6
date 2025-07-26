import asyncio
from typing import Dict, Any, Optional
import structlog
from ..config import settings

logger = structlog.get_logger()


class AIManager:
    """Central manager for all AI service integrations"""
    
    def __init__(self):
        self.text_generator = None
        self.image_generator = None
        self.audio_processor = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize all AI service components"""
        try:
            logger.info("Initializing AI Manager")
            
            # Import and initialize services
            from .text_generator import TextGenerator
            from .image_generator import ImageGenerator
            from .audio_processor import AudioProcessor
            
            self.text_generator = TextGenerator()
            self.image_generator = ImageGenerator()
            self.audio_processor = AudioProcessor()
            
            # Initialize each service
            await asyncio.gather(
                self.text_generator.initialize(),
                self.image_generator.initialize(),
                self.audio_processor.initialize(),
                return_exceptions=True
            )
            
            self.initialized = True
            logger.info("AI Manager initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize AI Manager", error=str(e))
            raise
    
    async def shutdown(self):
        """Shutdown all AI service components"""
        try:
            logger.info("Shutting down AI Manager")
            
            if self.text_generator:
                await self.text_generator.shutdown()
            if self.image_generator:
                await self.image_generator.shutdown()
            if self.audio_processor:
                await self.audio_processor.shutdown()
            
            self.initialized = False
            logger.info("AI Manager shutdown complete")
            
        except Exception as e:
            logger.error("Error during AI Manager shutdown", error=str(e))
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all AI services"""
        return {
            "initialized": self.initialized,
            "services": {
                "text_generator": self.text_generator.is_healthy() if self.text_generator else False,
                "image_generator": self.image_generator.is_healthy() if self.image_generator else False,
                "audio_processor": self.audio_processor.is_healthy() if self.audio_processor else False,
            },
            "api_keys_configured": {
                "openai": bool(settings.openai_api_key),
                "google": bool(settings.google_api_key),
                "stability": bool(settings.stability_api_key),
                "anthropic": bool(settings.anthropic_api_key),
            }
        }