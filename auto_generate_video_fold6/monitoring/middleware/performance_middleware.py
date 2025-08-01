#!/usr/bin/env python3
"""
效能監控中間件
追蹤應用程式效能指標並整合 Prometheus
"""

import time
import asyncio
from typing import Dict, Optional, Any, Callable, List
from datetime import datetime, timedelta
import logging
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import threading
import json

# Prometheus metrics (optional dependency)
try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        Summary,
        start_http_server,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

from ..logging.structured_logger import (
    get_logger,
    set_correlation_id,
    set_request_id,
)

logger = get_logger(__name__)


class PerformanceMetrics:
    """效能指標收集器"""

    def __init__(self):
        # Request metrics
        self.request_count = (
            Counter(
                "http_requests_total",
                "Total HTTP requests",
                ["method", "endpoint", "status", "service"],
            )
            if PROMETHEUS_AVAILABLE
            else None
        )

        self.request_duration = (
            Histogram(
                "http_request_duration_seconds",
                "HTTP request duration in seconds",
                ["method", "endpoint", "service"],
            )
            if PROMETHEUS_AVAILABLE
            else None
        )

        self.request_size = (
            Summary(
                "http_request_size_bytes",
                "HTTP request size in bytes",
                ["method", "endpoint", "service"],
            )
            if PROMETHEUS_AVAILABLE
            else None
        )

        self.response_size = (
            Summary(
                "http_response_size_bytes",
                "HTTP response size in bytes",
                ["method", "endpoint", "service"],
            )
            if PROMETHEUS_AVAILABLE
            else None
        )

        # Business metrics
        self.video_generation_duration = (
            Histogram(
                "video_generation_duration_seconds",
                "Video generation duration in seconds",
                ["status", "video_type"],
            )
            if PROMETHEUS_AVAILABLE
            else None
        )

        self.video_generation_total = (
            Counter(
                "video_generation_total",
                "Total video generations",
                ["status", "video_type", "platform"],
            )
            if PROMETHEUS_AVAILABLE
            else None
        )

        self.trend_analysis_duration = (
            Histogram(
                "trend_analysis_duration_seconds",
                "Trend analysis duration in seconds",
                ["source", "accuracy"],
            )
            if PROMETHEUS_AVAILABLE
            else None
        )

        self.trend_analysis_total = (
            Counter(
                "trend_analysis_total",
                "Total trend analyses",
                ["source", "status", "accuracy"],
            )
            if PROMETHEUS_AVAILABLE
            else None
        )

        self.social_publish_total = (
            Counter(
                "social_publish_total",
                "Total social media publishes",
                ["platform", "status", "content_type"],
            )
            if PROMETHEUS_AVAILABLE
            else None
        )

        # System metrics
        self.active_connections = (
            Gauge(
                "active_connections",
                "Number of active connections",
                ["service"],
            )
            if PROMETHEUS_AVAILABLE
            else None
        )

        self.queue_size = (
            Gauge(
                "queue_size", "Current queue size", ["queue_name", "service"]
            )
            if PROMETHEUS_AVAILABLE
            else None
        )

        self.cache_hits = (
            Counter(
                "cache_hits_total",
                "Total cache hits",
                ["cache_type", "service"],
            )
            if PROMETHEUS_AVAILABLE
            else None
        )

        self.cache_misses = (
            Counter(
                "cache_misses_total",
                "Total cache misses",
                ["cache_type", "service"],
            )
            if PROMETHEUS_AVAILABLE
            else None
        )

        # Application errors
        self.application_errors = (
            Counter(
                "application_errors_total",
                "Total application errors",
                ["service", "error_type", "endpoint"],
            )
            if PROMETHEUS_AVAILABLE
            else None
        )

        # In-memory metrics for fallback
        self._fallback_metrics = defaultdict(list)
        self._metrics_lock = threading.Lock()

        # Performance tracking
        self._request_history = deque(maxlen=1000)
        self._performance_stats = {
            "avg_response_time": 0.0,
            "request_rate": 0.0,
            "error_rate": 0.0,
            "last_updated": datetime.utcnow(),
        }

    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration: float,
        service: str,
        request_size: int = 0,
        response_size: int = 0,
    ):
        """記錄 HTTP 請求指標"""
        status = str(status_code)

        if PROMETHEUS_AVAILABLE and self.request_count:
            self.request_count.labels(
                method=method,
                endpoint=endpoint,
                status=status,
                service=service,
            ).inc()

            self.request_duration.labels(
                method=method, endpoint=endpoint, service=service
            ).observe(duration)

            if request_size > 0:
                self.request_size.labels(
                    method=method, endpoint=endpoint, service=service
                ).observe(request_size)

            if response_size > 0:
                self.response_size.labels(
                    method=method, endpoint=endpoint, service=service
                ).observe(response_size)

        # Fallback metrics
        with self._metrics_lock:
            self._fallback_metrics["requests"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "method": method,
                    "endpoint": endpoint,
                    "status": status,
                    "duration": duration,
                    "service": service,
                }
            )

            # Update request history for performance stats
            self._request_history.append(
                {
                    "timestamp": time.time(),
                    "duration": duration,
                    "status_code": status_code,
                }
            )

            self._update_performance_stats()

    def record_video_generation(
        self,
        duration: float,
        status: str,
        video_type: str,
        platform: str = "unknown",
    ):
        """記錄影片生成指標"""
        if PROMETHEUS_AVAILABLE and self.video_generation_duration:
            self.video_generation_duration.labels(
                status=status, video_type=video_type
            ).observe(duration)

            self.video_generation_total.labels(
                status=status, video_type=video_type, platform=platform
            ).inc()

        with self._metrics_lock:
            self._fallback_metrics["video_generation"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "duration": duration,
                    "status": status,
                    "video_type": video_type,
                    "platform": platform,
                }
            )

    def record_trend_analysis(
        self,
        duration: float,
        source: str,
        status: str,
        accuracy: str = "unknown",
    ):
        """記錄趨勢分析指標"""
        if PROMETHEUS_AVAILABLE and self.trend_analysis_duration:
            self.trend_analysis_duration.labels(
                source=source, accuracy=accuracy
            ).observe(duration)

            self.trend_analysis_total.labels(
                source=source, status=status, accuracy=accuracy
            ).inc()

        with self._metrics_lock:
            self._fallback_metrics["trend_analysis"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "duration": duration,
                    "source": source,
                    "status": status,
                    "accuracy": accuracy,
                }
            )

    def record_social_publish(
        self, platform: str, status: str, content_type: str = "video"
    ):
        """記錄社交媒體發布指標"""
        if PROMETHEUS_AVAILABLE and self.social_publish_total:
            self.social_publish_total.labels(
                platform=platform, status=status, content_type=content_type
            ).inc()

        with self._metrics_lock:
            self._fallback_metrics["social_publish"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "platform": platform,
                    "status": status,
                    "content_type": content_type,
                }
            )

    def record_error(self, service: str, error_type: str, endpoint: str):
        """記錄應用程式錯誤"""
        if PROMETHEUS_AVAILABLE and self.application_errors:
            self.application_errors.labels(
                service=service, error_type=error_type, endpoint=endpoint
            ).inc()

        with self._metrics_lock:
            self._fallback_metrics["errors"].append(
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "service": service,
                    "error_type": error_type,
                    "endpoint": endpoint,
                }
            )

    def record_cache_event(self, cache_type: str, service: str, hit: bool):
        """記錄快取事件"""
        if PROMETHEUS_AVAILABLE:
            if hit and self.cache_hits:
                self.cache_hits.labels(
                    cache_type=cache_type, service=service
                ).inc()
            elif not hit and self.cache_misses:
                self.cache_misses.labels(
                    cache_type=cache_type, service=service
                ).inc()

    def update_queue_size(self, queue_name: str, service: str, size: int):
        """更新隊列大小"""
        if PROMETHEUS_AVAILABLE and self.queue_size:
            self.queue_size.labels(queue_name=queue_name, service=service).set(
                size
            )

    def update_active_connections(self, service: str, count: int):
        """更新活躍連接數"""
        if PROMETHEUS_AVAILABLE and self.active_connections:
            self.active_connections.labels(service=service).set(count)

    def _update_performance_stats(self):
        """更新效能統計"""
        if not self._request_history:
            return

        now = time.time()
        recent_requests = [
            r for r in self._request_history if now - r["timestamp"] < 300
        ]  # Last 5 minutes

        if recent_requests:
            # Average response time
            avg_duration = sum(r["duration"] for r in recent_requests) / len(
                recent_requests
            )
            self._performance_stats["avg_response_time"] = avg_duration

            # Request rate (requests per second)
            time_span = max(now - recent_requests[0]["timestamp"], 1)
            self._performance_stats["request_rate"] = (
                len(recent_requests) / time_span
            )

            # Error rate
            error_count = sum(
                1 for r in recent_requests if r["status_code"] >= 400
            )
            self._performance_stats["error_rate"] = (
                error_count / len(recent_requests) * 100
            )

            self._performance_stats["last_updated"] = datetime.utcnow()

    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取效能統計"""
        with self._metrics_lock:
            return self._performance_stats.copy()

    def get_fallback_metrics(self) -> Dict[str, Any]:
        """獲取後備指標（用於非 Prometheus 環境）"""
        with self._metrics_lock:
            # Return recent metrics (last hour)
            cutoff_time = datetime.utcnow() - timedelta(hours=1)

            filtered_metrics = {}
            for metric_type, metrics in self._fallback_metrics.items():
                filtered_metrics[metric_type] = [
                    m
                    for m in metrics
                    if datetime.fromisoformat(m["timestamp"]) > cutoff_time
                ]

            return filtered_metrics


# Global metrics instance
metrics = PerformanceMetrics()


class PerformanceMiddleware:
    """效能監控中間件"""

    def __init__(self, app, service_name: str = "unknown"):
        self.app = app
        self.service_name = service_name
        self.logger = get_logger(f"{service_name}.performance")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request information
        method = scope["method"]
        path = scope["path"]

        # Generate correlation ID for request tracking
        import uuid

        correlation_id = str(uuid.uuid4())
        set_correlation_id(correlation_id)

        # Extract request ID from headers if present
        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", b"").decode()
        if request_id:
            set_request_id(request_id)

        start_time = time.time()
        request_size = 0
        response_size = 0
        status_code = 500  # Default to error

        # Calculate request size
        if "content-length" in headers:
            try:
                request_size = int(headers[b"content-length"].decode())
            except (ValueError, AttributeError):
                pass

        # Wrap send to capture response size and status
        async def send_wrapper(message):
            nonlocal response_size, status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = dict(message.get("headers", []))
                if b"content-length" in response_headers:
                    try:
                        response_size = int(
                            response_headers[b"content-length"].decode()
                        )
                    except (ValueError, AttributeError):
                        pass

            elif message["type"] == "http.response.body":
                if "body" in message:
                    response_size += len(message["body"])

            await send(message)

        try:
            # Process request
            await self.app(scope, receive, send_wrapper)

        except Exception as e:
            # Record error
            metrics.record_error(
                service=self.service_name,
                error_type=type(e).__name__,
                endpoint=path,
            )

            self.logger.error(
                f"Request failed: {method} {path}",
                exception=e,
                correlation_id=correlation_id,
                request_id=request_id,
                duration_ms=(time.time() - start_time) * 1000,
            )

            raise

        finally:
            # Record metrics
            duration = time.time() - start_time

            metrics.record_request(
                method=method,
                endpoint=path,
                status_code=status_code,
                duration=duration,
                service=self.service_name,
                request_size=request_size,
                response_size=response_size,
            )

            # Log request completion
            log_level = "warning" if status_code >= 400 else "info"
            getattr(self.logger, log_level)(
                f"Request completed: {method} {path} - {status_code}",
                method=method,
                endpoint=path,
                status_code=status_code,
                duration_ms=duration * 1000,
                request_size=request_size,
                response_size=response_size,
                correlation_id=correlation_id,
                request_id=request_id,
            )


@asynccontextmanager
async def performance_context(operation_name: str, **labels):
    """效能監控上下文管理器"""
    start_time = time.time()
    operation_logger = get_logger(f"performance.{operation_name}")

    operation_logger.info(f"Operation started: {operation_name}", **labels)

    try:
        yield
        duration = time.time() - start_time
        operation_logger.info(
            f"Operation completed: {operation_name}",
            duration_ms=duration * 1000,
            **labels,
        )

    except Exception as e:
        duration = time.time() - start_time
        operation_logger.error(
            f"Operation failed: {operation_name}",
            exception=e,
            duration_ms=duration * 1000,
            **labels,
        )
        raise


def performance_tracker(operation_type: str = "unknown"):
    """效能追蹤裝飾器"""

    def decorator(func):
        from functools import wraps
        import asyncio

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            async with performance_context(
                operation_name=func.__name__,
                operation_type=operation_type,
                function=f"{func.__module__}.{func.__name__}",
            ):
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time

            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(
                    f"Function completed: {func.__name__}",
                    operation_type=operation_type,
                    function=f"{func.__module__}.{func.__name__}",
                    duration_ms=duration * 1000,
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger.error(
                    f"Function failed: {func.__name__}",
                    exception=e,
                    operation_type=operation_type,
                    function=f"{func.__module__}.{func.__name__}",
                    duration_ms=duration * 1000,
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Utility functions for recording specific business metrics
def record_video_generation(
    duration: float, status: str, video_type: str, platform: str = "unknown"
):
    """記錄影片生成指標的便捷函數"""
    return metrics.record_video_generation(
        duration, status, video_type, platform
    )


def record_trend_analysis(
    duration: float, source: str, status: str, accuracy: str = "unknown"
):
    """記錄趨勢分析指標的便捷函數"""
    return metrics.record_trend_analysis(duration, source, status, accuracy)


def record_social_publish(
    platform: str, status: str, content_type: str = "video"
):
    """記錄社交媒體發布指標的便捷函數"""
    return metrics.record_social_publish(platform, status, content_type)


def start_metrics_server(port: int = 8000):
    """啟動 Prometheus 指標伺服器"""
    if PROMETHEUS_AVAILABLE:
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")
    else:
        logger.warning("Prometheus not available, metrics server not started")
