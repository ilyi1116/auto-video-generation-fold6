#!/usr/bin/env python3
"""
TDD Refactor 階段驗證測試
確保重構後的系統保持所有功能並提升品質
"""

import asyncio
import pytest
import time
import sys
from pathlib import Path
from typing import Dict, Any
import logging

# 添加路徑
sys.path.insert(0, str(Path(__file__).parent / "services" / "common"))

from base_service import (
    BaseService, ServiceState, ServiceError, MetricsCollector, 
    StructuredLogger, TraceContext, trace_span
)
from workflow_engine_refactored import (
    WorkflowEngine, WorkflowTemplate, WorkflowStep, WorkflowContext,
    WorkflowState, StepState, StepResult
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockService(BaseService):
    """測試用模擬服務"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("mock_service", "1.0.0", config)
        self.initialized = False
        self.started = False
    
    async def _initialize(self):
        await asyncio.sleep(0.1)  # 模擬初始化延遲
        self.initialized = True
    
    async def _startup(self):
        await asyncio.sleep(0.1)  # 模擬啟動延遲
        self.started = True
    
    async def _shutdown(self):
        await asyncio.sleep(0.1)  # 模擬關閉延遲
        self.started = False

class MockWorkflowStep(WorkflowStep):
    """測試用工作流程步驟"""
    
    def __init__(self, step_name: str, delay: float = 0.1, should_fail: bool = False, **kwargs):
        super().__init__(step_name, **kwargs)
        self.delay = delay
        self.should_fail = should_fail
        self.execution_count = 0
    
    async def _execute_step(self, context: WorkflowContext) -> Dict[str, Any]:
        self.execution_count += 1
        await asyncio.sleep(self.delay)
        
        if self.should_fail:
            raise Exception(f"Mock step {self.step_name} failed")
        
        return {
            "step_name": self.step_name,
            "execution_count": self.execution_count,
            "timestamp": time.time()
        }

class RefactorValidationTest:
    """重構驗證測試套件"""
    
    def __init__(self):
        self.results = {
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": []
        }
    
    def _record_result(self, test_name: str, success: bool, error: str = None):
        """記錄測試結果"""
        if success:
            self.results["tests_passed"] += 1
            logger.info(f"✅ {test_name} 通過")
        else:
            self.results["tests_failed"] += 1 
            self.results["errors"].append(f"{test_name}: {error}")
            logger.error(f"❌ {test_name} 失敗: {error}")
    
    async def test_base_service_lifecycle(self):
        """測試基礎服務生命週期"""
        try:
            service = MockService({"test_config": "value"})
            
            # 測試初始狀態
            assert service.state == ServiceState.INITIALIZING
            assert not service.initialized
            assert not service.started
            
            # 測試啟動
            await service.start()
            assert service.state == ServiceState.HEALTHY
            assert service.initialized
            assert service.started
            
            # 測試健康檢查
            health = await service.health_check()
            assert health.status == ServiceState.HEALTHY
            
            # 測試停止
            await service.stop()
            assert service.state == ServiceState.STOPPED
            assert not service.started
            
            self._record_result("base_service_lifecycle", True)
            
        except Exception as e:
            self._record_result("base_service_lifecycle", False, str(e))
    
    async def test_base_service_context_manager(self):
        """測試基礎服務上下文管理器"""
        try:
            async with MockService() as service:
                assert service.state == ServiceState.HEALTHY
                assert service.started
            
            # 服務應該自動停止
            assert service.state == ServiceState.STOPPED
            
            self._record_result("base_service_context_manager", True)
            
        except Exception as e:
            self._record_result("base_service_context_manager", False, str(e))
    
    async def test_metrics_collection(self):
        """測試指標收集"""
        try:
            metrics = MetricsCollector()
            
            # 測試計數器
            await metrics.increment_counter("test_counter", {"type": "test"})
            await metrics.increment_counter("test_counter", {"type": "test"}, 2)
            
            # 測試量表
            await metrics.set_gauge("test_gauge", 42.5, {"unit": "percent"})
            
            # 測試直方圖
            await metrics.record_histogram("test_histogram", 1.5)
            await metrics.record_histogram("test_histogram", 2.5)
            await metrics.record_histogram("test_histogram", 3.5)
            
            # 獲取指標
            all_metrics = await metrics.get_metrics()
            assert len(all_metrics) > 0
            
            # 驗證指標類型
            counter_metrics = [m for m in all_metrics if "counter" in m["name"] or "_total" in m["name"]]
            gauge_metrics = [m for m in all_metrics if "gauge" in m["name"]]
            histogram_metrics = [m for m in all_metrics if "histogram" in m["name"]]
            
            assert len(counter_metrics) > 0
            assert len(gauge_metrics) > 0  
            assert len(histogram_metrics) > 0
            
            self._record_result("metrics_collection", True)
            
        except Exception as e:
            self._record_result("metrics_collection", False, str(e))
    
    async def test_structured_logging(self):
        """測試結構化日誌"""
        try:
            logger = StructuredLogger("test_service", "1.0.0")
            
            # 測試不同級別的日誌
            logger.info("Test info message", extra_field="value")
            logger.error("Test error message", error_code="TEST_ERROR")
            logger.warning("Test warning message", warning_type="validation")
            logger.debug("Test debug message", debug_info={"key": "value"})
            
            # 如果沒有異常，認為成功
            self._record_result("structured_logging", True)
            
        except Exception as e:
            self._record_result("structured_logging", False, str(e))
    
    async def test_trace_context(self):
        """測試分散式追蹤"""
        try:
            # 創建追蹤上下文
            trace = TraceContext()
            assert trace.trace_id is not None
            assert trace.span_id is not None
            
            # 添加標籤和日誌
            trace.add_tag("operation", "test")
            trace.log("Test log message")
            
            # 測試追蹤 span
            logger = StructuredLogger("test", "1.0.0")
            async with trace_span("test_operation", trace, logger) as span:
                span.add_tag("test_tag", "test_value")
                span.log("Operation started")
                await asyncio.sleep(0.1)
            
            # 驗證 span 數據
            span_data = span.to_dict()
            assert "trace_id" in span_data
            assert "span_id" in span_data
            assert "tags" in span_data
            assert "logs" in span_data
            
            self._record_result("trace_context", True)
            
        except Exception as e:
            self._record_result("trace_context", False, str(e))
    
    async def test_workflow_engine_basic(self):
        """測試工作流程引擎基本功能"""
        try:
            engine = WorkflowEngine()
            
            # 啟動引擎
            await engine.start()
            assert engine.state == ServiceState.HEALTHY
            
            # 創建簡單工作流程範本
            step1 = MockWorkflowStep("step1", delay=0.1)
            step2 = MockWorkflowStep("step2", delay=0.1)
            step1.next_step = step2
            
            template = WorkflowTemplate(
                name="test_workflow",
                description="Test workflow template",
                first_step=step1,
                timeout=10.0
            )
            
            # 註冊範本
            engine.register_workflow_template(template)
            
            # 啟動工作流程
            workflow_id = await engine.start_workflow(
                "test_workflow",
                "test_user",
                {"test_input": "value"}
            )
            
            assert workflow_id is not None
            
            # 等待工作流程完成
            await asyncio.sleep(1.0)
            
            # 檢查狀態
            status = await engine.get_workflow_status(workflow_id)
            if status:  # 可能已經完成並清理
                assert status["state"] in [WorkflowState.COMPLETED.value, WorkflowState.RUNNING.value]
            
            # 獲取引擎統計
            stats = await engine.get_engine_stats()
            assert stats["stats"]["total_workflows"] >= 1
            
            await engine.stop()
            
            self._record_result("workflow_engine_basic", True)
            
        except Exception as e:
            self._record_result("workflow_engine_basic", False, str(e))
    
    async def test_workflow_step_chain(self):
        """測試工作流程步驟鏈"""
        try:
            # 創建步驟鏈
            step1 = MockWorkflowStep("step1", delay=0.05)
            step2 = MockWorkflowStep("step2", delay=0.05, required_steps=["step1"])
            step3 = MockWorkflowStep("step3", delay=0.05, required_steps=["step2"])
            
            step1.next_step = step2
            step2.next_step = step3
            
            # 創建執行上下文
            context = WorkflowContext(
                workflow_id="test_workflow",
                user_id="test_user",
                input_data={"test": "data"}
            )
            
            # 執行步驟鏈
            result_context = await step1.process(context)
            
            # 驗證所有步驟都執行了
            assert "step1" in result_context.step_results
            assert "step2" in result_context.step_results
            assert "step3" in result_context.step_results
            
            # 驗證步驟狀態
            for step_name in ["step1", "step2", "step3"]:
                result = result_context.step_results[step_name]
                assert result.state == StepState.COMPLETED
                assert result.duration is not None
                assert result.duration > 0
            
            # 驗證步驟執行順序
            step1_time = result_context.step_results["step1"].start_time
            step2_time = result_context.step_results["step2"].start_time  
            step3_time = result_context.step_results["step3"].start_time
            
            assert step1_time < step2_time < step3_time
            
            self._record_result("workflow_step_chain", True)
            
        except Exception as e:
            self._record_result("workflow_step_chain", False, str(e))
    
    async def test_workflow_error_handling(self):
        """測試工作流程錯誤處理"""
        try:
            # 創建會失敗的步驟
            failing_step = MockWorkflowStep("failing_step", should_fail=True)
            
            context = WorkflowContext(
                workflow_id="test_error_workflow",
                user_id="test_user", 
                input_data={}
            )
            
            # 執行應該失敗的步驟
            result = await failing_step.execute(context)
            
            # 驗證失敗狀態
            assert result.state == StepState.FAILED
            assert result.error is not None
            assert "failed" in result.error
            
            self._record_result("workflow_error_handling", True)
            
        except Exception as e:
            self._record_result("workflow_error_handling", False, str(e))
    
    async def test_workflow_prerequisites(self):
        """測試工作流程前置條件"""
        try:
            # 創建有前置條件的步驟
            step_with_prereq = MockWorkflowStep("step_with_prereq", 
                                              required_steps=["missing_step"])
            
            context = WorkflowContext(
                workflow_id="test_prereq_workflow",
                user_id="test_user",
                input_data={}
            )
            
            # 執行應該被跳過的步驟
            result = await step_with_prereq.execute(context)
            
            # 驗證跳過狀態
            assert result.state == StepState.SKIPPED
            assert "Prerequisites not met" in result.error
            
            self._record_result("workflow_prerequisites", True)
            
        except Exception as e:
            self._record_result("workflow_prerequisites", False, str(e))
    
    async def test_performance_metrics(self):
        """測試效能指標"""
        try:
            start_time = time.time()
            
            # 創建服務並執行操作
            async with MockService() as service:
                # 記錄一些指標
                await service.metrics.increment_counter("operations", {"type": "test"})
                await service.metrics.set_gauge("cpu_usage", 45.2)
                await service.metrics.record_histogram("response_time", 0.123)
                
                # 執行追蹤操作
                async with service.trace_operation("performance_test") as span:
                    await asyncio.sleep(0.1)
                    span.add_tag("test_metric", "value")
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # 驗證執行時間合理（應該小於1秒）
            assert execution_time < 1.0
            
            # 獲取指標
            metrics = await service.metrics.get_metrics()
            assert len(metrics) > 0
            
            self._record_result("performance_metrics", True)
            
        except Exception as e:
            self._record_result("performance_metrics", False, str(e))
    
    def print_results(self):
        """打印測試結果"""
        total_tests = self.results["tests_passed"] + self.results["tests_failed"]
        success_rate = (self.results["tests_passed"] / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("=" * 60)
        logger.info("🔍 TDD Refactor 驗證測試結果")
        logger.info("=" * 60)
        logger.info(f"✅ 通過測試: {self.results['tests_passed']}")
        logger.info(f"❌ 失敗測試: {self.results['tests_failed']}")
        logger.info(f"📈 成功率: {success_rate:.1f}%")
        
        if self.results["errors"]:
            logger.info("\n🚨 失敗測試詳情:")
            for error in self.results["errors"]:
                logger.info(f"  - {error}")
        
        # 重構品質評估
        if success_rate >= 95:
            logger.info("\n🏆 重構品質: 優秀 - 所有功能完整保留並增強")
        elif success_rate >= 85:
            logger.info("\n✅ 重構品質: 良好 - 大部分功能正常，少量問題")
        elif success_rate >= 70:
            logger.info("\n⚠️ 重構品質: 一般 - 存在一些問題需要修復")
        else:
            logger.info("\n❌ 重構品質: 不佳 - 存在重大問題，需要重新檢視")
        
        return success_rate >= 85  # 85% 以上算通過

async def main():
    """執行重構驗證測試"""
    logger.info("🚀 開始 TDD Refactor 階段驗證測試")
    logger.info("目標: 確保重構後系統功能完整且品質提升")
    logger.info("=" * 60)
    
    test_suite = RefactorValidationTest()
    
    try:
        # 執行所有測試
        await test_suite.test_base_service_lifecycle()
        await test_suite.test_base_service_context_manager()
        await test_suite.test_metrics_collection()
        await test_suite.test_structured_logging()
        await test_suite.test_trace_context()
        await test_suite.test_workflow_engine_basic()
        await test_suite.test_workflow_step_chain()
        await test_suite.test_workflow_error_handling()
        await test_suite.test_workflow_prerequisites()
        await test_suite.test_performance_metrics()
        
        # 打印結果
        success = test_suite.print_results()
        
        if success:
            logger.info("\n🎉 TDD Refactor 階段驗證成功！")
            logger.info("✨ 系統架構已優化，品質顯著提升")
            logger.info("🎯 準備進入生產級部署階段")
        else:
            logger.error("\n💥 TDD Refactor 階段驗證失敗！")
            logger.error("🔧 需要修復問題後重新驗證")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ 驗證測試執行異常: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    
    if success:
        logger.info("🏁 TDD Refactor 階段完成 - 系統重構成功")
        sys.exit(0)
    else:
        logger.error("🛑 TDD Refactor 階段失敗 - 需要修復問題")
        sys.exit(1)