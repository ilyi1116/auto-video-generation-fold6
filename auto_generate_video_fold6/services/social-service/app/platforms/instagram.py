import logging
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urlencode

import aiohttp

from ..config import settings

logger = logging.getLogger(__name__)


def get_auth_url() -> str:
    """生成 Instagram OAuth 授權 URL"""

    params = {
        "client_id": settings.INSTAGRAM_CLIENT_ID,
        "redirect_uri": "http://localhost:3000/auth/instagram/callback",
        "scope": "user_profile,user_media",
        "response_type": "code",
        "state": "random_state_string",
    }

    return f"https://api.instagram.com/oauth/authorize?{urlencode(params)}"


async def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """交換授權碼為 access token"""

    data = {
        "client_id": settings.INSTAGRAM_CLIENT_ID,
        "client_secret": settings.INSTAGRAM_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost:3000/auth/instagram/callback",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.instagram.com/oauth/access_token", data=data
        ) as response:
            if response.status == 200:
                result = await response.json()

                # 交換短期 token 為長期 token
                long_lived_token = await _exchange_for_long_lived_token(
                    result["access_token"]
                )

                return {
                    "access_token": long_lived_token["access_token"],
                    "expires_in": long_lived_token["expires_in"],
                    "token_type": "Bearer",
                }
            else:
                error_text = await response.text()
                raise Exception(
                    f"Instagram token exchange failed: {error_text}"
                )


async def _exchange_for_long_lived_token(short_token: str) -> Dict[str, Any]:
    """交換短期 token 為長期 token"""

    params = {
        "grant_type": "ig_exchange_token",
        "client_secret": settings.INSTAGRAM_CLIENT_SECRET,
        "access_token": short_token,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{settings.INSTAGRAM_API_BASE}/access_token", params=params
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise Exception(
                    f"Long-lived token exchange failed: {error_text}"
                )


async def publish_video(
    video_id: int,
    access_token: str,
    title: str = None,
    description: str = None,
    tags: List[str] = None,
    settings: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """發布影片到 Instagram"""

    try:
        # 獲取影片檔案 URL
        video_url = await _get_video_file_url(video_id)

        # 建立 Instagram 媒體容器
        container_data = {
            "media_type": "REELS",
            "video_url": video_url,
            "caption": f"{title or ''}\n{description or ''}",
            "access_token": access_token,
        }

        # 如果有標籤，加到 caption 中
        if tags:
            hashtags = " ".join([f"#{tag.replace('#', '')}" for tag in tags])
            container_data["caption"] += f"\n\n{hashtags}"

        async with aiohttp.ClientSession() as session:
            # 建立媒體容器
            async with session.post(
                f"{settings.INSTAGRAM_API_BASE}/me/media", data=container_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    creation_id = result["id"]

                    # 發布媒體
                    publish_data = {
                        "creation_id": creation_id,
                        "access_token": access_token,
                    }

                    async with session.post(
                        f"{settings.INSTAGRAM_API_BASE}/me/media_publish",
                        data=publish_data,
                    ) as publish_response:
                        if publish_response.status == 200:
                            publish_result = await publish_response.json()
                            media_id = publish_result["id"]

                            return {
                                "success": True,
                                "post_id": media_id,
                                "post_url": f"https://www.instagram.com/p/{media_id}/",
                            }
                        else:
                            error_text = await publish_response.text()
                            return {
                                "success": False,
                                "error": f"Instagram publish failed: {error_text}",
                            }
                else:
                    error_text = await response.text()
                    return {
                        "success": False,
                        "error": f"Instagram container creation failed: {error_text}",
                    }

    except Exception as e:
        logger.error(f"Instagram publish error: {e}")
        return {
            "success": False,
            "error": f"Instagram publish failed: {str(e)}",
        }


async def get_analytics(user_id: str) -> Dict[str, Any]:
    """獲取 Instagram 分析數據"""

    return {
        "platform": "instagram",
        "followers": 2100,
        "total_views": 89000,
        "total_likes": 6800,
        "total_comments": 520,
        "engagement_rate": 8.2,
        "last_updated": datetime.utcnow(),
    }


async def get_post_analytics(
    user_id: str, start_date: datetime, end_date: datetime
) -> List[Dict[str, Any]]:
    """獲取貼文分析數據"""

    return [
        {
            "post_id": "instagram_post_789",
            "platform": "instagram",
            "views": 18500,
            "likes": 1450,
            "comments": 85,
            "shares": 230,
            "engagement_rate": 9.4,
            "created_at": datetime.utcnow(),
        }
    ]


async def get_engagement_metrics(user_id: str, days: int) -> Dict[str, Any]:
    """獲取互動率指標"""

    return {
        "platform": "instagram",
        "period_days": days,
        "average_engagement_rate": 8.2,
        "best_performing_time": "18:00-20:00",
        "top_hashtags": ["#reels", "#viral", "#instagram"],
        "audience_insights": {
            "age_groups": {
                "13-17": 15,
                "18-24": 35,
                "25-34": 30,
                "35-44": 15,
                "45+": 5,
            },
            "gender": {"female": 58, "male": 42},
            "top_locations": ["台北", "高雄", "台中"],
        },
        "story_metrics": {
            "story_views": 1500,
            "story_reach": 1200,
            "story_exits": 120,
        },
    }


async def get_trending_content(category: str = None) -> Dict[str, Any]:
    """獲取趨勢內容"""

    return {
        "platform": "instagram",
        "category": category or "general",
        "trending_hashtags": [
            {"tag": "#reels", "posts": 850000},
            {"tag": "#viral", "posts": 620000},
            {"tag": "#trending", "posts": 450000},
        ],
        "trending_audio": [
            {"name": "Original Audio", "usage": 95000},
            {"name": "Trending Sound", "usage": 78000},
        ],
        "trending_effects": [
            {"name": "Beauty Effect", "usage": 65000},
            {"name": "Color Filter", "usage": 52000},
        ],
        "popular_formats": [
            {"format": "Before/After", "engagement": 12.5},
            {"format": "Tutorial", "engagement": 10.8},
            {"format": "Behind the Scenes", "engagement": 9.7},
        ],
    }


async def check_api_status() -> str:
    """檢查 Instagram API 狀態"""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{settings.INSTAGRAM_API_BASE}/me"
            ) as response:
                return (
                    "healthy" if response.status in [200, 401] else "unhealthy"
                )
    except:
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
