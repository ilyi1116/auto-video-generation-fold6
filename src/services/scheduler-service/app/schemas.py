from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class PlatformType(str, Enum):
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"


class PostStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SchedulePostRequest(BaseModel):
    video_id: int
    platform: PlatformType
    platform_account_id: Optional[str] = None
    scheduled_time: datetime
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    platform_settings: Optional[Dict[str, Any]] = {}


class SchedulePostResponse(BaseModel):
    id: int
    user_id: int
    video_id: int
    platform: str
    platform_account_id: Optional[str]
    scheduled_time: datetime
    status: str
    title: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    platform_settings: Optional[Dict[str, Any]]
    post_url: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class UpdateScheduleRequest(BaseModel):
    scheduled_time: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    platform_settings: Optional[Dict[str, Any]] = None


class PlatformAccountRequest(BaseModel):
    platform: PlatformType
    platform_user_id: str
    platform_username: Optional[str] = None
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None


class PlatformAccountResponse(BaseModel):
    id: int
    user_id: int
    platform: str
    platform_user_id: str
    platform_username: Optional[str]
    is_active: bool
    is_connected: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleListResponse(BaseModel):
    total: int
    items: List[SchedulePostResponse]
    page: int
    page_size: int
