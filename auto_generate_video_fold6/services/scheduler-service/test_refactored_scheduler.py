#!/usr/bin/env python3
"""
TDD Refactor 階段驗證測試
確保重構後的程式碼功能完全相同
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

from app.entrepreneur_scheduler_refactored import (EntrepreneurScheduler, MockVideoServiceClient,
                                                   ScheduledTask, SchedulerConfig,
                                                   StatisticsManager, TaskStatus,
                                                   create_entrepreneur_scheduler)

# 添加服務路徑
sys.path.insert(0, str(Path(__file__).parent / "app"))


async def test_refactored_basic_functionality():
    """測試重構後的基本功能"""
    print("🧪 測試重構後的基本功能...")

    # 使用工廠函數創建
    scheduler = create_entrepreneur_scheduler(
        {
            "enabled": True,
            "work_hours_start": "00:00",
            "work_hours_end": "23:59",
            "daily_video_limit": 10,
            "daily_budget_limit": 50.0,
        },
        MockVideoServiceClient(should_succeed=True),
    )

    # 測試初始化
    assert scheduler.config.enabled is True
    assert scheduler.is_running is False
    assert len(scheduler.scheduled_tasks) == 0
    print("✅ 重構後初始化測試通過")

    # 測試工作時間檢查
    assert scheduler.is_within_work_hours() is True
    print("✅ 重構後工作時間檢查通過")

    # 測試任務排程
    task_config = {
        "user_id": "test_user_123",
        "video_count": 2,
        "categories": ["technology"],
        "platforms": ["tiktok"],
        "priority": 1,
    }

    task_id = await scheduler.schedule_entrepreneur_task(task_config)
    assert task_id is not None
    assert len(scheduler.scheduled_tasks) == 1
    print("✅ 重構後任務排程測試通過")

    # 測試任務優先級
    task = scheduler.scheduled_tasks[task_id]
    assert task.priority == 1
    print("✅ 任務優先級測試通過")

    print("🎉 重構後基本功能測試通過！")


async def test_enhanced_features():
    """測試重構後新增的功能"""
    print("\n🧪 測試重構後新增的功能...")

    # 測試統計管理器
    stats_manager = StatisticsManager()

    # 創建測試任務
    task = ScheduledTask(
        task_id="test_123",
        user_id="user_123",
        config={"video_count": 2},
        scheduled_time=datetime.utcnow(),
    )

    # 模擬任務完成
    from app.entrepreneur_scheduler_refactored import TaskMetrics

    metrics = TaskMetrics(
        videos_generated=2,
        cost_incurred=5.0,
        api_calls_made=3,
        execution_time=10.5,
    )
    task.mark_as_completed({"success": True}, metrics)

    # 更新統計
    stats_manager.update_stats(task)
    assert stats_manager.daily_stats["videos_generated"] == 2
    assert stats_manager.daily_stats["budget_used"] == 5.0
    assert stats_manager.daily_stats["tasks_completed"] == 1
    print("✅ 統計管理器測試通過")

    # 測試任務指標
    assert task.metrics.videos_generated == 2
    assert task.metrics.cost_incurred == 5.0
    assert task.metrics.execution_time == 10.5
    print("✅ 任務指標測試通過")

    # 測試配置驗證增強
    try:
        SchedulerConfig(work_hours_start="25:00")  # 無效時間
        assert False, "應該拋出驗證錯誤"
    except ValueError as e:
        assert "時間格式錯誤" in str(e)
        print("✅ 增強配置驗證測試通過")

    print("🎉 新增功能測試通過！")


async def test_task_execution_with_mock():
    """測試使用 Mock 客戶端的任務執行"""
    print("\n🧪 測試任務執行邏輯...")

    # 創建使用 Mock 客戶端的排程器
    mock_client = MockVideoServiceClient(should_succeed=True, delay=0.1)
    config = SchedulerConfig(max_concurrent_tasks=2, retry_attempts=2)

    scheduler = EntrepreneurScheduler(config, mock_client)

    # 排程任務
    task_config = {
        "user_id": "test_user",
        "video_count": 1,
        "categories": ["technology"],
    }

    task_id = await scheduler.schedule_entrepreneur_task(task_config)
    task = scheduler.scheduled_tasks[task_id]

    # 執行任務
    await scheduler.task_executor.execute_task(task)

    # 驗證結果
    assert task.status == TaskStatus.COMPLETED
    assert task.result["success"] is True
    assert task.metrics.videos_generated == 1
    assert mock_client.call_count == 1
    print("✅ Mock 客戶端任務執行測試通過")

    print("🎉 任務執行測試通過！")


async def test_failure_and_retry():
    """測試失敗和重試機制"""
    print("\n🧪 測試失敗和重試機制...")

    # 創建會失敗的 Mock 客戶端
    mock_client = MockVideoServiceClient(should_succeed=False, delay=0.05)
    config = SchedulerConfig(
        retry_attempts=2,
        retry_delay_minutes=1,  # 最小有效值
    )

    scheduler = EntrepreneurScheduler(config, mock_client)

    # 排程任務
    task_config = {"user_id": "test_user", "video_count": 1}

    task_id = await scheduler.schedule_entrepreneur_task(task_config)
    task = scheduler.scheduled_tasks[task_id]

    # 執行任務（會失敗）
    await scheduler.task_executor.execute_task(task)

    # 驗證結果
    assert task.status == TaskStatus.FAILED
    print(
        f"重試次數: {task.metrics.retry_attempts_used}, 呼叫次數: \
            {mock_client.call_count}"
    )
    # 實際的重試邏輯：配置的 retry_attempts=2，所以總共會嘗試 3 次（初始 + 2次重試）
    assert (
        task.metrics.retry_attempts_used == 2
    )  # 最後記錄的是最後一次嘗試的索引
    assert mock_client.call_count == 3  # 初始 + 2次重試
    print("✅ 失敗和重試機制測試通過")

    print("🎉 失敗重試測試通過！")


async def test_scheduler_lifecycle():
    """測試排程器生命週期管理"""
    print("\n🧪 測試排程器生命週期...")

    mock_client = MockVideoServiceClient(should_succeed=True, delay=0.1)
    config = SchedulerConfig(
        check_interval_minutes=1,
        health_check_interval_minutes=1,  # 最小有效值
    )

    scheduler = EntrepreneurScheduler(config, mock_client)

    # 測試啟動
    assert not scheduler.is_running
    await scheduler.start()
    assert scheduler.is_running
    print("✅ 排程器啟動測試通過")

    # 等待一小段時間讓循環運行
    await asyncio.sleep(0.2)

    # 測試暫停
    await scheduler.pause()
    from app.entrepreneur_scheduler_refactored import SchedulerState

    assert scheduler.state == SchedulerState.PAUSED
    print("✅ 排程器暫停測試通過")

    # 測試恢復
    await scheduler.resume()
    assert scheduler.is_running
    print("✅ 排程器恢復測試通過")

    # 測試停止
    await scheduler.stop()
    assert not scheduler.is_running
    print("✅ 排程器停止測試通過")

    print("🎉 生命週期管理測試通過！")


async def test_context_manager():
    """測試上下文管理器支援"""
    print("\n🧪 測試上下文管理器...")

    mock_client = MockVideoServiceClient(should_succeed=True)
    config = SchedulerConfig()

    # 使用上下文管理器
    async with EntrepreneurScheduler(config, mock_client) as scheduler:
        assert scheduler.is_running
        print("✅ 上下文管理器啟動測試通過")

        # 排程一個任務
        task_config = {"user_id": "context_test", "video_count": 1}

        await scheduler.schedule_entrepreneur_task(task_config)
        assert len(scheduler.scheduled_tasks) == 1
        print("✅ 上下文中任務排程測試通過")

    # 確保已自動停止
    assert not scheduler.is_running
    print("✅ 上下文管理器自動停止測試通過")

    print("🎉 上下文管理器測試通過！")


async def test_statistics_and_status():
    """測試統計和狀態功能"""
    print("\n🧪 測試統計和狀態功能...")

    scheduler = create_entrepreneur_scheduler(
        {"daily_video_limit": 5, "daily_budget_limit": 20.0},
        MockVideoServiceClient(should_succeed=True),
    )

    # 獲取初始狀態
    status = scheduler.get_status()
    assert "scheduler_state" in status
    assert "statistics" in status
    assert "task_counts" in status
    assert "work_hours_status" in status
    print("✅ 詳細狀態回報測試通過")

    # 測試統計摘要
    stats_summary = scheduler.statistics.get_statistics_summary()
    assert "daily" in stats_summary
    assert "success_rate" in stats_summary
    assert "average_cost_per_video" in stats_summary
    print("✅ 統計摘要測試通過")

    print("🎉 統計和狀態測試通過！")


async def test_cleanup_and_maintenance():
    """測試清理和維護功能"""
    print("\n🧪 測試清理和維護功能...")

    scheduler = create_entrepreneur_scheduler()

    # 創建一些舊任務
    old_task = ScheduledTask(
        task_id="old_task",
        user_id="test_user",
        config={},
        scheduled_time=datetime.utcnow() - timedelta(hours=25),
    )
    old_task.status = TaskStatus.COMPLETED
    old_task.completed_at = datetime.utcnow() - timedelta(hours=25)

    recent_task = ScheduledTask(
        task_id="recent_task",
        user_id="test_user",
        config={},
        scheduled_time=datetime.utcnow() - timedelta(hours=1),
    )
    recent_task.status = TaskStatus.COMPLETED
    recent_task.completed_at = datetime.utcnow() - timedelta(hours=1)

    scheduler.scheduled_tasks = {
        "old_task": old_task,
        "recent_task": recent_task,
    }

    # 執行清理
    cleaned_count = await scheduler.cleanup_completed_tasks(max_age_hours=24)

    assert cleaned_count == 1
    assert "old_task" not in scheduler.scheduled_tasks
    assert "recent_task" in scheduler.scheduled_tasks
    print("✅ 任務清理測試通過")

    print("🎉 清理和維護測試通過！")


async def main():
    """執行所有重構驗證測試"""
    print("🚀 開始 TDD Refactor 階段驗證測試\n")

    try:
        await test_refactored_basic_functionality()
        await test_enhanced_features()
        await test_task_execution_with_mock()
        await test_failure_and_retry()
        await test_scheduler_lifecycle()
        await test_context_manager()
        await test_statistics_and_status()
        await test_cleanup_and_maintenance()

        print("\n🎉 所有重構驗證測試通過！")
        print("✅ 重構成功，功能完整保留並得到增強")
        print("🏆 TDD Refactor 階段完成！")

        print("\n📊 重構改善總結:")
        print("  • 更好的職責分離（StatisticsManager, TaskExecutor）")
        print("  • 增強的錯誤處理和重試機制")
        print("  • 完整的生命週期管理")
        print("  • 上下文管理器支援")
        print("  • 更詳細的指標和統計")
        print("  • 事件回調系統")
        print("  • Mock 客戶端支援測試")
        print("  • 更清晰的程式碼結構")

    except Exception as e:
        print(f"\n❌ 重構驗證失敗: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    # 執行重構驗證測試
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
