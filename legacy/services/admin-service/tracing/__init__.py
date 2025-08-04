"""
分散式追蹤系統模組

提供完整的分散式追蹤功能，包括：
- OpenTelemetry 整合
- 自定義 Span 裝飾器
- 分散式上下文傳播
- 追蹤資料收集與分析
"""

from .tracer import (
    tracer,
    trace_request,
    trace_function,
    trace_celery_task,
    add_span_attributes,
    get_current_span,
    start_span,
    TraceContext
)

from .middleware import TracingMiddleware
from .collector import TraceCollector
from .analyzer import TraceAnalyzer

__all__ = [
    "tracer",
    "trace_request",
    "trace_function", 
    "trace_celery_task",
    "add_span_attributes",
    "get_current_span",
    "start_span",
    "TraceContext",
    "TracingMiddleware",
    "TraceCollector",
    "TraceAnalyzer"
]