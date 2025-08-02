"""
TDD Red 階段: 創業者排程管理器測試

這些測試定義了排程管理器的預期行為：
1. 自動創業者模式排程
2. 工作時間檢查
3. 預算控制
4. 任務執行管理
5. 失敗重試機制

遵循 TDD 原則，這些測試會先失敗，然後我們實作讓它們通過
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
# 這些 import 會失敗，因為我們還沒實作 - 這就是 TDD Red 階段
from services.scheduler_service.app.entrepreneur_scheduler import (EntrepreneurScheduler,
                                                                   ScheduledTask, SchedulerConfig,
                                                                   TaskStatus)


class TestEntrepreneurSchedulerTDD:
    """創業者排程管理器 TDD 測試套件"""

    @pytest.fixture
    def scheduler_config(self):
        """測試用排程配置"""
        return SchedulerConfig(
            enabled=True,
            work_hours_start="09:00",
            work_hours_end="18:00",
            timezone="Asia/Taipei",
            check_interval_minutes=30,
            daily_video_limit=5,
            daily_budget_limit=20.0,
            max_concurrent_tasks=3,
            retry_attempts=3,
            retry_delay_minutes=5,
        )

    @pytest.fixture
    def scheduler(self, scheduler_config):
        """測試用排程管理器實例"""
        return EntrepreneurScheduler(scheduler_config)

    def test_scheduler_initialization(self, scheduler_config):
        """測試排程管理器初始化"""
        # TDD Red: 這個測試會失敗，因為 EntrepreneurScheduler 還不存在
        scheduler = EntrepreneurScheduler(scheduler_config)

        assert scheduler.config == scheduler_config
        assert scheduler.is_running is False
        assert len(scheduler.scheduled_tasks) == 0
        assert scheduler.current_tasks_count == 0

    @pytest.mark.asyncio
    async def test_start_scheduler_service(self, scheduler):
        """測試啟動排程服務"""
        # TDD Red: 測試啟動排程服務
        with patch.object(scheduler, "_schedule_loop") as mock_loop:
            mock_loop.return_value = AsyncMock()

            await scheduler.start()

            assert scheduler.is_running is True
            mock_loop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_scheduler_service(self, scheduler):
        """測試停止排程服務"""
        # TDD Red: 測試停止排程服務
        scheduler.is_running = True

        await scheduler.stop()

        assert scheduler.is_running is False

    def test_is_within_work_hours_true(self, scheduler):
        """測試工作時間內檢查 - 應該返回 True"""
        # TDD Red: 測試工作時間檢查邏輯
        with patch("datetime.datetime") as mock_datetime:
            # 模擬當前時間為 10:00
            mock_datetime.now.return_value.strftime.return_value = "10:00"

            result = scheduler.is_within_work_hours()

            assert result is True

    def test_is_within_work_hours_false(self, scheduler):
        """測試工作時間外檢查 - 應該返回 False"""
        # TDD Red: 測試工作時間外的情況
        with patch("datetime.datetime") as mock_datetime:
            # 模擬當前時間為 22:00
            mock_datetime.now.return_value.strftime.return_value = "22:00"

            result = scheduler.is_within_work_hours()

            assert result is False

    @pytest.mark.asyncio
    async def test_schedule_entrepreneur_task_success(self, scheduler):
        """測試排程創業者任務成功"""
        # TDD Red: 測試任務排程功能
        task_config = {
            "user_id": "test_user_123",
            "video_count": 3,
            "categories": ["technology", "entertainment"],
            "platforms": ["tiktok", "youtube-shorts"],
        }

        task_id = await scheduler.schedule_entrepreneur_task(task_config)

        assert task_id is not None
        assert len(scheduler.scheduled_tasks) == 1
        assert (
            scheduler.scheduled_tasks[task_id].status == TaskStatus.SCHEDULED
        )

    @pytest.mark.asyncio
    async def test_schedule_task_exceeds_daily_limit(self, scheduler):
        """測試超出每日限制時的排程行為"""
        # TDD Red: 測試每日限制檢查
        scheduler.daily_stats = {"videos_generated": 5}  # 已達限制

        task_config = {"user_id": "test_user_123", "video_count": 2}

        with pytest.raises(ValueError, match="已達每日影片限制"):
            await scheduler.schedule_entrepreneur_task(task_config)

    @pytest.mark.asyncio
    async def test_schedule_task_exceeds_budget_limit(self, scheduler):
        """測試超出預算限制時的排程行為"""
        # TDD Red: 測試預算限制檢查
        scheduler.daily_stats = {"budget_used": 20.0}  # 已達預算限制

        task_config = {"user_id": "test_user_123", "video_count": 1}

        with pytest.raises(ValueError, match="已達每日預算限制"):
            await scheduler.schedule_entrepreneur_task(task_config)

    @pytest.mark.asyncio
    async def test_execute_scheduled_task_success(self, scheduler):
        """測試執行排程任務成功"""
        # TDD Red: 測試任務執行邏輯
        task = ScheduledTask(
            task_id="test_task_123",
            user_id="test_user_123",
            config={"video_count": 2},
            scheduled_time=datetime.utcnow(),
            status=TaskStatus.SCHEDULED,
        )

        with patch.object(
            scheduler, "_call_video_service"
        ) as mock_video_service:
            mock_video_service.return_value = {
                "success": True,
                "videos_generated": 2,
            }

            await scheduler.execute_task(task)

            assert task.status == TaskStatus.COMPLETED
            assert task.result["success"] is True
            mock_video_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_task_failure_with_retry(self, scheduler):
        """測試任務失敗後重試機制"""
        # TDD Red: 測試失敗重試邏輯
        task = ScheduledTask(
            task_id="test_task_123",
            user_id="test_user_123",
            config={"video_count": 1},
            scheduled_time=datetime.utcnow(),
            status=TaskStatus.SCHEDULED,
            retry_count=0,
        )

        with patch.object(
            scheduler, "_call_video_service"
        ) as mock_video_service:
            # 第一次失敗，第二次成功
            mock_video_service.side_effect = [
                Exception("API 呼叫失敗"),
                {"success": True, "videos_generated": 1},
            ]

            await scheduler.execute_task(task)

            assert task.status == TaskStatus.COMPLETED
            assert task.retry_count == 1
            assert mock_video_service.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_task_max_retries_exceeded(self, scheduler):
        """測試超過最大重試次數後任務失敗"""
        # TDD Red: 測試重試次數限制
        task = ScheduledTask(
            task_id="test_task_123",
            user_id="test_user_123",
            config={"video_count": 1},
            scheduled_time=datetime.utcnow(),
            status=TaskStatus.SCHEDULED,
            retry_count=3,  # 已達最大重試次數
        )

        with patch.object(
            scheduler, "_call_video_service"
        ) as mock_video_service:
            mock_video_service.side_effect = Exception("持續失敗")

            await scheduler.execute_task(task)

            assert task.status == TaskStatus.FAILED
            assert "持續失敗" in task.error_message

    @pytest.mark.asyncio
    async def test_concurrent_task_limit(self, scheduler):
        """測試並行任務數量限制"""
        # TDD Red: 測試並行任務限制
        scheduler.current_tasks_count = 3  # 已達並行限制

        task = ScheduledTask(
            task_id="test_task_123",
            user_id="test_user_123",
            config={"video_count": 1},
            scheduled_time=datetime.utcnow(),
            status=TaskStatus.SCHEDULED,
        )

        result = scheduler.can_execute_task(task)

        assert result is False

    def test_get_next_execution_time(self, scheduler):
        """測試計算下次執行時間"""
        # TDD Red: 測試下次執行時間計算
        current_time = datetime.utcnow()

        with patch("datetime.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = current_time

            next_time = scheduler.get_next_execution_time()

            expected_time = current_time + timedelta(minutes=30)
            assert abs((next_time - expected_time).total_seconds()) < 60

    def test_update_daily_stats(self, scheduler):
        """測試更新每日統計"""
        # TDD Red: 測試統計數據更新
        scheduler.update_daily_stats(videos_generated=2, budget_used=5.50)

        assert scheduler.daily_stats["videos_generated"] == 2
        assert scheduler.daily_stats["budget_used"] == 5.50
        assert scheduler.daily_stats["last_updated"] is not None

    def test_reset_daily_stats_new_day(self, scheduler):
        """測試新的一天重置統計"""
        # TDD Red: 測試每日統計重置
        scheduler.daily_stats = {
            "videos_generated": 5,
            "budget_used": 15.0,
            "last_reset": datetime.utcnow() - timedelta(days=1),
        }

        scheduler.check_and_reset_daily_stats()

        assert scheduler.daily_stats["videos_generated"] == 0
        assert scheduler.daily_stats["budget_used"] == 0.0

    @pytest.mark.asyncio
    async def test_cleanup_completed_tasks(self, scheduler):
        """測試清理已完成任務"""
        # TDD Red: 測試任務清理邏輯
        old_task = ScheduledTask(
            task_id="old_task",
            user_id="test_user",
            config={},
            scheduled_time=datetime.utcnow() - timedelta(hours=25),
            status=TaskStatus.COMPLETED,
        )

        recent_task = ScheduledTask(
            task_id="recent_task",
            user_id="test_user",
            config={},
            scheduled_time=datetime.utcnow() - timedelta(hours=1),
            status=TaskStatus.COMPLETED,
        )

        scheduler.scheduled_tasks = {
            "old_task": old_task,
            "recent_task": recent_task,
        }

        cleaned_count = await scheduler.cleanup_completed_tasks(
            max_age_hours=24
        )

        assert cleaned_count == 1
        assert "old_task" not in scheduler.scheduled_tasks
        assert "recent_task" in scheduler.scheduled_tasks

    def test_get_scheduler_status(self, scheduler):
        """測試獲取排程器狀態"""
        # TDD Red: 測試狀態回報功能
        scheduler.is_running = True
        scheduler.daily_stats = {"videos_generated": 2, "budget_used": 8.5}

        status = scheduler.get_status()

        assert status["is_running"] is True
        assert status["daily_stats"]["videos_generated"] == 2
        assert status["daily_stats"]["budget_used"] == 8.5
        assert "next_execution_time" in status
        assert "active_tasks_count" in status

    @pytest.mark.asyncio
    async def test_pause_and_resume_scheduler(self, scheduler):
        """測試暫停和恢復排程器"""
        # TDD Red: 測試暫停/恢復功能
        scheduler.is_running = True

        await scheduler.pause()
        assert scheduler.is_running is False

        await scheduler.resume()
        assert scheduler.is_running is True

    @pytest.mark.asyncio
    async def test_handle_service_unavailable(self, scheduler):
        """測試服務不可用時的處理"""
        # TDD Red: 測試服務不可用的錯誤處理
        task = ScheduledTask(
            task_id="test_task",
            user_id="test_user",
            config={"video_count": 1},
            scheduled_time=datetime.utcnow(),
            status=TaskStatus.SCHEDULED,
        )

        with patch.object(scheduler, "_call_video_service") as mock_service:
            mock_service.side_effect = ConnectionError("服務不可用")

            await scheduler.execute_task(task)

            assert task.status == TaskStatus.FAILED
            assert "服務不可用" in task.error_message


# 資料模型測試
class TestScheduledTaskModel:
    """排程任務模型測試"""

    def test_scheduled_task_creation(self):
        """測試排程任務創建"""
        # TDD Red: 測試任務模型創建
        task = ScheduledTask(
            task_id="test_123",
            user_id="user_123",
            config={"video_count": 3},
            scheduled_time=datetime.utcnow(),
        )

        assert task.task_id == "test_123"
        assert task.user_id == "user_123"
        assert task.status == TaskStatus.SCHEDULED
        assert task.retry_count == 0
        assert task.created_at is not None

    def test_task_status_transitions(self):
        """測試任務狀態轉換"""
        # TDD Red: 測試狀態轉換邏輯
        task = ScheduledTask(
            task_id="test_123",
            user_id="user_123",
            config={},
            scheduled_time=datetime.utcnow(),
        )

        # 測試狀態轉換
        task.mark_as_running()
        assert task.status == TaskStatus.RUNNING
        assert task.started_at is not None

        task.mark_as_completed({"videos_generated": 2})
        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at is not None
        assert task.result["videos_generated"] == 2

        # 測試失敗狀態
        task.mark_as_failed("測試錯誤")
        assert task.status == TaskStatus.FAILED
        assert task.error_message == "測試錯誤"


class TestSchedulerConfig:
    """排程配置測試"""

    def test_config_validation_valid(self):
        """測試有效配置驗證"""
        # TDD Red: 測試配置驗證
        config = SchedulerConfig(
            enabled=True,
            work_hours_start="09:00",
            work_hours_end="18:00",
            daily_video_limit=5,
            daily_budget_limit=20.0,
        )

        assert config.validate() is True

    def test_config_validation_invalid_time_format(self):
        """測試無效時間格式"""
        # TDD Red: 測試無效配置檢查
        with pytest.raises(ValueError, match="時間格式錯誤"):
            SchedulerConfig(
                enabled=True,
                work_hours_start="25:00",  # 無效時間
                work_hours_end="18:00",
            )

    def test_config_validation_invalid_limits(self):
        """測試無效限制設定"""
        # TDD Red: 測試限制值驗證
        with pytest.raises(ValueError, match="每日限制必須大於 0"):
            SchedulerConfig(
                enabled=True,
                daily_video_limit=0,  # 無效限制
                daily_budget_limit=-5.0,  # 無效預算
            )


# 整合測試
class TestEntrepreneurSchedulerIntegration:
    """創業者排程管理器整合測試"""

    @pytest.mark.asyncio
    async def test_full_scheduling_workflow(self):
        """測試完整排程工作流程"""
        # TDD Red: 整合測試 - 從排程到執行的完整流程
        config = SchedulerConfig(
            enabled=True,
            work_hours_start="00:00",  # 全天運行以便測試
            work_hours_end="23:59",
            check_interval_minutes=1,  # 快速檢查以便測試
            daily_video_limit=10,
            daily_budget_limit=50.0,
        )

        scheduler = EntrepreneurScheduler(config)

        # 排程任務
        task_config = {
            "user_id": "integration_test_user",
            "video_count": 2,
            "categories": ["technology"],
            "platforms": ["tiktok"],
        }

        with patch.object(scheduler, "_call_video_service") as mock_service:
            mock_service.return_value = {
                "success": True,
                "videos_generated": 2,
                "cost": 4.5,
            }

            # 排程任務
            task_id = await scheduler.schedule_entrepreneur_task(task_config)
            assert task_id is not None

            # 執行任務
            task = scheduler.scheduled_tasks[task_id]
            await scheduler.execute_task(task)

            # 驗證結果
            assert task.status == TaskStatus.COMPLETED
            assert scheduler.daily_stats["videos_generated"] == 2
            assert scheduler.daily_stats["budget_used"] == 4.5


if __name__ == "__main__":
    # 執行測試（這些會失敗，因為我們還沒實作）
    pytest.main([__file__, "-v"])
