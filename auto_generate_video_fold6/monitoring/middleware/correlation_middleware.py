#!/usr/bin/env python3
"""
關聯ID中間件
為每個請求生成和傳播關聯ID，支持分佈式追踪
"""

import uuid
import time
from typing import Optional, Dict, Any
from contextvars import ContextVar
import logging
from datetime import datetime

# 使用相對導入的替代方案
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from logging.performance_logger import (
        get_performance_logger,
        set_correlation_id,
        set_request_id,
    )

    logger = get_performance_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

    # 定義替代函數
    def set_correlation_id(correlation_id: str):
        pass

    def set_request_id(request_id: str):
        pass


# 全域上下文變數
correlation_id_context: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)
trace_id_context: ContextVar[Optional[str]] = ContextVar(
    "trace_id", default=None
)
span_id_context: ContextVar[Optional[str]] = ContextVar(
    "span_id", default=None
)


class CorrelationMiddleware:
    """關聯ID和分佈式追踪中間件"""

    def __init__(self, app, service_name: str = "unknown"):
        self.app = app
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}.correlation")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # 提取或生成關聯ID
        headers = dict(scope.get("headers", []))
        correlation_id = self._extract_correlation_id(headers)
        trace_id = self._extract_trace_id(headers)
        span_id = self._generate_span_id()
        request_id = self._extract_request_id(headers)

        # 設定上下文
        correlation_id_context.set(correlation_id)
        trace_id_context.set(trace_id)
        span_id_context.set(span_id)

        # 設定結構化日誌上下文
        set_correlation_id(correlation_id)
        if request_id:
            set_request_id(request_id)

        # 記錄請求開始
        start_time = time.time()
        self.logger.info(
            f"Request started: {scope['method']} {scope['path']}",
            correlation_id=correlation_id,
            trace_id=trace_id,
            span_id=span_id,
            request_id=request_id,
            service=self.service_name,
            method=scope["method"],
            path=scope["path"],
            user_agent=headers.get(b"user-agent", b"").decode(),
            client_ip=self._get_client_ip(scope, headers),
        )

        # 包裝 send 以添加關聯頭部
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # 添加關聯頭部到回應
                response_headers = list(message.get("headers", []))
                response_headers.extend(
                    [
                        [b"x-correlation-id", correlation_id.encode()],
                        [b"x-trace-id", trace_id.encode()],
                        [b"x-span-id", span_id.encode()],
                    ]
                )

                if request_id:
                    response_headers.append(
                        [b"x-request-id", request_id.encode()]
                    )

                message["headers"] = response_headers

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # 記錄異常
            self.logger.error(
                f"Request failed: {scope['method']} {scope['path']}",
                correlation_id=correlation_id,
                trace_id=trace_id,
                span_id=span_id,
                request_id=request_id,
                exception=e,
                duration_ms=(time.time() - start_time) * 1000,
            )
            raise
        finally:
            # 記錄請求完成
            duration = time.time() - start_time
            self.logger.info(
                f"Request completed: {scope['method']} {scope['path']}",
                correlation_id=correlation_id,
                trace_id=trace_id,
                span_id=span_id,
                request_id=request_id,
                duration_ms=duration * 1000,
            )

    def _extract_correlation_id(self, headers: Dict[bytes, bytes]) -> str:
        """提取或生成關聯ID"""
        # 檢查多種可能的頭部名稱
        correlation_headers = [
            b"x-correlation-id",
            b"x-correlation-id",
            b"correlation-id",
            b"x-request-id",
            b"request-id",
        ]

        for header_name in correlation_headers:
            if header_name in headers:
                correlation_id = headers[header_name].decode()
                if correlation_id and len(correlation_id) > 0:
                    return correlation_id

        # 生成新的關聯ID
        return str(uuid.uuid4())

    def _extract_trace_id(self, headers: Dict[bytes, bytes]) -> str:
        """提取或生成追踪ID"""
        # 檢查分佈式追踪頭部
        trace_headers = [
            b"x-trace-id",
            b"trace-id",
            b"x-b3-traceid",  # Zipkin B3
            b"traceparent",  # W3C Trace Context
        ]

        for header_name in trace_headers:
            if header_name in headers:
                trace_value = headers[header_name].decode()
                if trace_value and len(trace_value) > 0:
                    # 如果是 W3C traceparent，提取 trace-id 部分
                    if header_name == b"traceparent":
                        parts = trace_value.split("-")
                        if len(parts) >= 2:
                            return parts[1]
                    return trace_value

        # 生成新的追踪ID
        return str(uuid.uuid4()).replace("-", "")[:16]

    def _extract_request_id(
        self, headers: Dict[bytes, bytes]
    ) -> Optional[str]:
        """提取請求ID"""
        request_id_headers = [b"x-request-id", b"request-id"]

        for header_name in request_id_headers:
            if header_name in headers:
                request_id = headers[header_name].decode()
                if request_id and len(request_id) > 0:
                    return request_id

        return None

    def _generate_span_id(self) -> str:
        """生成新的 Span ID"""
        return str(uuid.uuid4()).replace("-", "")[:8]

    def _get_client_ip(
        self, scope: Dict[str, Any], headers: Dict[bytes, bytes]
    ) -> str:
        """獲取客戶端IP地址"""
        # 檢查代理頭部
        proxy_headers = [
            b"x-forwarded-for",
            b"x-real-ip",
            b"x-client-ip",
            b"cf-connecting-ip",  # Cloudflare
        ]

        for header_name in proxy_headers:
            if header_name in headers:
                ip_value = headers[header_name].decode()
                if ip_value:
                    # X-Forwarded-For 可能包含多個IP，取第一個
                    if "," in ip_value:
                        ip_value = ip_value.split(",")[0].strip()
                    return ip_value

        # 從 scope 獲取客戶端地址
        client = scope.get("client")
        if client:
            return client[0]

        return "unknown"


