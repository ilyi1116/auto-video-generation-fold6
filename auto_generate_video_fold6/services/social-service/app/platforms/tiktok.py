import logging
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlencode

import aiohttp

from ..config import settings

logger = logging.getLogger(__name__)


def get_auth_url() -> str:
    """生成 TikTok OAuth 授權 URL"""

    params = {
        "client_key": settings.TIKTOK_CLIENT_ID,
        "scope": "user.info.basic,video.upload,video.publish",
        "response_type": "code",
        "redirect_uri": "http://localhost:3000/auth/tiktok/callback",
        "state": "random_state_string",
    }

    return f"{settings.TIKTOK_API_BASE}/platform/oauth/authorize/?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """交換授權碼為 access token"""

    data = {
        "client_key": settings.TIKTOK_CLIENT_ID,
        "client_secret": settings.TIKTOK_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost:3000/auth/tiktok/callback",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{settings.TIKTOK_API_BASE}/oauth/access_token/", json=data
        ) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    "access_token": result["data"]["access_token"],
                    "refresh_token": result["data"]["refresh_token"],
                    "expires_in": result["data"]["expires_in"],
                    "token_type": "Bearer",
                }
            else:
                error_text = await response.text()
                raise Exception(f"TikTok token exchange failed: {error_text}")


async def publish_video(
    video_id: int,
    access_token: str,
    title: str = None,
    description: str = None,
    tags: List[str] = None,
    settings: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """發布影片到 TikTok"""

    try:
        # 首先獲取影片檔案
        video_url = await _get_video_file_url(video_id)

        # 上傳影片到 TikTok
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        upload_data = {
            "source_info": {"source": "FILE_UPLOAD", "video_url": video_url},
            "post_info": {
                "title": title or "",
                "description": description or "",
                "disable_duet": (
                    settings.get("disable_duet", False) if settings else False
                ),
                "disable_comment": (
                    settings.get("disable_comment", False)
                    if settings
                    else False
                ),
                "disable_stitch": (
                    settings.get("disable_stitch", False)
                    if settings
                    else False
                ),
                "video_cover_timestamp_ms": (
                    settings.get("cover_timestamp", 1000) if settings else 1000
                ),
            },
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{settings.TIKTOK_API_BASE}/share/video/upload/",
                headers=headers,
                json=upload_data,
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "post_id": result["data"]["share_id"],
                        "post_url": f"https://www.tiktok \
                            .com/@user/video/{result['data']['share_id']}",
                    }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"TikTok upload failed: {error_text}",
                    }

    except Exception as e:
        logger.error(f"TikTok publish error: {e}")
        return {"success": False, "error": f"TikTok publish failed: {str(e)}"}


async def get_analytics(user_id: str) -> Dict[str, Any]:
    """獲取 TikTok 分析數據"""

    # 模擬數據，實際應該調用 TikTok Analytics API
    return {
        "platform": "tiktok",
        "followers": 1250,
        "total_views": 58000,
        "total_likes": 4200,
        "total_comments": 380,
        "engagement_rate": 7.8,
        "last_updated": datetime.utcnow(),
    }


async def get_post_analytics(
    user_id: str, start_date: datetime, end_date: datetime
) -> List[Dict[str, Any]]:
    """獲取貼文分析數據"""

    # 模擬數據
    return [
        {
            "post_id": "tiktok_post_123",
            "platform": "tiktok",
            "views": 12500,
            "likes": 850,
            "comments": 45,
            "shares": 120,
            "engagement_rate": 8.1,
            "created_at": datetime.utcnow(),
        }
    ]


async def get_engagement_metrics(user_id: str, days: int) -> Dict[str, Any]:
    """獲取互動率指標"""

    return {
        "platform": "tiktok",
        "period_days": days,
        "average_engagement_rate": 7.8,
        "best_performing_time": "20:00-22:00",
        "top_hashtags": ["#fyp", "#viral", "#trending"],
        "audience_age_groups": {
            "13-17": 25,
            "18-24": 45,
            "25-34": 20,
            "35+": 10,
        },
    }


async def get_trending_content(category: str = None) -> Dict[str, Any]:
    """獲取趨勢內容"""

    return {
        "platform": "tiktok",
        "category": category or "general",
        "trending_hashtags": [
            {"tag": "#fyp", "posts": 1500000},
            {"tag": "#viral", "posts": 850000},
            {"tag": "#trending", "posts": 650000},
        ],
        "trending_sounds": [
            {"name": "Original Sound", "usage": 125000},
            {"name": "Trending Beat", "usage": 98000},
        ],
        "trending_effects": [
            {"name": "Beauty Filter", "usage": 78000},
            {"name": "Color Pop", "usage": 65000},
        ],
    }


async def check_api_status() -> str:
    """檢查 TikTok API 狀態"""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{settings.TIKTOK_API_BASE}/oauth/access_token/"
            ) as response:
                return (
                    "healthy" if response.status in [200, 400] else "unhealthy"
                )
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
                raise Exception(
                    f"Failed to get video file URL: {response.status}"
                )
