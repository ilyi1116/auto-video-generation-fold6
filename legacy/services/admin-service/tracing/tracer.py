"""
分散式追蹤核心模組
提供 OpenTelemetry 整合和自定義追蹤功能
"""

import functools
import time
import uuid
from typing import Any, Dict, Optional, Callable, List
from contextvars import ContextVar
from datetime import datetime
import logging

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor
)
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor

logger = logging.getLogger(__name__)

# 全域追蹤上下文
_trace_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    'trace_context', default=None
)


class TraceContext:
    """追蹤上下文管理"""
    
    def __init__(self, trace_id: str = None, span_id: str = None, 
                 parent_span_id: str = None, service_name: str = "admin-service"):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.span_id = span_id or str(uuid.uuid4())
        self.parent_span_id = parent_span_id
        self.service_name = service_name
        self.created_at = datetime.utcnow()
        self.attributes = {}
        
    def add_attribute(self, key: str, value: Any):
        """添加追蹤屬性"""
        self.attributes[key] = value
        
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "service_name": self.service_name,
            "created_at": self.created_at.isoformat(),
            "attributes": self.attributes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TraceContext':
        """從字典創建追蹤上下文"""
        context = cls(
            trace_id=data.get("trace_id"),
            span_id=data.get("span_id"),
            parent_span_id=data.get("parent_span_id"),
            service_name=data.get("service_name", "admin-service")
        )
        context.attributes = data.get("attributes", {})
        return context


class CustomTracer:
    """自定義追蹤器"""
    
    def __init__(self):
        self.setup_tracer()
        self.spans_cache: Dict[str, Dict[str, Any]] = {}
        
    def setup_tracer(self):
        """設置 OpenTelemetry 追蹤器"""
        # 創建資源
        resource = Resource.create({
            "service.name": "admin-service",
            "service.version": "1.0.0",
            "deployment.environment": "production"
        })
        
        # 設置追蹤提供者
        trace.set_tracer_provider(TracerProvider(resource=resource))
        
        # 獲取追蹤器
        self.tracer = trace.get_tracer(__name__)
        
        # 設置導出器
        self.setup_exporters()
        
        # 設置自動儀器
        self.setup_auto_instrumentation()
        
    def setup_exporters(self):
        """設置追蹤資料導出器"""
        try:
            # Jaeger 導出器 (如果可用)
            jaeger_exporter = JaegerExporter(
                agent_host_name="localhost",
                agent_port=6831,
            )
            
            trace.get_tracer_provider().add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )
            logger.info("Jaeger 導出器設置成功")
            
        except Exception as e:
            logger.warning(f"Jaeger 導出器設置失敗: {e}")
            
            # 回退到控制台導出器
            console_exporter = ConsoleSpanExporter()
            trace.get_tracer_provider().add_span_processor(
                SimpleSpanProcessor(console_exporter)
            )
            logger.info("使用控制台導出器")
    
    def setup_auto_instrumentation(self):
        """設置自動儀器"""
        try:
            # FastAPI 自動儀器
            FastAPIInstrumentor.instrument()
            
            # Requests 自動儀器
            RequestsInstrumentor().instrument()
            
            # Celery 自動儀器
            CeleryInstrumentor().instrument()
            
            logger.info("自動儀器設置完成")
            
        except Exception as e:
            logger.error(f"自動儀器設置失敗: {e}")
    
    def start_span(self, name: str, parent_context: Optional[TraceContext] = None,
                   attributes: Optional[Dict[str, Any]] = None) -> TraceContext:
        """開始新的 Span"""
        context = TraceContext(
            parent_span_id=parent_context.span_id if parent_context else None,
            trace_id=parent_context.trace_id if parent_context else None
        )
        
        if attributes:
            context.attributes.update(attributes)
            
        # 快取 Span 資訊
        self.spans_cache[context.span_id] = {
            "name": name,
            "context": context,
            "start_time": time.time(),
            "status": "active"
        }
        
        logger.debug(f"開始 Span: {name} (ID: {context.span_id})")
        return context
    
    def finish_span(self, context: TraceContext, status: str = "success",
                   error: Optional[Exception] = None):
        """結束 Span"""
        if context.span_id in self.spans_cache:
            span_info = self.spans_cache[context.span_id]
            span_info["end_time"] = time.time()
            span_info["duration"] = span_info["end_time"] - span_info["start_time"]
            span_info["status"] = status
            
            if error:
                span_info["error"] = str(error)
                context.add_attribute("error.message", str(error))
                context.add_attribute("error.type", type(error).__name__)
            
            logger.debug(f"結束 Span: {span_info['name']} "
                        f"(耗時: {span_info['duration']:.3f}s)")
    
    def get_current_context(self) -> Optional[TraceContext]:
        """獲取當前追蹤上下文"""
        return _trace_context.get()
    
    def set_current_context(self, context: TraceContext):
        """設置當前追蹤上下文"""
        _trace_context.set(context)
    
    def get_span_info(self, span_id: str) -> Optional[Dict[str, Any]]:
        """獲取 Span 資訊"""
        return self.spans_cache.get(span_id)
    
    def get_all_spans(self) -> List[Dict[str, Any]]:
        """獲取所有 Span 資訊"""
        return list(self.spans_cache.values())
    
    def clear_cache(self, max_age: int = 3600):
        """清理過期的 Span 快取"""
        current_time = time.time()
        expired_spans = []
        
        for span_id, span_info in self.spans_cache.items():
            if current_time - span_info.get("start_time", 0) > max_age:
                expired_spans.append(span_id)
        
        for span_id in expired_spans:
            del self.spans_cache[span_id]
        
        if expired_spans:
            logger.info(f"清理了 {len(expired_spans)} 個過期 Span")


