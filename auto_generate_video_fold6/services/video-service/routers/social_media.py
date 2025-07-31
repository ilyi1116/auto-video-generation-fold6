"""
Social Media Integration API Routes

Provides endpoints for publishing videos to various social media platforms,
managing platform connections, and retrieving publication statistics.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..social.platforms import (
    PublishRequest,
    SocialMediaManager,
)

router = APIRouter()
logger = structlog.get_logger()

# Global social media manager
social_manager = SocialMediaManager()


class SocialPublishRequest(BaseModel):
    """API request for social media publishing"""

    video_url: str
    platforms: List[str]
    title: str
    description: Optional[str] = None
    tags: List[str] = []
    privacy: str = "public"
    scheduled_time: Optional[datetime] = None
    platform_specific: Dict[str, Dict[str, Any]] = {}


class SocialPublishResponse(BaseModel):
    """API response for social media publishing"""

    success: bool
    message: str
    results: List[Dict[str, Any]]
    total_platforms: int
    successful_publishes: int
    failed_publishes: int


class PlatformStatsResponse(BaseModel):
    """API response for platform statistics"""

    platform: str
    platform_id: str
    stats: Dict[str, Any]
    retrieved_at: datetime


class PlatformConnectionResponse(BaseModel):
    """API response for platform connection status"""

    platform: str
    connected: bool
    last_check: datetime
    error_message: Optional[str] = None


@router.post("/publish", response_model=SocialPublishResponse)
async def publish_to_social_media(
    request: SocialPublishRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Publish video to selected social media platforms"""
    try:
        logger.info(
            "Social media publishing requested",
            user_id=current_user.get("id"),
            platforms=request.platforms,
            title=request.title,
        )

        # Validate platforms
        available_platforms = social_manager.get_available_platforms()
        invalid_platforms = [
            p for p in request.platforms if p not in available_platforms
        ]

        if invalid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid platforms: {invalid_platforms}. \
                    Available: {available_platforms}",
            )

        # Create publish request
        publish_request = PublishRequest(
            video_url=request.video_url,
            title=request.title,
            description=request.description,
            tags=request.tags,
            privacy=request.privacy,
            scheduled_time=request.scheduled_time,
            custom_metadata=request.platform_specific,
        )

        # Publish to platforms
        if request.scheduled_time:
            # Schedule for later publishing
            background_tasks.add_task(
                _scheduled_publish,
                publish_request,
                request.platforms,
                current_user.get("id"),
            )

            return SocialPublishResponse(
                success=True,
                message=f"Publishing scheduled for {request.scheduled_time}",
                results=[],
                total_platforms=len(request.platforms),
                successful_publishes=0,
                failed_publishes=0,
            )
        else:
            # Publish immediately
            results = await social_manager.publish_to_all(
                publish_request, request.platforms
            )

            # Format results
            formatted_results = []
            successful = 0
            failed = 0

            for result in results:
                formatted_result = {
                    "platform": result.platform,
                    "success": result.success,
                    "platform_id": result.platform_id,
                    "url": result.url,
                    "error_message": result.error_message,
                    "published_at": result.published_at.isoformat(),
                }
                formatted_results.append(formatted_result)

                if result.success:
                    successful += 1
                else:
                    failed += 1

            logger.info(
                "Social media publishing completed",
                user_id=current_user.get("id"),
                successful=successful,
                failed=failed,
            )

            return SocialPublishResponse(
                success=successful > 0,
                message=f"Published to {successful}/{len(request
                                                         .platforms)} \
                                                             platforms successfully",
                results=formatted_results,
                total_platforms=len(request.platforms),
                successful_publishes=successful,
                failed_publishes=failed,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Social media publishing failed",
            error=str(e),
            user_id=current_user.get("id"),
        )
        raise HTTPException(
            status_code=500, detail=f"Publishing failed: {str(e)}"
        )


