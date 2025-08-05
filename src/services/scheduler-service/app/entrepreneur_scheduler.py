"""
TDD Green 階段: 創業者排程管理器實作

實作最小程式碼讓測試通過，遵循 YAGNI 原則
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任務狀態枚舉"""

    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SchedulerConfig:
    """排程器配置"""

    enabled: bool = True
    work_hours_start: str = "09:00"
    work_hours_end: str = "18:00"
    timezone: str = "Asia/Taipei"
    check_interval_minutes: int = 30
    daily_video_limit: int = 5
    daily_budget_limit: float = 20.0
    max_concurrent_tasks: int = 3
    retry_attempts: int = 3
    retry_delay_minutes: int = 5

    def validate(self) -> bool:
        """驗證配置"""
        # 驗證時間格式
        try:
            start_hour, start_min = map(int, self.work_hours_start.split(":"))
            end_hour, end_min = map(int, self.work_hours_end.split(":"))

            if not (0 <= start_hour <= 23 and 0 <= start_min <= 59):
                raise ValueError("時間格式錯誤")
            if not (0 <= end_hour <= 23 and 0 <= end_min <= 59):
                raise ValueError("時間格式錯誤")
        except Exception:
            raise ValueError("時間格式錯誤")

        # 驗證限制值
        if self.daily_video_limit <= 0 or self.daily_budget_limit <= 0:
            raise ValueError("每日限制必須大於 0")

        return True


