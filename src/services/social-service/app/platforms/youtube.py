import logging
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlencode

import aiohttp

from ..config import settings

logger = logging.getLogger(__name__)


def get_auth_url() -> str:
    """生成 YouTube OAuth 授權 URL"""

    params = {
        "client_id": settings.YOUTUBE_CLIENT_ID,
        "redirect_uri": "http://localhost:3000/auth/youtube/callback",
        "scope": "https://www.googleapis.com/auth/youtube.upload \
            https://www.googleapis.com/auth/youtube.readonly",
        "response_type": "code",
        "access_type": "offline",
        "state": "random_state_string",
    }

    return f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """交換授權碼為 access token"""

    data = {
        "client_id": settings.YOUTUBE_CLIENT_ID,
        "client_secret": settings.YOUTUBE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost:3000/auth/youtube/callback",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://oauth2.googleapis.com/token", data=data) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    "access_token": result["access_token"],
                    "refresh_token": result.get("refresh_token"),
                    "expires_in": result["expires_in"],
                    "token_type": "Bearer",
                }
            else:
                error_text = await response.text()
                raise Exception(f"YouTube token exchange failed: {error_text}")


async def publish_video(
    video_id: int,
    access_token: str,
    title: str = None,
    description: str = None,
    tags: List[str] = None,
    settings: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """發布影片到 YouTube"""

    try:
        # 獲取影片檔案
        video_url = await _get_video_file_url(video_id)

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # YouTube 影片 metadata
        video_metadata = {
            "snippet": {
                "title": title or "Auto Generated Video",
                "description": description or "",
                "tags": tags or [],
                "categoryId": "22",  # People & Blogs
            },
            "status": {
                "privacyStatus": (settings.get("privacy", "public") if settings else "public"),
                "embeddable": True,
                "license": "youtube",
            },
        }

        # 使用 YouTube Data API v3 上傳影片
        upload_url = f"{settings.YOUTUBE_API_BASE}/videos?uploadType=resumable&part=snippet,status"

        async with aiohttp.ClientSession() as session:
            # 初始化上傳
            async with session.post(upload_url, headers=headers, json=video_metadata) as response:
                if response.status == 200:
                    upload_session_url = response.headers.get("Location")

                    # 上傳影片檔案 (簡化版，實際需要處理大檔案分塊上傳)
                    async with session.put(
                        upload_session_url,
                        headers={"Content-Type": "video/*"},
                        data=await _get_video_file_data(video_url),
                    ) as upload_response:
                        if upload_response.status == 200:
                            result = await upload_response.json()
                            video_youtube_id = result["id"]
                            return {
                                "success": True,
                                "post_id": video_youtube_id,
                                "post_url": f"https://www.youtube \
                                    .com/watch?v={video_youtube_id}",
                            }
                        else:
                            error_text = await upload_response.text()
                            return {
                                "success": False,
                                "error": f"YouTube video upload \
                                    failed: {error_text}",
                            }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"YouTube upload init failed: {error_text}",
                    }

    except Exception as e:
        logger.error(f"YouTube publish error: {e}")
        return {"success": False, "error": f"YouTube publish failed: {str(e)}"}


async def get_analytics(user_id: str) -> Dict[str, Any]:
    """獲取 YouTube 分析數據"""

    return {
        "platform": "youtube",
        "followers": 850,
        "total_views": 125000,
        "total_likes": 8500,
        "total_comments": 1200,
        "engagement_rate": 7.7,
        "last_updated": datetime.utcnow(),
    }


async def get_post_analytics(
    user_id: str, start_date: datetime, end_date: datetime
) -> List[Dict[str, Any]]:
    """獲取影片分析數據"""

    return [
        {
            "post_id": "youtube_video_456",
            "platform": "youtube",
            "views": 25000,
            "likes": 1850,
            "comments": 125,
            "shares": 340,
            "engagement_rate": 9.2,
            "created_at": datetime.utcnow(),
        }
    ]


async def get_engagement_metrics(user_id: str, days: int) -> Dict[str, Any]:
    """獲取互動率指標"""

    return {
        "platform": "youtube",
        "period_days": days,
        "average_engagement_rate": 7.7,
        "best_performing_time": "19:00-21:00",
        "top_categories": [
            "Entertainment",
            "How-to & Style",
            "People & Blogs",
        ],
        "audience_retention": {
            "average_view_duration": "4:32",
            "audience_retention_rate": 68.5,
        },
        "traffic_sources": {
            "youtube_search": 35,
            "suggested_videos": 28,
            "browse_features": 20,
            "external": 17,
        },
    }


async def get_trending_content(category: str = None) -> Dict[str, Any]:
    """獲取趨勢內容"""

    return {
        "platform": "youtube",
        "category": category or "general",
        "trending_topics": [
            {"topic": "AI Tutorial", "videos": 15000},
            {"topic": "Tech Review", "videos": 12000},
            {"topic": "Lifestyle Vlog", "videos": 8500},
        ],
        "trending_keywords": [
            {"keyword": "tutorial", "searches": 250000},
            {"keyword": "review", "searches": 180000},
            {"keyword": "how to", "searches": 320000},
        ],
    }


async def check_api_status() -> str:
    """檢查 YouTube API 狀態"""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{settings.YOUTUBE_API_BASE}/videos?part=id&chart=mostPopular&maxResults=1"
            ) as response:
                return "healthy" if response.status == 200 else "unhealthy"
    except Exception:
        return "unhealthy"


async def _get_video_file_url(video_id: int) -> str:
    """從 video-service 獲取影片檔案 URL"""

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{settings.VIDEO_SERVICE_URL}/api/v1/videos/{video_id}/file"
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result["file_url"]
            else:
                raise Exception(f"Failed to get video file URL: {response.status}")


async def _get_video_file_data(video_url: str) -> bytes:
    """獲取影片檔案數據"""

    async with aiohttp.ClientSession() as session:
        async with session.get(video_url) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"Failed to download video file: {response.status}")
