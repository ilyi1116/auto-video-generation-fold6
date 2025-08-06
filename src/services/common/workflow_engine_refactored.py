"""
TDD Refactor 階段: 重構後的工作流程引擎
使用責任鏈模式和觀察者模式優化工作流程處理
"""

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# from some_module import (
#     BaseService,
#     ServiceError,
#     TraceContext,
#     handle_service_errors,
# )


class WorkflowState(Enum):
    """工作流程狀態"""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepState(Enum):
    """步驟狀態"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """步驟執行結果"""

    step_name: str
    state: StepState
    start_time: float
    end_time: Optional[float] = None
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metrics: Dict[str, float] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "state": self.state.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "data": self.data,
            "error": self.error,
            "metrics": self.metrics,
        }


@dataclass
class WorkflowContext:
    """工作流程執行上下文"""

    workflow_id: str
    user_id: str
    input_data: Dict[str, Any]
    shared_data: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    trace_context: Optional[Any] = None  # TraceContext
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_step_result(self, step_name: str) -> Optional[StepResult]:
        """獲取步驟結果"""
        return self.step_results.get(step_name)

    def get_step_data(self, step_name: str) -> Dict[str, Any]:
        """獲取步驟數據"""
        result = self.get_step_result(step_name)
        return result.data if result else {}

    def set_shared_data(self, key: str, value: Any) -> None:
        """設定共享數據"""
        self.shared_data[key] = value

    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """獲取共享數據"""
        return self.shared_data.get(key, default)


class WorkflowStep(ABC):
    """工作流程步驟抽象基類 - 責任鏈模式"""

    def __init__(
        self,
        step_name: str,
        next_step: Optional["WorkflowStep"] = None,
        required_steps: Optional[List[str]] = None,
        timeout: float = 300.0,
    ):
        self.step_name = step_name
        self.next_step = next_step
        self.required_steps = required_steps or []
        self.timeout = timeout
        self._observers: List[Callable[[StepResult], None]] = []

    def add_observer(self, observer: Callable[[StepResult], None]) -> None:
        """添加觀察者"""
        self._observers.append(observer)

    def _notify_observers(self, result: StepResult) -> None:
        """通知觀察者"""
        for observer in self._observers:
            try:
                observer(result)
            except Exception:
                # 觀察者錯誤不應影響主流程
                pass

    def _check_prerequisites(self, context: WorkflowContext) -> bool:
        """檢查前置條件"""
        for required_step in self.required_steps:
            result = context.get_step_result(required_step)
            if not result or result.state != StepState.COMPLETED:
                return False
        return True

    @abstractmethod
    async def _execute_step(self, context: WorkflowContext) -> Dict[str, Any]:
        """執行步驟邏輯（子類實作）"""
        pass

    async def execute(self, context: WorkflowContext) -> StepResult:
        """執行步驟"""
        result = StepResult(
            step_name=self.step_name,
            state=StepState.RUNNING,
            start_time=time.time(),
        )

        try:
            # 檢查前置條件
            if not self._check_prerequisites(context):
                result.state = StepState.FAILED
                result.error = f"Prerequisites not met: {self.required_steps}"
                result.end_time = time.time()
                self._notify_observers(result)
                return result

            # 執行步驟邏輯
            step_data = await asyncio.wait_for(
                self._execute_step(context), timeout=self.timeout
            )

            result.data = step_data
            result.state = StepState.COMPLETED
            result.end_time = time.time()
            result.metrics = {
                "execution_time": result.duration or 0,
                "data_size": len(str(result.data)),
                "success": 1,
            }

        except asyncio.TimeoutError:
            result.state = StepState.FAILED
            result.error = f"Step {self.step_name} timed out after {self.timeout} seconds"
            result.end_time = time.time()
            result.metrics = {"timeout": 1, "success": 0}

        except Exception as e:
            result.state = StepState.FAILED
            result.error = str(e)
            result.end_time = time.time()
            result.metrics = {"error": 1, "success": 0}

        finally:
            # 儲存結果到上下文
            context.step_results[self.step_name] = result
            self._notify_observers(result)

        return result

    async def process(self, context: WorkflowContext) -> StepResult:
        """處理當前步驟並繼續到下一步"""
        result = await self.execute(context)

        # 如果步驟失敗且是關鍵步驟，停止處理
        if result.state == StepState.FAILED:
            raise Exception(f"Critical step {self.step_name} failed: {result.error}")

        # 處理下一步
        if self.next_step:
            await self.next_step.process(context)

        return result


class WorkflowStepError(Exception):
    """工作流程步驟錯誤"""

    def __init__(self, message: str, step_name: str, error_code: str = "WORKFLOW_STEP_ERROR", context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.step_name = step_name
        self.error_code = error_code
        self.context = context or {}


# 基本的 BaseService 替代類（如果沒有實際的 BaseService）
class BaseService:
    """基本服務類"""
    
    def __init__(self, service_name: str, version: str, config: Dict[str, Any]):
        self.service_name = service_name
        self.version = version
        self.config = config
        self.logger = None  # 簡化的 logger
    
    def add_health_check(self, name: str, func: Callable) -> None:
        """添加健康檢查"""
        pass
    
    async def start(self) -> None:
        """啟動服務"""
        await self._initialize()
    
    async def stop(self) -> None:
        """停止服務"""
        pass
    
    async def _initialize(self) -> None:
        """初始化服務"""
        pass


class WorkflowEngine(BaseService):
    """重構後的工作流程引擎"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("workflow_engine", "2.0.0", config or {})

        # 工作流程註冊表
        self._workflow_templates: Dict[str, "WorkflowTemplate"] = {}
        self._active_workflows: Dict[str, "WorkflowExecution"] = {}

        # 觀察者
        self._workflow_observers: List[Callable] = []
        self._step_observers: List[Callable] = []

        # 執行統計
        self._execution_stats = {
            "total_workflows": 0,
            "completed_workflows": 0,
            "failed_workflows": 0,
            "active_workflows": 0,
        }

    async def _initialize(self) -> None:
        """初始化工作流程引擎"""
        self.add_health_check("workflow_capacity", self._check_workflow_capacity)
        self.add_health_check("memory_usage", self._check_memory_usage)

    async def start(self) -> None:
        """啟動工作流程引擎"""
        await super().start()
        if self.logger:
            self.logger.info("Workflow engine started")

    async def stop(self) -> None:
        """關閉工作流程引擎"""
        # 取消所有活躍的工作流程
        for workflow_id in list(self._active_workflows.keys()):
            await self.cancel_workflow(workflow_id)
        await super().stop()
        if self.logger:
            self.logger.info("Workflow engine shutdown")

    def _check_workflow_capacity(self) -> bool:
        """檢查工作流程容量"""
        max_workflows = int(self.config.get("max_concurrent_workflows", 100))
        return len(self._active_workflows) < max_workflows

    def _check_memory_usage(self) -> bool:
        """檢查記憶體使用量"""
        # 簡化的記憶體檢查
        return True

    def register_workflow_template(self, template: "WorkflowTemplate") -> None:
        """註冊工作流程範本"""
        self._workflow_templates[template.name] = template
        if self.logger:
            self.logger.info(f"Registered workflow template: {template.name}")

    def add_workflow_observer(self, observer: Callable) -> None:
        """添加工作流程觀察者"""
        self._workflow_observers.append(observer)

    def add_step_observer(self, observer: Callable) -> None:
        """添加步驟觀察者"""
        self._step_observers.append(observer)

    async def start_workflow(
        self,
        template_name: str,
        user_id: str,
        input_data: Dict[str, Any],
        workflow_id: Optional[str] = None,
    ) -> str:
        """啟動工作流程"""
        workflow_id = workflow_id or str(uuid.uuid4())

        # 檢查範本是否存在
        if template_name not in self._workflow_templates:
            raise Exception(f"Workflow template not found: {template_name}")

        template = self._workflow_templates[template_name]

        # 檢查容量
        if not self._check_workflow_capacity():
            raise Exception("Workflow capacity exceeded")

        # 創建執行實例
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            template=template,
            user_id=user_id,
            input_data=input_data,
        )

        # 為所有步驟添加觀察者
        for observer in self._step_observers:
            execution.add_step_observer(observer)

        # 註冊到活躍工作流程
        self._active_workflows[workflow_id] = execution

        # 更新統計
        self._execution_stats["total_workflows"] += 1

        # 通知工作流程觀察者
        for observer in self._workflow_observers:
            try:
                observer("workflows_started", {"template": template_name})
            except Exception:
                pass

        # 啟動執行
        asyncio.create_task(self._execute_workflow(execution))

        if self.logger:
            self.logger.info(f"Started workflow {workflow_id} from template {template_name}")

        return workflow_id

    async def _execute_workflow(self, execution: "WorkflowExecution") -> None:
        """執行工作流程"""
        try:
            # 執行工作流程
            await execution.execute()

            # 更新統計
            self._execution_stats["completed_workflows"] += 1

            # 通知觀察者
            for observer in self._workflow_observers:
                try:
                    observer("workflows_completed", {"template": execution.template.name})
                except Exception:
                    pass

        except Exception as e:
            # 標記為失敗
            execution.state = WorkflowState.FAILED
            execution.error = str(e)
            execution.end_time = time.time()

            # 更新統計
            self._execution_stats["failed_workflows"] += 1

            # 通知觀察者
            for observer in self._workflow_observers:
                try:
                    observer("workflows_failed", {"template": execution.template.name})
                except Exception:
                    pass

            if self.logger:
                self.logger.error(f"Workflow {execution.workflow_id} failed: {e}")

        finally:
            # 從活躍工作流程中移除
            self._active_workflows.pop(execution.workflow_id, None)
            
            # 更新活躍工作流程統計
            self._execution_stats["active_workflows"] = len(self._active_workflows)

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """獲取工作流程狀態"""
        execution = self._active_workflows.get(workflow_id)
        if execution:
            return execution.to_dict()
        return None

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """取消工作流程"""
        execution = self._active_workflows.get(workflow_id)
        if execution:
            await execution.cancel()
            self._active_workflows.pop(workflow_id, None)
            
            if self.logger:
                self.logger.info(f"Cancelled workflow {workflow_id}")
            
            # 通知觀察者
            for observer in self._workflow_observers:
                try:
                    observer("workflows_cancelled", {"template": execution.template.name})
                except Exception:
                    pass
            
            return True
        return False

    def get_engine_stats(self) -> Dict[str, Any]:
        """獲取引擎統計信息"""
        return {
            "stats": self._execution_stats.copy(),
            "templates": list(self._workflow_templates.keys()),
            "active_workflows": list(self._active_workflows.keys()),
        }


