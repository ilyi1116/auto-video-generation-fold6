"""
創業者排程管理器 API 路由
提供排程管理的 RESTful API 介面
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..auth import verify_token
from ..entrepreneur_scheduler import (
    EntrepreneurScheduler,
    SchedulerConfig,
    TaskStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局排程管理器實例
scheduler_instance: Optional[EntrepreneurScheduler] = None


# Pydantic 模型定義
class SchedulerConfigModel(BaseModel):
    """排程器配置模型"""

    enabled: bool = Field(default=True, description="是否啟用排程器")
    work_hours_start: str = Field(default="09:00", description="工作開始時間")
    work_hours_end: str = Field(default="18:00", description="工作結束時間")
    timezone: str = Field(default="Asia/Taipei", description="時區")
    check_interval_minutes: int = Field(
        default=30, ge=1, le=1440, description="檢查間隔（分鐘）"
    )
    daily_video_limit: int = Field(
        default=5, ge=1, le=50, description="每日影片限制"
    )
    daily_budget_limit: float = Field(
        default=20.0, ge=1.0, le=1000.0, description="每日預算限制"
    )
    max_concurrent_tasks: int = Field(
        default=3, ge=1, le=10, description="最大並行任務數"
    )
    retry_attempts: int = Field(default=3, ge=1, le=10, description="重試次數")
    retry_delay_minutes: int = Field(
        default=5, ge=1, le=60, description="重試延遲（分鐘）"
    )


class ScheduleTaskRequest(BaseModel):
    """排程任務請求"""

    user_id: str = Field(..., description="用戶ID")
    video_count: int = Field(default=1, ge=1, le=10, description="影片數量")
    categories: List[str] = Field(
        default=["technology"], description="內容類別"
    )
    platforms: List[str] = Field(default=["tiktok"], description="目標平台")
    quality_threshold: float = Field(
        default=0.7, ge=0.1, le=1.0, description="品質門檻"
    )
    budget_per_video: float = Field(
        default=3.0, ge=0.5, le=20.0, description="單影片預算"
    )


class TaskStatusResponse(BaseModel):
    """任務狀態回應"""

    task_id: str
    user_id: str
    status: str
    scheduled_time: datetime
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int
    error_message: Optional[str] = None


class SchedulerStatusResponse(BaseModel):
    """排程器狀態回應"""

    is_running: bool
    daily_stats: Dict[str, Any]
    active_tasks_count: int
    scheduled_tasks_count: int
    next_execution_time: str
    config: Dict[str, Any]


def get_scheduler() -> EntrepreneurScheduler:
    """獲取排程管理器實例"""
    global scheduler_instance
    if scheduler_instance is None:
        # 使用預設配置創建排程器
        default_config = SchedulerConfig()
        scheduler_instance = EntrepreneurScheduler(default_config)
    return scheduler_instance


@router.post("/configure")
async def configure_scheduler(
    config: SchedulerConfigModel, current_user: dict = Depends(verify_token)
):
    """配置排程器"""
    try:
        global scheduler_instance

        # 如果排程器正在運行，先停止
        if scheduler_instance and scheduler_instance.is_running:
            await scheduler_instance.stop()

        # 創建新配置
        scheduler_config = SchedulerConfig(
            enabled=config.enabled,
            work_hours_start=config.work_hours_start,
            work_hours_end=config.work_hours_end,
            timezone=config.timezone,
            check_interval_minutes=config.check_interval_minutes,
            daily_video_limit=config.daily_video_limit,
            daily_budget_limit=config.daily_budget_limit,
            max_concurrent_tasks=config.max_concurrent_tasks,
            retry_attempts=config.retry_attempts,
            retry_delay_minutes=config.retry_delay_minutes,
        )

        # 創建新的排程器實例
        scheduler_instance = EntrepreneurScheduler(scheduler_config)

        # 如果啟用，立即啟動
        if config.enabled:
            await scheduler_instance.start()

        logger.info(f"排程器已重新配置 - 用戶: {current_user.get('sub')}")

        return {
            "message": "排程器配置已更新",
            "config": config.dict(),
            "status": "running" if config.enabled else "stopped",
        }

    except Exception as e:
        logger.error(f"配置排程器失敗: {e}")
        raise HTTPException(status_code=500, detail=f"配置失敗: {str(e)}")


@router.post("/start")
async def start_scheduler(current_user: dict = Depends(verify_token)):
    """啟動排程器"""
    try:
        scheduler = get_scheduler()

        if scheduler.is_running:
            return {"message": "排程器已在運行中", "status": "running"}

        await scheduler.start()

        logger.info(f"排程器已啟動 - 用戶: {current_user.get('sub')}")

        return {
            "message": "排程器已啟動",
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"啟動排程器失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟動失敗: {str(e)}")


@router.post("/stop")
async def stop_scheduler(current_user: dict = Depends(verify_token)):
    """停止排程器"""
    try:
        scheduler = get_scheduler()

        if not scheduler.is_running:
            return {"message": "排程器已停止", "status": "stopped"}

        await scheduler.stop()

        logger.info(f"排程器已停止 - 用戶: {current_user.get('sub')}")

        return {
            "message": "排程器已停止",
            "status": "stopped",
            "stopped_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"停止排程器失敗: {e}")
        raise HTTPException(status_code=500, detail=f"停止失敗: {str(e)}")


@router.post("/pause")
async def pause_scheduler(current_user: dict = Depends(verify_token)):
    """暫停排程器"""
    try:
        scheduler = get_scheduler()
        await scheduler.pause()

        return {
            "message": "排程器已暫停",
            "status": "paused",
            "paused_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"暫停排程器失敗: {e}")
        raise HTTPException(status_code=500, detail=f"暫停失敗: {str(e)}")


@router.post("/resume")
async def resume_scheduler(current_user: dict = Depends(verify_token)):
    """恢復排程器"""
    try:
        scheduler = get_scheduler()
        await scheduler.resume()

        return {
            "message": "排程器已恢復",
            "status": "running",
            "resumed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"恢復排程器失敗: {e}")
        raise HTTPException(status_code=500, detail=f"恢復失敗: {str(e)}")


@router.post("/schedule-task")
async def schedule_entrepreneur_task(
    request: ScheduleTaskRequest, current_user: dict = Depends(verify_token)
):
    """排程創業者任務"""
    try:
        scheduler = get_scheduler()
        user_id = current_user.get("sub", request.user_id)

        # 準備任務配置
        task_config = {
            "user_id": user_id,
            "video_count": request.video_count,
            "categories": request.categories,
            "platforms": request.platforms,
            "quality_threshold": request.quality_threshold,
            "budget_per_video": request.budget_per_video,
        }

        # 排程任務
        task_id = await scheduler.schedule_entrepreneur_task(task_config)

        logger.info(f"創業者任務已排程: {task_id} - 用戶: {user_id}")

        return {
            "task_id": task_id,
            "message": "任務已排程",
            "scheduled_time": datetime.utcnow().isoformat(),
            "config": task_config,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"排程任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"排程任務失敗: {str(e)}")


@router.get("/status", response_model=SchedulerStatusResponse)
async def get_scheduler_status(current_user: dict = Depends(verify_token)):
    """獲取排程器狀態"""
    try:
        scheduler = get_scheduler()
        status = scheduler.get_status()

        return SchedulerStatusResponse(**status)

    except Exception as e:
        logger.error(f"獲取排程器狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取狀態失敗: {str(e)}")


@router.get("/tasks")
async def list_scheduled_tasks(
    status_filter: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: dict = Depends(verify_token),
):
    """列出排程任務"""
    try:
        scheduler = get_scheduler()
        user_id = current_user.get("sub", "unknown")

        # 篩選用戶的任務
        user_tasks = []
        for task in scheduler.scheduled_tasks.values():
            if task.user_id == user_id:
                if status_filter is None or task.status.value == status_filter:
                    user_tasks.append(
                        {
                            "task_id": task.task_id,
                            "status": task.status.value,
                            "scheduled_time": task.scheduled_time.isoformat(),
                            "created_at": task.created_at.isoformat(),
                            "retry_count": task.retry_count,
                            "config": task.config,
                        }
                    )

        # 排序和分頁
        user_tasks.sort(key=lambda x: x["created_at"], reverse=True)
        total = len(user_tasks)
        tasks = user_tasks[offset : offset + limit]  # noqa: E203

        return {
            "tasks": tasks,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"列出任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"列出任務失敗: {str(e)}")


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str, current_user: dict = Depends(verify_token)
):
    """獲取任務狀態"""
    try:
        scheduler = get_scheduler()
        user_id = current_user.get("sub", "unknown")

        task = scheduler.scheduled_tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任務不存在")

        # 檢查權限
        if task.user_id != user_id:
            raise HTTPException(status_code=403, detail="無權限訪問此任務")

        return TaskStatusResponse(
            task_id=task.task_id,
            user_id=task.user_id,
            status=task.status.value,
            scheduled_time=task.scheduled_time,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            retry_count=task.retry_count,
            error_message=task.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取任務狀態失敗: {e}")
        raise HTTPException(
            status_code=500, detail=f"獲取任務狀態失敗: {str(e)}"
        )


@router.delete("/tasks/{task_id}")
async def cancel_task(
    task_id: str, current_user: dict = Depends(verify_token)
):
    """取消任務"""
    try:
        scheduler = get_scheduler()
        user_id = current_user.get("sub", "unknown")

        task = scheduler.scheduled_tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任務不存在")

        # 檢查權限
        if task.user_id != user_id:
            raise HTTPException(status_code=403, detail="無權限操作此任務")

        # 只能取消未開始的任務
        if task.status not in [TaskStatus.SCHEDULED]:
            raise HTTPException(status_code=400, detail="只能取消未開始的任務")

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()

        return {
            "message": "任務已取消",
            "task_id": task_id,
            "cancelled_at": task.completed_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"取消任務失敗: {str(e)}")


@router.post("/cleanup")
async def cleanup_completed_tasks(
    max_age_hours: int = Field(default=24, ge=1, le=720),
    current_user: dict = Depends(verify_token),
):
    """清理已完成任務"""
    try:
        scheduler = get_scheduler()

        cleaned_count = await scheduler.cleanup_completed_tasks(max_age_hours)

        return {
            "message": f"已清理 {cleaned_count} 個任務",
            "cleaned_count": cleaned_count,
            "max_age_hours": max_age_hours,
        }

    except Exception as e:
        logger.error(f"清理任務失敗: {e}")
        raise HTTPException(status_code=500, detail=f"清理任務失敗: {str(e)}")


@router.get("/health")
async def scheduler_health_check():
    """排程器健康檢查"""
    try:
        scheduler = get_scheduler()

        return {
            "status": "healthy",
            "service": "entrepreneur_scheduler",
            "is_running": scheduler.is_running,
            "active_tasks": scheduler.current_tasks_count,
            "scheduled_tasks": len(scheduler.scheduled_tasks),
            "daily_stats": scheduler.daily_stats,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