@router.get("/platforms")
async def get_available_platforms(
    current_user: dict = Depends(get_current_user),
):
    """Get list of available social media platforms"""
    try:
        platforms = social_manager.get_available_platforms()

        platform_info = {
            "youtube": {
                "name": "YouTube",
                "description": "Video sharing platform",
                "max_duration": 43200,  # 12 hours in seconds
                "supported_formats": [
                    "mp4",
                    "mov",
                    "avi",
                    "wmv",
                    "flv",
                    "webm",
                ],
                "max_file_size_mb": 256000,  # 256 GB
                "recommended_resolution": "1920x1080",
            },
            "tiktok": {
                "name": "TikTok",
                "description": "Short-form video platform",
                "max_duration": 180,  # 3 minutes
                "supported_formats": ["mp4", "mov"],
                "max_file_size_mb": 500,
                "recommended_resolution": "1080x1920",
            },
            "instagram": {
                "name": "Instagram",
                "description": "Photo and video sharing",
                "max_duration": 60,  # 1 minute for reels
                "supported_formats": ["mp4", "mov"],
                "max_file_size_mb": 100,
                "recommended_resolution": "1080x1080",
            },
        }

        available_info = []
        for platform in platforms:
            info = platform_info.get(
                platform,
                {
                    "name": platform.title(),
                    "description": f"{platform.title()} platform",
                },
            )
            info["id"] = platform
            info["connected"] = True
            available_info.append(info)

        return {"platforms": available_info, "total": len(available_info)}

    except Exception as e:
        logger.error("Failed to get platforms", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve platforms"
        )


