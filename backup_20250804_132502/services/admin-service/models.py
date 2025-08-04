from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()


class AIProviderType(enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE_GEMINI = "google_gemini"
    AZURE_OPENAI = "azure_openai"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"


class CrawlerStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PAUSED = "paused"


class ScheduleType(enum.Enum):
    ONCE = "once"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM_CRON = "custom_cron"


class SocialPlatform(enum.Enum):
    TIKTOK = "tiktok"
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"


class TrendTimeframe(enum.Enum):
    ONE_DAY = "1d"
    ONE_WEEK = "1w"
    ONE_MONTH = "1m"
    THREE_MONTHS = "3m"
    SIX_MONTHS = "6m"


class LogLevel(enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AIProvider(Base):
    """AI Provider 設定表"""
    __tablename__ = "ai_providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    provider_type = Column(Enum(AIProviderType), nullable=False)
    api_key = Column(String(500), nullable=False)  # 加密存儲
    api_url = Column(String(500), nullable=True)
    model_name = Column(String(200), nullable=True)
    max_tokens = Column(Integer, default=2048)
    temperature = Column(String(10), default="0.7")
    timeout = Column(Integer, default=30)
    rate_limit = Column(Integer, default=60)  # requests per minute
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    extra_config = Column(JSON, nullable=True)  # 額外配置參數
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<AIProvider(name={self.name}, type={self.provider_type})>"


class CrawlerConfig(Base):
    """爬蟲配置表"""
    __tablename__ = "crawler_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    target_url = Column(String(1000), nullable=False)
    keywords = Column(JSON, nullable=False)  # 關鍵字列表
    css_selectors = Column(JSON, nullable=True)  # CSS 選擇器配置
    headers = Column(JSON, nullable=True)  # HTTP 請求頭
    schedule_type = Column(Enum(ScheduleType), default=ScheduleType.DAILY)
    schedule_config = Column(JSON, nullable=True)  # 排程配置（cron 表達式等）
    status = Column(Enum(CrawlerStatus), default=CrawlerStatus.ACTIVE)
    max_pages = Column(Integer, default=10)
    delay_seconds = Column(Integer, default=1)
    retry_attempts = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=30)
    use_proxy = Column(Boolean, default=False)
    proxy_config = Column(JSON, nullable=True)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    next_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<CrawlerConfig(name={self.name}, url={self.target_url})>"


class SocialTrendConfig(Base):
    """社交媒體熱門關鍵字配置表"""
    __tablename__ = "social_trend_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(Enum(SocialPlatform), nullable=False)
    region = Column(String(10), default="global")  # 地區代碼（如 US, TW）
    category = Column(String(100), nullable=True)  # 分類（如 音樂、科技）
    language = Column(String(10), default="en")  # 語言代碼
    api_endpoint = Column(String(500), nullable=True)
    api_key = Column(String(500), nullable=True)  # 加密存儲
    timeframes = Column(JSON, nullable=False)  # 支援的時間範圍
    schedule_config = Column(JSON, nullable=False)  # 爬取排程
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=100)  # API 呼叫限制
    extra_params = Column(JSON, nullable=True)  # 額外 API 參數
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<SocialTrendConfig(platform={self.platform}, region={self.region})>"


class KeywordTrend(Base):
    """熱門關鍵字趨勢表 (主要資料表)"""
    __tablename__ = "keyword_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False)  # "TikTok", "YouTube", "Instagram", "Facebook", "Twitter"
    keyword = Column(String(500), nullable=False)
    period = Column(String(20), nullable=False)  # "day", "week", "month", "3_months", "6_months"
    rank = Column(Integer, nullable=False)
    search_volume = Column(Integer, nullable=True)
    collected_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 額外欄位
    region = Column(String(10), default="global")
    category = Column(String(100), nullable=True)
    score = Column(Integer, nullable=True)  # 熱門度分數
    change_percentage = Column(String(10), nullable=True)  # 變化百分比
    metadata = Column(JSON, nullable=True)  # 額外元數據
    
    def __repr__(self):
        return f"<KeywordTrend(platform={self.platform}, keyword={self.keyword}, rank={self.rank})>"