# 全域追蹤器實例
tracer = CustomTracer()


def trace_request(operation_name: str = None, 
                 include_headers: bool = False,
                 include_params: bool = False):
    """HTTP 請求追蹤裝飾器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 獲取請求資訊
            request = None
            for arg in args:
                if hasattr(arg, 'method') and hasattr(arg, 'url'):
                    request = arg
                    break
            
            name = operation_name or f"{func.__name__}"
            if request:
                name = f"{request.method} {name}"
            
            # 開始追蹤
            parent_context = tracer.get_current_context()
            context = tracer.start_span(name, parent_context)
            
            # 添加請求屬性
            if request:
                context.add_attribute("http.method", request.method)
                context.add_attribute("http.url", str(request.url))
                context.add_attribute("http.user_agent", 
                                    request.headers.get("user-agent", ""))
                
                if include_headers:
                    context.add_attribute("http.headers", dict(request.headers))
                
                if include_params and request.query_params:
                    context.add_attribute("http.query_params", 
                                        dict(request.query_params))
            
            # 設置當前上下文
            tracer.set_current_context(context)
            
            try:
                result = await func(*args, **kwargs)
                
                # 添加回應屬性
                if hasattr(result, 'status_code'):
                    context.add_attribute("http.status_code", result.status_code)
                
                tracer.finish_span(context, "success")
                return result
                
            except Exception as e:
                tracer.finish_span(context, "error", e)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__name__}"
            
            parent_context = tracer.get_current_context()
            context = tracer.start_span(name, parent_context)
            tracer.set_current_context(context)
            
            try:
                result = func(*args, **kwargs)
                tracer.finish_span(context, "success")
                return result
            except Exception as e:
                tracer.finish_span(context, "error", e)
                raise
        
        return async_wrapper if functools.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def trace_function(operation_name: str = None, 
                  capture_args: bool = False,
                  capture_result: bool = False):
    """通用函數追蹤裝飾器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            
            parent_context = tracer.get_current_context()
            context = tracer.start_span(name, parent_context)
            
            # 捕獲參數
            if capture_args:
                context.add_attribute("function.args", str(args))
                context.add_attribute("function.kwargs", str(kwargs))
            
            tracer.set_current_context(context)
            
            try:
                result = await func(*args, **kwargs)
                
                # 捕獲結果
                if capture_result and result is not None:
                    context.add_attribute("function.result", str(result)[:1000])
                
                tracer.finish_span(context, "success")
                return result
                
            except Exception as e:
                tracer.finish_span(context, "error", e)
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = operation_name or f"{func.__module__}.{func.__name__}"
            
            parent_context = tracer.get_current_context()
            context = tracer.start_span(name, parent_context)
            
            if capture_args:
                context.add_attribute("function.args", str(args))
                context.add_attribute("function.kwargs", str(kwargs))
            
            tracer.set_current_context(context)
            
            try:
                result = func(*args, **kwargs)
                
                if capture_result and result is not None:
                    context.add_attribute("function.result", str(result)[:1000])
                
                tracer.finish_span(context, "success")
                return result
            except Exception as e:
                tracer.finish_span(context, "error", e)
                raise
        
        return async_wrapper if functools.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


def trace_celery_task(task_name: str = None):
    """Celery 任務追蹤裝飾器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            name = task_name or f"celery.{func.__name__}"
            
            # 從 Celery 上下文獲取任務資訊
            task_id = getattr(self, 'request', {}).get('id', 'unknown')
            
            context = tracer.start_span(name)
            context.add_attribute("celery.task_id", task_id)
            context.add_attribute("celery.task_name", name)
            context.add_attribute("celery.args", str(args))
            context.add_attribute("celery.kwargs", str(kwargs))
            
            tracer.set_current_context(context)
            
            try:
                result = func(self, *args, **kwargs)
                tracer.finish_span(context, "success")
                return result
            except Exception as e:
                tracer.finish_span(context, "error", e)
                raise
        
        return wrapper
    
    return decorator


def add_span_attributes(attributes: Dict[str, Any]):
    """添加屬性到當前 Span"""
    current_context = tracer.get_current_context()
    if current_context:
        for key, value in attributes.items():
            current_context.add_attribute(key, value)


def get_current_span() -> Optional[TraceContext]:
    """獲取當前 Span 上下文"""
    return tracer.get_current_context()


def start_span(name: str, attributes: Optional[Dict[str, Any]] = None) -> TraceContext:
    """手動開始新的 Span"""
    parent_context = tracer.get_current_context()
    return tracer.start_span(name, parent_context, attributes)


def finish_span(context: TraceContext, status: str = "success", 
               error: Optional[Exception] = None):
    """手動結束 Span"""
    tracer.finish_span(context, status, error)