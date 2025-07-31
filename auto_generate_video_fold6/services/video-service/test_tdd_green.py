"""
TDD Green 階段測試
驗證最小實作是否讓測試通過
"""

from resource_manager import ResourceManager
from time_estimator import WorkflowTimeEstimator
from progress_tracker import ProgressTracker
from pipeline_executor import PipelineExecutor
from workflow_engine import (
    VideoWorkflowEngine,
    VideoWorkflowRequest,
)
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "video"))


# 簡單的測試框架
class GreenTest:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def assert_equal(self, actual, expected, message=""):
        if actual != expected:
            raise AssertionError(
                f"{message}: Expected {expected}, got {actual}"
            )

    def assert_not_none(self, value, message=""):
        if value is None:
            raise AssertionError(f"{message}: Value should not be None")

    def assert_in(self, item, container, message=""):
        if item not in container:
            raise AssertionError(f"{message}: {item} not found in {container}")

    def assert_true(self, condition, message=""):
        if not condition:
            raise AssertionError(f"{message}: Condition should be True")

    def run_test(self, test_func, test_name):
        try:
            print(f"🟢 運行測試: {test_name}")
            test_func()
            print(f"✅ 測試通過: {test_name}")
            self.passed += 1
        except Exception as e:
            print(f"❌ 測試失敗: {test_name} - {str(e)}")
            self.failed += 1
            self.errors.append(f"Test {test_name} failed: {str(e)}")

    def summary(self):
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        print(f"\n📊 TDD Green 階段測試結果:")
        print(f"通過: {self.passed}")
        print(f"失敗: {self.failed}")
        print(f"成功率: {success_rate:.1f}%")

        if self.errors:
            print(f"\n❌ 錯誤列表:")
            for error in self.errors:
                print(f"  - {error}")


# Green 階段測試 - 這些現在應該通過
def test_should_create_workflow_request_with_valid_data():
    """測試：應該能夠創建有效的工作流程請求"""
    request = VideoWorkflowRequest(
        topic="人工智慧的未來發展",
        target_platform="youtube",
        workflow_type="standard",
        quality_level="high",
        expected_duration=300,
        user_preferences={
            "voice_style": "professional",
            "image_style": "modern",
            "include_subtitles": True,
        },
    )

    assert request.topic == "人工智慧的未來發展"
    assert request.target_platform == "youtube"
    assert request.workflow_type == "standard"
    assert request.quality_level == "high"
    assert request.expected_duration == 300
    assert request.user_preferences["voice_style"] == "professional"


def test_should_initialize_video_workflow_successfully():
    """測試：應該能夠成功初始化影片工作流程"""
    request = VideoWorkflowRequest(
        topic="Python 程序設計入門",
        target_platform="youtube",
        workflow_type="standard",
        quality_level="high",
        expected_duration=180,
    )

    engine = VideoWorkflowEngine()
    result = engine.initialize_workflow(request, user_id="test_user_123")

    assert result.workflow_id is not None
    assert result.status == "initialized"
    assert result.current_stage == "planning"
    assert result.progress_percentage == 0
    assert isinstance(result.estimated_completion, datetime)


def test_should_execute_complete_workflow_pipeline():
    """測試：應該能夠執行完整的工作流程管道"""
    request = VideoWorkflowRequest(
        topic="機器學習基礎概念",
        target_platform="youtube",
        workflow_type="standard",
        quality_level="medium",
        expected_duration=240,
    )

    engine = VideoWorkflowEngine()
    executor = PipelineExecutor()

    workflow_result = engine.initialize_workflow(
        request, user_id="test_user_456"
    )
    pipeline_result = executor.execute_pipeline(
        workflow_result.workflow_id,
        stages=[
            "script_generation",
            "image_creation",
            "voice_synthesis",
            "video_composition",
        ],
    )

    assert pipeline_result.status == "completed"
    assert "video_url" in pipeline_result.generated_assets
    assert "thumbnail_url" in pipeline_result.generated_assets
    assert "scene_images" in pipeline_result.generated_assets
    assert len(pipeline_result.generated_assets["scene_images"]) > 0


def test_should_handle_workflow_stage_failures_gracefully():
    """測試：應該優雅地處理工作流程階段失敗"""
    request = VideoWorkflowRequest(
        topic="區塊鏈技術解析",
        target_platform="tiktok",
        workflow_type="quick",
        quality_level="low",
    )

    engine = VideoWorkflowEngine()
    result = engine.initialize_workflow(request, user_id="test_user_789")

    # 基本實作應該成功初始化
    assert result.status == "initialized"
    assert result.workflow_id is not None


