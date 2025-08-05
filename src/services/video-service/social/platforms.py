"""
Social Media Platform Integration

This module handles integration with various social media platforms
for automated video publishing and management.
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PublishRequest(BaseModel):
    """Video publishing request"""

    video_url: str
    thumbnail_url: Optional[str] = None
    title: str
    description: Optional[str] = None
    tags: List[str] = []
    privacy: str = "public"  # public, private, unlisted
    scheduled_time: Optional[datetime] = None
    custom_metadata: Dict[str, Any] = {}


class PublishResult(BaseModel):
    """Video publishing result"""

    platform: str
    success: bool
    platform_id: Optional[str] = None  # Platform-specific video ID
    url: Optional[str] = None  # Public URL on platform
    error_message: Optional[str] = None
    published_at: datetime
    metadata: Dict[str, Any] = {}


class SocialPlatform(ABC):
    """Abstract base class for social media platforms"""

    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    @abstractmethod
    async def publish_video(self, request: PublishRequest) -> PublishResult:
        """Publish video to platform"""

    @abstractmethod
    async def get_video_stats(self, platform_id: str) -> Dict[str, Any]:
        """Get video statistics from platform"""

    @abstractmethod
    async def delete_video(self, platform_id: str) -> bool:
        """Delete video from platform"""

    async def health_check(self) -> Dict[str, Any]:
        """Check platform API health"""
        return {"status": "unknown", "platform": self.__class__.__name__}

    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()


class TikTokClient(SocialPlatform):
    """TikTok API client for video publishing"""

    def __init__(self, api_key: str, client_id: str, client_secret: str):
        super().__init__(api_key)
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://open-api.tiktok.com/v1.3"
        self.upload_url = "https://open-upload.tiktokapis.com/v1"

    async def publish_video(self, request: PublishRequest) -> PublishResult:
        """Publish video to TikTok"""

        try:
            logger.info(f"Publishing video to TikTok: {request.title}")

            # Step 1: Upload video
            upload_result = await self._upload_video(request.video_url)

            if not upload_result.get("success"):
                raise Exception(f"Video upload failed: {upload_result.get('error')}")

            # Step 2: Create post
            post_result = await self._create_post(upload_result["video_id"], request)

            return PublishResult(
                platform="tiktok",
                success=True,
                platform_id=post_result["video_id"],
                url=post_result.get("share_url"),
                published_at=datetime.utcnow(),
                metadata={
                    "upload_id": upload_result["video_id"],
                    "publish_id": post_result["video_id"],
                },
            )

        except Exception as e:
            logger.error(f"TikTok publishing failed: {str(e)}")
            return PublishResult(
                platform="tiktok",
                success=False,
                error_message=str(e),
                published_at=datetime.utcnow(),
            )

    async def _upload_video(self, video_url: str) -> Dict[str, Any]:
        """Upload video to TikTok"""

        session = await self._get_session()

        # Get video data
        async with session.get(video_url) as response:
            if response.status != 200:
                raise Exception(f"Failed to download video: {response.status}")

            video_data = await response.read()

        # Upload to TikTok
        data = aiohttp.FormData()
        data.add_field("video", video_data, filename="video.mp4", content_type="video/mp4")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "multipart/form-data",
        }

        async with session.post(
            f"{self.upload_url}/video/upload", data=data, headers=headers
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(
                    f"TikTok upload API error: {response.status} - \
                        {error_text}"
                )

            result = await response.json()

            if result.get("error"):
                raise Exception(f"TikTok upload error: {result['error']['message']}")

            return {"success": True, "video_id": result["data"]["video_id"]}

    async def _create_post(self, video_id: str, request: PublishRequest) -> Dict[str, Any]:
        """Create TikTok post"""

        session = await self._get_session()

        payload = {
            "video_id": video_id,
            "text": request.description or request.title,
            "privacy_level": ("PUBLIC_TO_EVERYONE" if request.privacy == "public" else "SELF_ONLY"),
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
            "video_cover_timestamp_ms": 1000,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with session.post(
            f"{self.base_url}/video/publish", json=payload, headers=headers
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(
                    f"TikTok publish API error: {response.status} - \
                        {error_text}"
                )

            result = await response.json()

            if result.get("error"):
                raise Exception(f"TikTok publish error: {result['error']['message']}")

            return {
                "video_id": result["data"]["video_id"],
                "share_url": result["data"].get("share_url"),
            }

    async def get_video_stats(self, platform_id: str) -> Dict[str, Any]:
        """Get TikTok video statistics"""

        try:
            session = await self._get_session()

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with session.get(
                f"{self.base_url}/video/query",
                params={"video_id": platform_id},
                headers=headers,
            ) as response:
                if response.status != 200:
                    return {"error": f"API error: {response.status}"}

                result = await response.json()

                if result.get("error"):
                    return {"error": result["error"]["message"]}

                data = result["data"]
                return {
                    "views": data.get("view_count", 0),
                    "likes": data.get("like_count", 0),
                    "comments": data.get("comment_count", 0),
                    "shares": data.get("share_count", 0),
                    "status": data.get("status"),
                    "created_at": data.get("create_time"),
                }

        except Exception as e:
            logger.error(f"Failed to get TikTok video stats: {str(e)}")
            return {"error": str(e)}

    async def delete_video(self, platform_id: str) -> bool:
        """Delete video from TikTok"""

        try:
            session = await self._get_session()

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            async with session.delete(
                f"{self.base_url}/video/delete",
                params={"video_id": platform_id},
                headers=headers,
            ) as response:
                return response.status == 200

        except Exception as e:
            logger.error(f"Failed to delete TikTok video: {str(e)}")
            return False


class YouTubeClient(SocialPlatform):
    """YouTube API client for video publishing"""

    def __init__(self, api_key: str, oauth_token: str):
        super().__init__(api_key)
        self.oauth_token = oauth_token
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.upload_url = "https://www.googleapis.com/upload/youtube/v3"

    async def publish_video(self, request: PublishRequest) -> PublishResult:
        """Publish video to YouTube"""

        try:
            logger.info(f"Publishing video to YouTube: {request.title}")

            # Upload video with metadata
            result = await self._upload_video_with_metadata(request)

            return PublishResult(
                platform="youtube",
                success=True,
                platform_id=result["video_id"],
                url=f"https://www.youtube.com/watch?v={result['video_id']}",
                published_at=datetime.utcnow(),
                metadata=result,
            )

        except Exception as e:
            logger.error(f"YouTube publishing failed: {str(e)}")
            return PublishResult(
                platform="youtube",
                success=False,
                error_message=str(e),
                published_at=datetime.utcnow(),
            )

    async def _upload_video_with_metadata(self, request: PublishRequest) -> Dict[str, Any]:
        """Upload video to YouTube with metadata"""

        session = await self._get_session()

        # Prepare metadata
        snippet = {
            "title": request.title,
            "description": request.description or "",
            "tags": request.tags,
            "categoryId": "22",  # People & Blogs
        }

        status = {
            "privacyStatus": request.privacy,
            "selfDeclaredMadeForKids": False,
        }

        metadata = {"snippet": snippet, "status": status}

        # Download video
        async with session.get(request.video_url) as response:
            if response.status != 200:
                raise Exception(f"Failed to download video: {response.status}")

            video_data = await response.read()

        # Create multipart upload
        boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"

        body_parts = []

        # Add metadata part
        body_parts.append(f"--{boundary}")
        body_parts.append("Content-Type: application/json; charset=UTF-8")
        body_parts.append("")
        body_parts.append(json.dumps(metadata))

        # Add video part
        body_parts.append(f"--{boundary}")
        body_parts.append("Content-Type: video/mp4")
        body_parts.append("")

        body = (
            "\r\n".join(body_parts).encode()
            + b"\r\n"
            + video_data
            + f"\r\n--{boundary}--\r\n".encode()
        )

        headers = {
            "Authorization": f"Bearer {self.oauth_token}",
            "Content-Type": f"multipart/related; boundary={boundary}",
            "Content-Length": str(len(body)),
        }

        async with session.post(
            f"{self.upload_url}/videos?uploadType=multipart&part=snippet,status",
            data=body,
            headers=headers,
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(
                    f"YouTube upload API error: {response.status} - \
                        {error_text}"
                )

            result = await response.json()

            return {
                "video_id": result["id"],
                "upload_status": result.get("status", {}).get("uploadStatus"),
                "privacy_status": result.get("status", {}).get("privacyStatus"),
            }

    async def get_video_stats(self, platform_id: str) -> Dict[str, Any]:
        """Get YouTube video statistics"""

        try:
            session = await self._get_session()

            params = {
                "part": "statistics,status",
                "id": platform_id,
                "key": self.api_key,
            }

            async with session.get(f"{self.base_url}/videos", params=params) as response:
                if response.status != 200:
                    return {"error": f"API error: {response.status}"}

                result = await response.json()

                if not result.get("items"):
                    return {"error": "Video not found"}

                item = result["items"][0]
                stats = item.get("statistics", {})

                return {
                    "views": int(stats.get("viewCount", 0)),
                    "likes": int(stats.get("likeCount", 0)),
                    "comments": int(stats.get("commentCount", 0)),
                    "status": item.get("status", {}).get("uploadStatus"),
                }

        except Exception as e:
            logger.error(f"Failed to get YouTube video stats: {str(e)}")
            return {"error": str(e)}

    async def delete_video(self, platform_id: str) -> bool:
        """Delete video from YouTube"""

        try:
            session = await self._get_session()

            headers = {
                "Authorization": f"Bearer {self.oauth_token}",
                "Content-Type": "application/json",
            }

            async with session.delete(
                f"{self.base_url}/videos",
                params={"id": platform_id},
                headers=headers,
            ) as response:
                return response.status == 204

        except Exception as e:
            logger.error(f"Failed to delete YouTube video: {str(e)}")
            return False


class InstagramClient(SocialPlatform):
    """Instagram API client for video publishing"""

    def __init__(self, api_key: str, business_account_id: str):
        super().__init__(api_key)
        self.business_account_id = business_account_id
        self.base_url = "https://graph.facebook.com/v18.0"

    async def publish_video(self, request: PublishRequest) -> PublishResult:
        """Publish video to Instagram"""

        try:
            logger.info(f"Publishing video to Instagram: {request.title}")

            # Step 1: Create media container
            container_id = await self._create_media_container(request)

            # Step 2: Publish media
            result = await self._publish_media(container_id)

            return PublishResult(
                platform="instagram",
                success=True,
                platform_id=result["media_id"],
                url=result.get("permalink"),
                published_at=datetime.utcnow(),
                metadata={
                    "container_id": container_id,
                    "media_id": result["media_id"],
                },
            )

        except Exception as e:
            logger.error(f"Instagram publishing failed: {str(e)}")
            return PublishResult(
                platform="instagram",
                success=False,
                error_message=str(e),
                published_at=datetime.utcnow(),
            )

    async def _create_media_container(self, request: PublishRequest) -> str:
        """Create Instagram media container"""

        session = await self._get_session()

        params = {
            "video_url": request.video_url,
            "media_type": ("REELS" if request.custom_metadata.get("is_reels") else "VIDEO"),
            "caption": f"{request.title}\n\n{request.description or ''}",
            "access_token": self.api_key,
        }

        # Add thumbnail if provided
        if request.thumbnail_url:
            params["thumb_offset"] = 0

        async with session.post(
            f"{self.base_url}/{self.business_account_id}/media", params=params
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(
                    f"Instagram media creation error: {response.status} - {
                        error_text
                    }"
                )

            result = await response.json()

            if "error" in result:
                raise Exception(f"Instagram API error: {result['error']['message']}")

            return result["id"]

    async def _publish_media(self, container_id: str) -> Dict[str, Any]:
        """Publish Instagram media container"""

        session = await self._get_session()

        params = {"creation_id": container_id, "access_token": self.api_key}

        async with session.post(
            f"{self.base_url}/{self.business_account_id}/media_publish",
            params=params,
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(
                    f"Instagram publish error: {response.status} - \
                        {error_text}"
                )

            result = await response.json()

            if "error" in result:
                raise Exception(f"Instagram API error: {result['error']['message']}")

            # Get media permalink
            media_id = result["id"]
            permalink = await self._get_media_permalink(media_id)

            return {"media_id": media_id, "permalink": permalink}

    async def _get_media_permalink(self, media_id: str) -> Optional[str]:
        """Get media permalink"""

        try:
            session = await self._get_session()

            params = {"fields": "permalink", "access_token": self.api_key}

            async with session.get(f"{self.base_url}/{media_id}", params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("permalink")

                return None

        except Exception as e:
            logger.error(f"Failed to get Instagram permalink: {str(e)}")
            return None

    async def get_video_stats(self, platform_id: str) -> Dict[str, Any]:
        """Get Instagram video statistics"""

        try:
            session = await self._get_session()

            params = {
                "fields": "insights.metric(reach,impressions \
                    ,video_views,likes,comments,shares,saves)",
                "access_token": self.api_key,
            }

            async with session.get(f"{self.base_url}/{platform_id}", params=params) as response:
                if response.status != 200:
                    return {"error": f"API error: {response.status}"}

                result = await response.json()
                insights = result.get("insights", {}).get("data", [])

                stats = {}
                for insight in insights:
                    metric = insight.get("name")
                    value = insight.get("values", [{}])[0].get("value", 0)
                    stats[metric] = value

                return {
                    "views": stats.get("video_views", 0),
                    "likes": stats.get("likes", 0),
                    "comments": stats.get("comments", 0),
                    "shares": stats.get("shares", 0),
                    "saves": stats.get("saves", 0),
                    "reach": stats.get("reach", 0),
                    "impressions": stats.get("impressions", 0),
                }

        except Exception as e:
            logger.error(f"Failed to get Instagram video stats: {str(e)}")
            return {"error": str(e)}

    async def delete_video(self, platform_id: str) -> bool:
        """Delete video from Instagram"""

        try:
            session = await self._get_session()

            params = {"access_token": self.api_key}

            async with session.delete(f"{self.base_url}/{platform_id}", params=params) as response:
                return response.status == 200

        except Exception as e:
            logger.error(f"Failed to delete Instagram video: {str(e)}")
            return False


class SocialMediaManager:
    """Unified social media platform manager"""

    def __init__(self):
        self.platforms: Dict[str, SocialPlatform] = {}
        self._initialize_platforms()

    def _initialize_platforms(self):
        """Initialize platform clients based on environment variables"""

        # TikTok
        tiktok_api_key = os.getenv("TIKTOK_API_KEY")
        tiktok_client_id = os.getenv("TIKTOK_CLIENT_ID")
        tiktok_client_secret = os.getenv("TIKTOK_CLIENT_SECRET")

        if all([tiktok_api_key, tiktok_client_id, tiktok_client_secret]):
            self.platforms["tiktok"] = TikTokClient(
                tiktok_api_key, tiktok_client_id, tiktok_client_secret
            )

        # YouTube
        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        youtube_oauth_token = os.getenv("YOUTUBE_OAUTH_TOKEN")

        if all([youtube_api_key, youtube_oauth_token]):
            self.platforms["youtube"] = YouTubeClient(youtube_api_key, youtube_oauth_token)

        # Instagram
        instagram_api_key = os.getenv("INSTAGRAM_API_KEY")
        instagram_business_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

        if all([instagram_api_key, instagram_business_id]):
            self.platforms["instagram"] = InstagramClient(instagram_api_key, instagram_business_id)

    async def publish_to_platform(self, platform: str, request: PublishRequest) -> PublishResult:
        """Publish video to specific platform"""

        if platform not in self.platforms:
            return PublishResult(
                platform=platform,
                success=False,
                error_message=f"Platform {platform} not configured",
                published_at=datetime.utcnow(),
            )

        return await self.platforms[platform].publish_video(request)

    async def publish_to_all(
        self, request: PublishRequest, platforms: Optional[List[str]] = None
    ) -> List[PublishResult]:
        """Publish video to multiple platforms"""

        target_platforms = platforms or list(self.platforms.keys())
        results = []

        tasks = []
        for platform in target_platforms:
            if platform in self.platforms:
                task = self.publish_to_platform(platform, request)
                tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    platform = target_platforms[i]
                    final_results.append(
                        PublishResult(
                            platform=platform,
                            success=False,
                            error_message=str(result),
                            published_at=datetime.utcnow(),
                        )
                    )
                else:
                    final_results.append(result)

            return final_results

        return []

    async def get_platform_stats(self, platform: str, platform_id: str) -> Dict[str, Any]:
        """Get video statistics from platform"""

        if platform not in self.platforms:
            return {"error": f"Platform {platform} not configured"}

        return await self.platforms[platform].get_video_stats(platform_id)

    async def delete_from_platform(self, platform: str, platform_id: str) -> bool:
        """Delete video from platform"""

        if platform not in self.platforms:
            return False

        return await self.platforms[platform].delete_video(platform_id)

    async def health_check_all(self) -> Dict[str, Any]:
        """Check health of all configured platforms"""

        results = {}

        for platform_name, platform_client in self.platforms.items():
            results[platform_name] = await platform_client.health_check()

        return results

    async def close_all(self):
        """Close all platform connections"""

        for platform_client in self.platforms.values():
            await platform_client.close()

    def get_available_platforms(self) -> List[str]:
        """Get list of available platforms"""
        return list(self.platforms.keys())