@dataclass
class WorkflowTemplate:
    """工作流程範本"""

    name: str
    description: str
    steps: List[WorkflowStep]
    timeout: float = 3600.0  # 預設1小時超時
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_step_chain(self) -> Optional[WorkflowStep]:
        """獲取步驟鏈"""
        if not self.steps:
            return None
        
        # 建立步驟鏈
        for i in range(len(self.steps) - 1):
            self.steps[i].next_step = self.steps[i + 1]
        
        return self.steps[0]


@dataclass
class WorkflowExecution:
    """工作流程執行實例"""

    workflow_id: str
    template: WorkflowTemplate
    user_id: str
    input_data: Dict[str, Any]
    state: WorkflowState = WorkflowState.PENDING
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    error: Optional[str] = None
    retry_count: int = 0
    context: WorkflowContext = field(init=False)

    def __post_init__(self) -> None:
        self.context = WorkflowContext(
            workflow_id=self.workflow_id,
            user_id=self.user_id,
            input_data=self.input_data,
        )

    def add_step_observer(self, observer: Callable[[StepResult], None]) -> None:
        """為所有步驟添加觀察者"""
        for step in self.template.steps:
            step.add_observer(observer)

    async def execute(self) -> None:
        """執行工作流程"""
        self.state = WorkflowState.RUNNING
        
        try:
            # 獲取步驟鏈
            first_step = self.template.get_step_chain()
            if first_step:
                # 執行步驟鏈
                await asyncio.wait_for(
                    first_step.process(self.context),
                    timeout=self.template.timeout
                )
            
            self.state = WorkflowState.COMPLETED
            self.end_time = time.time()

        except asyncio.TimeoutError:
            self.state = WorkflowState.FAILED
            self.error = f"Workflow timed out after {self.template.timeout} seconds"
            self.end_time = time.time()
            raise

        except Exception as e:
            self.state = WorkflowState.FAILED
            self.error = str(e)
            self.end_time = time.time()
            raise

    async def cancel(self) -> None:
        """取消工作流程"""
        self.state = WorkflowState.CANCELLED
        self.end_time = time.time()

    @property
    def duration(self) -> Optional[float]:
        """獲取執行持續時間"""
        if self.end_time:
            return self.end_time - self.start_time
        return None

    def get_progress(self) -> Dict[str, Any]:
        """獲取執行進度"""
        total_steps = len(self.template.steps)
        completed_steps = sum(
            1 for result in self.context.step_results.values()
            if result.state == StepState.COMPLETED
        )
        
        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "progress_percentage": (
                (completed_steps / total_steps * 100) if total_steps > 0 else 0
            ),
        }

    def get_current_step(self) -> Optional[str]:
        """獲取當前執行步驟"""
        for step in self.template.steps:
            result = self.context.step_results.get(step.step_name)
            if not result or result.state in [StepState.PENDING, StepState.RUNNING]:
                return step.step_name
        return None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "workflow_id": self.workflow_id,
            "template_name": self.template.name,
            "user_id": self.user_id,
            "state": self.state.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "error": self.error,
            "retry_count": self.retry_count,
            "progress": self.get_progress(),
            "step_results": {
                name: result.to_dict()
                for name, result in self.context.step_results.items()
            },
            "metadata": self.context.metadata,
        }