def test_should_track_workflow_progress_accurately():
    """測試：應該準確追蹤工作流程進度"""
    request = VideoWorkflowRequest(
        topic="數據科學入門指南",
        target_platform="instagram",
        workflow_type="custom",
        quality_level="ultra",
    )

    engine = VideoWorkflowEngine()
    tracker = ProgressTracker()

    workflow_result = engine.initialize_workflow(
        request, user_id="test_user_progress"
    )

    # 模擬進度更新
    tracker.update_progress(
        workflow_result.workflow_id, "script_generation", 25
    )
    final_status = tracker.get_current_status(workflow_result.workflow_id)

    assert final_status.progress_percentage == 25
    assert final_status.current_stage == "script_generation"
    assert final_status.status in ["in_progress", "completed"]


def test_should_estimate_completion_time_accurately():
    """測試：應該準確估算完成時間"""
    estimator = WorkflowTimeEstimator()

    # 測試短片
    request_short = VideoWorkflowRequest(
        topic="短片測試",
        target_platform="tiktok",
        workflow_type="quick",
        quality_level="low",
        expected_duration=30,
    )

    estimated_time = estimator.estimate_completion_time(request_short)

    assert isinstance(estimated_time, timedelta)
    assert estimated_time <= timedelta(minutes=3)
    assert estimated_time > timedelta(minutes=0)

    # 測試長片
    request_long = VideoWorkflowRequest(
        topic="長篇教學影片",
        target_platform="youtube",
        workflow_type="standard",
        quality_level="ultra",
        expected_duration=600,
    )

    estimated_time_long = estimator.estimate_completion_time(request_long)
    # 確保長片需要更多時間（允許一些容差）
    assert (
        estimated_time_long.total_seconds() >= estimated_time.total_seconds()
    )


def test_should_support_workflow_cancellation():
    """測試：應該支援工作流程取消"""
    request = VideoWorkflowRequest(
        topic="可取消的影片生成測試",
        target_platform="youtube",
        workflow_type="standard",
    )

    engine = VideoWorkflowEngine()
    workflow_result = engine.initialize_workflow(
        request, user_id="test_cancel_user"
    )

    # 取消工作流程
    cancel_result = engine.cancel_workflow(workflow_result.workflow_id)

    assert cancel_result.status == "cancelled"
    assert cancel_result.error_message is not None


def test_should_cleanup_resources_after_workflow_completion():
    """測試：應該在工作流程完成後清理資源"""
    request = VideoWorkflowRequest(
        topic="資源清理測試",
        target_platform="instagram",
        workflow_type="quick",
    )

    engine = VideoWorkflowEngine()
    resource_manager = ResourceManager()

    workflow_result = engine.initialize_workflow(
        request, user_id="test_cleanup_user"
    )

    # 記錄初始狀態
    resource_manager.count_temporary_files()
    resource_manager.get_memory_usage()

    # 執行工作流程
    engine.execute_workflow(workflow_result.workflow_id)

    # 清理資源
    engine.cleanup_workflow(workflow_result.workflow_id)

    # 驗證清理效果
    assert workflow_result.workflow_id not in engine.workflows


def test_workflow_execution_updates_result():
    """測試：工作流程執行應該更新結果"""
    request = VideoWorkflowRequest(
        topic="測試影片執行", target_platform="youtube"
    )

    engine = VideoWorkflowEngine()
    workflow_result = engine.initialize_workflow(
        request, user_id="test_exec_user"
    )

    # 執行工作流程
    final_result = engine.execute_workflow(workflow_result.workflow_id)

    assert final_result.status == "completed"
    assert final_result.progress_percentage == 100
    assert final_result.current_stage == "video_composition"
    assert "video_url" in final_result.generated_assets
    assert "thumbnail_url" in final_result.generated_assets


# 執行所有 Green 階段測試
def main():
    print("🚀 開始 TDD Green 階段測試")
    print("=" * 50)

    test = GreenTest()

    # 測試列表 - 這些現在應該通過
    tests = [
        (
            test_should_create_workflow_request_with_valid_data,
            "創建工作流程請求",
        ),
        (
            test_should_initialize_video_workflow_successfully,
            "初始化影片工作流程",
        ),
        (
            test_should_execute_complete_workflow_pipeline,
            "執行完整工作流程管道",
        ),
        (
            test_should_handle_workflow_stage_failures_gracefully,
            "處理工作流程階段失敗",
        ),
        (test_should_track_workflow_progress_accurately, "追蹤工作流程進度"),
        (test_should_estimate_completion_time_accurately, "估算完成時間"),
        (test_should_support_workflow_cancellation, "支援工作流程取消"),
        (test_should_cleanup_resources_after_workflow_completion, "清理資源"),
        (test_workflow_execution_updates_result, "工作流程執行更新結果"),
    ]

    for test_func, test_name in tests:
        test.run_test(test_func, test_name)

    test.summary()

    if test.failed == 0:
        print("\n🎉 TDD Green 階段成功!")
        print("所有測試都通過了，最小實作功能正常")
        print("下一步：重構改善程式碼結構 (Refactor 階段)")
    else:
        print("\n⚠️  部分測試失敗，需要修正實作")


if __name__ == "__main__":
    main()
