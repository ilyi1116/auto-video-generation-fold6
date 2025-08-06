"""
統一的資料庫模型 - 定義所有微服務共享的核心業務模型
"""

from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class UserRole(PyEnum):
    ADMIN = "admin"
    USER = "user"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class ProjectStatus(PyEnum):
    DRAFT = "draft"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class VideoStatus(PyEnum):
    PENDING = "pending"
    GENERATING_SCRIPT = "generating_script"
    GENERATING_AUDIO = "generating_audio"
    GENERATING_IMAGES = "generating_images"
    GENERATING_MUSIC = "generating_music"
    COMPOSITING = "compositing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(PyEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"


# ============================================================================
# 核心業務模型
# ============================================================================


class User(Base):
    """用戶模型"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)

    # 角色和狀態
    role = Column(Enum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # 個人資訊
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)

    # 訂閱和計費
    subscription_tier = Column(String(50), default="free")
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)

    # 使用量統計
    api_calls_count = Column(Integer, default=0)
    videos_created = Column(Integer, default=0)
    storage_used_mb = Column(Integer, default=0)

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # 關聯
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    videos = relationship("Video", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    """專案模型 - 管理用戶的影片專案"""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 專案基本資訊
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.DRAFT)

    # 專案設定
    settings = Column(JSON, nullable=True)  # 專案相關設定
    template_id = Column(String(100), nullable=True)  # 使用的模板ID

    # 統計資訊
    total_videos = Column(Integer, default=0)
    completed_videos = Column(Integer, default=0)

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 關聯
    user = relationship("User", back_populates="projects")
    videos = relationship("Video", back_populates="project", cascade="all, delete-orphan")


class Video(Base):
    """影片模型 - 核心的影片生成實體"""

    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)

    # 影片基本資訊
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING)

    # 生成參數
    topic = Column(String(500), nullable=False)
    style = Column(String(100), default="modern")
    duration_seconds = Column(Integer, default=60)
    platform = Column(String(50), default="tiktok")  # tiktok, youtube, instagram
    language = Column(String(10), default="zh-TW")

    # 內容組件
    script_content = Column(Text, nullable=True)
    voice_style = Column(String(100), default="natural")
    music_style = Column(String(100), nullable=True)
    image_style = Column(String(100), default="realistic")

    # 檔案路徑
    final_video_url = Column(String(1000), nullable=True)
    audio_url = Column(String(1000), nullable=True)
    thumbnail_url = Column(String(1000), nullable=True)

    # 處理狀態和統計
    progress_percentage = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    processing_time_seconds = Column(Integer, nullable=True)

    # 性能指標
    file_size_mb = Column(Float, nullable=True)
    video_quality = Column(String(20), default="1080p")
    frame_rate = Column(Integer, default=30)

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # 關聯
    user = relationship("User", back_populates="videos")
    project = relationship("Project", back_populates="videos")
    assets = relationship("VideoAsset", back_populates="video", cascade="all, delete-orphan")
    tasks = relationship("ProcessingTask", back_populates="video", cascade="all, delete-orphan")
    social_posts = relationship("SocialPost", back_populates="video", cascade="all, delete-orphan")


class VideoAsset(Base):
    """影片資產模型 - 儲存影片生成過程中的各種資產"""

    __tablename__ = "video_assets"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)

    # 資產基本資訊
    asset_type = Column(String(50), nullable=False)  # script, audio, image, music, video_segment
    asset_name = Column(String(255), nullable=False)
    file_url = Column(String(1000), nullable=False)

    # 檔案資訊
    file_size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    duration_seconds = Column(Float, nullable=True)  # 用於音頻和影片

    # 處理參數和中繼資料
    generation_parameters = Column(JSON, nullable=True)
    asset_metadata = Column(JSON, nullable=True)  # 重命名避免與SQLAlchemy衝突

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 關聯
    video = relationship("Video", back_populates="assets")


class ProcessingTask(Base):
    """處理任務模型 - 追蹤異步處理任務"""

    __tablename__ = "processing_tasks"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 任務基本資訊
    task_type = Column(String(100), nullable=False)  # script_generation, voice_synthesis, etc.
    task_name = Column(String(255), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.QUEUED)

    # 任務參數和結果
    input_parameters = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # 執行資訊
    worker_id = Column(String(100), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 關聯
    video = relationship("Video", back_populates="tasks")
    user = relationship("User")


# ============================================================================
# 社交媒體和發布相關模型
# ============================================================================


class SocialAccount(Base):
    """社交媒體帳戶模型"""

    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 帳戶資訊
    platform = Column(String(50), nullable=False)  # youtube, tiktok, instagram, facebook
    account_name = Column(String(255), nullable=False)
    account_id = Column(String(255), nullable=False)

    # 認證資訊 (加密存儲)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)

    # 狀態
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # 統計資訊
    posts_count = Column(Integer, default=0)
    followers_count = Column(Integer, default=0)

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_sync = Column(DateTime(timezone=True), nullable=True)

    # 關聯
    user = relationship("User")
    posts = relationship("SocialPost", back_populates="social_account")


class SocialPost(Base):
    """社交媒體發布記錄模型"""

    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    social_account_id = Column(Integer, ForeignKey("social_accounts.id"), nullable=False)

    # 發布資訊
    post_title = Column(String(500), nullable=True)
    post_description = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)  # 以逗號分隔的標籤

    # 外部平台資訊
    external_post_id = Column(String(255), nullable=True)
    external_url = Column(String(1000), nullable=True)

    # 狀態
    status = Column(String(50), default="draft")  # draft, scheduled, published, failed
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)

    # 統計資訊 (從平台同步)
    views_count = Column(Integer, default=0)
    likes_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 關聯
    video = relationship("Video", back_populates="social_posts")
    social_account = relationship("SocialAccount", back_populates="posts")


# ============================================================================
# 趨勢和分析相關模型
# ============================================================================


class TrendTopic(Base):
    """趋势话题模型"""

    __tablename__ = "trend_topics"

    id = Column(Integer, primary_key=True, index=True)

    # 話題基本資訊
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)

    # 趨勢指標
    trending_score = Column(Float, default=0.0)
    search_volume = Column(Integer, default=0)
    competition_level = Column(String(20), default="medium")  # low, medium, high

    # 關鍵字和標籤
    keywords = Column(JSON, nullable=True)  # 相關關鍵字列表
    hashtags = Column(JSON, nullable=True)  # 推薦標籤列表

    # 平台特定數據
    platform_data = Column(JSON, nullable=True)  # 各平台的特定數據

    # 時效性
    peak_time = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UserAnalytics(Base):
    """用戶分析數據模型"""

    __tablename__ = "user_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 分析時間範圍
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly

    # 使用統計
    videos_created = Column(Integer, default=0)
    videos_completed = Column(Integer, default=0)
    api_calls = Column(Integer, default=0)

    # 內容統計
    total_watch_time = Column(Integer, default=0)  # 秒
    total_views = Column(Integer, default=0)
    total_likes = Column(Integer, default=0)
    total_shares = Column(Integer, default=0)

    # 存儲統計
    storage_used_mb = Column(Float, default=0.0)
    bandwidth_used_mb = Column(Float, default=0.0)

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 關聯
    user = relationship("User")


# ============================================================================
# 支付和訂閱相關模型
# ============================================================================


class Subscription(Base):
    """訂閱模型"""

    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 訂閱資訊
    plan_id = Column(String(100), nullable=False)
    plan_name = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")

    # 外部支付系統資訊
    external_subscription_id = Column(String(255), nullable=True)  # Stripe subscription ID
    payment_method_id = Column(String(255), nullable=True)

    # 訂閱狀態
    status = Column(String(50), default="active")  # active, cancelled, expired, past_due
    trial_end = Column(DateTime(timezone=True), nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)

    # 限制和配額
    video_quota = Column(Integer, default=10)  # 每月影片配額
    storage_quota_gb = Column(Integer, default=5)  # 存儲配額
    api_quota = Column(Integer, default=1000)  # API 呼叫配額

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    # 關聯
    user = relationship("User")
    payments = relationship("Payment", back_populates="subscription")


class Payment(Base):
    """支付記錄模型"""

    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)

    # 支付資訊
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    description = Column(String(500), nullable=True)

    # 外部支付系統資訊
    payment_method = Column(String(50), nullable=False)  # stripe, paypal
    external_payment_id = Column(String(255), nullable=True)
    external_transaction_id = Column(String(255), nullable=True)

    # 支付狀態
    status = Column(String(50), default="pending")  # pending, succeeded, failed, refunded
    payment_date = Column(DateTime(timezone=True), nullable=True)

    # 發票資訊
    invoice_number = Column(String(100), nullable=True)
    receipt_url = Column(String(1000), nullable=True)

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 關聯
    user = relationship("User")
    subscription = relationship("Subscription", back_populates="payments")


# ============================================================================
# 系統和配置相關模型
# ============================================================================


class SystemConfig(Base):
    """系統配置模型"""

    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)

    # 配置資訊
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(50), default="string")  # string, integer, float, boolean, json

    # 配置描述和分組
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    is_public = Column(Boolean, default=False)  # 是否對前端公開

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AuditLog(Base):
    """審計日誌模型"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 操作資訊
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=True)

    # 請求資訊
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    endpoint = Column(String(500), nullable=True)
    http_method = Column(String(10), nullable=True)

    # 詳細資訊
    details = Column(JSON, nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)

    # 結果
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 關聯
    user = relationship("User")


class APIUsage(Base):
    """API使用統計模型"""

    __tablename__ = "api_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # API資訊
    endpoint = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    service_name = Column(String(100), nullable=False)

    # 請求資訊
    request_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # 回應資訊
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    request_size_bytes = Column(Integer, nullable=True)
    response_size_bytes = Column(Integer, nullable=True)

    # 錯誤資訊
    error_message = Column(Text, nullable=True)

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # 關聯
    user = relationship("User")
