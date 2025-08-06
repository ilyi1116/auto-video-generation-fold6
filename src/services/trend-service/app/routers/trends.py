from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..models import TrendingTopic, ViralContent
from ..schemas import (
    PlatformType,
    TrendingTopicResponse,
    TrendSuggestion,
    ViralContentResponse,
)
from ..services import trend_analyzer

router = APIRouter()


@router.get("/trending", response_model=List[TrendingTopicResponse])
async def get_trending_topics(
    platform: Optional[PlatformType] = None,
    category: Optional[str] = None,
    region: str = Query("TW"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """獲取趨勢主題"""

    query = db.query(TrendingTopic)

    if platform:
        query = query.filter(TrendingTopic.platform == platform)

    if category:
        query = query.filter(TrendingTopic.category == category)

    query = query.filter(TrendingTopic.region == region)

    # 按趨勢分數排序，優先顯示最新的數據
    trends = (
        query.order_by(
            TrendingTopic.trend_score.desc(), TrendingTopic.trend_date.desc()
        )
        .limit(limit)
        .all()
    )

    return trends


@router.get("/viral", response_model=List[ViralContentResponse])
async def get_viral_content(
    platform: Optional[PlatformType] = None,
    days: int = Query(7, ge=1, le=30),
    min_viral_score: float = Query(70.0, ge=0, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """獲取病毒式內容"""

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    query = db.query(ViralContent).filter(
        ViralContent.discovered_at >= cutoff_date,
        ViralContent.viral_score >= min_viral_score,
    )

    if platform:
        query = query.filter(ViralContent.platform == platform)

    viral_content = (
        query.order_by(
            ViralContent.viral_score.desc(), ViralContent.discovered_at.desc()
        )
        .limit(50)
        .all()
    )

    return viral_content


@router.get("/suggestions", response_model=List[TrendSuggestion])
async def get_trend_suggestions(
    category: Optional[str] = None,
    platforms: Optional[str] = Query(
        None, description="Comma-separated platform names"
    ),
    region: str = Query("TW"),
    current_user: dict = Depends(verify_token),
):
    """獲取趨勢建議"""

    platform_list = []
    if platforms:
        platform_list = [p.strip() for p in platforms.split(",")]
    else:
        platform_list = ["google", "youtube", "tiktok", "instagram"]

    suggestions = await trend_analyzer.generate_trend_suggestions(
        category=category, platforms=platform_list, region=region
    )

    return suggestions


@router.get("/realtime/{platform}")
async def get_realtime_trends(
    platform: PlatformType,
    region: str = Query("TW"),
    current_user: dict = Depends(verify_token),
):
    """獲取實時趨勢數據"""

    try:
        realtime_data = await trend_analyzer.fetch_realtime_trends(
            platform=platform, region=region
        )

        return {
            "platform": platform,
            "region": region,
            "last_updated": datetime.utcnow(),
            "trends": realtime_data,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch realtime trends: {str(e)}",
        )


@router.get("/categories")
async def get_trend_categories(
    platform: Optional[PlatformType] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """獲取趨勢分類"""

    query = db.query(TrendingTopic.category).distinct()

    if platform:
        query = query.filter(TrendingTopic.platform == platform)

    categories = [cat[0] for cat in query.all() if cat[0]]

    return {"categories": categories}


@router.get("/hashtags/{platform}")
async def get_trending_hashtags(
    platform: PlatformType,
    category: Optional[str] = None,
    limit: int = Query(30, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """獲取熱門標籤"""

    hashtags_data = await trend_analyzer.get_trending_hashtags(
        platform=platform, category=category, limit=limit
    )

    return {
        "platform": platform,
        "hashtags": hashtags_data,
        "last_updated": datetime.utcnow(),
    }


@router.post("/refresh/{platform}")
async def refresh_platform_trends(
    platform: PlatformType,
    region: str = Query("TW"),
    current_user: dict = Depends(verify_token),
):
    """手動刷新平台趨勢數據"""

    try:
        result = await trend_analyzer.refresh_platform_data(
            platform=platform, region=region
        )

        return {
            "message": f"Successfully refreshed {platform} trends",
            "updated_count": result.get("updated_count", 0),
            "new_count": result.get("new_count", 0),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to refresh trends: {str(e)}"
        )


@router.get("/performance/{keyword}")
async def get_keyword_performance(
    keyword: str,
    platforms: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """獲取關鍵字表現歷史"""

    platform_list = (
        platforms.split(",")
        if platforms
        else ["google", "youtube", "tiktok", "instagram"]
    )

    performance_data = await trend_analyzer.get_keyword_performance_history(
        keyword=keyword, platforms=platform_list, days=days
    )

    return performance_data