class TrendingKeyword(Base):
    """熱門關鍵字數據表 (舊版，保持相容性)"""
    __tablename__ = "trending_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(Enum(SocialPlatform), nullable=False)
    keyword = Column(String(500), nullable=False)
    rank = Column(Integer, nullable=False)
    score = Column(Integer, nullable=True)  # 熱門度分數
    timeframe = Column(Enum(TrendTimeframe), nullable=False)
    region = Column(String(10), default="global")
    category = Column(String(100), nullable=True)
    trend_date = Column(DateTime(timezone=True), nullable=False)
    metadata = Column(JSON, nullable=True)  # 額外元數據
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<TrendingKeyword(platform={self.platform}, keyword={self.keyword}, rank={self.rank})>"


class SystemLog(Base):
    """系統操作日誌表"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # 操作用戶 ID
    username = Column(String(100), nullable=True)  # 操作用戶名
    action = Column(String(200), nullable=False)  # 操作類型
    resource_type = Column(String(100), nullable=False)  # 資源類型
    resource_id = Column(String(100), nullable=True)  # 資源 ID
    level = Column(Enum(LogLevel), default=LogLevel.INFO)
    message = Column(Text, nullable=False)  # 日誌訊息
    details = Column(JSON, nullable=True)  # 詳細信息
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(String(500), nullable=True)  # 用戶代理
    request_id = Column(String(100), nullable=True)  # 請求追蹤 ID
    session_id = Column(String(100), nullable=True)  # 會話 ID
    duration_ms = Column(Integer, nullable=True)  # 操作耗時（毫秒）
    status_code = Column(Integer, nullable=True)  # HTTP 狀態碼
    error_code = Column(String(50), nullable=True)  # 錯誤代碼
    stack_trace = Column(Text, nullable=True)  # 錯誤堆疊追蹤
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<SystemLog(action={self.action}, level={self.level}, user={self.username})>"


class CrawlerResult(Base):
    """爬蟲結果表"""
    __tablename__ = "crawler_results"
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, nullable=False)  # 關聯到 CrawlerConfig
    run_id = Column(String(100), nullable=False)  # 運行 ID（UUID）
    url = Column(String(1000), nullable=False)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    keywords_found = Column(JSON, nullable=True)  # 找到的關鍵字
    metadata = Column(JSON, nullable=True)  # 額外元數據
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<CrawlerResult(config_id={self.config_id}, url={self.url[:50]}...)>"


class CrawlerTask(Base):
    """爬蟲任務表 - 符合用戶要求的資料模型"""
    __tablename__ = "crawler_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(200), unique=True, nullable=False)
    keywords = Column(Text, nullable=False)  # JSON 格式的關鍵字清單
    target_url = Column(String(1000), nullable=True)  # 目標網址，可為空
    schedule_type = Column(String(50), nullable=False, default="daily")  # daily, weekly, hourly, cron
    schedule_time = Column(String(100), nullable=True)  # 排程時間
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 關聯關係
    task_results = relationship("CrawlerTaskResult", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CrawlerTask(task_name={self.task_name}, schedule_type={self.schedule_type})>"


class CrawlerTaskResult(Base):
    """爬蟲任務結果表"""
    __tablename__ = "crawler_task_results"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("crawler_tasks.id"), nullable=False)
    run_id = Column(String(100), nullable=False)  # 執行ID（UUID）
    url = Column(String(2000), nullable=True)
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    matched_keywords = Column(Text, nullable=True)  # JSON 格式
    page_number = Column(Integer, default=1)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 關聯關係
    task = relationship("CrawlerTask", back_populates="task_results")
    
    def __repr__(self):
        return f"<CrawlerTaskResult(task_id={self.task_id}, url={self.url[:50] if self.url else 'N/A'}...)>"


class AdminUser(Base):
    """後台管理用戶表"""
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(200), nullable=True)
    role = Column(String(50), default="admin")  # admin, super_admin, readonly
    permissions = Column(JSON, nullable=True)  # 權限配置
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<AdminUser(username={self.username}, role={self.role})>"