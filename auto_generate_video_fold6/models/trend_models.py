"""
趨勢分析相關模型
"""

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from .base import Base


class TrendingTopic(Base):
    """熱門話題模型"""

    __tablename__ = "trending_topics"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # google, youtube, tiktok, instagram

    # 趨勢數據
    search_volume = Column(Integer, default=0)
    trend_score = Column(Float, default=0.0)
    growth_rate = Column(Float, default=0.0)  # 增長率百分比

    # 分類
    category = Column(String(100))
    tags = Column(JSON)  # 相關標籤

    # 地理資訊
    region = Column(String(50), default="TW")  # 地區代碼

    # 時間資訊
    trend_date = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class KeywordResearch(Base):
    """關鍵字研究模型"""

    __tablename__ = "keyword_research"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), nullable=False, index=True)

    # 搜尋數據
    monthly_searches = Column(Integer, default=0)
    competition_level = Column(String(20))  # low, medium, high
    cpc = Column(Float, default=0.0)  # 每次點擊成本

    # SEO 數據
    difficulty_score = Column(Float, default=0.0)  # 1-100
    opportunity_score = Column(Float, default=0.0)  # 1-100

    # 相關關鍵字
    related_keywords = Column(JSON)
    long_tail_keywords = Column(JSON)

    # 平台特定數據
    youtube_results = Column(Integer, default=0)
    tiktok_hashtag_views = Column(Integer, default=0)
    instagram_posts = Column(Integer, default=0)

    # 時間資訊
    research_date = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class ViralContent(Base):
    """病毒式內容模型"""

    __tablename__ = "viral_content"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)
    content_id = Column(String(255), nullable=False)  # 平台原始 ID
    content_url = Column(String(500))

    # 內容資訊
    title = Column(Text)
    description = Column(Text)
    creator = Column(String(255))
    duration = Column(Integer)  # 秒數

    # 病毒式傳播數據
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)

    # 病毒係數
    viral_score = Column(Float, default=0.0)
    growth_velocity = Column(Float, default=0.0)  # 增長速度

    # 內容分析
    hashtags = Column(JSON)
    topics = Column(JSON)
    emotions = Column(JSON)  # 情感分析結果

    # 時間資訊
    published_at = Column(DateTime)
    discovered_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class TrendAnalysis(Base):
    """趨勢分析模型"""

    __tablename__ = "trend_analysis"

    id = Column(Integer, primary_key=True, index=True)
    analysis_type = Column(String(50), nullable=False)  # keyword, topic, content
    target = Column(String(255), nullable=False)  # 分析目標

    # 分析結果
    analysis_data = Column(JSON)
    insights = Column(JSON)
    recommendations = Column(JSON)

    # 評分
    trend_potential = Column(Float, default=0.0)  # 趨勢潛力 1-100
    commercial_value = Column(Float, default=0.0)  # 商業價值 1-100
    content_difficulty = Column(Float, default=0.0)  # 內容製作難度 1-100

    # 預測
    predicted_growth = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)

    # 時間資訊
    analysis_date = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