@router.get("/platforms/health")
async def check_platform_health(
    current_user: dict = Depends(get_current_user),
):
    """Check health status of all connected platforms"""
    try:
        health_results = await social_manager.health_check_all()

        connections = []
        for platform, health in health_results.items():
            connections.append(
                PlatformConnectionResponse(
                    platform=platform,
                    connected=health.get("status") == "healthy",
                    last_check=datetime.utcnow(),
                    error_message=health.get("error"),
                )
            )

        return {
            "connections": connections,
            "total_platforms": len(connections),
            "healthy_platforms": len([c for c in connections if c.connected]),
        }

    except Exception as e:
        logger.error("Platform health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get(
    "/stats/{platform}/{platform_id}", response_model=PlatformStatsResponse
)
async def get_video_stats(
    platform: str,
    platform_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get video statistics from specific platform"""
    try:
        stats = await social_manager.get_platform_stats(platform, platform_id)

        if "error" in stats:
            raise HTTPException(status_code=400, detail=stats["error"])

        return PlatformStatsResponse(
            platform=platform,
            platform_id=platform_id,
            stats=stats,
            retrieved_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get video stats",
            error=str(e),
            platform=platform,
            platform_id=platform_id,
        )
        raise HTTPException(
            status_code=500, detail="Failed to retrieve video statistics"
        )


@router.delete("/videos/{platform}/{platform_id}")
async def delete_video_from_platform(
    platform: str,
    platform_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete video from specific platform"""
    try:
        success = await social_manager.delete_from_platform(
            platform, platform_id
        )

        if success:
            logger.info(
                "Video deleted from platform",
                user_id=current_user.get("id"),
                platform=platform,
                platform_id=platform_id,
            )
            return {
                "message": "Video deleted successfully",
                "platform": platform,
                "platform_id": platform_id,
            }
        else:
            raise HTTPException(
                status_code=400, detail="Failed to delete video"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Video deletion failed",
            error=str(e),
            platform=platform,
            platform_id=platform_id,
        )
        raise HTTPException(status_code=500, detail="Video deletion failed")


@router.get("/templates/{platform}")
async def get_platform_templates(
    platform: str, current_user: dict = Depends(get_current_user)
):
    """Get platform-specific content templates and best practices"""

    templates = {
        "youtube": {
            "video_templates": [
                {
                    "name": "Tutorial",
                    "description": "Educational content template",
                    "structure": [
                        "Hook",
                        "Introduction",
                        "Main Content",
                        "Recap",
                        "Call to Action",
                    ],
                    "recommended_length": "8-12 minutes",
                    "tags_suggestions": [
                        "tutorial",
                        "howto",
                        "education",
                        "learning",
                    ],
                },
                {
                    "name": "Review",
                    "description": "Product or service review",
                    "structure": [
                        "Introduction",
                        "Overview",
                        "Pros/Cons",
                        "Demo",
                        "Conclusion",
                    ],
                    "recommended_length": "5-10 minutes",
                    "tags_suggestions": [
                        "review",
                        "honest",
                        "opinion",
                        "recommendation",
                    ],
                },
            ],
            "best_practices": {
                "title": "Keep titles under 60 characters, include keywords",
                "description": "Use first 125 characters effectively, \
                    include CTAs",
                "thumbnails": "Use bright colors, clear text, \
                    emotional expressions",
                "timing": "Upload consistently, consider timezone",
            },
        },
        "tiktok": {
            "video_templates": [
                {
                    "name": "Hook & Reveal",
                    "description": "Quick hook with surprising reveal",
                    "structure": [
                        "Strong Hook (0-3s)",
                        "Build tension",
                        "Reveal/Payoff",
                    ],
                    "recommended_length": "15-30 seconds",
                    "tags_suggestions": ["trending", "viral", "fyp", "foryou"],
                },
                {
                    "name": "Tutorial Quick",
                    "description": "Fast-paced tutorial",
                    "structure": [
                        "Problem statement",
                        "Quick solution",
                        "Result",
                    ],
                    "recommended_length": "30-60 seconds",
                    "tags_suggestions": [
                        "lifehack",
                        "tutorial",
                        "tips",
                        "howto",
                    ],
                },
            ],
            "best_practices": {
                "hook": "Grab attention in first 3 seconds",
                "captions": "Use trending sounds and hashtags",
                "vertical": "Always use vertical 9:16 format",
                "trending": "Jump on trending topics quickly",
            },
        },
        "instagram": {
            "video_templates": [
                {
                    "name": "Reels Showcase",
                    "description": "Product or lifestyle showcase",
                    "structure": [
                        "Eye-catching opener",
                        "Feature highlights",
                        "Final shot",
                    ],
                    "recommended_length": "15-30 seconds",
                    "tags_suggestions": [
                        "reels",
                        "instagram",
                        "lifestyle",
                        "showcase",
                    ],
                },
                {
                    "name": "Behind the Scenes",
                    "description": "Process or behind-the-scenes content",
                    "structure": ["Setup", "Process", "Final result"],
                    "recommended_length": "30-60 seconds",
                    "tags_suggestions": [
                        "bts",
                        "process",
                        "creation",
                        "behindthescenes",
                    ],
                },
            ],
            "best_practices": {
                "quality": "High-quality visuals are essential",
                "hashtags": "Use 5-10 relevant hashtags",
                "timing": "Post when your audience is most active",
                "engagement": "Respond to comments quickly",
            },
        },
    }

    if platform not in templates:
        raise HTTPException(
            status_code=404,
            detail=f"Templates not found for platform: {platform}",
        )

    return templates[platform]


@router.post("/schedule")
async def schedule_publication(
    request: SocialPublishRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Schedule video publication for later"""
    try:
        if not request.scheduled_time:
            raise HTTPException(
                status_code=400, detail="scheduled_time is required"
            )

        if request.scheduled_time <= datetime.utcnow():
            raise HTTPException(
                status_code=400, detail="scheduled_time must be in the future"
            )

        # Store scheduled publication
        # (in production, this would use a job queue)
        background_tasks.add_task(
            _scheduled_publish,
            PublishRequest(
                video_url=request.video_url,
                title=request.title,
                description=request.description,
                tags=request.tags,
                privacy=request.privacy,
                scheduled_time=request.scheduled_time,
                custom_metadata=request.platform_specific,
            ),
            request.platforms,
            current_user.get("id"),
        )

        logger.info(
            "Publication scheduled",
            user_id=current_user.get("id"),
            scheduled_time=request.scheduled_time,
            platforms=request.platforms,
        )

        return {
            "message": "Publication scheduled successfully",
            "scheduled_time": request.scheduled_time.isoformat(),
            "platforms": request.platforms,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Scheduling failed", error=str(e), user_id=current_user.get("id")
        )
        raise HTTPException(
            status_code=500, detail="Failed to schedule publication"
        )


async def _scheduled_publish(
    request: PublishRequest, platforms: List[str], user_id: str
):
    """Execute scheduled publication (background task)"""
    try:
        # In production, this would be handled by a proper job queue like
        # Celery
        import asyncio

        # Wait until scheduled time
        if request.scheduled_time:
            now = datetime.utcnow()
            if request.scheduled_time > now:
                wait_seconds = (request.scheduled_time - now).total_seconds()
                await asyncio.sleep(wait_seconds)

        # Execute publication
        results = await social_manager.publish_to_all(request, platforms)

        logger.info(
            "Scheduled publication executed",
            user_id=user_id,
            platforms=platforms,
            successful=[r.platform for r in results if r.success],
        )

    except Exception as e:
        logger.error(
            "Scheduled publication failed", error=str(e), user_id=user_id
        )
