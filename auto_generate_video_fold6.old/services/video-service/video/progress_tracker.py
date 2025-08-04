"""
工作流程進度追蹤器

TDD Green 階段：最小實作讓測試通過
"""

from datetime import datetime


class ProgressStatus:
    """進度狀態 - 最小實作"""

    def __init__(
        self, progress_percentage: int, status: str, current_stage: str
    ):
        self.progress_percentage = progress_percentage
        self.status = status
        self.current_stage = current_stage


class ProgressTracker:
    """進度追蹤器 - 最小實作"""

    def __init__(self):
        self.progress_data = {}

    def update_progress(self, workflow_id: str, stage: str, percentage: int):
        """更新進度 - 最小實作"""
        self.progress_data[workflow_id] = {
            "stage": stage,
            "percentage": percentage,
            "updated_at": datetime.utcnow(),
        }

    def get_current_status(self, workflow_id: str) -> ProgressStatus:
        """取得目前狀態 - 最小實作"""
        if workflow_id not in self.progress_data:
            return ProgressStatus(0, "not_found", "unknown")

        data = self.progress_data[workflow_id]
        status = "completed" if data["percentage"] == 100 else "in_progress"

        return ProgressStatus(
            progress_percentage=data["percentage"],
            status=status,
            current_stage=data["stage"],
        )
