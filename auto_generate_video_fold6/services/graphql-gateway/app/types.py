"""
GraphQL 類型定義
統一的資料模型，整合所有微服務的資料結構
"""

import strawberry
from typing import List, Optional
from datetime import datetime
from enum import Enum

@strawberry.enum
class ProjectStatus(Enum):
    """專案狀態列舉"""
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@strawberry.enum
class Platform(Enum):
    """平台類型列舉"""
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"

@strawberry.type
class User:
    """用戶類型"""
    id: strawberry.ID
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    is_active: bool = True

@strawberry.type
class VideoProject:
    """影片專案類型"""
    id: strawberry.ID
    user_id: strawberry.ID
    title: str
    description: Optional[str] = None
    status: ProjectStatus
    platform: Platform
    duration: Optional[int] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    script_id: Optional[strawberry.ID] = None
    voice_id: Optional[strawberry.ID] = None
    created_at: datetime
    updated_at: datetime
    
    @strawberry.field
    async def script(self) -> Optional["AIScript"]:
        """關聯的 AI 腳本"""
        if not self.script_id:
            return None
        # 這裡會調用 AI 服務獲取腳本詳情
        return None
    
    @strawberry.field
    async def voice_synthesis(self) -> Optional["VoiceSynthesis"]:
        """關聯的語音合成"""
        if not self.voice_id:
            return None
        # 這裡會調用語音服務獲取語音詳情
        return None

@strawberry.type
class AIScript:
    """AI 腳本類型"""
    id: strawberry.ID
    user_id: strawberry.ID
    topic: str
    content: str
    platform: Platform
    target_duration: int
    keywords: List[str]
    sentiment_score: Optional[float] = None
    readability_score: Optional[float] = None
    created_at: datetime

@strawberry.type
class VoiceSynthesis:
    """語音合成類型"""
    id: strawberry.ID
    script_id: strawberry.ID
    voice_model: str
    emotion: Optional[str] = None
    speed: float = 1.0
    pitch: float = 1.0
    audio_url: Optional[str] = None
    duration: Optional[float] = None
    status: str
    created_at: datetime

@strawberry.type
class ImageGeneration:
    """圖像生成類型"""
    id: strawberry.ID
    user_id: strawberry.ID
    prompt: str
    style: str
    resolution: str
    image_url: Optional[str] = None
    status: str
    created_at: datetime

@strawberry.type
class TrendAnalysis:
    """趨勢分析類型"""
    id: strawberry.ID
    keyword: str
    platform: Platform
    trend_score: float
    search_volume: int
    competition_level: str
    related_keywords: List[str]
    analysis_date: datetime

@strawberry.type
class SocialPost:
    """社群媒體貼文類型"""
    id: strawberry.ID
    project_id: strawberry.ID
    platform: Platform
    post_id: Optional[str] = None
    status: str
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    analytics: Optional["PostAnalytics"] = None

@strawberry.type
class PostAnalytics:
    """貼文分析類型"""
    views: int
    likes: int
    shares: int
    comments: int
    engagement_rate: float
    reach: Optional[int] = None

@strawberry.input
class VideoProjectInput:
    """影片專案輸入類型"""
    title: str
    description: Optional[str] = None
    platform: Platform = Platform.YOUTUBE
    target_duration: Optional[int] = 60

@strawberry.input
class AIScriptInput:
    """AI 腳本輸入類型"""
    topic: str
    platform: Platform = Platform.YOUTUBE
    target_duration: int = 60
    keywords: Optional[List[str]] = None
    tone: Optional[str] = "neutral"

@strawberry.input
class VoiceSynthesisInput:
    """語音合成輸入類型"""
    script_id: strawberry.ID
    voice_model: str = "default"
    emotion: Optional[str] = "neutral"
    speed: float = 1.0
    pitch: float = 1.0