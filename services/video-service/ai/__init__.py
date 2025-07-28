"""
AI Services Module

This module provides AI service clients for video generation:
- Suno.ai Pro for voice synthesis and music generation
- Google Gemini Pro for script generation and content creation
- Stable Diffusion for image generation and visual content
"""

from .suno_client import SunoAIClient, VoiceGenerationRequest, VoiceGenerationResponse
from .gemini_client import GeminiClient, ScriptScene, ScriptGenerationResponse
from .stable_diffusion_client import (
    StableDiffusionClient,
    ImageGenerationRequest,
    ImageGenerationResponse,
)

__all__ = [
    # Suno.ai Client
    "SunoAIClient",
    "VoiceGenerationRequest",
    "VoiceGenerationResponse",
    # Gemini Client
    "GeminiClient",
    "ScriptScene",
    "ScriptGenerationResponse",
    # Stable Diffusion Client
    "StableDiffusionClient",
    "ImageGenerationRequest",
    "ImageGenerationResponse",
]
