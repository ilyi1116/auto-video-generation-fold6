"""
影片生成工作流程引擎 - 重構版

TDD Refactor 階段：在保持測試通過的前提下改善程式碼結構
遵循 Clean Code 和 SOLID 原則
"""

import logging
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Protocol

# 設定日誌
logger = logging.getLogger(__name__)


class WorkflowStatus(Enum):
    """工作流程狀態枚舉"""

    INITIALIZED = "initialized"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class WorkflowStage(Enum):
    """工作流程階段枚舉"""

    PLANNING = "planning"
    SCRIPT_GENERATION = "script_generation"
    IMAGE_CREATION = "image_creation"
    VOICE_SYNTHESIS = "voice_synthesis"
    VIDEO_COMPOSITION = "video_composition"
    FINALIZATION = "finalization"


class VideoWorkflowRequest:
    """影片工作流程請求模型 - 重構版"""

    def __init__(
        self,
        topic: str,
        target_platform: str = "youtube",
        workflow_type: str = "standard",
        quality_level: str = "high",
        expected_duration: int = 60,
        user_preferences: Optional[Dict] = None,
    ):
        self._validate_inputs(
            topic,
            target_platform,
            workflow_type,
            quality_level,
            expected_duration,
        )

        self.topic = topic
        self.target_platform = target_platform
        self.workflow_type = workflow_type
        self.quality_level = quality_level
        self.expected_duration = expected_duration
        self.user_preferences = user_preferences or {}
        self.created_at = datetime.utcnow()

    def _validate_inputs(
        self,
        topic: str,
        target_platform: str,
        workflow_type: str,
        quality_level: str,
        expected_duration: int,
    ) -> None:
        """驗證輸入參數"""
        if not topic or len(topic.strip()) == 0:
            raise ValueError("Topic cannot be empty")

        valid_platforms = {"youtube", "tiktok", "instagram", "facebook"}
        if target_platform not in valid_platforms:
            raise ValueError(
                f"Invalid platform. Must be one of: {valid_platforms}"
            )

        valid_workflow_types = {"standard", "quick", "custom"}
        if workflow_type not in valid_workflow_types:
            raise ValueError(
                f"Invalid workflow type. Must be one of: \
                    {valid_workflow_types}"
            )

        valid_quality_levels = {"low", "medium", "high", "ultra"}
        if quality_level not in valid_quality_levels:
            raise ValueError(
                f"Invalid quality level. Must be one of: \
                    {valid_quality_levels}"
            )

        if expected_duration <= 0:
            raise ValueError("Expected duration must be positive")

    def to_dict(self) -> Dict:
        """轉換為字典格式"""
        return {
            "topic": self.topic,
            "target_platform": self.target_platform,
            "workflow_type": self.workflow_type,
            "quality_level": self.quality_level,
            "expected_duration": self.expected_duration,
            "user_preferences": self.user_preferences,
            "created_at": self.created_at.isoformat(),
        }


class VideoWorkflowResult:
    """影片工作流程結果模型 - 重構版"""

    def __init__(
        self,
        workflow_id: str,
        status: WorkflowStatus,
        current_stage: WorkflowStage,
        progress_percentage: int,
        estimated_completion: datetime,
        generated_assets: Optional[Dict] = None,
        error_message: Optional[str] = None,
    ):
        self.workflow_id = workflow_id
        self.status = status
        self.current_stage = current_stage
        self.progress_percentage = self._validate_progress(progress_percentage)
        self.estimated_completion = estimated_completion
        self.generated_assets = generated_assets or {}
        self.error_message = error_message
        self.updated_at = datetime.utcnow()

    def _validate_progress(self, progress: int) -> int:
        """驗證進度百分比"""
        return max(0, min(100, progress))

    def update_progress(
        self,
        stage: WorkflowStage,
        progress: int,
        assets: Optional[Dict] = None,
    ) -> None:
        """更新進度"""
        self.current_stage = stage
        self.progress_percentage = self._validate_progress(progress)
        if assets:
            self.generated_assets.update(assets)
        self.updated_at = datetime.utcnow()

        # 根據進度自動更新狀態
        if progress >= 100:
            self.status = WorkflowStatus.COMPLETED
        elif progress > 0:
            self.status = WorkflowStatus.IN_PROGRESS


class WorkflowRepository(Protocol):
    """工作流程儲存庫協議"""

    def save(
        self,
        workflow_id: str,
        request: VideoWorkflowRequest,
        result: VideoWorkflowResult,
        user_id: str,
    ) -> None:
        """儲存工作流程"""

    def get(self, workflow_id: str) -> Optional[Dict]:
        """取得工作流程"""

    def delete(self, workflow_id: str) -> None:
        """刪除工作流程"""


class InMemoryWorkflowRepository:
    """記憶體工作流程儲存庫 - 簡單實作"""

    def __init__(self):
        self._workflows: Dict[str, Dict] = {}

    def save(
        self,
        workflow_id: str,
        request: VideoWorkflowRequest,
        result: VideoWorkflowResult,
        user_id: str,
    ) -> None:
        """儲存工作流程"""
        self._workflows[workflow_id] = {
            "request": request,
            "result": result,
            "user_id": user_id,
            "created_at": datetime.utcnow(),
        }
        logger.info(f"Workflow {workflow_id} saved for user {user_id}")

    def get(self, workflow_id: str) -> Optional[Dict]:
        """取得工作流程"""
        return self._workflows.get(workflow_id)

    def delete(self, workflow_id: str) -> None:
        """刪除工作流程"""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            logger.info(f"Workflow {workflow_id} deleted")


