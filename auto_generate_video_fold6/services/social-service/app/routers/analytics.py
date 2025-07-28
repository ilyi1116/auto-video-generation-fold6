import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import verify_token
from ..platforms import instagram, tiktok, youtube
from ..schemas import PlatformAnalytics, PostAnalytics

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/platforms", response_model=List[PlatformAnalytics])
async def get_platform_analytics(
    platforms: Optional[str] = Query(None, description="Comma-separated platform names"),
    current_user: dict = Depends(verify_token),
):
    """獲取平台總體分析數據"""

    if platforms:
        platform_list = [p.strip() for p in platforms.split(",")]
    else:
        platform_list = ["tiktok", "youtube", "instagram"]

    analytics_data = []

    for platform in platform_list:
        try:
            if platform == "tiktok":
                data = await tiktok.get_analytics(current_user["user_id"])
            elif platform == "youtube":
                data = await youtube.get_analytics(current_user["user_id"])
            elif platform == "instagram":
                data = await instagram.get_analytics(current_user["user_id"])
            else:
                continue

            analytics_data.append(PlatformAnalytics(**data))

        except Exception as e:
            logger.error(f"Failed to get analytics for {platform}: {e}")
            continue

    return analytics_data


@router.get("/posts", response_model=List[PostAnalytics])
async def get_post_analytics(
    platform: Optional[str] = Query(None),
    days: int = Query(30, description="Number of days to look back"),
    current_user: dict = Depends(verify_token),
):
    """獲取貼文分析數據"""

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    post_analytics = []

    platforms_to_check = [platform] if platform else ["tiktok", "youtube", "instagram"]

    for platform_name in platforms_to_check:
        try:
            if platform_name == "tiktok":
                posts = await tiktok.get_post_analytics(
                    current_user["user_id"], start_date, end_date
                )
            elif platform_name == "youtube":
                posts = await youtube.get_post_analytics(
                    current_user["user_id"], start_date, end_date
                )
            elif platform_name == "instagram":
                posts = await instagram.get_post_analytics(
                    current_user["user_id"], start_date, end_date
                )
            else:
                continue

            for post_data in posts:
                post_analytics.append(PostAnalytics(**post_data))

        except Exception as e:
            logger.error(f"Failed to get post analytics for {platform_name}: {e}")
            continue

    return post_analytics


@router.get("/engagement/{platform}")
async def get_engagement_metrics(
    platform: str,
    days: int = Query(7, description="Number of days to analyze"),
    current_user: dict = Depends(verify_token),
):
    """獲取互動率指標"""

    try:
        if platform == "tiktok":
            metrics = await tiktok.get_engagement_metrics(current_user["user_id"], days)
        elif platform == "youtube":
            metrics = await youtube.get_engagement_metrics(current_user["user_id"], days)
        elif platform == "instagram":
            metrics = await instagram.get_engagement_metrics(current_user["user_id"], days)
        else:
            raise HTTPException(status_code=400, detail="Unsupported platform")

        return metrics

    except Exception as e:
        logger.error(f"Failed to get engagement metrics for {platform}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get engagement metrics: {str(e)}")


@router.get("/trending/{platform}")
async def get_trending_content(
    platform: str, category: Optional[str] = Query(None), current_user: dict = Depends(verify_token)
):
    """獲取趨勢內容"""

    try:
        if platform == "tiktok":
            trending = await tiktok.get_trending_content(category)
        elif platform == "youtube":
            trending = await youtube.get_trending_content(category)
        elif platform == "instagram":
            trending = await instagram.get_trending_content(category)
        else:
            raise HTTPException(status_code=400, detail="Unsupported platform")

        return trending

    except Exception as e:
        logger.error(f"Failed to get trending content for {platform}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trending content: {str(e)}")
