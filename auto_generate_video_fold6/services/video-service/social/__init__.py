"""
Social Media Integration Module

This module handles integration with social media platforms:
- TikTok, YouTube, Instagram API clients
- Automated video publishing and management
- Social media analytics and statistics
"""

from .platforms import (
    InstagramClient,
    PublishRequest,
    PublishResult,
    SocialMediaManager,
    SocialPlatform,
    TikTokClient,
    YouTubeClient,
)

__all__ = [
    "SocialMediaManager",
    "PublishRequest",
    "PublishResult",
    "TikTokClient",
    "YouTubeClient",
    "InstagramClient",
    "SocialPlatform",
]
