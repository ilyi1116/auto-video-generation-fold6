from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class PublishRequest(BaseModel):
    video_id: int
    access_token: str
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    settings: Optional[Dict[str, Any]] = {}


class PublishResponse(BaseModel):
    success: bool
    post_url: Optional[str] = None
    post_id: Optional[str] = None
    error: Optional[str] = None


class PlatformAuth(BaseModel):
    platform: str
    auth_url: str
    client_id: str


class OAuthCallback(BaseModel):
    code: str
    state: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    token_type: str = "Bearer"


class PlatformAnalytics(BaseModel):
    platform: str
    followers: int
    total_views: int
    total_likes: int
    total_comments: int
    engagement_rate: float
    last_updated: datetime


class PostAnalytics(BaseModel):
    post_id: str
    platform: str
    views: int
    likes: int
    comments: int
    shares: int
    engagement_rate: float
    created_at: datetime
