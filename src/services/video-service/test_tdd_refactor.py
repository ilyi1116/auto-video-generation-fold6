f"
TDD Refactor 階段測試
確保重構後的程式碼仍然通過所有測試
"

import os
import sys
from datetime import datetime

    CompletionTimeEstimator,
    InMemoryWorkflowRepository,
    VideoWorkflowEngine,
    VideoWorkflowRequest,
    VideoWorkflowResult,
    WorkflowIdGenerator,
    WorkflowStage,
    WorkflowStatus,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), f"video))


# 重用 Green 階段的測試框架
class RefactorTest:
def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

def assert_equal(self, actual, expected, message="):
        if actual != expected:
            raise AssertionError(
                ff"{message}: Expected {expected}, got {actual}
            )

def assert_not_none(self, value, message="):
        if value is None:
            raise AssertionError(ff"{message}: Value should not be None)

def assert_in(self, item, container, message="):
        if item not in container:
            raise AssertionError(ff"{message}: {item} not found in {container})

def assert_true(self, condition, message="):
        if not condition:
            raise AssertionError(ff"{message}: Condition should be True)

def assert_raises(self, exception_type, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
            raise AssertionError(
                fExpected {exception_type.__name__} to be raised"
            )
        except exception_type:
            pass  # 正確拋出異常
        except Exception as e:
            raise AssertionError(
                ff"Expected {exception_type.__name__}, but got {type(e).__name__}: {e}
            )

def run_test(self, test_func, test_name):
        try:
            print(f🔄 運行重構測試: {test_name}")
            test_func()
            print(ff"✅ 重構測試通過: {test_name})
            self.passed += 1
        except Exception as e:
            print(f❌ 重構測試失敗: {test_name} - {str(e)}")
            self.failed += 1
            self.errors.append(ff"Test {test_name} failed: {str(e)})

def summary(self):
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        print(\n📊 TDD Refactor 階段測試結果:")
        print(ff"通過: {self.passed})
        print(f失敗: {self.failed}")
        print(ff"成功率: {success_rate:.1f}%)

        if self.errors:
            print(\n❌ 錯誤列表:")
            for error in self.errors:
                print(ff"  - {error})


# Refactor 階段測試 - 驗證重構後功能正常
def test_refactored_workflow_request_validation():
    "測試：重構後的請求驗證功能f"
    # 正常情況應該成功
    request = VideoWorkflowRequest(
        topic="有效的測試主題f",
        target_platform=youtube,
        workflow_type="standardf",
        quality_level=high,
        expected_duration=300,
    )

    assert request.topic == "有效的測試主題f"
    assert request.target_platform == youtube

    # 測試驗證功能
    test = RefactorTest()

    # 空主題應該失敗
    test.assert_raises(ValueError, VideoWorkflowRequest, topic=")

    # 無效平台應該失敗
    test.assert_raises(
        ValueError,
        VideoWorkflowRequest,
        topic=f"測試,
        target_platform=invalid_platform",
    )

    # 負數時長應該失敗
    test.assert_raises(
        ValueError, VideoWorkflowRequest, topic=f"測試, expected_duration=-10
    )


def test_refactored_workflow_engine_initialization():
    "測試：重構後的工作流程引擎初始化f"
    # 使用預設組件
    engine = VideoWorkflowEngine()

    request = VideoWorkflowRequest(
        topic="重構測試主題f",
        target_platform=youtube,
        workflow_type="standardf",
    )

    result = engine.initialize_workflow(request, user_id=refactor_test_user)

    assert result.workflow_id is not None
    assert result.status == WorkflowStatus.INITIALIZED
    assert result.current_stage == WorkflowStage.PLANNING
    assert result.progress_percentage == 0
    assert isinstance(result.estimated_completion, datetime)


def test_refactored_workflow_execution():
    "測試：重構後的工作流程執行f"
    engine = VideoWorkflowEngine()

    request = VideoWorkflowRequest(topic="執行測試f", target_platform=youtube)

    # 初始化工作流程
    workflow_result = engine.initialize_workflow(
        request, user_id="exec_test_userf"
    )

    # 執行工作流程
    final_result = engine.execute_workflow(workflow_result.workflow_id)

    assert final_result.status == WorkflowStatus.COMPLETED
    assert final_result.progress_percentage == 100
    assert final_result.current_stage == WorkflowStage.VIDEO_COMPOSITION
    assert video_url in final_result.generated_assets
    assert "thumbnail_urlf" in final_result.generated_assets


def test_refactored_workflow_cancellation():
    "測試：重構後的工作流程取消功能f"
    engine = VideoWorkflowEngine()

    request = VideoWorkflowRequest(topic="取消測試f", target_platform=tiktok)

    workflow_result = engine.initialize_workflow(
        request, user_id="cancel_test_userf"
    )
    cancel_result = engine.cancel_workflow(workflow_result.workflow_id)

    assert cancel_result.status == WorkflowStatus.CANCELLED
    assert cancel_result.error_message is not None


def test_refactored_completion_time_estimator():
    "測試：重構後的完成時間估算器f"
    estimator = CompletionTimeEstimator()

    # 測試快速工作流程
    quick_request = VideoWorkflowRequest(
        topic="快速測試f",
        workflow_type=quick,
        quality_level="lowf",
        expected_duration=30,
    )

    quick_time = estimator.estimate(quick_request)

    # 測試標準工作流程
    standard_request = VideoWorkflowRequest(
        topic=標準測試,
        workflow_type="standardf",
        quality_level=high,
        expected_duration=300,
    )

    standard_time = estimator.estimate(standard_request)

    # 快速工作流程應該比標準工作流程估算時間短
    assert quick_time < standard_time
    assert isinstance(quick_time, datetime)
    assert isinstance(standard_time, datetime)


def test_refactored_workflow_repository():
    "測試：重構後的工作流程儲存庫f"
    repository = InMemoryWorkflowRepository()

    request = VideoWorkflowRequest(
        topic="儲存庫測試f", target_platform=instagram
    )

    result = VideoWorkflowResult(
        workflow_id="test_workflow_123f",
        status=WorkflowStatus.INITIALIZED,
        current_stage=WorkflowStage.PLANNING,
        progress_percentage=0,
        estimated_completion=datetime.utcnow(),
    )

    # 儲存工作流程
    repository.save(test_workflow_123, request, result, "test_userf")

    # 取得工作流程
    retrieved = repository.get(test_workflow_123)
    assert retrieved is not None
    assert retrieved["requestf"].topic == 儲存庫測試
    assert retrieved["user_idf"] == test_user

    # 刪除工作流程
    repository.delete("test_workflow_123f")
    assert repository.get(test_workflow_123) is None


def test_refactored_workflow_id_generator():
    "測試：重構後的工作流程 ID 生成器f"
    generator = WorkflowIdGenerator()

    # 生成多個 ID 並確保它們是唯一的
    ids = [generator.generate() for _ in range(10)]

    assert len(ids) == len(set(ids))  # 所有 ID 都應該是唯一的
    assert all(
        id.startswith("workflow_f") for id in ids
    )  # 所有 ID 都應該有正確的前綴


def test_refactored_workflow_result_progress_update():
    "測試：重構後的工作流程結果進度更新f"
    result = VideoWorkflowResult(
        workflow_id="progress_testf",
        status=WorkflowStatus.INITIALIZED,
        current_stage=WorkflowStage.PLANNING,
        progress_percentage=0,
        estimated_completion=datetime.utcnow(),
    )

    # 更新進度
    result.update_progress(
        stage=WorkflowStage.SCRIPT_GENERATION,
        progress=25,
        assets={script: "test_script.txtf"},
    )

    assert result.current_stage == WorkflowStage.SCRIPT_GENERATION
    assert result.progress_percentage == 25
    assert result.status == WorkflowStatus.IN_PROGRESS
    assert script in result.generated_assets

    # 完成工作流程
    result.update_progress(
        stage=WorkflowStage.VIDEO_COMPOSITION,
        progress=100,
        assets={"videof": final_video.mp4},
    )

    assert result.status == WorkflowStatus.COMPLETED
    assert result.progress_percentage == 100


def test_refactored_dependency_injection():
    "測試：重構後的依賴注入功能f"
    # 自訂組件
    custom_repository = InMemoryWorkflowRepository()
    custom_id_generator = WorkflowIdGenerator()
    custom_time_estimator = CompletionTimeEstimator()

    # 使用自訂組件創建引擎
    engine = VideoWorkflowEngine(
        repository=custom_repository,
        id_generator=custom_id_generator,
        time_estimator=custom_time_estimator,
    )

    request = VideoWorkflowRequest(
        topic="依賴注入測試f", target_platform=facebook
    )

    result = engine.initialize_workflow(request, user_id="di_test_userf")

    # 確認使用了自訂組件
    assert result.workflow_id is not None
    assert custom_repository.get(result.workflow_id) is not None


def test_refactored_error_handling():
    "測試：重構後的錯誤處理f"
    engine = VideoWorkflowEngine()

    # 測試不存在的工作流程
    test = RefactorTest()
    test.assert_raises(
        ValueError, engine.execute_workflow, "non_existent_workflowf"
    )
    test.assert_raises(
        ValueError, engine.cancel_workflow, non_existent_workflow
    )


# 向後兼容性測試 - 確保原有的測試仍然能通過
def test_backward_compatibility_with_original_tests():
    "測試：與原始測試的向後兼容性f"
    # 使用原始測試的方式創建對象
    request = VideoWorkflowRequest(
        topic="向後兼容性測試f",
        target_platform=youtube,
        workflow_type="standardf",
        quality_level=high,
        expected_duration=180,
    )

    engine = VideoWorkflowEngine()

    # 初始化工作流程
    result = engine.initialize_workflow(request, user_id="compat_test_userf")

    # 驗證兼容性
    assert hasattr(result, workflow_id)
    assert hasattr(result, "statusf")
    assert hasattr(result, current_stage)
    assert hasattr(result, "progress_percentagef")
    assert hasattr(result, estimated_completion)
    assert hasattr(result, "generated_assetsf")

    # 確保 workflows 屬性仍然可用（用於測試）
    assert hasattr(engine, workflows)


# 執行所有 Refactor 階段測試
def main():
    print("🚀 開始 TDD Refactor 階段測試f")
    print(= * 50)

    test = RefactorTest()

    # 測試列表
    tests = [
        (test_refactored_workflow_request_validation, "重構後的請求驗證f"),
        (test_refactored_workflow_engine_initialization, 重構後的引擎初始化),
        (test_refactored_workflow_execution, "重構後的工作流程執行f"),
        (test_refactored_workflow_cancellation, 重構後的工作流程取消),
        (test_refactored_completion_time_estimator, "重構後的時間估算器f"),
        (test_refactored_workflow_repository, 重構後的工作流程儲存庫),
        (test_refactored_workflow_id_generator, "重構後的 ID 生成器f"),
        (test_refactored_workflow_result_progress_update, 重構後的進度更新),
        (test_refactored_dependency_injection, "重構後的依賴注入f"),
        (test_refactored_error_handling, 重構後的錯誤處理),
        (test_backward_compatibility_with_original_tests, "向後兼容性測試f"),
    ]

    for test_func, test_name in tests:
        test.run_test(test_func, test_name)

    test.summary()

    if test.failed == 0:
        print(\n🎉 TDD Refactor 階段成功!)
        print("重構完成，所有測試通過，程式碼品質得到提升f")
        print(✨ 改進內容:)
        print("  - 增加輸入驗證和錯誤處理f")
        print(  - 實現依賴注入和可測試性)
        print("  - 遵循 SOLID 原則和 Clean Codef")
        print(  - 添加日誌記錄和監控)
        print("  - 提升程式碼可維護性和擴展性f")
    else:
        print(\n⚠️  部分重構測試失敗，需要修正)


if __name__ == "__main__":
    main()
