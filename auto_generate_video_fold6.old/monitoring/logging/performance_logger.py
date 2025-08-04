#!/usr/bin/env python3
"""
高效能結構化日誌記錄器
為監控系統提供優化的日誌記錄功能
"""

import asyncio
import json
import logging
import queue
import threading
import time
import uuid
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# 上下文變數
correlation_id_context: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)
request_id_context: ContextVar[Optional[str]] = ContextVar(
    "request_id", default=None
)


class PerformanceLogger:
    """高效能結構化日誌記錄器"""

    def __init__(
        self,
        service_name: str,
        buffer_size: int = 1000,
        flush_interval: float = 1.0,
        enable_async: bool = True,
    ):
        self.service_name = service_name
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.enable_async = enable_async

        # 高效能緩衝區
        self.log_buffer = deque(maxlen=buffer_size)
        self.buffer_lock = threading.Lock()

        # 異步處理
        if enable_async:
            self.log_queue = queue.Queue(maxsize=buffer_size * 2)
            self.worker_thread = threading.Thread(
                target=self._worker_loop, daemon=True
            )
            self.worker_thread.start()

        # 標準日誌記錄器作為後備
        self.stdlib_logger = logging.getLogger(service_name)
        if not self.stdlib_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.stdlib_logger.addHandler(handler)
            self.stdlib_logger.setLevel(logging.INFO)

        # 效能指標
        self.stats = {
            "logs_processed": 0,
            "total_processing_time": 0.0,
            "avg_processing_time": 0.0,
            "buffer_utilization": 0.0,
            "last_flush_time": time.time(),
        }

    def _create_log_entry(
        self, level: str, message: str, **kwargs
    ) -> Dict[str, Any]:
        """創建高效能日誌條目"""
        timestamp = datetime.now(timezone.utc).isoformat()

        entry = {
            "timestamp": timestamp,
            "level": level,
            "service": self.service_name,
            "message": message,
            "correlation_id": correlation_id_context.get(),
            "request_id": request_id_context.get(),
        }

        # 只添加有值的欄位以減少記憶體使用
        for key, value in kwargs.items():
            if value is not None:
                entry[key] = value

        return entry

    def _worker_loop(self):
        """異步工作線程"""
        while True:
            try:
                # 批量處理日誌條目
                entries = []
                try:
                    # 收集一批日誌條目
                    while len(entries) < 50:  # 批量大小
                        entry = self.log_queue.get(timeout=0.1)
                        entries.append(entry)
                except queue.Empty:
                    pass

                if entries:
                    self._flush_entries(entries)

            except Exception as e:
                # 錯誤處理，避免工作線程崩潰
                self.stdlib_logger.error(f"Log worker error: {e}")
                time.sleep(0.1)

    def _flush_entries(self, entries: list):
        """批量刷新日誌條目"""
        start_time = time.perf_counter()

        for entry in entries:
            # 輸出為 JSON 格式
            json_line = json.dumps(
                entry, separators=(",", ":"), ensure_ascii=False
            )
            print(json_line, flush=True)

        # 更新統計信息
        processing_time = time.perf_counter() - start_time
        self.stats["logs_processed"] += len(entries)
        self.stats["total_processing_time"] += processing_time
        self.stats["avg_processing_time"] = (
            self.stats["total_processing_time"] / self.stats["logs_processed"]
        )
        self.stats["last_flush_time"] = time.time()

    def log(self, level: str, message: str, **kwargs):
        """高效能日誌記錄"""
        entry = self._create_log_entry(level, message, **kwargs)

        if self.enable_async:
            try:
                self.log_queue.put(entry, block=False)
            except queue.Full:
                # 如果隊列滿了，直接輸出
                self._flush_entries([entry])
        else:
            # 同步模式：使用緩衝區
            with self.buffer_lock:
                self.log_buffer.append(entry)

                if len(self.log_buffer) >= self.buffer_size:
                    self._flush_entries(list(self.log_buffer))
                    self.log_buffer.clear()

    def info(self, message: str, **kwargs):
        """INFO 級別日誌"""
        self.log("INFO", message, **kwargs)

    def error(self, message: str, **kwargs):
        """ERROR 級別日誌"""
        self.log("ERROR", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """WARNING 級別日誌"""
        self.log("WARNING", message, **kwargs)

    def debug(self, message: str, **kwargs):
        """DEBUG 級別日誌"""
        self.log("DEBUG", message, **kwargs)

    def flush(self):
        """強制刷新緩衝區"""
        if not self.enable_async:
            with self.buffer_lock:
                if self.log_buffer:
                    self._flush_entries(list(self.log_buffer))
                    self.log_buffer.clear()

    def get_stats(self) -> Dict[str, Any]:
        """獲取效能統計"""
        with self.buffer_lock:
            self.stats["buffer_utilization"] = (
                len(self.log_buffer) / self.buffer_size
            )

        return self.stats.copy()


class LogContext:
    """高效能日誌上下文管理器"""

    def __init__(self, correlation_id: str = None, request_id: str = None):
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.request_id = request_id or str(uuid.uuid4())
        self.tokens = []

    def __enter__(self):
        self.tokens.append(correlation_id_context.set(self.correlation_id))
        self.tokens.append(request_id_context.set(self.request_id))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for token in reversed(self.tokens):
            token.var.reset(token)


# 裝飾器用於函數效能測量
def measure_performance(
    logger: PerformanceLogger = None, operation_name: str = None
):
    """函數效能測量裝飾器"""

    def decorator(func):
        from functools import wraps

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal logger
            if not logger:
                logger = get_performance_logger(func.__module__)

            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.perf_counter()

            try:
                result = await func(*args, **kwargs)
                duration = (time.perf_counter() - start_time) * 1000

                logger.info(
                    f"Operation completed: {name}",
                    operation=name,
                    duration_ms=duration,
                    status="success",
                )

                return result

            except Exception as e:
                duration = (time.perf_counter() - start_time) * 1000

                logger.error(
                    f"Operation failed: {name}",
                    operation=name,
                    duration_ms=duration,
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal logger
            if not logger:
                logger = get_performance_logger(func.__module__)

            name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                duration = (time.perf_counter() - start_time) * 1000

                logger.info(
                    f"Operation completed: {name}",
                    operation=name,
                    duration_ms=duration,
                    status="success",
                )

                return result

            except Exception as e:
                duration = (time.perf_counter() - start_time) * 1000

                logger.error(
                    f"Operation failed: {name}",
                    operation=name,
                    duration_ms=duration,
                    status="error",
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 全域記錄器管理
_performance_loggers: Dict[str, PerformanceLogger] = {}
_loggers_lock = threading.Lock()


def get_performance_logger(service_name: str, **kwargs) -> PerformanceLogger:
    """獲取或創建高效能日誌記錄器"""
    with _loggers_lock:
        if service_name not in _performance_loggers:
            _performance_loggers[service_name] = PerformanceLogger(
                service_name=service_name, **kwargs
            )
        return _performance_loggers[service_name]


def set_correlation_id(correlation_id: str):
    """設定關聯ID"""
    correlation_id_context.set(correlation_id)


def set_request_id(request_id: str):
    """設定請求ID"""
    request_id_context.set(request_id)


def get_correlation_id() -> Optional[str]:
    """獲取關聯ID"""
    return correlation_id_context.get()


def get_request_id() -> Optional[str]:
    """獲取請求ID"""
    return request_id_context.get()


@contextmanager
def performance_context(correlation_id: str = None, request_id: str = None):
    """效能監控上下文管理器"""
    with LogContext(correlation_id, request_id):
        yield


# 批量日誌處理器
class BatchLogProcessor:
    """批量日誌處理器，用於高吞吐量場景"""

    def __init__(self, batch_size: int = 100, flush_interval: float = 5.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batch = []
        self.last_flush = time.time()
        self.lock = threading.Lock()

    def add_log(self, entry: Dict[str, Any]):
        """添加日誌條目到批次"""
        with self.lock:
            self.batch.append(entry)

            # 檢查是否需要刷新
            if (
                len(self.batch) >= self.batch_size
                or time.time() - self.last_flush >= self.flush_interval
            ):
                self._flush_batch()

    def _flush_batch(self):
        """刷新批次"""
        if not self.batch:
            return

        # 批量輸出
        for entry in self.batch:
            json_line = json.dumps(
                entry, separators=(",", ":"), ensure_ascii=False
            )
            print(json_line, flush=True)

        self.batch.clear()
        self.last_flush = time.time()

    def flush(self):
        """強制刷新"""
        with self.lock:
            self._flush_batch()


# 效能監控工具
class PerformanceMonitor:
    """效能監控工具"""

    def __init__(self):
        self.metrics = {}
        self.lock = threading.Lock()

    def record_timing(self, operation: str, duration_ms: float):
        """記錄操作時間"""
        with self.lock:
            if operation not in self.metrics:
                self.metrics[operation] = {
                    "count": 0,
                    "total_time": 0.0,
                    "min_time": float("inf"),
                    "max_time": 0.0,
                    "recent_times": deque(maxlen=100),
                }

            metric = self.metrics[operation]
            metric["count"] += 1
            metric["total_time"] += duration_ms
            metric["min_time"] = min(metric["min_time"], duration_ms)
            metric["max_time"] = max(metric["max_time"], duration_ms)
            metric["recent_times"].append(duration_ms)

    def get_stats(self) -> Dict[str, Any]:
        """獲取效能統計"""
        with self.lock:
            stats = {}
            for operation, metric in self.metrics.items():
                avg_time = metric["total_time"] / metric["count"]
                recent_avg = sum(metric["recent_times"]) / len(
                    metric["recent_times"]
                )

                stats[operation] = {
                    "count": metric["count"],
                    "avg_time_ms": avg_time,
                    "min_time_ms": metric["min_time"],
                    "max_time_ms": metric["max_time"],
                    "recent_avg_ms": recent_avg,
                }

            return stats


# 全域效能監控器
performance_monitor = PerformanceMonitor()
