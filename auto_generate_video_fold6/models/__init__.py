"""
統一資料庫模型
Auto Video Generation System - Unified Database Models
"""

from .auth_models import User
from .trend_models import TrendingTopic, KeywordResearch, ViralContent, TrendAnalysis
from .storage_models import StoredFile, FileProcessingJob, FileDownload
from .video_models import VideoProject, VideoGeneration, VideoAsset
from .scheduler_models import ScheduledTask, TaskExecution
from .base import Base

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