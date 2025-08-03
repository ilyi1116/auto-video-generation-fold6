from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class AIProviderTypeEnum(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE_GEMINI = "google_gemini"
    AZURE_OPENAI = "azure_openai"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"


class CrawlerStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PAUSED = "paused"


class ScheduleTypeEnum(str, Enum):
    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM_CRON = "custom_cron"


class SocialPlatformEnum(str, Enum):
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"


class TrendTimeframeEnum(str, Enum):
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1m"
    THREE_MONTHS = "3m"
    SIX_MONTHS = "6m"


class LogLevelEnum(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# AI Provider Schemas
class AIProviderBase(BaseModel):
    name: str = Field(..., max_length=100)
    provider_type: AIProviderTypeEnum
    api_key: str = Field(..., max_length=500)
    api_url: Optional[str] = Field(None, max_length=500)
    model_name: Optional[str] = Field(None, max_length=200)
    max_tokens: int = Field(2048, gt=0, le=32000)
    temperature: str = Field("0.7")
    timeout: int = Field(30, gt=0, le=300)
    rate_limit: int = Field(60, gt=0, le=10000)
    is_active: bool = True
    is_default: bool = False
    extra_config: Optional[Dict[str, Any]] = None


class AIProviderCreate(AIProviderBase):
    pass


class AIProviderUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    provider_type: Optional[AIProviderTypeEnum] = None
    api_key: Optional[str] = Field(None, max_length=500)
    api_url: Optional[str] = Field(None, max_length=500)
    model_name: Optional[str] = Field(None, max_length=200)
    max_tokens: Optional[int] = Field(None, gt=0, le=32000)
    temperature: Optional[str] = None
    timeout: Optional[int] = Field(None, gt=0, le=300)
    rate_limit: Optional[int] = Field(None, gt=0, le=10000)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    extra_config: Optional[Dict[str, Any]] = None


class AIProviderResponse(AIProviderBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Crawler Config Schemas
class CrawlerConfigBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    target_url: str = Field(..., max_length=1000)
    keywords: List[str] = Field(..., min_items=1)
    css_selectors: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    schedule_type: ScheduleTypeEnum = ScheduleTypeEnum.DAILY
    schedule_config: Optional[Dict[str, Any]] = None
    status: CrawlerStatusEnum = CrawlerStatusEnum.ACTIVE
    max_pages: int = Field(10, gt=0, le=1000)
    delay_seconds: int = Field(1, ge=0, le=60)
    retry_attempts: int = Field(3, ge=0, le=10)
    timeout_seconds: int = Field(30, gt=0, le=300)
    use_proxy: bool = False
    proxy_config: Optional[Dict[str, str]] = None

    @validator('keywords')
    def validate_keywords(cls, v):
        if not v or len(v) == 0:
            raise ValueError('至少需要一個關鍵字')
        return v


class CrawlerConfigCreate(CrawlerConfigBase):
    pass


class CrawlerConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    target_url: Optional[str] = Field(None, max_length=1000)
    keywords: Optional[List[str]] = None
    css_selectors: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    schedule_type: Optional[ScheduleTypeEnum] = None
    schedule_config: Optional[Dict[str, Any]] = None
    status: Optional[CrawlerStatusEnum] = None
    max_pages: Optional[int] = Field(None, gt=0, le=1000)
    delay_seconds: Optional[int] = Field(None, ge=0, le=60)
    retry_attempts: Optional[int] = Field(None, ge=0, le=10)
    timeout_seconds: Optional[int] = Field(None, gt=0, le=300)
    use_proxy: Optional[bool] = None
    proxy_config: Optional[Dict[str, str]] = None


class CrawlerConfigResponse(CrawlerConfigBase):
    id: int
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Social Trend Config Schemas
class SocialTrendConfigBase(BaseModel):
    platform: SocialPlatformEnum
    region: str = Field("global", max_length=10)
    category: Optional[str] = Field(None, max_length=100)
    language: str = Field("en", max_length=10)
    api_endpoint: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = Field(None, max_length=500)
    timeframes: List[TrendTimeframeEnum] = Field(..., min_items=1)
    schedule_config: Dict[str, Any]
    is_active: bool = True
    rate_limit: int = Field(100, gt=0, le=10000)
    extra_params: Optional[Dict[str, Any]] = None


class SocialTrendConfigCreate(SocialTrendConfigBase):
    pass


class SocialTrendConfigUpdate(BaseModel):
    platform: Optional[SocialPlatformEnum] = None
    region: Optional[str] = Field(None, max_length=10)
    category: Optional[str] = Field(None, max_length=100)
    language: Optional[str] = Field(None, max_length=10)
    api_endpoint: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = Field(None, max_length=500)
    timeframes: Optional[List[TrendTimeframeEnum]] = None
    schedule_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    rate_limit: Optional[int] = Field(None, gt=0, le=10000)
    extra_params: Optional[Dict[str, Any]] = None


class SocialTrendConfigResponse(SocialTrendConfigBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Trending Keywords Schemas
class TrendingKeywordBase(BaseModel):
    platform: SocialPlatformEnum
    keyword: str = Field(..., max_length=500)
    rank: int = Field(..., gt=0)
    score: Optional[int] = None
    timeframe: TrendTimeframeEnum
    region: str = Field("global", max_length=10)
    category: Optional[str] = Field(None, max_length=100)
    trend_date: datetime
    metadata: Optional[Dict[str, Any]] = None


class TrendingKeywordCreate(TrendingKeywordBase):
    pass


class TrendingKeywordResponse(TrendingKeywordBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# System Log Schemas
class SystemLogBase(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = Field(None, max_length=100)
    action: str = Field(..., max_length=200)
    resource_type: str = Field(..., max_length=100)
    resource_id: Optional[str] = Field(None, max_length=100)
    level: LogLevelEnum = LogLevelEnum.INFO
    message: str
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)
    request_id: Optional[str] = Field(None, max_length=100)
    session_id: Optional[str] = Field(None, max_length=100)
    duration_ms: Optional[int] = None
    status_code: Optional[int] = None
    error_code: Optional[str] = Field(None, max_length=50)
    stack_trace: Optional[str] = None


class SystemLogCreate(SystemLogBase):
    pass


class SystemLogResponse(SystemLogBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Admin User Schemas
class AdminUserBase(BaseModel):
    username: str = Field(..., max_length=100)
    email: str = Field(..., max_length=255)
    full_name: Optional[str] = Field(None, max_length=200)
    role: str = Field("admin", max_length=50)
    permissions: Optional[Dict[str, Any]] = None
    is_active: bool = True
    is_superuser: bool = False


class AdminUserCreate(AdminUserBase):
    password: str = Field(..., min_length=8)


class AdminUserUpdate(BaseModel):
    username: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    full_name: Optional[str] = Field(None, max_length=200)
    role: Optional[str] = Field(None, max_length=50)
    permissions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class AdminUserResponse(AdminUserBase):
    id: int
    last_login_at: Optional[datetime] = None
    login_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Pagination and Query Schemas
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)


class LogQueryParams(PaginationParams):
    level: Optional[LogLevelEnum] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    username: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TrendQueryParams(PaginationParams):
    platform: Optional[SocialPlatformEnum] = None
    timeframe: Optional[TrendTimeframeEnum] = None
    region: Optional[str] = None
    category: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


# Dashboard Statistics
class DashboardStats(BaseModel):
    total_ai_providers: int
    active_ai_providers: int
    total_crawlers: int
    active_crawlers: int
    total_trends_today: int
    total_logs_today: int
    error_logs_today: int
    last_24h_activity: Dict[str, int]


# API Response Wrappers
class APIResponse(BaseModel):
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None
    errors: Optional[List[str]] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: Optional[List[str]] = None
    error_code: Optional[str] = None