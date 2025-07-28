from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..models import KeywordResearch
from ..schemas import (
    KeywordResearchResponse,
    KeywordSearchRequest,
)
from ..services import keyword_analyzer

router = APIRouter()


@router.post("/research", response_model=KeywordResearchResponse)
async def research_keyword(
    request: KeywordSearchRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """研究關鍵字"""

    try:
        # 檢查是否已有近期研究結果
        existing_research = (
            db.query(KeywordResearch)
            .filter(KeywordResearch.keyword == request.keyword)
            .first()
        )

        if existing_research:
            # 如果研究結果在24小時內，直接返回
            from datetime import datetime, timedelta

            if existing_research.research_date > datetime.utcnow() - timedelta(
                hours=24
            ):
                return existing_research

        # 執行新的關鍵字研究
        research_data = await keyword_analyzer.analyze_keyword(
            keyword=request.keyword,
            platforms=request.platforms,
            region=request.region,
        )

        # 保存或更新研究結果
        if existing_research:
            for key, value in research_data.items():
                setattr(existing_research, key, value)
            existing_research.research_date = datetime.utcnow()
            db.commit()
            db.refresh(existing_research)
            return existing_research
        else:
            keyword_research = KeywordResearch(
                keyword=request.keyword, **research_data
            )
            db.add(keyword_research)
            db.commit()
            db.refresh(keyword_research)
            return keyword_research

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Keyword research failed: {str(e)}"
        )


@router.get("/suggestions/{seed_keyword}")
async def get_keyword_suggestions(
    seed_keyword: str,
    limit: int = Query(20, le=100),
    include_questions: bool = Query(True),
    include_long_tail: bool = Query(True),
    current_user: dict = Depends(verify_token),
):
    """獲取關鍵字建議"""

    try:
        suggestions = await keyword_analyzer.get_keyword_suggestions(
            seed_keyword=seed_keyword,
            limit=limit,
            include_questions=include_questions,
            include_long_tail=include_long_tail,
        )

        return {
            "seed_keyword": seed_keyword,
            "suggestions": suggestions["keywords"],
            "questions": (
                suggestions.get("questions", []) if include_questions else []
            ),
            "long_tail": (
                suggestions.get("long_tail", []) if include_long_tail else []
            ),
            "total_suggestions": len(suggestions["keywords"]),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get keyword suggestions: {str(e)}",
        )


@router.get("/difficulty/{keyword}")
async def get_keyword_difficulty(
    keyword: str,
    platform: str = Query("google"),
    current_user: dict = Depends(verify_token),
):
    """分析關鍵字競爭難度"""

    try:
        difficulty_data = await keyword_analyzer.analyze_keyword_difficulty(
            keyword=keyword, platform=platform
        )

        return {
            "keyword": keyword,
            "platform": platform,
            "difficulty_score": difficulty_data["difficulty_score"],
            "competition_level": difficulty_data["competition_level"],
            "top_competitors": difficulty_data["top_competitors"],
            "content_gap_opportunities": difficulty_data["opportunities"],
            "recommended_strategy": difficulty_data["strategy"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Keyword difficulty analysis failed: {str(e)}",
        )


@router.get("/volume/{keyword}")
async def get_keyword_volume(
    keyword: str,
    platforms: Optional[str] = Query(None),
    region: str = Query("TW"),
    timeframe: str = Query("12m", description="3m, 6m, 12m, 24m"),
    current_user: dict = Depends(verify_token),
):
    """獲取關鍵字搜尋量趨勢"""

    platform_list = platforms.split(",") if platforms else ["google"]

    try:
        volume_data = await keyword_analyzer.get_search_volume_trends(
            keyword=keyword,
            platforms=platform_list,
            region=region,
            timeframe=timeframe,
        )

        return {
            "keyword": keyword,
            "region": region,
            "timeframe": timeframe,
            "volume_trends": volume_data["trends"],
            "average_monthly_searches": volume_data["average_monthly"],
            "peak_months": volume_data["peak_months"],
            "seasonal_patterns": volume_data["seasonal_patterns"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get keyword volume: {str(e)}"
        )


@router.get("/comparison")
async def compare_keywords(
    keywords: str = Query(..., description="Comma-separated keywords"),
    platform: str = Query("google"),
    region: str = Query("TW"),
    current_user: dict = Depends(verify_token),
):
    """比較多個關鍵字"""

    keyword_list = [kw.strip() for kw in keywords.split(",")]

    if len(keyword_list) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 keywords allowed for comparison",
        )

    try:
        comparison_data = await keyword_analyzer.compare_keywords(
            keywords=keyword_list, platform=platform, region=region
        )

        return {
            "keywords": keyword_list,
            "platform": platform,
            "region": region,
            "comparison": comparison_data["comparison_table"],
            "best_opportunity": comparison_data["best_opportunity"],
            "recommendations": comparison_data["recommendations"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Keyword comparison failed: {str(e)}"
        )


@router.get("/gaps/{competitor_domain}")
async def find_keyword_gaps(
    competitor_domain: str,
    your_domain: Optional[str] = None,
    limit: int = Query(50, le=200),
    current_user: dict = Depends(verify_token),
):
    """發現關鍵字機會空隙"""

    try:
        gap_analysis = await keyword_analyzer.find_keyword_gaps(
            competitor_domain=competitor_domain,
            your_domain=your_domain,
            limit=limit,
        )

        return {
            "competitor_domain": competitor_domain,
            "your_domain": your_domain,
            "keyword_gaps": gap_analysis["gaps"],
            "content_opportunities": gap_analysis["opportunities"],
            "priority_keywords": gap_analysis["priority_list"],
            "estimated_traffic_potential": gap_analysis["traffic_potential"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Keyword gap analysis failed: {str(e)}"
        )


@router.get("/content-ideas/{keyword}")
async def get_content_ideas(
    keyword: str,
    content_type: str = Query("video", description="video, blog, social"),
    platform: str = Query("youtube"),
    limit: int = Query(10, le=30),
    current_user: dict = Depends(verify_token),
):
    """基於關鍵字生成內容創意"""

    try:
        content_ideas = await keyword_analyzer.generate_content_ideas(
            keyword=keyword,
            content_type=content_type,
            platform=platform,
            limit=limit,
        )

        return {
            "keyword": keyword,
            "content_type": content_type,
            "platform": platform,
            "ideas": content_ideas["ideas"],
            "trending_angles": content_ideas["trending_angles"],
            "suggested_titles": content_ideas["titles"],
            "hashtag_recommendations": content_ideas["hashtags"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Content idea generation failed: {str(e)}"
        )
