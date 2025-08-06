"""
影片生成相關模型
"""

import uuid
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class VideoProject(Base):
    """影片專案模型"""
    
    __tablename__ = "video_projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True)

    # Project metadata
    title = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    tags = Column(JSON)

    # Project settings  
    target_platform = Column(String(50))  # tiktok, youtube, instagram
    video_style = Column(String(50))  # modern, vintage, minimal, etc.
    aspect_ratio = Column(String(10))  # 9:16, 16:9, 1:1
    duration_target = Column(Integer)  # seconds

    # AI generation settings
    script_tone = Column(String(50))  # professional, casual, funny, etc.
    voice_style = Column(String(50))  # male, female, child, etc.
    music_genre = Column(String(50))  # electronic, acoustic, etc.

    # Project status
    status = Column(String(20), default="draft")  # draft, processing, completed, failed
    progress_percentage = Column(Integer, default=0)
    
    # Project configuration
    generation_config = Column(JSON)  # AI settings, templates, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_generated_at = Column(DateTime(timezone=True))

    # Relationships
    generations = relationship("VideoGeneration", back_populates="project")
    assets = relationship("VideoAsset", back_populates="project")

    def __repr__(self):
        return f"<VideoProject(id={self.id}, title='{self.title}')>"


class VideoGeneration(Base):
    """影片生成記錄模型"""
    
    __tablename__ = "video_generations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("video_projects.id"), nullable=False)
    user_id = Column(String, nullable=False, index=True)

    # Generation metadata
    generation_type = Column(String(50))  # full, script_only, images_only, etc.
    source_keyword = Column(String(255))  # Original keyword/topic
    generated_script = Column(Text)
    
    # AI generation details
    text_model_used = Column(String(50))  # gpt-4, gemini-pro, etc.
    image_model_used = Column(String(50))  # dall-e-3, stable-diffusion, etc.
    voice_model_used = Column(String(50))  # elevenlabs, etc.
    music_model_used = Column(String(50))  # suno, etc.

    # Generation settings
    generation_settings = Column(JSON)
    
    # Results
    output_video_path = Column(String(500))
    output_video_url = Column(String(500))
    thumbnail_path = Column(String(500))
    
    # Quality metrics
    estimated_quality_score = Column(Float, default=0.0)
    viral_potential_score = Column(Float, default=0.0)
    engagement_prediction = Column(Float, default=0.0)
    
    # Generation statistics
    processing_time_seconds = Column(Integer)
    tokens_used = Column(Integer)
    images_generated = Column(Integer)
    audio_duration_seconds = Column(Integer)
    
    # Status and progress
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    progress_percentage = Column(Integer, default=0)
    current_step = Column(String(100))
    error_message = Column(Text)
    
    # Cost tracking
    estimated_cost_usd = Column(Float, default=0.0)
    actual_cost_usd = Column(Float, default=0.0)
    
    # Publishing information
    is_published = Column(Boolean, default=False)
    published_platforms = Column(JSON)
    scheduled_publish_at = Column(DateTime(timezone=True))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    project = relationship("VideoProject", back_populates="generations")

    def __repr__(self):
        return f"<VideoGeneration(id={self.id}, status='{self.status}')>"


class VideoAsset(Base):
    """影片素材模型"""
    
    __tablename__ = "video_assets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("video_projects.id"), nullable=False)
    generation_id = Column(String, ForeignKey("video_generations.id"))
    user_id = Column(String, nullable=False, index=True)

    # Asset metadata
    asset_type = Column(String(50), nullable=False)  # script, image, audio, video, music
    asset_name = Column(String(255))
    asset_description = Column(Text)
    
    # File information
    file_path = Column(String(500))
    file_url = Column(String(500))
    file_size_bytes = Column(Integer)
    mime_type = Column(String(100))
    
    # Asset-specific metadata
    duration_seconds = Column(Integer)  # for audio/video
    dimensions = Column(String(20))  # for images/video (e.g., "1920x1080")
    quality = Column(String(20))  # low, medium, high, ultra
    
    # AI generation metadata
    generation_prompt = Column(Text)
    model_used = Column(String(50))
    generation_parameters = Column(JSON)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime(timezone=True))
    
    # Asset status
    status = Column(String(20), default="active")  # active, archived, deleted
    is_favorite = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("VideoProject", back_populates="assets")

    def __repr__(self):
        return f"<VideoAsset(id={self.id}, asset_type='{self.asset_type}')>"