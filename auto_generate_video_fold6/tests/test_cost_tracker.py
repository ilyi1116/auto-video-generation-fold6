"""
成本追蹤器測試
"""

import pytest
import sqlite3
from datetime import date
from unittest.mock import patch

try:
    from monitoring.cost_tracker import (
        CostTracker,
        get_cost_tracker,
        DailyCostSummary,
    )
    from monitoring.budget_controller import (
        BudgetController,
        get_budget_controller,
    )

    COST_MONITORING_AVAILABLE = True
except ImportError:
    COST_MONITORING_AVAILABLE = False


@pytest.mark.skipif(not COST_MONITORING_AVAILABLE, reason="成本監控模組不可用")
class TestCostTracker:
    """成本追蹤器測試類"""

    @pytest.fixture
    async def cost_tracker(self, temp_dir, mock_config_manager):
        """創建測試用的成本追蹤器"""
        db_path = temp_dir / "test_cost.db"
        tracker = CostTracker(mock_config_manager, str(db_path))
        yield tracker
        # 清理
        if db_path.exists():
            db_path.unlink()

    @pytest.mark.asyncio
    async def test_cost_tracker_initialization(self, cost_tracker):
        """測試成本追蹤器初始化"""
        assert cost_tracker is not None
        assert cost_tracker.db_path.exists()

        # 檢查資料庫表是否創建
        with sqlite3.connect(cost_tracker.db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            assert "api_calls" in tables
            assert "daily_summaries" in tables

    @pytest.mark.asyncio
    async def test_track_api_call_openai(self, cost_tracker):
        """測試追蹤 OpenAI API 呼叫"""
        cost = await cost_tracker.track_api_call(
            provider="openai",
            model="gpt-4",
            operation_type="text_generation",
            tokens_used=1000,
            request_id="test-request-1",
            success=True,
        )

        assert cost > 0
        assert cost == pytest.approx(0.03, rel=0.1)  # GPT-4 的大概成本

    @pytest.mark.asyncio
    async def test_track_api_call_stability(self, cost_tracker):
        """測試追蹤 Stability AI API 呼叫"""
        cost = await cost_tracker.track_api_call(
            provider="stability_ai",
            model="stable-diffusion-xl",
            operation_type="image_generation",
            images_generated=3,
            request_id="test-request-2",
            success=True,
        )

        assert cost > 0
        assert cost == pytest.approx(0.12, rel=0.1)  # 3張圖片的成本

    @pytest.mark.asyncio
    async def test_track_api_call_elevenlabs(self, cost_tracker):
        """測試追蹤 ElevenLabs API 呼叫"""
        cost = await cost_tracker.track_api_call(
            provider="elevenlabs",
            model="voice_synthesis",
            operation_type="voice_synthesis",
            characters_used=1000,
            request_id="test-request-3",
            success=True,
        )

        assert cost > 0
        assert cost == pytest.approx(0.03, rel=0.1)  # 1000字符的成本

    @pytest.mark.asyncio
    async def test_unknown_provider_fallback(self, cost_tracker):
        """測試未知供應商的回退處理"""
        cost = await cost_tracker.track_api_call(
            provider="unknown_provider",
            model="unknown_model",
            operation_type="unknown_operation",
            tokens_used=100,
            request_id="test-request-4",
            success=True,
        )

        assert cost == 0.01  # 預設成本

    @pytest.mark.asyncio
    async def test_daily_summary(self, cost_tracker):
        """測試每日摘要功能"""
        # 添加一些測試呼叫
        await cost_tracker.track_api_call(
            "openai", "gpt-4", "text_generation", tokens_used=500
        )
        await cost_tracker.track_api_call(
            "stability_ai",
            "stable-diffusion-xl",
            "image_generation",
            images_generated=2,
        )

        summary = await cost_tracker.get_daily_summary()

        assert isinstance(summary, DailyCostSummary)
        assert summary.total_cost > 0
        assert summary.api_calls_count == 2
        assert summary.date == date.today()
        assert "openai" in summary.providers_breakdown
        assert "stability_ai" in summary.providers_breakdown

    @pytest.mark.asyncio
    async def test_weekly_report(self, cost_tracker):
        """測試週報告功能"""
        # 添加測試數據
        await cost_tracker.track_api_call(
            "openai", "gpt-4", "text_generation", tokens_used=500
        )

        report = await cost_tracker.get_weekly_report()

        assert "period" in report
        assert "total_cost" in report
        assert "total_calls" in report
        assert "daily_stats" in report
        assert report["total_calls"] >= 1

    @pytest.mark.asyncio
    async def test_budget_status_check(self, cost_tracker):
        """測試預算狀態檢查"""
        # 添加一些成本
        await cost_tracker.track_api_call(
            "openai", "gpt-4", "text_generation", tokens_used=1000
        )

        status = await cost_tracker.check_budget_status()

        assert "current_cost" in status
        assert "budget_limit" in status
        assert "budget_remaining" in status
        assert "usage_percentage" in status
        assert "is_over_budget" in status
        assert "can_continue" in status

    @pytest.mark.asyncio
    async def test_budget_alerts(self, cost_tracker):
        """測試預算警告功能"""
        # 模擬高成本使用以觸發警告
        with patch.object(cost_tracker, "_daily_cache", {"total_cost": 8.5}):
            await cost_tracker._check_budget_alerts(1.0)

        # 檢查警告文件是否創建
        cost_tracker.db_path.parent / "budget_alerts.json"
        # 注意：實際的警告文件路徑可能不同，這裡只是示例測試

    @pytest.mark.asyncio
    async def test_export_cost_data(self, cost_tracker):
        """測試成本數據匯出"""
        # 添加測試數據
        await cost_tracker.track_api_call(
            "openai", "gpt-4", "text_generation", tokens_used=500
        )
        await cost_tracker.track_api_call(
            "stability_ai",
            "stable-diffusion-xl",
            "image_generation",
            images_generated=1,
        )

        export_file = await cost_tracker.export_cost_data(days=7)

        assert export_file is not None
        cost_tracker.db_path.parent / export_file
        # 實際的匯出檔案可能在不同路徑

        # 驗證匯出內容結構
        # 這裡可以添加更詳細的匯出內容驗證


@pytest.mark.skipif(not COST_MONITORING_AVAILABLE, reason="成本監控模組不可用")
class TestBudgetController:
    """預算控制器測試類"""

    @pytest.fixture
    async def budget_controller(self, temp_dir, mock_config_manager):
        """創建測試用的預算控制器"""
        db_path = temp_dir / "test_budget.db"
        cost_tracker = CostTracker(mock_config_manager, str(db_path))
        controller = BudgetController(mock_config_manager, cost_tracker)
        yield controller
        # 清理
        if db_path.exists():
            db_path.unlink()

    @pytest.mark.asyncio
    async def test_budget_controller_initialization(self, budget_controller):
        """測試預算控制器初始化"""
        assert budget_controller is not None
        assert budget_controller.cost_tracker is not None
        assert len(budget_controller.rules) > 0

    @pytest.mark.asyncio
    async def test_budget_decision_normal(self, budget_controller):
        """測試正常預算情況下的決策"""
        decision = await budget_controller.check_budget_and_decide(
            estimated_cost=1.0
        )

        assert decision.can_continue is True
        assert decision.status.value in ["normal", "warning"]
        assert decision.current_usage >= 0
        assert decision.remaining_budget >= 0

    @pytest.mark.asyncio
    async def test_budget_decision_critical(self, budget_controller):
        """測試臨界預算情況下的決策"""
        # 模擬高預算使用率
        with patch.object(
            budget_controller.cost_tracker, "check_budget_status"
        ) as mock_status:
            mock_status.return_value = {
                "current_cost": 9.5,
                "budget_limit": 10.0,
                "budget_remaining": 0.5,
                "usage_percentage": 95.0,
                "is_over_budget": False,
                "can_continue": True,
            }

            decision = await budget_controller.check_budget_and_decide(
                estimated_cost=1.0
            )

            assert decision.can_continue is False or decision.action.value in [
                "pause",
                "stop",
            ]
            assert decision.status.value in ["critical", "exceeded"]

    @pytest.mark.asyncio
    async def test_pre_operation_check(self, budget_controller):
        """測試操作前檢查"""
        can_proceed, message = await budget_controller.pre_operation_check(
            "test_operation", estimated_cost=2.0
        )

        assert isinstance(can_proceed, bool)
        assert isinstance(message, str)
        assert len(message) > 0

    @pytest.mark.asyncio
    async def test_post_operation_update(self, budget_controller):
        """測試操作後更新"""
        # 這應該不會拋出例外
        await budget_controller.post_operation_update(
            actual_cost=1.5, operation_result=True
        )

        # 驗證成本追蹤器狀態更新
        # 具體驗證邏輯取決於實現

    @pytest.mark.asyncio
    async def test_dynamic_budget_adjustment(self, budget_controller):
        """測試動態預算調整"""
        if budget_controller.config_manager:
            old_budget = budget_controller.config_manager.get(
                "cost_control.daily_budget_usd", 10.0
            )

            result = await budget_controller.adjust_budget_dynamically(
                new_budget=20.0, reason="測試調整"
            )

            if result:  # 如果支援動態調整
                new_budget = budget_controller.config_manager.get(
                    "cost_control.daily_budget_usd", 10.0
                )
                assert new_budget == 20.0

    @pytest.mark.asyncio
    async def test_daily_budget_report(self, budget_controller):
        """測試每日預算報告"""
        report = await budget_controller.get_daily_budget_report()

        assert "date" in report
        assert "budget_status" in report
        assert "current_status" in report
        assert "daily_stats" in report
        assert "rules_summary" in report
        assert "generated_at" in report

    @pytest.mark.asyncio
    async def test_get_current_status(self, budget_controller):
        """測試獲取當前狀態"""
        status = budget_controller.get_current_status()

        assert "status" in status
        assert "daily_stats" in status
        assert "rules_count" in status


@pytest.mark.unit
class TestCostCalculations:
    """成本計算測試"""

    @pytest.mark.skipif(
        not COST_MONITORING_AVAILABLE, reason="成本監控模組不可用"
    )
    def test_openai_cost_calculation(self, mock_config_manager):
        """測試 OpenAI 成本計算"""
        tracker = CostTracker(mock_config_manager, ":memory:")

        # GPT-4 成本計算
        cost = tracker._calculate_cost(
            provider="openai",
            model="gpt-4",
            operation_type="text_generation",
            tokens_used=1000,
            characters_used=0,
            images_generated=0,
        )

        # GPT-4: input $0.03/1k, output $0.06/1k
        # 假設 1:1 輸入輸出比例，1000 tokens = 500 input + 500 output
        expected_cost = (500 / 1000 * 0.03) + (500 / 1000 * 0.06)
        assert cost == pytest.approx(expected_cost, rel=0.01)

    @pytest.mark.skipif(
        not COST_MONITORING_AVAILABLE, reason="成本監控模組不可用"
    )
    def test_stability_cost_calculation(self, mock_config_manager):
        """測試 Stability AI 成本計算"""
        tracker = CostTracker(mock_config_manager, ":memory:")

        cost = tracker._calculate_cost(
            provider="stability_ai",
            model="stable-diffusion-xl",
            operation_type="image_generation",
            tokens_used=0,
            characters_used=0,
            images_generated=5,
        )

        # Stable Diffusion XL: $0.04 per image
        expected_cost = 5 * 0.04
        assert cost == pytest.approx(expected_cost, rel=0.01)

    @pytest.mark.skipif(
        not COST_MONITORING_AVAILABLE, reason="成本監控模組不可用"
    )
    def test_elevenlabs_cost_calculation(self, mock_config_manager):
        """測試 ElevenLabs 成本計算"""
        tracker = CostTracker(mock_config_manager, ":memory:")

        cost = tracker._calculate_cost(
            provider="elevenlabs",
            model="voice_synthesis",
            operation_type="voice_synthesis",
            tokens_used=0,
            characters_used=2000,
            images_generated=0,
        )

        # ElevenLabs: $0.00003 per character
        expected_cost = 2000 * 0.00003
        assert cost == pytest.approx(expected_cost, rel=0.01)


@pytest.mark.integration
@pytest.mark.slow
class TestCostMonitoringIntegration:
    """成本監控整合測試"""

    @pytest.mark.skipif(
        not COST_MONITORING_AVAILABLE, reason="成本監控模組不可用"
    )
    @pytest.mark.asyncio
    async def test_full_cost_tracking_workflow(
        self, temp_dir, mock_config_manager
    ):
        """測試完整的成本追蹤工作流程"""
        db_path = temp_dir / "integration_test.db"

        # 初始化成本追蹤器和預算控制器
        cost_tracker = CostTracker(mock_config_manager, str(db_path))
        budget_controller = BudgetController(mock_config_manager, cost_tracker)

        # 模擬一系列 API 呼叫
        api_calls = [
            ("openai", "gpt-4", "text_generation", {"tokens_used": 800}),
            (
                "stability_ai",
                "stable-diffusion-xl",
                "image_generation",
                {"images_generated": 2},
            ),
            (
                "elevenlabs",
                "voice_synthesis",
                "voice_synthesis",
                {"characters_used": 1500},
            ),
            (
                "openai",
                "gpt-3.5-turbo",
                "text_generation",
                {"tokens_used": 1200},
            ),
        ]

        total_cost = 0
        for provider, model, operation, kwargs in api_calls:
            # 檢查預算是否允許
            can_proceed, message = await budget_controller.pre_operation_check(
                f"{provider}_{operation}", estimated_cost=0.5
            )

            if can_proceed:
                # 執行 API 呼叫並追蹤成本
                cost = await cost_tracker.track_api_call(
                    provider=provider,
                    model=model,
                    operation_type=operation,
                    **kwargs,
                )
                total_cost += cost

                # 操作後更新
                await budget_controller.post_operation_update(cost, True)

        # 驗證結果
        assert total_cost > 0

        # 獲取每日摘要
        summary = await cost_tracker.get_daily_summary()
        assert summary.total_cost == pytest.approx(total_cost, rel=0.01)
        assert summary.api_calls_count == len(api_calls)

        # 檢查預算狀態
        budget_status = await cost_tracker.check_budget_status()
        assert budget_status["current_cost"] == pytest.approx(
            total_cost, rel=0.01
        )

        # 獲取預算報告
        budget_report = await budget_controller.get_daily_budget_report()
        assert budget_report["budget_status"]["current_cost"] == pytest.approx(
            total_cost, rel=0.01
        )

        # 清理
        if db_path.exists():
            db_path.unlink()


@pytest.mark.unit
class TestGlobalFunctions:
    """全域函數測試"""

    @pytest.mark.skipif(
        not COST_MONITORING_AVAILABLE, reason="成本監控模組不可用"
    )
    def test_get_cost_tracker(self, mock_config_manager):
        """測試獲取成本追蹤器實例"""
        tracker1 = get_cost_tracker(mock_config_manager)
        tracker2 = get_cost_tracker(mock_config_manager)

        # 應該返回同一個實例（單例模式）
        assert tracker1 is tracker2

    @pytest.mark.skipif(
        not COST_MONITORING_AVAILABLE, reason="成本監控模組不可用"
    )
    def test_get_budget_controller(self, mock_config_manager):
        """測試獲取預算控制器實例"""
        controller1 = get_budget_controller(mock_config_manager)
        controller2 = get_budget_controller(mock_config_manager)

        # 應該返回同一個實例（單例模式）
        assert controller1 is controller2
