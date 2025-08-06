"""
TDD Refactor 階段: 統一服務基礎架構
提供所有微服務的基礎功能和標準化介面
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import structlog


class ServiceState(Enum):
    """服務狀態枚舉"""

    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


@dataclass
class ServiceMetric:
    """服務指標"""

    name: str
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp,
            "labels": self.labels,
        }


@dataclass
class HealthCheckResult:
    """健康檢查結果"""

    status: ServiceState
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    checks: Dict[str, bool] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "checks": self.checks,
            "timestamp": self.timestamp,
        }


class ServiceError(Exception):
    """服務基礎異常"""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: Dict = None,
        cause: Exception = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.utcnow()
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp.isoformat(),
                "cause": str(self.cause) if self.cause else None,
            }
        }


class MetricsCollector:
    """指標收集器"""

    def __init__(self):
        self.metrics: List[ServiceMetric] = []
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()

    async def increment_counter(self, name: str, labels: Dict[str, str] = None, value: int = 1):
        """計數器遞增"""
        async with self._lock:
            key = self._generate_key(name, labels)
            self.counters[key] = self.counters.get(key, 0) + value

            metric = ServiceMetric(
                name=f"{name}_total",
                value=self.counters[key],
                timestamp=time.time(),
                labels=labels or {},
            )
            self.metrics.append(metric)

    async def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """設定量表值"""
        async with self._lock:
            key = self._generate_key(name, labels)
            self.gauges[key] = value

            metric = ServiceMetric(
                name=name,
                value=value,
                timestamp=time.time(),
                labels=labels or {},
            )
            self.metrics.append(metric)

    async def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """記錄直方圖"""
        async with self._lock:
            key = self._generate_key(name, labels)
            if key not in self.histograms:
                self.histograms[key] = []

            self.histograms[key].append(value)

            # 計算統計值
            values = self.histograms[key]
            stats = {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            }

            for stat_name, stat_value in stats.items():
                metric = ServiceMetric(
                    name=f"{name}_{stat_name}",
                    value=stat_value,
                    timestamp=time.time(),
                    labels=labels or {},
                )
                self.metrics.append(metric)

    def _generate_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """生成指標唯一鍵值"""
        labels_str = json.dumps(labels or {}, sort_keys=True)
        return f"{name}_{hash(labels_str)}"

    async def get_metrics(self, last_n: int = 100) -> List[Dict[str, Any]]:
        """獲取最近的指標"""
        async with self._lock:
            recent_metrics = self.metrics[-last_n:] if last_n > 0 else self.metrics
            return [metric.to_dict() for metric in recent_metrics]

    async def clear_metrics(self):
        """清理指標"""
        async with self._lock:
            self.metrics.clear()


class StructuredLogger:
    """結構化日誌器"""

    def __init__(self, service_name: str, service_version: str = "1.0.0"):
        self.service_name = service_name
        self.service_version = service_version

        # 配置 structlog
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="ISO"),
                (
                    structlog.dev.ConsoleRenderer()
                    if __debug__
                    else structlog.processors.JSONRenderer()
                ),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            logger_factory=structlog.WriteLoggerFactory(),
            cache_logger_on_first_use=True,
        )

        self.logger = structlog.get_logger(service=service_name, version=service_version)

    def info(self, message: str, **kwargs):
        self.logger.info(message, **kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(message, **kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, **kwargs)

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, **kwargs)


class TraceContext:
    """分散式追蹤上下文"""

    def __init__(
        self,
        trace_id: str = None,
        span_id: str = None,
        parent_span_id: str = None,
    ):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.span_id = span_id or str(uuid.uuid4())
        self.parent_span_id = parent_span_id
        self.tags: Dict[str, Any] = {}
        self.logs: List[Dict[str, Any]] = []
        self.start_time = time.time()

    def add_tag(self, key: str, value: Any):
        """添加標籤"""
        self.tags[key] = value

    def log(self, message: str, level: str = "info", **kwargs):
        """添加日誌"""
        self.logs.append(
            {
                "timestamp": time.time(),
                "level": level,
                "message": message,
                **kwargs,
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "tags": self.tags,
            "logs": self.logs,
            "start_time": self.start_time,
            "end_time": time.time(),
        }


@asynccontextmanager
async def trace_span(
    operation_name: str,
    context: TraceContext = None,
    logger: StructuredLogger = None,
):
    """分散式追蹤 span 上下文管理器"""
    parent_context = context or TraceContext()
    span_context = TraceContext(
        trace_id=parent_context.trace_id, parent_span_id=parent_context.span_id
    )

    span_context.add_tag("operation.name", operation_name)
    span_start = time.time()

    if logger:
        logger.info(
            f"Span started: {operation_name}",
            trace_id=span_context.trace_id,
            span_id=span_context.span_id,
        )

    try:
        yield span_context
        span_context.add_tag("success", True)
    except Exception as e:
        span_context.add_tag("error", True)
        span_context.add_tag("error.message", str(e))
        span_context.log(f"Exception in {operation_name}: {str(e)}", "error")

        if logger:
            logger.error(
                f"Span failed: {operation_name}",
                error=str(e),
                trace_id=span_context.trace_id,
                span_id=span_context.span_id,
            )
        raise
    finally:
        span_duration = time.time() - span_start
        span_context.add_tag("duration", span_duration)

        if logger:
            logger.info(
                f"Span completed: {operation_name}",
                duration=span_duration,
                trace_id=span_context.trace_id,
                span_id=span_context.span_id,
            )


class BaseService(ABC):
    """統一服務基礎抽象類別"""

    def __init__(
        self,
        service_name: str,
        service_version: str = "1.0.0",
        config: Dict[str, Any] = None,
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.config = config or {}

        # 初始化核心組件
        self.state = ServiceState.INITIALIZING
        self.logger = StructuredLogger(service_name, service_version)
        self.metrics = MetricsCollector()

        # 生命週期回調
        self._startup_callbacks: List[Callable] = []
        self._shutdown_callbacks: List[Callable] = []

        # 健康檢查
        self._health_checks: Dict[str, Callable] = {}

        # 啟動時間
        self._start_time: Optional[float] = None

        self.logger.info(f"Service {service_name} v{service_version} initializing...")

    # === 抽象方法 ===

    @abstractmethod
    async def _initialize(self) -> None:
        """服務初始化邏輯（子類實作）"""

    @abstractmethod
    async def _startup(self) -> None:
        """服務啟動邏輯（子類實作）"""

    @abstractmethod
    async def _shutdown(self) -> None:
        """服務關閉邏輯（子類實作）"""

    # === 生命週期管理 ===

    async def start(self) -> None:
        """啟動服務"""
        if self.state != ServiceState.INITIALIZING:
            self.logger.warning(f"Service already in {self.state.value} state, cannot start")
            return

        try:
            self._start_time = time.time()
            self.logger.info("Starting service...")

            # 執行初始化
            await self._initialize()

            # 執行啟動邏輯
            await self._startup()

            # 執行啟動回調
            for callback in self._startup_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception as e:
                    self.logger.error(f"Startup callback failed: {e}")

            self.state = ServiceState.HEALTHY
            await self.metrics.increment_counter("service_starts", {"service": self.service_name})

            self.logger.info(
                f"Service {self.service_name} started successfully",
                startup_time=time.time() - self._start_time,
            )

        except Exception as e:
            self.state = ServiceState.UNHEALTHY
            await self.metrics.increment_counter(
                "service_start_failures", {"service": self.service_name}
            )
            self.logger.error(f"Failed to start service: {e}")
            raise ServiceError(f"Service startup failed: {e}", "SERVICE_START_FAILED", cause=e)

    async def stop(self) -> None:
        """停止服務"""
        if self.state in [ServiceState.SHUTTING_DOWN, ServiceState.STOPPED]:
            return

        self.state = ServiceState.SHUTTING_DOWN
        self.logger.info("Shutting down service...")

        try:
            # 執行關閉回調
            for callback in reversed(self._shutdown_callbacks):
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception as e:
                    self.logger.error(f"Shutdown callback failed: {e}")

            # 執行關閉邏輯
            await self._shutdown()

            self.state = ServiceState.STOPPED
            await self.metrics.increment_counter("service_stops", {"service": self.service_name})

            uptime = time.time() - (self._start_time or time.time())
            self.logger.info(f"Service {self.service_name} stopped", uptime=uptime)

        except Exception as e:
            self.state = ServiceState.UNHEALTHY
            self.logger.error(f"Failed to stop service cleanly: {e}")
            raise ServiceError(f"Service shutdown failed: {e}", "SERVICE_STOP_FAILED", cause=e)

    # === 健康檢查 ===

    def add_health_check(self, name: str, check_func: Callable[[], bool]):
        """添加健康檢查"""
        self._health_checks[name] = check_func

    async def health_check(self) -> HealthCheckResult:
        """執行健康檢查"""
        checks = {}
        overall_healthy = True
        details = {
            "service": self.service_name,
            "version": self.service_version,
            "uptime": time.time() - (self._start_time or time.time()),
            "state": self.state.value,
        }

        # 執行自訂健康檢查
        for check_name, check_func in self._health_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                checks[check_name] = bool(result)
                if not result:
                    overall_healthy = False
            except Exception as e:
                checks[check_name] = False
                overall_healthy = False
                details[f"{check_name}_error"] = str(e)

        # 判斷整體健康狀態
        if self.state == ServiceState.HEALTHY and overall_healthy:
            status = ServiceState.HEALTHY
            message = "Service is healthy"
        elif self.state == ServiceState.HEALTHY and not overall_healthy:
            status = ServiceState.DEGRADED
            message = "Service is degraded"
        else:
            status = self.state
            message = f"Service is {self.state.value}"

        return HealthCheckResult(status=status, message=message, details=details, checks=checks)

    # === 回調管理 ===

    def add_startup_callback(self, callback: Callable):
        """添加啟動回調"""
        self._startup_callbacks.append(callback)

    def add_shutdown_callback(self, callback: Callable):
        """添加關閉回調"""
        self._shutdown_callbacks.append(callback)

    # === 上下文管理器支援 ===

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    # === 工具方法 ===

    @asynccontextmanager
    async def trace_operation(self, operation_name: str, context: TraceContext = None):
        """追蹤操作"""
        async with trace_span(operation_name, context, self.logger) as span:
            await self.metrics.increment_counter(
                "operations",
                {"operation": operation_name, "service": self.service_name},
            )
            yield span

    async def get_service_info(self) -> Dict[str, Any]:
        """獲取服務資訊"""
        health = await self.health_check()
        metrics = await self.metrics.get_metrics(50)  # 最近50個指標

        return {
            "service": {
                "name": self.service_name,
                "version": self.service_version,
                "state": self.state.value,
                "uptime": time.time() - (self._start_time or time.time()),
                "start_time": self._start_time,
            },
            "health": health.to_dict(),
            "metrics": metrics,
            "config": {k: v for k, v in self.config.items() if not k.startswith("secret")},
        }


# === 常用服務錯誤類別 ===


class ValidationError(ServiceError):
    """驗證錯誤"""

    def __init__(self, message: str, field: str = None, details: Dict = None):
        super().__init__(message, "VALIDATION_ERROR", details or {"field": field})


class NotFoundError(ServiceError):
    """資源未找到錯誤"""

    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(
            message,
            "NOT_FOUND",
            {"resource": resource, "identifier": identifier},
        )


class ConflictError(ServiceError):
    """衝突錯誤"""

    def __init__(self, message: str, resource: str = None):
        super().__init__(message, "CONFLICT", {"resource": resource})


class RateLimitError(ServiceError):
    """速率限制錯誤"""

    def __init__(self, limit: int, window: int):
        message = f"Rate limit exceeded: {limit} requests per {window} seconds"
        super().__init__(message, "RATE_LIMIT_EXCEEDED", {"limit": limit, "window": window})


# === 錯誤處理裝飾器 ===


def handle_service_errors(func):
    """服務錯誤處理裝飾器"""

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ServiceError:
            raise  # 重新拋出服務錯誤
        except Exception as e:
            # 將未知異常包裝為服務錯誤
            raise ServiceError(
                f"Unexpected error in {func.__name__}: {e}",
                "INTERNAL_ERROR",
                cause=e,
            )

    return wrapper
