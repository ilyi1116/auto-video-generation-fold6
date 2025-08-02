"""
創業者模式工作流程 API 路由
提供創業者自動化影片生成的 RESTful API 介面
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ..auth import verify_token
from ..video.entrepreneur_workflow_engine import (
    EntrepreneurWorkflowEngine,
    EntrepreneurWorkflowConfig,
    EntrepreneurWorkflowRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局工作流程引擎實例
workflow_engine = EntrepreneurWorkflowEngine()


# Pydantic 模型定義
class WorkflowConfigRequest(BaseModel):
    """工作流程配置請求模型"""

    daily_video_count: int = Field(
        default=3, ge=1, le=20, description="每日影片數量限制"
    )
    target_categories: List[str] = Field(
        default=["technology", "entertainment", "lifestyle"],
        description="目標內容類別",
    )
    target_platforms: List[str] = Field(
        default=["tiktok", "youtube-shorts"], description="目標平台"
    )
    video_duration: int = Field(
        default=30, ge=15, le=180, description="影片長度（秒）"
    )
    language: str = Field(default="zh-TW", description="內容語言")
    min_trend_score: float = Field(
        default=0.7, ge=0.1, le=1.0, description="最低趨勢分數"
    )
    content_quality_threshold: float = Field(
        default=0.8, ge=0.1, le=1.0, description="內容品質門檻"
    )
    monetization_threshold: float = Field(
        default=0.6, ge=0.1, le=1.0, description="獲利潛力門檻"
    )
    daily_budget: float = Field(
        default=10.0, ge=1.0, le=1000.0, description="每日預算限制（USD）"
    )
    cost_per_video_limit: float = Field(
        default=5.0, ge=0.5, le=50.0, description="單部影片成本限制（USD）"
    )
    stop_on_budget_exceeded: bool = Field(
        default=True, description="超出預算時是否停止"
    )
    operating_hours: Dict[str, str] = Field(
        default={"start": "09:00", "end": "18:00"}, description="運行時間"
    )
    max_workflow_duration: int = Field(
        default=1800, ge=300, le=7200, description="最大工作流程時間（秒）"
    )
    auto_publish: bool = Field(default=False, description="是否自動發布")
    scheduled_publishing: bool = Field(
        default=True, description="是否使用定時發布"
    )
    optimal_publishing_times: List[str] = Field(
        default=["10:00", "14:00", "18:00"], description="最佳發布時間"
    )
    retry_attempts: int = Field(default=3, ge=1, le=10, description="重試次數")
    parallel_workflows: int = Field(
        default=2, ge=1, le=5, description="並行工作流程數量"
    )
    quality_check_enabled: bool = Field(
        default=True, description="是否啟用品質檢查"
    )


class CreateWorkflowRequest(BaseModel):
    """創建工作流程請求"""

    workflow_type: str = Field(
        default="entrepreneur_auto", description="工作流程類型"
    )
    config: WorkflowConfigRequest = Field(description="工作流程配置")
    priority: int = Field(
        default=1, ge=1, le=3, description="優先級（1=高, 2=中, 3=低）"
    )
    tags: List[str] = Field(default=[], description="標籤")
    custom_requirements: Dict[str, Any] = Field(
        default={}, description="自定義需求"
    )


class WorkflowStatusResponse(BaseModel):
    """工作流程狀態回應"""

    workflow_id: str
    status: str
    current_stage: str
    progress_percentage: int
    estimated_completion: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None


class WorkflowResultResponse(BaseModel):
    """工作流程結果回應"""

    workflow_id: str
    status: str
    current_stage: str
    progress_percentage: int
    generated_assets: Dict[str, Any]
    metrics: Dict[str, Any]
    stage_outputs: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None


class DailyStatsResponse(BaseModel):
    """每日統計回應"""

    videos_generated: int
    total_cost: float
    success_count: int
    failure_count: int
    success_rate: float
    average_cost_per_video: float
    last_updated: str


@router.post("/create", response_model=Dict[str, str])
async def create_entrepreneur_workflow(
    request: CreateWorkflowRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_token),
):
    """創建創業者模式工作流程"""
    try:
        user_id = current_user.get("sub", "unknown")

        # 轉換配置
        config = EntrepreneurWorkflowConfig(
            daily_video_count=request.config.daily_video_count,
            target_categories=request.config.target_categories,
            target_platforms=request.config.target_platforms,
            video_duration=request.config.video_duration,
            language=request.config.language,
            min_trend_score=request.config.min_trend_score,
            content_quality_threshold=request.config.content_quality_threshold,
            monetization_threshold=request.config.monetization_threshold,
            daily_budget=request.config.daily_budget,
            cost_per_video_limit=request.config.cost_per_video_limit,
            stop_on_budget_exceeded=request.config.stop_on_budget_exceeded,
            operating_hours=request.config.operating_hours,
            max_workflow_duration=request.config.max_workflow_duration,
            auto_publish=request.config.auto_publish,
            scheduled_publishing=request.config.scheduled_publishing,
            optimal_publishing_times=request.config.optimal_publishing_times,
            retry_attempts=request.config.retry_attempts,
            parallel_workflows=request.config.parallel_workflows,
            quality_check_enabled=request.config.quality_check_enabled,
        )

        # 創建工作流程請求
        workflow_request = EntrepreneurWorkflowRequest(
            user_id=user_id,
            workflow_type=request.workflow_type,
            config=config,
            priority=request.priority,
            tags=request.tags,
            custom_requirements=request.custom_requirements,
        )

        # 創建工作流程
        workflow_id = await workflow_engine.create_workflow(workflow_request)

        # 在背景執行工作流程
        background_tasks.add_task(
            workflow_engine.execute_workflow, workflow_id
        )

        logger.info(f"創業者工作流程已創建: {workflow_id} - 用戶: {user_id}")

        return {
            "workflow_id": workflow_id,
            "message": "工作流程已創建並開始執行",
            "status": "created",
        }

    except Exception as e:
        logger.error(f"創建工作流程失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"創建工作流程失敗: {str(e)}"
        )


@router.get("/status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str, current_user: dict = Depends(verify_token)
):
    """獲取工作流程狀態"""
    try:
        result = workflow_engine.get_workflow_status(workflow_id)

        if not result:
            raise HTTPException(status_code=404, detail="工作流程不存在")

        # 檢查用戶權限（可選）
        user_id = current_user.get("sub", "unknown")
        if result.request.user_id != user_id:
            raise HTTPException(status_code=403, detail="無權限訪問此工作流程")

        return WorkflowStatusResponse(
            workflow_id=result.workflow_id,
            status=result.status.value,
            current_stage=result.current_stage.value,
            progress_percentage=result.progress_percentage,
            estimated_completion=result.estimated_completion,
            created_at=result.created_at,
            updated_at=result.updated_at,
            error_message=result.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取工作流程狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取狀態失敗: {str(e)}")


@router.get("/result/{workflow_id}", response_model=WorkflowResultResponse)
async def get_workflow_result(
    workflow_id: str, current_user: dict = Depends(verify_token)
):
    """獲取工作流程詳細結果"""
    try:
        result = workflow_engine.get_workflow_status(workflow_id)

        if not result:
            raise HTTPException(status_code=404, detail="工作流程不存在")

        # 檢查用戶權限
        user_id = current_user.get("sub", "unknown")
        if result.request.user_id != user_id:
            raise HTTPException(status_code=403, detail="無權限訪問此工作流程")

        # 轉換生成的資產為字典
        assets_dict = {
            "script": result.generated_assets.script,
            "images": result.generated_assets.images,
            "audio_file": result.generated_assets.audio_file,
            "video_file": result.generated_assets.video_file,
            "thumbnail": result.generated_assets.thumbnail,
            "captions": result.generated_assets.captions,
            "hashtags": result.generated_assets.hashtags,
            "metadata": result.generated_assets.metadata,
        }

        # 轉換指標為字典
        metrics_dict = {
            "start_time": (
                result.metrics.start_time.isoformat()
                if result.metrics.start_time
                else None
            ),
            "end_time": (
                result.metrics.end_time.isoformat()
                if result.metrics.end_time
                else None
            ),
            "total_duration": (
                str(result.metrics.total_duration)
                if result.metrics.total_duration
                else None
            ),
            "stage_durations": result.metrics.stage_durations,
            "cost_breakdown": result.metrics.cost_breakdown,
            "total_cost": result.metrics.total_cost,
            "success_rate": result.metrics.success_rate,
            "quality_score": result.metrics.quality_score,
            "monetization_potential": result.metrics.monetization_potential,
        }

        return WorkflowResultResponse(
            workflow_id=result.workflow_id,
            status=result.status.value,
            current_stage=result.current_stage.value,
            progress_percentage=result.progress_percentage,
            generated_assets=assets_dict,
            metrics=metrics_dict,
            stage_outputs=result.stage_outputs,
            created_at=result.created_at,
            updated_at=result.updated_at,
            error_message=result.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取工作流程結果失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取結果失敗: {str(e)}")


@router.post("/cancel/{workflow_id}")
async def cancel_workflow(
    workflow_id: str, current_user: dict = Depends(verify_token)
):
    """取消工作流程"""
    try:
        result = workflow_engine.get_workflow_status(workflow_id)

        if not result:
            raise HTTPException(status_code=404, detail="工作流程不存在")

        # 檢查用戶權限
        user_id = current_user.get("sub", "unknown")
        if result.request.user_id != user_id:
            raise HTTPException(status_code=403, detail="無權限操作此工作流程")

        success = await workflow_engine.cancel_workflow(workflow_id)

        if success:
            return {"message": "工作流程已取消", "workflow_id": workflow_id}
        else:
            raise HTTPException(status_code=400, detail="無法取消工作流程")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消工作流程失敗: {e}")
        raise HTTPException(status_code=500, detail=f"取消失敗: {str(e)}")


@router.get("/stats/daily", response_model=DailyStatsResponse)
async def get_daily_stats(current_user: dict = Depends(verify_token)):
    """獲取每日統計數據"""
    try:
        stats = workflow_engine.get_daily_stats()

        return DailyStatsResponse(
            videos_generated=stats["videos_generated"],
            total_cost=stats["total_cost"],
            success_count=stats["success_count"],
            failure_count=stats["failure_count"],
            success_rate=stats["success_rate"],
            average_cost_per_video=stats["average_cost_per_video"],
            last_updated=stats["last_updated"],
        )

    except Exception as e:
        logger.error(f"獲取每日統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取統計失敗: {str(e)}")


@router.get("/workflows/list")
async def list_user_workflows(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(verify_token),
):
    """列出用戶的工作流程"""
    try:
        user_id = current_user.get("sub", "unknown")

        # 篩選用戶的工作流程
        user_workflows = []
        for workflow_id, result in workflow_engine.workflows.items():
            if result.request.user_id == user_id:
                if status is None or result.status.value == status:
                    user_workflows.append(
                        {
                            "workflow_id": workflow_id,
                            "status": result.status.value,
                            "current_stage": result.current_stage.value,
                            "progress_percentage": result.progress_percentage,
                            "created_at": result.created_at.isoformat(),
                            "updated_at": result.updated_at.isoformat(),
                            "estimated_completion": (
                                result.estimated_completion.isoformat()
                                if result.estimated_completion
                                else None
                            ),
                        }
                    )

        # 分頁
        total = len(user_workflows)
        workflows = user_workflows[offset:offset + limit]  # noqa: E203

        return {
            "workflows": workflows,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"列出工作流程失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"列出工作流程失敗: {str(e)}"
        )


@router.post("/batch/create")
async def create_batch_workflows(
    request: CreateWorkflowRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(verify_token),
    count: int = Field(default=1, ge=1, le=10),
):
    """批次創建多個工作流程"""
    try:
        user_id = current_user.get("sub", "unknown")

        workflow_ids = []

        for i in range(count):
            # 為每個工作流程添加批次標籤
            batch_request = request.copy(deep=True)
            batch_request.tags.append(
                f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            )
            batch_request.tags.append(f"batch_item_{i + 1}")

            # 轉換配置
            config = EntrepreneurWorkflowConfig(
                daily_video_count=batch_request.config.daily_video_count,
                target_categories=batch_request.config.target_categories,
                target_platforms=batch_request.config.target_platforms,
                video_duration=batch_request.config.video_duration,
                language=batch_request.config.language,
                min_trend_score=batch_request.config.min_trend_score,
                content_quality_threshold=batch_request.config.content_quality_threshold,
                monetization_threshold=batch_request.config.monetization_threshold,
                daily_budget=batch_request.config.daily_budget,
                cost_per_video_limit=batch_request.config.cost_per_video_limit,
                stop_on_budget_exceeded=batch_request.config.stop_on_budget_exceeded,
                operating_hours=batch_request.config.operating_hours,
                max_workflow_duration=batch_request.config.max_workflow_duration,
                auto_publish=batch_request.config.auto_publish,
                scheduled_publishing=batch_request.config.scheduled_publishing,
                optimal_publishing_times=batch_request.config.optimal_publishing_times,
                retry_attempts=batch_request.config.retry_attempts,
                parallel_workflows=batch_request.config.parallel_workflows,
                quality_check_enabled=batch_request.config.quality_check_enabled,
            )

            # 創建工作流程請求
            workflow_request = EntrepreneurWorkflowRequest(
                user_id=user_id,
                workflow_type=batch_request.workflow_type,
                config=config,
                priority=batch_request.priority,
                tags=batch_request.tags,
                custom_requirements=batch_request.custom_requirements,
            )

            # 創建工作流程
            workflow_id = await workflow_engine.create_workflow(
                workflow_request
            )
            workflow_ids.append(workflow_id)

            # 在背景執行工作流程（加入延遲避免同時執行太多）
            background_tasks.add_task(
                execute_workflow_with_delay,
                workflow_id,
                i * 30,  # 每個工作流程間隔30秒
            )

        logger.info(f"批次創建 {count} 個工作流程 - 用戶: {user_id}")

        return {
            "workflow_ids": workflow_ids,
            "message": f"已創建 {count} 個工作流程",
            "total_count": count,
        }

    except Exception as e:
        logger.error(f"批次創建工作流程失敗: {e}")
        raise HTTPException(status_code=500, detail=f"批次創建失敗: {str(e)}")


async def execute_workflow_with_delay(workflow_id: str, delay_seconds: int):
    """延遲執行工作流程"""
    if delay_seconds > 0:
        await asyncio.sleep(delay_seconds)

    await workflow_engine.execute_workflow(workflow_id)


@router.post("/cleanup")
async def cleanup_old_workflows(
    max_age_hours: int = Field(default=24, ge=1, le=168),
    current_user: dict = Depends(verify_token),
):
    """清理舊的工作流程（管理員功能）"""
    try:
        # 這裡可以加入管理員權限檢查
        user_role = current_user.get("role", "user")
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="需要管理員權限")

        cleaned_count = workflow_engine.cleanup_completed_workflows(
            max_age_hours
        )

        return {
            "message": f"已清理 {cleaned_count} 個舊工作流程",
            "cleaned_count": cleaned_count,
            "max_age_hours": max_age_hours,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清理工作流程失敗: {e}")
        raise HTTPException(status_code=500, detail=f"清理失敗: {str(e)}")


@router.get("/health")
async def workflow_engine_health():
    """工作流程引擎健康檢查"""
    try:
        stats = workflow_engine.get_daily_stats()

        return {
            "status": "healthy",
            "engine": "entrepreneur_workflow_engine",
            "active_workflows": len(workflow_engine.running_workflows),
            "total_workflows": len(workflow_engine.workflows),
            "daily_stats": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
