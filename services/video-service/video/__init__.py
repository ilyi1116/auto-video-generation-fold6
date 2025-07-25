"""
Video Processing Module

This module handles video composition, rendering, and media processing:
- Video composition from AI-generated components
- Multi-platform video rendering and optimization
- Media file management and storage
"""

from .composer import (
    VideoComposer,
    SceneComposition,
    CompositionRequest,
    CompositionResult,
    FinalRenderResult
)

__all__ = [
    "VideoComposer",
    "SceneComposition", 
    "CompositionRequest",
    "CompositionResult",
    "FinalRenderResult",
]