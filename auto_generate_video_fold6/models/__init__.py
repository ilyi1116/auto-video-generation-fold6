"""
統一資料庫模型
Auto Video Generation System - Unified Database Models
"""

from .auth_models import User
from .base import Base
from .scheduler_models import ScheduledTask, TaskExecution
from .storage_models import FileDownload, FileProcessingJob, StoredFile
from .trend_models import (
    KeywordResearch,
    TrendAnalysis,
    TrendingTopic,
    ViralContent,
)
from .video_models import VideoAsset, VideoGeneration, VideoProject

__all__ = [
    "Base",
    # Auth Models
    "User",
    # Trend Models
    "TrendingTopic",
    "KeywordResearch",
    "ViralContent",
    "TrendAnalysis",
    # Storage Models
    "StoredFile",
    "FileProcessingJob",
    "FileDownload",
    # Video Models
    "VideoProject",
    "VideoGeneration",
    "VideoAsset",
    # Scheduler Models
    "ScheduledTask",
    "TaskExecution",
]
