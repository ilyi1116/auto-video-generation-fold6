"""
TDD Refactor 階段: 重構後的工作流程引擎
使用責任鏈模式和觀察者模式優化工作流程處理
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Union
import time

from base_service import BaseService, ServiceError, TraceContext, handle_service_errors

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
            "metrics": self.metrics
        }

@dataclass 
class WorkflowContext:
    """工作流程執行上下文"""
    workflow_id: str
    user_id: str
    input_data: Dict[str, Any]
    shared_data: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, StepResult] = field(default_factory=dict)
    trace_context: Optional[TraceContext] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_step_result(self, step_name: str) -> Optional[StepResult]:
        """獲取步驟結果"""
        return self.step_results.get(step_name)
    
    def get_step_data(self, step_name: str) -> Dict[str, Any]:
        """獲取步驟數據"""
        result = self.get_step_result(step_name)
        return result.data if result else {}
    
    def set_shared_data(self, key: str, value: Any):
        """設定共享數據"""
        self.shared_data[key] = value
    
    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """獲取共享數據"""
        return self.shared_data.get(key, default)

class WorkflowStep(ABC):
    """工作流程步驟抽象基類 - 責任鏈模式"""
    
    def __init__(self, 
                 step_name: str,
                 next_step: Optional['WorkflowStep'] = None,
                 required_steps: List[str] = None,
                 timeout: float = 300.0):
        self.step_name = step_name
        self.next_step = next_step
        self.required_steps = required_steps or []
        self.timeout = timeout
        self._observers: List[Callable] = []
    
    def add_observer(self, observer: Callable[[StepResult], None]):
        """添加觀察者"""
        self._observers.append(observer)
    
    def _notify_observers(self, result: StepResult):
        """通知觀察者"""
        for observer in self._observers:
            try:
                observer(result)
            except Exception as e:
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
            start_time=time.time()
        )
        
        try:
            # 檢查前置條件
            if not self._check_prerequisites(context):
                result.state = StepState.SKIPPED
                result.error = f"Prerequisites not met: {self.required_steps}"
                result.end_time = time.time()
                return result
            
            # 執行步驟邏輯（帶超時）
            step_data = await asyncio.wait_for(
                self._execute_step(context),
                timeout=self.timeout
            )
            
            result.data = step_data or {}
            result.state = StepState.COMPLETED
            result.end_time = time.time()
            
            # 記錄指標
            result.metrics = {
                "execution_time": result.duration or 0,
                "data_size": len(str(result.data)),
                "success": 1
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
            # 通知觀察者
            self._notify_observers(result)
            
            # 存儲結果到上下文
            context.step_results[self.step_name] = result
        
        return result
    
    async def process(self, context: WorkflowContext) -> WorkflowContext:
        """處理當前步驟並繼續到下一步"""
        # 執行當前步驟
        result = await self.execute(context)
        
        # 如果步驟失敗且為必要步驟，停止處理
        if result.state == StepState.FAILED:
            raise WorkflowStepError(f"Critical step {self.step_name} failed: {result.error}")
        
        # 繼續到下一步
        if self.next_step:
            return await self.next_step.process(context)
        
        return context

class WorkflowStepError(ServiceError):
    """工作流程步驟錯誤"""
    def __init__(self, message: str, step_name: str = None):
        super().__init__(message, "WORKFLOW_STEP_ERROR", {"step_name": step_name})

class WorkflowEngine(BaseService):
    """重構後的工作流程引擎"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("workflow_engine", "2.0.0", config)
        
        # 工作流程註冊表
        self._workflow_templates: Dict[str, 'WorkflowTemplate'] = {}
        self._active_workflows: Dict[str, 'WorkflowExecution'] = {}
        
        # 觀察者
        self._workflow_observers: List[Callable] = []
        self._step_observers: List[Callable] = []
        
        # 執行統計
        self._execution_stats = {
            "total_workflows": 0,
            "completed_workflows": 0,
            "failed_workflows": 0,
            "active_workflows": 0
        }
    
    async def _initialize(self):
        """初始化工作流程引擎"""
        self.add_health_check("workflow_capacity", self._check_workflow_capacity)
        self.add_health_check("memory_usage", self._check_memory_usage)
        
    async def _startup(self):
        """啟動工作流程引擎"""
        self.logger.info("Workflow engine started")
        
    async def _shutdown(self):
        """關閉工作流程引擎"""
        # 取消所有活動工作流程
        for workflow_id in list(self._active_workflows.keys()):
            await self.cancel_workflow(workflow_id)
        
        self.logger.info("Workflow engine shutdown")
    
    def _check_workflow_capacity(self) -> bool:
        """檢查工作流程容量"""
        max_workflows = self.config.get("max_concurrent_workflows", 100)
        return len(self._active_workflows) < max_workflows
    
    def _check_memory_usage(self) -> bool:
        """檢查記憶體使用量"""
        # 簡化的記憶體檢查
        return len(self._active_workflows) < 1000
    
    def register_workflow_template(self, template: 'WorkflowTemplate'):
        """註冊工作流程範本"""
        self._workflow_templates[template.name] = template
        self.logger.info(f"Registered workflow template: {template.name}")
    
    def add_workflow_observer(self, observer: Callable[['WorkflowExecution'], None]):
        """添加工作流程觀察者"""
        self._workflow_observers.append(observer)
    
    def add_step_observer(self, observer: Callable[[StepResult], None]):
        """添加步驟觀察者"""
        self._step_observers.append(observer)
    
    @handle_service_errors
    async def start_workflow(self, 
                           template_name: str,
                           user_id: str,
                           input_data: Dict[str, Any],
                           workflow_id: str = None,
                           trace_context: TraceContext = None) -> str:
        """啟動工作流程"""
        
        # 檢查範本是否存在
        if template_name not in self._workflow_templates:
            raise ServiceError(f"Workflow template not found: {template_name}", 
                             "TEMPLATE_NOT_FOUND")
        
        # 檢查容量
        if not self._check_workflow_capacity():
            raise ServiceError("Workflow capacity exceeded", "CAPACITY_EXCEEDED")
        
        # 創建工作流程執行實例
        workflow_id = workflow_id or str(uuid.uuid4())
        template = self._workflow_templates[template_name]
        
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            template=template,
            user_id=user_id,
            input_data=input_data,
            trace_context=trace_context,
            engine=self
        )
        
        # 添加觀察者
        for observer in self._step_observers:
            execution.add_step_observer(observer)
        
        # 註冊執行實例
        self._active_workflows[workflow_id] = execution
        
        # 更新統計
        self._execution_stats["total_workflows"] += 1
        self._execution_stats["active_workflows"] = len(self._active_workflows)
        
        # 記錄指標
        await self.metrics.increment_counter("workflows_started", 
                                             {"template": template_name})
        
        # 啟動執行（異步）
        asyncio.create_task(self._execute_workflow(execution))
        
        self.logger.info(f"Started workflow {workflow_id} from template {template_name}",
                        workflow_id=workflow_id, user_id=user_id)
        
        return workflow_id
    
    async def _execute_workflow(self, execution: 'WorkflowExecution'):
        """執行工作流程"""
        try:
            async with self.trace_operation(f"workflow_{execution.template.name}", 
                                          execution.context.trace_context) as span:
                span.add_tag("workflow_id", execution.workflow_id)
                span.add_tag("user_id", execution.user_id)
                
                # 執行工作流程
                await execution.execute()
                
                # 更新統計
                if execution.state == WorkflowState.COMPLETED:
                    self._execution_stats["completed_workflows"] += 1
                    await self.metrics.increment_counter("workflows_completed",
                                                        {"template": execution.template.name})
                elif execution.state == WorkflowState.FAILED:
                    self._execution_stats["failed_workflows"] += 1  
                    await self.metrics.increment_counter("workflows_failed",
                                                        {"template": execution.template.name})
                
                # 記錄執行時間
                if execution.end_time and execution.start_time:
                    duration = execution.end_time - execution.start_time
                    await self.metrics.record_histogram("workflow_duration",
                                                       duration,
                                                       {"template": execution.template.name})
                
                # 通知觀察者
                for observer in self._workflow_observers:
                    try:
                        observer(execution)
                    except Exception as e:
                        self.logger.error(f"Workflow observer error: {e}")
                
        except Exception as e:
            execution.state = WorkflowState.FAILED
            execution.error = str(e)
            execution.end_time = time.time()
            
            self.logger.error(f"Workflow {execution.workflow_id} failed: {e}",
                            workflow_id=execution.workflow_id)
            
            self._execution_stats["failed_workflows"] += 1
            await self.metrics.increment_counter("workflows_failed",
                                                {"template": execution.template.name})
        
        finally:
            # 清理活動工作流程
            self._active_workflows.pop(execution.workflow_id, None)
            self._execution_stats["active_workflows"] = len(self._active_workflows)
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """獲取工作流程狀態"""
        execution = self._active_workflows.get(workflow_id)
        if not execution:
            return None
        
        return execution.to_dict()
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """取消工作流程"""
        execution = self._active_workflows.get(workflow_id)
        if not execution:
            return False
        
        execution.cancel()
        self.logger.info(f"Cancelled workflow {workflow_id}")
        
        await self.metrics.increment_counter("workflows_cancelled",
                                            {"template": execution.template.name})
        return True
    
    async def get_engine_stats(self) -> Dict[str, Any]:
        """獲取引擎統計信息"""
        return {
            "stats": self._execution_stats.copy(),
            "templates": list(self._workflow_templates.keys()),
            "active_workflows": list(self._active_workflows.keys())
        }

