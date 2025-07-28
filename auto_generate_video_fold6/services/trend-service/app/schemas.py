from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PlatformType(str, Enum):
    GOOGLE = "google"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"


class CompetitionLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TrendingTopicResponse(BaseModel):
    id: int
    keyword: str
    platform: str
    search_volume: int
    trend_score: float
    growth_rate: float
    category: Optional[str]
    tags: Optional[List[str]]
    region: str
    trend_date: datetime

    class Config:
        from_attributes = True


class KeywordResearchResponse(BaseModel):
    id: int
    keyword: str
    monthly_searches: int
    competition_level: str
    cpc: float
    difficulty_score: float
    opportunity_score: float
    related_keywords: Optional[List[str]]
    long_tail_keywords: Optional[List[str]]
    youtube_results: int
    tiktok_hashtag_views: int
    instagram_posts: int
    research_date: datetime

    class Config:
        from_attributes = True


class ViralContentResponse(BaseModel):
    id: int
    platform: str
    content_id: str
    content_url: Optional[str]
    title: Optional[str]
    description: Optional[str]
    creator: Optional[str]
    duration: Optional[int]
    views: int
    likes: int
    shares: int
    comments: int
    viral_score: float
    growth_velocity: float
    hashtags: Optional[List[str]]
    topics: Optional[List[str]]
    emotions: Optional[Dict[str, float]]
    published_at: Optional[datetime]
    discovered_at: datetime

    class Config:
        from_attributes = True


class TrendAnalysisResponse(BaseModel):
    id: int
    analysis_type: str
    target: str
    analysis_data: Optional[Dict[str, Any]]
    insights: Optional[List[str]]
    recommendations: Optional[List[str]]
    trend_potential: float
    commercial_value: float
    content_difficulty: float
    predicted_growth: float
    confidence_score: float
    analysis_date: datetime

    class Config:
        from_attributes = True


class KeywordSearchRequest(BaseModel):
    keyword: str
    platforms: Optional[List[PlatformType]] = [PlatformType.GOOGLE]
    region: Optional[str] = "TW"


class TrendAnalysisRequest(BaseModel):
    target: str
    analysis_type: str = "keyword"  # keyword, topic, content
    platforms: Optional[List[PlatformType]] = None
    region: Optional[str] = "TW"


class TrendSuggestion(BaseModel):
    keyword: str
    trend_score: float
    search_volume: int
    competition: str
    opportunity_score: float
    platforms: List[str]
    hashtags: List[str]
    estimated_reach: int


class ViralContentAnalysis(BaseModel):
    content_url: str
    viral_factors: List[str]
    success_probability: float
    recommendations: List[str]
    optimal_timing: str
    target_audience: Dict[str, Any]


class CompetitorAnalysis(BaseModel):
    competitor: str
    top_content: List[Dict[str, Any]]
    engagement_rate: float
    posting_frequency: str
    content_themes: List[str]
    performance_insights: List[str]
