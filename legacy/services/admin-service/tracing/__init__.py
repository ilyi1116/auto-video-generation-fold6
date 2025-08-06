"""
分散式追蹤系統模組

提供完整的分散式追蹤功能，包括：
- OpenTelemetry 整合
- 自定義 Span 裝飾器
- 分散式上下文傳播
- 追蹤資料收集與分析
"""

from .analyzer import TraceAnalyzer
from .collector import TraceCollector
from .middleware import TracingMiddleware
from .tracer import (
    TraceContext,
    add_span_attributes,
    get_current_span,
    start_span,
    trace_celery_task,
    trace_function,
    trace_request,
    tracer,
)

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
    "TraceAnalyzer",
]
