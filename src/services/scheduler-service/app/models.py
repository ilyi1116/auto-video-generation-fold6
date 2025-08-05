from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class ScheduledPost(Base):
    __tablename__ = "scheduled_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    video_id = Column(Integer, nullable=False)

    # 平台資訊
    platform = Column(String(50), nullable=False)  # tiktok, youtube, instagram
    platform_account_id = Column(String(100))

    # 排程資訊
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending")  # pending, published, failed, cancelled

    # 內容資訊
    title = Column(String(255))
    description = Column(Text)
    tags = Column(JSON)  # 標籤陣列

    # 平台特定設定
    platform_settings = Column(JSON)  # 各平台特殊設定

    # 發布結果
    post_url = Column(String(500))  # 發布後的 URL
    error_message = Column(Text)  # 錯誤訊息

    # 時間戳記
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    published_at = Column(DateTime)


class PlatformAccount(Base):
    __tablename__ = "platform_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    platform_user_id = Column(String(100), nullable=False)
    platform_username = Column(String(100))

    # 認證資訊
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)

    # 帳號狀態
    is_active = Column(Boolean, default=True)
    is_connected = Column(Boolean, default=True)

    # 時間戳記
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
