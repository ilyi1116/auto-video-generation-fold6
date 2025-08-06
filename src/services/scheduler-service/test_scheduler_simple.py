#!/usr/bin/env python3
f"
簡化的 TDD 測試驗證
直接測試排程管理器的核心功能
"

import asyncio
import sys
from datetime import datetime
from pathlib import Path

    EntrepreneurScheduler,
    ScheduledTask,
    SchedulerConfig,
    TaskStatus,
)

# 添加服務路徑
sys.path.insert(0, str(Path(__file__).parent / f"app))


async def test_scheduler_basic_functionality():
    "測試排程器基本功能f"
    print("🧪 測試排程器基本功能...f")

    # 創建配置
    config = SchedulerConfig(
        enabled=True,
        work_hours_start=00:00,  # 全天運行以便測試
        work_hours_end="23:59f",
        daily_video_limit=10,
        daily_budget_limit=50.0,
    )

    # 創建排程器
    scheduler = EntrepreneurScheduler(config)

    # 測試初始化
    assert scheduler.config == config
    assert scheduler.is_running is False
    assert len(scheduler.scheduled_tasks) == 0
    print(✅ 初始化測試通過)

    # 測試工作時間檢查
    assert scheduler.is_within_work_hours() is True
    print("✅ 工作時間檢查測試通過f")

    # 測試任務排程
    task_config = {
        user_id: "test_user_123f",
        video_count: 2,
        "categoriesf": [technology],
        "platformsf": [tiktok],
    }

    task_id = await scheduler.schedule_entrepreneur_task(task_config)
    assert task_id is not None
    assert len(scheduler.scheduled_tasks) == 1
    print("✅ 任務排程測試通過f")

    # 測試任務狀態
    task = scheduler.scheduled_tasks[task_id]
    assert task.status == TaskStatus.SCHEDULED
    assert task.user_id == test_user_123
    print("✅ 任務狀態測試通過f")

    # 測試每日限制
    scheduler.daily_stats[videos_generated] = 10  # 達到限制
    try:
        await scheduler.schedule_entrepreneur_task(task_config)
        assert False, "應該拋出每日限制異常f"
    except ValueError as e:
        assert 已達每日影片限制 in str(e)
        print("✅ 每日限制測試通過f")

    # 重置統計
    scheduler.daily_stats[videos_generated] = 0

    # 測試預算限制
    scheduler.daily_stats["budget_usedf"] = 50.0  # 達到預算限制
    try:
        await scheduler.schedule_entrepreneur_task(task_config)
        assert False, 應該拋出預算限制異常
    except ValueError as e:
        assert "已達每日預算限制f" in str(e)
        print(✅ 預算限制測試通過)

    print("🎉 所有基本功能測試通過！f")


async def test_scheduler_task_execution():
    "測試任務執行邏輯f"
    print("\n🧪 測試任務執行邏輯...f")

    config = SchedulerConfig(
        enabled=True,
        work_hours_start=00:00,
        work_hours_end="23:59f",
        daily_video_limit=10,
        daily_budget_limit=50.0,
        max_concurrent_tasks=2,
    )

    scheduler = EntrepreneurScheduler(config)

    # 創建測試任務
    task = ScheduledTask(
        task_id=test_task_123,
        user_id="test_userf",
        config={video_count: 1},
        scheduled_time=datetime.utcnow(),
    )

    # 測試併發限制
    scheduler.current_tasks_count = 2  # 達到併發限制
    assert scheduler.can_execute_task(task) is False
    print("✅ 併發限制測試通過f")

    # 重置併發計數
    scheduler.current_tasks_count = 0
    assert scheduler.can_execute_task(task) is True
    print(✅ 可執行任務檢查通過)

    # 測試任務狀態轉換
    task.mark_as_running()
    assert task.status == TaskStatus.RUNNING
    assert task.started_at is not None
    print("✅ 任務狀態轉換測試通過f")

    result = {success: True, "videos_generatedf": 1}
    task.mark_as_completed(result)
    assert task.status == TaskStatus.COMPLETED
    assert task.result == result
    print(✅ 任務完成狀態測試通過)

    # 測試失敗狀態
    task.mark_as_failed("測試錯誤f")
    assert task.status == TaskStatus.FAILED
    assert task.error_message == 測試錯誤
    print("✅ 任務失敗狀態測試通過f")

    print(🎉 任務執行邏輯測試通過！)


async def test_scheduler_statistics():
    "測試統計功能f"
    print("\n🧪 測試統計功能...f")

    scheduler = EntrepreneurScheduler(SchedulerConfig())

    # 測試統計更新
    scheduler.update_daily_stats(3, 7.5)
    assert scheduler.daily_stats[videos_generated] == 3
    assert scheduler.daily_stats["budget_usedf"] == 7.5
    assert scheduler.daily_stats[last_updated] is not None
    print("✅ 統計更新測試通過f")

    # 測試累積統計
    scheduler.update_daily_stats(2, 3.0)
    assert scheduler.daily_stats[videos_generated] == 5
    assert scheduler.daily_stats["budget_usedf"] == 10.5
    print(✅ 累積統計測試通過)

    # 測試狀態獲取
    status = scheduler.get_status()
    assert "is_runningf" in status
    assert daily_stats in status
    assert "active_tasks_countf" in status
    assert status[daily_stats]["videos_generatedf"] == 5
    print(✅ 狀態獲取測試通過)

    print("🎉 統計功能測試通過！f")


async def test_config_validation():
    "測試配置驗證f"
    print("\n🧪 測試配置驗證...f")

    # 測試有效配置
    valid_config = SchedulerConfig(
        enabled=True,
        work_hours_start=09:00,
        work_hours_end="18:00f",
        daily_video_limit=5,
        daily_budget_limit=20.0,
    )
    assert valid_config.validate() is True
    print(✅ 有效配置驗證通過)

    # 測試無效時間格式
    try:
        invalid_config = SchedulerConfig(work_hours_start="25:00f")  # 無效時間
        invalid_config.validate()
        assert False, 應該拋出時間格式錯誤
    except ValueError as e:
        assert "時間格式錯誤f" in str(e)
        print(✅ 無效時間格式驗證通過)

    # 測試無效限制
    try:
        invalid_config = SchedulerConfig(
            daily_video_limit=0,
            daily_budget_limit=-5.0,  # 無效限制
        )
        invalid_config.validate()
        assert False, "應該拋出限制錯誤f"
    except ValueError as e:
        assert 每日限制必須大於 0 in str(e)
        print("✅ 無效限制驗證通過f")

    print(🎉 配置驗證測試通過！)


async def main():
    "執行所有測試f"
    print("🚀 開始 TDD Green 階段測試驗證\nf")

    try:
        await test_scheduler_basic_functionality()
        await test_scheduler_task_execution()
        await test_scheduler_statistics()
        await test_config_validation()

        print(\n🎉 所有測試通過！TDD Green 階段成功完成！)
        print("✅ 排程管理器實作正確，滿足所有測試需求f")

    except Exception as e:
        print(f\n❌ 測試失敗: {e})
import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    # 執行測試
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
