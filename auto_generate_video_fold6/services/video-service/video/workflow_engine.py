"""
影片生成工作流程引擎

TDD Green 階段：實作最小程式碼讓測試通過
遵循 YAGNI (You Aren't Gonna Need It) 原則
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional


class VideoWorkflowRequest:
    """影片工作流程請求模型 - 最小實作"""
    
    def __init__(self, topic: str, target_platform: str = "youtube", 
                 workflow_type: str = "standard", quality_level: str = "high",
                 expected_duration: int = 60, user_preferences: Optional[Dict] = None):
        self.topic = topic
        self.target_platform = target_platform
        self.workflow_type = workflow_type
        self.quality_level = quality_level
        self.expected_duration = expected_duration
        self.user_preferences = user_preferences or {}


class VideoWorkflowResult:
    """影片工作流程結果模型 - 最小實作"""
    
    def __init__(self, workflow_id: str, status: str, current_stage: str,
                 progress_percentage: int, estimated_completion: datetime,
                 generated_assets: Optional[Dict] = None, error_message: Optional[str] = None):
        self.workflow_id = workflow_id
        self.status = status
        self.current_stage = current_stage
        self.progress_percentage = progress_percentage
        self.estimated_completion = estimated_completion
        self.generated_assets = generated_assets or {}
        self.error_message = error_message


class VideoWorkflowEngine:
    """影片工作流程引擎 - 最小實作讓測試通過"""
    
    def __init__(self):
        self.workflows = {}  # 儲存工作流程狀態
    
    def initialize_workflow(self, request: VideoWorkflowRequest, user_id: str) -> VideoWorkflowResult:
        """初始化工作流程 - 最小實作"""
        workflow_id = str(uuid.uuid4())
        estimated_completion = datetime.utcnow() + timedelta(minutes=5)
        
        result = VideoWorkflowResult(
            workflow_id=workflow_id,
            status="initialized",
            current_stage="planning",
            progress_percentage=0,
            estimated_completion=estimated_completion
        )
        
        # 儲存工作流程狀態
        self.workflows[workflow_id] = {
            "request": request,
            "user_id": user_id,
            "result": result,
            "created_at": datetime.utcnow()
        }
        
        return result
    
    def execute_workflow(self, workflow_id: str) -> VideoWorkflowResult:
        """執行工作流程 - 最小實作"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        result = workflow["result"]
        
        # 模擬工作流程執行
        result.status = "completed"
        result.current_stage = "video_composition"
        result.progress_percentage = 100
        result.generated_assets = {
            "video_url": f"https://example.com/video_{workflow_id}.mp4",
            "thumbnail_url": f"https://example.com/thumb_{workflow_id}.jpg"
        }
        
        return result
    
    def cancel_workflow(self, workflow_id: str) -> VideoWorkflowResult:
        """取消工作流程 - 最小實作"""
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.workflows[workflow_id]
        result = workflow["result"]
        
        result.status = "cancelled"
        result.error_message = "Workflow cancelled by user"
        
        return result
    
    def cleanup_workflow(self, workflow_id: str):
        """清理工作流程 - 最小實作"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]