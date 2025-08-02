"""
Video Processing Module

This module handles video composition, rendering, and media processing:
- Video composition from AI-generated components
- Multi-platform video rendering and optimization
- Media file management and storage
- TDD-driven workflow management
"""

from .composer import (
    CompositionRequest,
    CompositionResult,
    FinalRenderResult,
    SceneComposition,
    VideoComposer,
)
from .pipeline_executor import PipelineExecutor, PipelineResult
from .progress_tracker import ProgressStatus, ProgressTracker
from .resource_manager import ResourceManager
from .time_estimator import WorkflowTimeEstimator

# TDD 實作的新功能
from .workflow_engine import (
    VideoWorkflowEngine,
    VideoWorkflowRequest,
    VideoWorkflowResult,
)

__all__ = [
    # 原有功能
    "VideoComposer",
    "SceneComposition",
    "CompositionRequest",
    "CompositionResult",
    "FinalRenderResult",
    # TDD 新功能
    "VideoWorkflowEngine",
    "VideoWorkflowRequest",
    "VideoWorkflowResult",
    "PipelineExecutor",
    "PipelineResult",
    "ProgressTracker",
    "ProgressStatus",
    "WorkflowTimeEstimator",
    "ResourceManager",
]