# 具體步驟實作範例
class TrendAnalysisStep(WorkflowStep):
    """趨勢分析步驟"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__("trend_analysis", **kwargs)

    async def _execute_step(self, context: WorkflowContext) -> Dict[str, Any]:
        """執行趨勢分析"""
        categories = context.input_data.get("categories", ["technology"])
        platforms = context.input_data.get("platforms", ["tiktok"])

        # 模擬趨勢分析邏輯
        trends_data = {
            "categories": categories,
            "platforms": platforms,
            "hours_back": 24,
            "trends": [],  # 實際應該包含趨勢數據
        }

        # 模擬排序和選擇
        trends = trends_data.get("trends", [])
        if trends:
            top_trends = sorted(
                trends,
                key=lambda t: t.get("engagement_score", 0),
                reverse=True,
            )[:5]
        else:
            top_trends = []

        return {
            "total_trends_analyzed": len(trends_data.get("trends", [])),
            "categories": categories,
            "platforms": platforms,
            "top_trends": top_trends,
        }


class ScriptGenerationStep(WorkflowStep):
    """腳本生成步驟"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            "script_generation", required_steps=["trend_analysis"], **kwargs
        )

    async def _execute_step(self, context: WorkflowContext) -> Dict[str, Any]:
        """執行腳本生成"""
        trends_data = context.get_step_data("trend_analysis")
        top_trends = trends_data.get("top_trends", [])

        if not top_trends:
            raise Exception("No trends available for script generation")

        # 選擇主要趨勢
        main_trend = top_trends[0] if top_trends else {}

        # 模擬腳本生成
        script_params = {
            "trend_keyword": main_trend.get("keyword"),
            "platform": context.input_data.get("platforms", ["tiktok"])[0],
            "duration": context.input_data.get("duration", 30),
        }

        # 這裡應該調用 AI 服務生成腳本
        script_data = {"script": "Generated script content", "title": "Generated title", "description": "Generated description"}

        return {
            "script": script_data.get("script"),
            "title": script_data.get("title"),
            "description": script_data.get("description"),
            "script_params": script_params,
            "main_trend": main_trend,
        }