@dataclass
class WorkflowTemplate:
    """工作流程範本"""
    name: str
    description: str
    first_step: WorkflowStep
    timeout: float = 3600.0  # 1小時預設超時
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_step_chain(self) -> List[str]:
        """獲取步驟鏈"""
        steps = []
        current_step = self.first_step
        while current_step:
            steps.append(current_step.step_name)
            current_step = current_step.next_step
        return steps

class WorkflowExecution:
    """工作流程執行實例"""
    
    def __init__(self,
                 workflow_id: str,
                 template: WorkflowTemplate, 
                 user_id: str,
                 input_data: Dict[str, Any],
                 trace_context: TraceContext = None,
                 engine: WorkflowEngine = None):
        self.workflow_id = workflow_id
        self.template = template
        self.user_id = user_id
        self.engine = engine
        
        # 執行狀態
        self.state = WorkflowState.PENDING
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.error: Optional[str] = None
        self.retry_count = 0
        
        # 執行上下文
        self.context = WorkflowContext(
            workflow_id=workflow_id,
            user_id=user_id,
            input_data=input_data,
            trace_context=trace_context or TraceContext()
        )
        
        # 取消標誌
        self._cancelled = False
        
        # 當前執行任務
        self._execution_task: Optional[asyncio.Task] = None
    
    def add_step_observer(self, observer: Callable[[StepResult], None]):
        """為所有步驟添加觀察者"""
        current_step = self.template.first_step
        while current_step:
            current_step.add_observer(observer)
            current_step = current_step.next_step
    
    async def execute(self):
        """執行工作流程"""
        if self.state != WorkflowState.PENDING:
            return
        
        self.state = WorkflowState.RUNNING
        self.start_time = time.time()
        
        try:
            # 執行步驟鏈
            self._execution_task = asyncio.current_task()
            
            # 帶超時執行
            await asyncio.wait_for(
                self.template.first_step.process(self.context),
                timeout=self.template.timeout
            )
            
            if not self._cancelled:
                self.state = WorkflowState.COMPLETED
                self.end_time = time.time()
            
        except asyncio.CancelledError:
            self.state = WorkflowState.CANCELLED
            self.end_time = time.time()
            
        except asyncio.TimeoutError:
            self.state = WorkflowState.FAILED
            self.error = f"Workflow timed out after {self.template.timeout} seconds"
            self.end_time = time.time()
            
        except Exception as e:
            self.state = WorkflowState.FAILED
            self.error = str(e)
            self.end_time = time.time()
    
    def cancel(self):
        """取消工作流程"""
        self._cancelled = True
        if self._execution_task and not self._execution_task.done():
            self._execution_task.cancel()
        self.state = WorkflowState.CANCELLED
        self.end_time = time.time()
    
    @property
    def duration(self) -> Optional[float]:
        """獲取執行持續時間"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None
    
    def get_progress(self) -> Dict[str, Any]:
        """獲取執行進度"""
        total_steps = len(self.template.get_step_chain())
        completed_steps = sum(1 for result in self.context.step_results.values() 
                            if result.state == StepState.COMPLETED)
        
        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "progress_percentage": (completed_steps / total_steps * 100) if total_steps > 0 else 0,
            "current_step": self._get_current_step()
        }
    
    def _get_current_step(self) -> Optional[str]:
        """獲取當前執行步驟"""
        for step_name in self.template.get_step_chain():
            result = self.context.get_step_result(step_name)
            if not result or result.state in [StepState.PENDING, StepState.RUNNING]:
                return step_name
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
            "step_results": {name: result.to_dict() 
                           for name, result in self.context.step_results.items()},
            "shared_data": self.context.shared_data,
            "metadata": self.context.metadata
        }

# === 具體步驟實作範例 ===

class TrendAnalysisStep(WorkflowStep):
    """趨勢分析步驟"""
    
    def __init__(self, trend_service_client, **kwargs):
        super().__init__("trend_analysis", **kwargs)
        self.trend_service = trend_service_client
    
    async def _execute_step(self, context: WorkflowContext) -> Dict[str, Any]:
        """執行趨勢分析"""
        categories = context.input_data.get("categories", ["technology"])
        platforms = context.input_data.get("platforms", ["tiktok"])
        
        # 調用趨勢服務
        trends_data = await self.trend_service.fetch_trends({
            "categories": categories,
            "platforms": platforms,
            "hours_back": 24
        })
        
        # 選擇最佳趨勢
        best_trends = sorted(
            trends_data.get("trends", []),
            key=lambda t: t.get("engagement_score", 0),
            reverse=True
        )[:5]
        
        return {
            "trends": best_trends,
            "total_trends_analyzed": len(trends_data.get("trends", [])),
            "categories": categories,
            "platforms": platforms
        }

class ScriptGenerationStep(WorkflowStep):
    """腳本生成步驟"""
    
    def __init__(self, ai_service_client, **kwargs):
        super().__init__("script_generation", required_steps=["trend_analysis"], **kwargs)
        self.ai_service = ai_service_client
    
    async def _execute_step(self, context: WorkflowContext) -> Dict[str, Any]:
        """執行腳本生成"""
        trends_data = context.get_step_data("trend_analysis")
        trends = trends_data.get("trends", [])
        
        if not trends:
            raise WorkflowStepError("No trends available for script generation", "script_generation")
        
        # 選擇主要趨勢
        main_trend = trends[0]
        
        # 生成腳本
        script_data = await self.ai_service.generate_script({
            "trend_keyword": main_trend.get("keyword"),
            "platform": context.input_data.get("platforms", ["tiktok"])[0],
            "duration": context.input_data.get("duration", 30)
        })
        
        return {
            "script": script_data.get("script"),
            "title": script_data.get("title"),
            "description": script_data.get("description"),
            "keywords": script_data.get("keywords", []),
            "main_trend": main_trend
        }