class DistributedTracingContext:
    """分佈式追踪上下文管理器"""

    def __init__(self, operation_name: str, service_name: str = "unknown"):
        self.operation_name = operation_name
        self.service_name = service_name
        self.start_time = None
        self.span_id = None
        self.parent_span_id = None

    def __enter__(self):
        self.start_time = time.time()
        self.parent_span_id = span_id_context.get()
        self.span_id = str(uuid.uuid4()).replace("-", "")[:8]

        # 設定新的 span context
        span_id_context.set(self.span_id)

        # 記錄 span 開始
        logger.info(
            f"Span started: {self.operation_name}",
            correlation_id=correlation_id_context.get(),
            trace_id=trace_id_context.get(),
            span_id=self.span_id,
            parent_span_id=self.parent_span_id,
            service=self.service_name,
            operation=self.operation_name,
        )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        # 記錄 span 結束
        if exc_type is None:
            logger.info(
                f"Span completed: {self.operation_name}",
                correlation_id=correlation_id_context.get(),
                trace_id=trace_id_context.get(),
                span_id=self.span_id,
                parent_span_id=self.parent_span_id,
                service=self.service_name,
                operation=self.operation_name,
                duration_ms=duration * 1000,
                status="success",
            )
        else:
            logger.error(
                f"Span failed: {self.operation_name}",
                correlation_id=correlation_id_context.get(),
                trace_id=trace_id_context.get(),
                span_id=self.span_id,
                parent_span_id=self.parent_span_id,
                service=self.service_name,
                operation=self.operation_name,
                duration_ms=duration * 1000,
                status="error",
                exception=exc_val,
            )

        # 恢復父 span context
        span_id_context.set(self.parent_span_id)


# 便捷函數
def get_correlation_id() -> Optional[str]:
    """獲取當前關聯ID"""
    return correlation_id_context.get()


def get_trace_id() -> Optional[str]:
    """獲取當前追踪ID"""
    return trace_id_context.get()


def get_span_id() -> Optional[str]:
    """獲取當前 Span ID"""
    return span_id_context.get()


def create_child_span(operation_name: str, service_name: str = "unknown"):
    """創建子 Span 上下文管理器"""
    return DistributedTracingContext(operation_name, service_name)


def trace_function(
    operation_name: Optional[str] = None, service_name: str = "unknown"
):
    """函數追踪裝飾器"""

    def decorator(func):
        from functools import wraps
        import asyncio

        actual_operation_name = (
            operation_name or f"{func.__module__}.{func.__name__}"
        )

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with create_child_span(actual_operation_name, service_name):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with create_child_span(actual_operation_name, service_name):
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 分佈式追踪輔助類別
class TraceEvent:
    """追踪事件"""

    def __init__(self, event_name: str, **attributes):
        self.event_name = event_name
        self.timestamp = datetime.utcnow()
        self.attributes = attributes
        self.correlation_id = get_correlation_id()
        self.trace_id = get_trace_id()
        self.span_id = get_span_id()

    def log_event(self):
        """記錄追踪事件"""
        logger.info(
            f"Trace event: {self.event_name}",
            correlation_id=self.correlation_id,
            trace_id=self.trace_id,
            span_id=self.span_id,
            event_name=self.event_name,
            timestamp=self.timestamp.isoformat(),
            **self.attributes,
        )


def log_trace_event(event_name: str, **attributes):
    """記錄追踪事件的便捷函數"""
    event = TraceEvent(event_name, **attributes)
    event.log_event()
    return event
