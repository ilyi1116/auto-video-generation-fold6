"""
工作流程時間估算器

TDD Green 階段：最小實作讓測試通過
"""

from datetime import timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .workflow_engine import VideoWorkflowRequest


class WorkflowTimeEstimator:
    """時間估算器 - 最小實作"""

    def estimate_completion_time(self, request) -> timedelta:
        """估算完成時間 - 最小實作讓測試通過"""
        # 基礎估算邏輯
        base_minutes = 2.0

        # 根據影片長度調整
        if hasattr(request, "expected_duration"):
            if request.expected_duration <= 30:  # 短片
                base_minutes = 1.0
            elif request.expected_duration <= 300:  # 中等長度
                base_minutes = 5.0
            else:  # 長片
                base_minutes = 15.0

        # 根據品質調整
        if hasattr(request, "quality_level"):
            if request.quality_level == "low":
                base_minutes *= 0.5
            elif request.quality_level == "ultra":
                base_minutes *= 2.0

        # 根據工作流程類型調整
        if hasattr(request, "workflow_type"):
            if request.workflow_type == "quick":
                base_minutes *= 0.7
            elif request.workflow_type == "custom":
                base_minutes *= 1.5

        # 確保最小時間
        base_minutes = max(base_minutes, 0.5)

        return timedelta(minutes=base_minutes)