@dataclass
class ScheduledTask:
    """排程任務模型"""

    task_id: str
    user_id: str
    config: Dict[str, Any]
    scheduled_time: datetime
    status: TaskStatus = TaskStatus.SCHEDULED
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

    def mark_as_running(self):
        """標記為執行中"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.utcnow()

    def mark_as_completed(self, result: Dict[str, Any]):
        """標記為完成"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result

    def mark_as_failed(self, error_message: str):
        """標記為失敗"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message


class EntrepreneurScheduler:
    """創業者排程管理器 - TDD Green 實作"""

    def __init__(self, config: SchedulerConfig):
        config.validate()  # 驗證配置
        self.config = config
        self.is_running = False
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.current_tasks_count = 0
        self.daily_stats = {
            "videos_generated": 0,
            "budget_used": 0.0,
            "last_reset": datetime.utcnow(),
            "last_updated": None,
        }
        self._schedule_task: Optional[asyncio.Task] = None

        logger.info("創業者排程管理器已初始化")

    async def start(self):
        """啟動排程服務"""
        if self.is_running:
            return

        self.is_running = True
        self._schedule_task = asyncio.create_task(self._schedule_loop())
        logger.info("排程服務已啟動")

    async def stop(self):
        """停止排程服務"""
        self.is_running = False
        if self._schedule_task:
            self._schedule_task.cancel()
            try:
                await self._schedule_task
            except asyncio.CancelledError:
                pass
        logger.info("排程服務已停止")

    async def pause(self):
        """暫停排程服務"""
        self.is_running = False
        logger.info("排程服務已暫停")

    async def resume(self):
        """恢復排程服務"""
        if not self.is_running:
            await self.start()
        logger.info("排程服務已恢復")

    def is_within_work_hours(self) -> bool:
        """檢查是否在工作時間內"""
        current_time = datetime.now().strftime("%H:%M")
        return self.config.work_hours_start <= current_time <= self.config.work_hours_end

    async def schedule_entrepreneur_task(self, task_config: Dict[str, Any]) -> str:
        """排程創業者任務"""
        # 檢查每日限制
        if self.daily_stats["videos_generated"] >= self.config.daily_video_limit:
            raise ValueError("已達每日影片限制")

        # 檢查預算限制
        if self.daily_stats["budget_used"] >= self.config.daily_budget_limit:
            raise ValueError("已達每日預算限制")

        # 創建任務
        task_id = str(uuid.uuid4())
        task = ScheduledTask(
            task_id=task_id,
            user_id=task_config["user_id"],
            config=task_config,
            scheduled_time=datetime.utcnow(),
        )

        self.scheduled_tasks[task_id] = task
        logger.info(f"已排程創業者任務: {task_id}")

        return task_id

    def can_execute_task(self, task: ScheduledTask) -> bool:
        """檢查是否可以執行任務"""
        return self.current_tasks_count < self.config.max_concurrent_tasks

    async def execute_task(self, task: ScheduledTask):
        """執行任務"""
        if not self.can_execute_task(task):
            return

        try:
            self.current_tasks_count += 1
            task.mark_as_running()

            # 呼叫影片服務
            result = await self._call_video_service(task.config)

            # 更新統計
            if result.get("success"):
                videos_generated = result.get("videos_generated", 0)
                cost = result.get("cost", 0.0)
                self.update_daily_stats(videos_generated, cost)
                task.mark_as_completed(result)
            else:
                raise Exception(result.get("error", "影片生成失敗"))

        except Exception as e:
            # 重試邏輯
            if task.retry_count < self.config.retry_attempts:
                task.retry_count += 1
                logger.warning(
                    f"任務執行失敗，準備重試 ({task.retry_count}/{self.config.retry_attempts}): {e}"
                )
                # 延遲後重試
                await asyncio.sleep(self.config.retry_delay_minutes * 60)
                await self.execute_task(task)
            else:
                task.mark_as_failed(str(e))
                logger.error(f"任務執行失敗，已達最大重試次數: {e}")
        finally:
            self.current_tasks_count -= 1

    async def _call_video_service(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """呼叫影片生成服務"""
        # 模擬 API 呼叫
        video_service_url = "http://localhost:8003/api/v1/entrepreneur/create"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(video_service_url, json=config) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "videos_generated": config.get("video_count", 1),
                            "cost": config.get("video_count", 1) * 2.5,  # 估算成本
                            "workflow_id": result.get("workflow_id"),
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"API 回應錯誤: {response.status}",
                        }
        except ConnectionError:
            raise ConnectionError("服務不可用")
        except Exception as e:
            raise Exception(f"API 呼叫失敗: {str(e)}")

    def get_next_execution_time(self) -> datetime:
        """計算下次執行時間"""
        return datetime.utcnow() + timedelta(minutes=self.config.check_interval_minutes)

    def update_daily_stats(self, videos_generated: int, budget_used: float):
        """更新每日統計"""
        self.daily_stats["videos_generated"] += videos_generated
        self.daily_stats["budget_used"] += budget_used
        self.daily_stats["last_updated"] = datetime.utcnow()

    def check_and_reset_daily_stats(self):
        """檢查並重置每日統計"""
        now = datetime.utcnow()
        last_reset = self.daily_stats.get("last_reset", now)

        # 如果是新的一天，重置統計
        if now.date() != last_reset.date():
            self.daily_stats = {
                "videos_generated": 0,
                "budget_used": 0.0,
                "last_reset": now,
                "last_updated": now,
            }
            logger.info("每日統計已重置")

    async def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        """清理已完成的任務"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        tasks_to_remove = []
        for task_id, task in self.scheduled_tasks.items():
            if task.status in [
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
            ]:
                if task.completed_at and task.completed_at < cutoff_time:
                    tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.scheduled_tasks[task_id]

        logger.info(f"清理了 {len(tasks_to_remove)} 個舊任務")
        return len(tasks_to_remove)

    def get_status(self) -> Dict[str, Any]:
        """獲取排程器狀態"""
        return {
            "is_running": self.is_running,
            "daily_stats": self.daily_stats,
            "active_tasks_count": self.current_tasks_count,
            "scheduled_tasks_count": len(self.scheduled_tasks),
            "next_execution_time": self.get_next_execution_time().isoformat(),
            "config": {
                "daily_video_limit": self.config.daily_video_limit,
                "daily_budget_limit": self.config.daily_budget_limit,
                "work_hours": f"{self.config.work_hours_start}-{self.config.work_hours_end}",
            },
        }

    async def _schedule_loop(self):
        """排程主循環"""
        while self.is_running:
            try:
                # 檢查並重置每日統計
                self.check_and_reset_daily_stats()

                # 檢查是否在工作時間內
                if not self.is_within_work_hours():
                    logger.debug("不在工作時間內，跳過此次檢查")
                    await asyncio.sleep(300)  # 5分鐘後再檢查
                    continue

                # 執行待處理的任務
                tasks_to_execute = []
                for task in self.scheduled_tasks.values():
                    if (
                        task.status == TaskStatus.SCHEDULED
                        and task.scheduled_time <= datetime.utcnow()
                        and self.can_execute_task(task)
                    ):
                        tasks_to_execute.append(task)

                # 並行執行任務（受限於併發數量）
                if tasks_to_execute:
                    available_slots = self.config.max_concurrent_tasks - self.current_tasks_count
                    tasks_to_run = tasks_to_execute[:available_slots]

                    await asyncio.gather(
                        *[self.execute_task(task) for task in tasks_to_run],
                        return_exceptions=True,
                    )

                # 等待下次檢查
                await asyncio.sleep(self.config.check_interval_minutes * 60)

            except Exception as e:
                logger.error(f"排程循環錯誤: {e}")
                await asyncio.sleep(60)  # 發生錯誤時等待1分鐘