class WorkflowIdGenerator:
    """工作流程 ID 生成器"""

    @staticmethod
    def generate() -> str:
        """生成唯一的工作流程 ID"""
        return f"workflow_{uuid.uuid4().hex[:12]}"


class CompletionTimeEstimator:
    """完成時間估算器 - 重構版"""

    def __init__(self):
        self._base_estimates = {
            "quick": 2.0,  # 分鐘
            "standard": 5.0,
            "custom": 8.0,
        }

        self._quality_multipliers = {
            "low": 0.6,
            "medium": 1.0,
            "high": 1.4,
            "ultra": 2.0,
        }

        self._duration_multipliers = {
            (0, 30): 0.8,  # 短片
            (31, 300): 1.0,  # 中等長度
            (301, float("inf")): 1.5,  # 長片
        }

    def estimate(self, request: VideoWorkflowRequest) -> datetime:
        """估算完成時間"""
        base_minutes = self._base_estimates.get(request.workflow_type, 5.0)

        # 品質調整
        quality_multiplier = self._quality_multipliers.get(
            request.quality_level, 1.0
        )
        base_minutes *= quality_multiplier

        # 長度調整
        duration_multiplier = self._get_duration_multiplier(
            request.expected_duration
        )
        base_minutes *= duration_multiplier

        # 確保最小時間
        base_minutes = max(base_minutes, 0.5)

        return datetime.utcnow() + timedelta(minutes=base_minutes)

    def _get_duration_multiplier(self, duration: int) -> float:
        """取得長度乘數"""
        for (
            min_dur,
            max_dur,
        ), multiplier in self._duration_multipliers.items():
            if min_dur <= duration <= max_dur:
                return multiplier
        return 1.0


class VideoWorkflowEngine:
    """影片工作流程引擎 - 重構版

    遵循單一責任原則和依賴注入原則
    """

    def __init__(
        self,
        repository: Optional[WorkflowRepository] = None,
        id_generator: Optional[WorkflowIdGenerator] = None,
        time_estimator: Optional[CompletionTimeEstimator] = None,
    ):
        self._repository = repository or InMemoryWorkflowRepository()
        self._id_generator = id_generator or WorkflowIdGenerator()
        self._time_estimator = time_estimator or CompletionTimeEstimator()

        logger.info("VideoWorkflowEngine initialized")

    def initialize_workflow(
        self, request: VideoWorkflowRequest, user_id: str
    ) -> VideoWorkflowResult:
        """初始化工作流程"""
        try:
            workflow_id = self._id_generator.generate()
            estimated_completion = self._time_estimator.estimate(request)

            result = VideoWorkflowResult(
                workflow_id=workflow_id,
                status=WorkflowStatus.INITIALIZED,
                current_stage=WorkflowStage.PLANNING,
                progress_percentage=0,
                estimated_completion=estimated_completion,
            )

            self._repository.save(workflow_id, request, result, user_id)

            logger.info(
                f"Workflow {workflow_id} initialized for user {user_id}"
            )
            return result

        except Exception as e:
            logger.error(f"Failed to initialize workflow: {str(e)}")
            raise

    def execute_workflow(self, workflow_id: str) -> VideoWorkflowResult:
        """執行工作流程"""
        workflow_data = self._repository.get(workflow_id)
        if not workflow_data:
            raise ValueError(f"Workflow {workflow_id} not found")

        result = workflow_data["result"]

        try:
            # 模擬執行各階段
            self._execute_stages(result)

            logger.info(f"Workflow {workflow_id} completed successfully")
            return result

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.error_message = f"Workflow execution failed: {str(e)}"
            logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            return result

    def _execute_stages(self, result: VideoWorkflowResult) -> None:
        """執行工作流程各階段"""
        stages = [
            (WorkflowStage.SCRIPT_GENERATION, 25),
            (WorkflowStage.IMAGE_CREATION, 50),
            (WorkflowStage.VOICE_SYNTHESIS, 75),
            (WorkflowStage.VIDEO_COMPOSITION, 100),
        ]

        for stage, progress in stages:
            result.update_progress(
                stage=stage,
                progress=progress,
                assets=(
                    self._generate_mock_assets(result.workflow_id)
                    if progress == 100
                    else None
                ),
            )

    def _generate_mock_assets(self, workflow_id: str) -> Dict:
        """生成模擬資產"""
        return {
            "video_url": f"https://example.com/video_{workflow_id}.mp4",
            "thumbnail_url": f"https://example.com/thumb_{workflow_id}.jpg",
        }

    def cancel_workflow(self, workflow_id: str) -> VideoWorkflowResult:
        """取消工作流程"""
        workflow_data = self._repository.get(workflow_id)
        if not workflow_data:
            raise ValueError(f"Workflow {workflow_id} not found")

        result = workflow_data["result"]
        result.status = WorkflowStatus.CANCELLED
        result.error_message = "Workflow cancelled by user"

        logger.info(f"Workflow {workflow_id} cancelled")
        return result

    def cleanup_workflow(self, workflow_id: str) -> None:
        """清理工作流程"""
        self._repository.delete(workflow_id)
        logger.info(f"Workflow {workflow_id} cleaned up")

    @property
    def workflows(self) -> Dict:
        """取得所有工作流程（用於測試兼容性）"""
        if hasattr(self._repository, "_workflows"):
            return self._repository._workflows
        return {}
