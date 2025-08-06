from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import verify_token
from ..database import get_db
from ..models import TrendAnalysis
from ..schemas import (
    CompetitorAnalysis,
    TrendAnalysisRequest,
    TrendAnalysisResponse,
    ViralContentAnalysis,
)
from ..services import competitor_analyzer, content_analyzer

router = APIRouter()


@router.post("/trends", response_model=TrendAnalysisResponse)
async def analyze_trend(
    request: TrendAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_token),
):
    """執行趨勢分析"""

    try:
        analysis_result = await content_analyzer.analyze_trend_potential(
            target=request.target,
            analysis_type=request.analysis_type,
            platforms=request.platforms or ["google", "youtube", "tiktok"],
            region=request.region,
        )

        # 保存分析結果
        trend_analysis = TrendAnalysis(
            analysis_type=request.analysis_type,
            target=request.target,
            analysis_data=analysis_result["data"],
            insights=analysis_result["insights"],
            recommendations=analysis_result["recommendations"],
            trend_potential=analysis_result["trend_potential"],
            commercial_value=analysis_result["commercial_value"],
            content_difficulty=analysis_result["content_difficulty"],
            predicted_growth=analysis_result["predicted_growth"],
            confidence_score=analysis_result["confidence_score"],
        )

        db.add(trend_analysis)
        db.commit()
        db.refresh(trend_analysis)

        return trend_analysis

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.get("/viral-potential")
async def analyze_viral_potential(
    content_url: str = Query(...),
    platform: str = Query("youtube"),
    current_user: dict = Depends(verify_token),
) -> ViralContentAnalysis:
    """分析內容的病毒式傳播潛力"""

    try:
        viral_analysis = await content_analyzer.analyze_viral_potential(
            content_url=content_url, platform=platform
        )

        return ViralContentAnalysis(
            content_url=content_url,
            viral_factors=viral_analysis["viral_factors"],
            success_probability=viral_analysis["success_probability"],
            recommendations=viral_analysis["recommendations"],
            optimal_timing=viral_analysis["optimal_timing"],
            target_audience=viral_analysis["target_audience"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Viral potential analysis failed: {str(e)}",
        )


@router.get("/competitor/{competitor}")
async def analyze_competitor(
    competitor: str,
    platform: str = Query("youtube"),
    analysis_depth: str = Query("standard", description="basic, standard, deep"),
    current_user: dict = Depends(verify_token),
) -> CompetitorAnalysis:
    """分析競爭對手"""

    try:
        competitor_data = await competitor_analyzer.analyze_competitor(
            competitor=competitor, platform=platform, depth=analysis_depth
        )

        return CompetitorAnalysis(
            competitor=competitor,
            top_content=competitor_data["top_content"],
            engagement_rate=competitor_data["engagement_rate"],
            posting_frequency=competitor_data["posting_frequency"],
            content_themes=competitor_data["content_themes"],
            performance_insights=competitor_data["insights"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Competitor analysis failed: {str(e)}")


@router.get("/market-opportunity")
async def analyze_market_opportunity(
    niche: str = Query(...),
    region: str = Query("TW"),
    timeframe: str = Query("6m"),
    current_user: dict = Depends(verify_token),
):
    """分析市場機會"""

    try:
        opportunity_analysis = await content_analyzer.analyze_market_opportunity(
            niche=niche, region=region, timeframe=timeframe
        )

        return {
            "niche": niche,
            "region": region,
            "market_size": opportunity_analysis["market_size"],
            "growth_trend": opportunity_analysis["growth_trend"],
            "competition_level": opportunity_analysis["competition_level"],
            "entry_barriers": opportunity_analysis["entry_barriers"],
            "success_factors": opportunity_analysis["success_factors"],
            "monetization_potential": opportunity_analysis["monetization"],
            "recommended_strategy": opportunity_analysis["strategy"],
            "timeline_forecast": opportunity_analysis["forecast"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Market opportunity analysis failed: {str(e)}",
        )


@router.get("/content-performance")
async def analyze_content_performance(
    content_type: str = Query("video"),
    platform: str = Query("youtube"),
    category: Optional[str] = None,
    days: int = Query(30, ge=7, le=365),
    current_user: dict = Depends(verify_token),
):
    """分析內容表現模式"""

    try:
        performance_analysis = await content_analyzer.analyze_content_performance_patterns(
            content_type=content_type,
            platform=platform,
            category=category,
            days=days,
        )

        return {
            "content_type": content_type,
            "platform": platform,
            "analysis_period": f"{days} days",
            "top_performing_formats": performance_analysis["top_formats"],
            "optimal_length": performance_analysis["optimal_length"],
            "best_posting_times": performance_analysis["posting_times"],
            "engagement_patterns": performance_analysis["engagement_patterns"],
            "thumbnail_insights": performance_analysis["thumbnail_insights"],
            "title_patterns": performance_analysis["title_patterns"],
            "content_recommendations": performance_analysis["recommendations"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Content performance analysis failed: {str(e)}",
        )


@router.get("/audience-insights")
async def get_audience_insights(
    target_keyword: str = Query(...),
    platform: str = Query("youtube"),
    demographic_focus: str = Query("age_gender", description="age_gender, interests, behavior"),
    current_user: dict = Depends(verify_token),
):
    """獲取目標受眾洞察"""

    try:
        audience_data = await content_analyzer.analyze_target_audience(
            keyword=target_keyword, platform=platform, focus=demographic_focus
        )

        return {
            "target_keyword": target_keyword,
            "platform": platform,
            "audience_demographics": audience_data["demographics"],
            "interests": audience_data["interests"],
            "online_behavior": audience_data["behavior"],
            "preferred_content_types": audience_data["content_preferences"],
            "engagement_patterns": audience_data["engagement_patterns"],
            "purchasing_behavior": audience_data["purchasing"],
            "content_strategy_recommendations": audience_data["strategy_recommendations"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Audience insights analysis failed: {str(e)}",
        )


@router.get("/seasonal-trends")
async def get_seasonal_trends(
    keyword: str = Query(...),
    years_back: int = Query(2, ge=1, le=5),
    granularity: str = Query("monthly", description="weekly, monthly, quarterly"),
    current_user: dict = Depends(verify_token),
):
    """分析季節性趨勢"""

    try:
        seasonal_data = await content_analyzer.analyze_seasonal_trends(
            keyword=keyword, years_back=years_back, granularity=granularity
        )

        return {
            "keyword": keyword,
            "analysis_period": f"{years_back} years",
            "seasonal_patterns": seasonal_data["patterns"],
            "peak_seasons": seasonal_data["peak_seasons"],
            "low_seasons": seasonal_data["low_seasons"],
            "year_over_year_growth": seasonal_data["yoy_growth"],
            "content_planning_calendar": seasonal_data["content_calendar"],
            "optimization_recommendations": seasonal_data["recommendations"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Seasonal trends analysis failed: {str(e)}",
        )
