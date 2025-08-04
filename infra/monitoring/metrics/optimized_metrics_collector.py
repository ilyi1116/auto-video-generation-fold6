#!/usr/bin/env python3
"""
優化的指標收集器
高效能的 Prometheus 指標收集和業務指標處理
"""

import asyncio
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class MetricType(Enum):
    """指標類型"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricEntry:
    """高效能指標條目"""

    name: str
    value: Union[int, float]
    labels: Dict[str, str]
    timestamp: float
    metric_type: MetricType


class OptimizedMetricsCollector:
    """優化的指標收集器"""

    def __init__(
        self,
        buffer_size: int = 10000,
        flush_interval: float = 5.0,
        enable_sampling: bool = True,
        sampling_rate: float = 0.1,
    ):
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.enable_sampling = enable_sampling
        self.sampling_rate = sampling_rate

        # 高效能緩衝區
        self.metrics_buffer = deque(maxlen=buffer_size)
        self.buffer_lock = threading.RLock()

        # 聚合指標快取
        self.aggregated_metrics = defaultdict(list)
        self.last_aggregation = time.time()

        # 效能統計
        self.performance_stats = {
            "metrics_processed": 0,
            "buffer_flushes": 0,
            "processing_time_ms": 0.0,
            "last_flush_time": time.time(),
            "buffer_utilization": 0.0,
        }

        # 異步處理器
        self.executor = ThreadPoolExecutor(
            max_workers=2, thread_name_prefix="metrics"
        )

        # 開始後台處理
        self._start_background_processing()

    def _start_background_processing(self):
        """開始後台指標處理"""

        def background_worker():
            while True:
                try:
                    time.sleep(self.flush_interval)
                    self._flush_metrics()
                    self._aggregate_metrics()
                except Exception as e:
                    print(f"Background metrics processing error: {e}")

        worker_thread = threading.Thread(target=background_worker, daemon=True)
        worker_thread.start()

    def record_metric(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
        metric_type: MetricType = MetricType.GAUGE,
    ) -> bool:
        """高效能指標記錄"""
        start_time = time.perf_counter()

        # 採樣優化
        if self.enable_sampling and metric_type != MetricType.COUNTER:
            import random

            if random.random() > self.sampling_rate:
                return False

        # 創建指標條目
        entry = MetricEntry(
            name=name,
            value=value,
            labels=labels or {},
            timestamp=time.time(),
            metric_type=metric_type,
        )

        # 線程安全地添加到緩衝區
        with self.buffer_lock:
            self.metrics_buffer.append(entry)

            # 更新統計
            self.performance_stats["metrics_processed"] += 1
            processing_time = (time.perf_counter() - start_time) * 1000
            self.performance_stats["processing_time_ms"] += processing_time

            # 檢查是否需要立即刷新
            if len(self.metrics_buffer) >= self.buffer_size * 0.9:
                self.executor.submit(self._flush_metrics)

        return True

    def _flush_metrics(self):
        """刷新指標緩衝區"""
        with self.buffer_lock:
            if not self.metrics_buffer:
                return

            # 複製緩衝區內容
            metrics_to_flush = list(self.metrics_buffer)
            self.metrics_buffer.clear()

        # 批量處理指標
        self._process_metrics_batch(metrics_to_flush)

        # 更新統計
        self.performance_stats["buffer_flushes"] += 1
        self.performance_stats["last_flush_time"] = time.time()

    def _process_metrics_batch(self, metrics: List[MetricEntry]):
        """批量處理指標"""
        start_time = time.perf_counter()

        # 按指標名稱分組
        grouped_metrics = defaultdict(list)
        for metric in metrics:
            grouped_metrics[metric.name].append(metric)

        # 處理每組指標
        for name, metric_group in grouped_metrics.items():
            self._process_metric_group(name, metric_group)

        processing_time = (time.perf_counter() - start_time) * 1000
        print(f"Processed {len(metrics)} metrics in {processing_time:.2f}ms")

    def _process_metric_group(self, name: str, metrics: List[MetricEntry]):
        """處理單個指標組"""
        if not metrics:
            return

        first_metric = metrics[0]

        if first_metric.metric_type == MetricType.COUNTER:
            # 計數器：累加值
            total_value = sum(m.value for m in metrics)
            self._emit_metric(
                name, total_value, first_metric.labels, "counter"
            )

        elif first_metric.metric_type == MetricType.GAUGE:
            # 測量器：使用最新值
            latest_metric = max(metrics, key=lambda m: m.timestamp)
            self._emit_metric(
                name, latest_metric.value, latest_metric.labels, "gauge"
            )

        elif first_metric.metric_type == MetricType.HISTOGRAM:
            # 直方圖：統計分佈
            values = [m.value for m in metrics]
            histogram_data = self._calculate_histogram(values)
            self._emit_histogram(name, histogram_data, first_metric.labels)

        elif first_metric.metric_type == MetricType.SUMMARY:
            # 摘要：計算分位數
            values = [m.value for m in metrics]
            summary_data = self._calculate_summary(values)
            self._emit_summary(name, summary_data, first_metric.labels)

    def _calculate_histogram(self, values: List[float]) -> Dict[str, Any]:
        """計算直方圖統計"""
        if not values:
            return {}

        # 定義桶邊界
        buckets = [
            0.005,
            0.01,
            0.025,
            0.05,
            0.1,
            0.25,
            0.5,
            1.0,
            2.5,
            5.0,
            10.0,
            float("inf"),
        ]
        bucket_counts = [0] * len(buckets)

        # 計算每個桶的計數
        for value in values:
            for i, bucket in enumerate(buckets):
                if value <= bucket:
                    bucket_counts[i] += 1

        return {
            "count": len(values),
            "sum": sum(values),
            "buckets": dict(zip([str(b) for b in buckets], bucket_counts)),
        }

    def _calculate_summary(self, values: List[float]) -> Dict[str, Any]:
        """計算摘要統計"""
        if not values:
            return {}

        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            "count": count,
            "sum": sum(values),
            "quantiles": {
                "0.5": sorted_values[int(count * 0.5)],
                "0.9": sorted_values[int(count * 0.9)],
                "0.95": sorted_values[int(count * 0.95)],
                "0.99": (
                    sorted_values[int(count * 0.99)]
                    if count > 1
                    else sorted_values[0]
                ),
            },
        }

    def _emit_metric(
        self,
        name: str,
        value: Union[int, float],
        labels: Dict[str, str],
        metric_type: str,
    ):
        """輸出 Prometheus 格式指標"""
        labels_str = (
            ",".join([f'{k}="{v}"' for k, v in labels.items()])
            if labels
            else ""
        )
        labels_part = f"{{{labels_str}}}" if labels_str else ""

        # 輸出 Prometheus 格式
        print(f"# TYPE {name} {metric_type}")
        print(f"{name}{labels_part} {value} {int(time.time() * 1000)}")

    def _emit_histogram(
        self, name: str, histogram_data: Dict[str, Any], labels: Dict[str, str]
    ):
        """輸出直方圖指標"""
        labels_str = (
            ",".join([f'{k}="{v}"' for k, v in labels.items()])
            if labels
            else ""
        )
        base_labels = f"{{{labels_str}}}" if labels_str else ""

        print(f"# TYPE {name} histogram")

        # 輸出桶計數
        for bucket, count in histogram_data["buckets"].items():
            bucket_labels = (
                f'{{{labels_str},le="{bucket}"}}'
                if labels_str
                else f'{{le="{bucket}"}}'
            )
            print(f"{name}_bucket{bucket_labels} {count}")

        # 輸出總計數和總和
        print(f"{name}_count{base_labels} {histogram_data['count']}")
        print(f"{name}_sum{base_labels} {histogram_data['sum']}")

    def _emit_summary(
        self, name: str, summary_data: Dict[str, Any], labels: Dict[str, str]
    ):
        """輸出摘要指標"""
        labels_str = (
            ",".join([f'{k}="{v}"' for k, v in labels.items()])
            if labels
            else ""
        )
        base_labels = f"{{{labels_str}}}" if labels_str else ""

        print(f"# TYPE {name} summary")

        # 輸出分位數
        for quantile, value in summary_data["quantiles"].items():
            quantile_labels = (
                f'{{{labels_str},quantile="{quantile}"}}'
                if labels_str
                else f'{{quantile="{quantile}"}}'
            )
            print(f"{name}{quantile_labels} {value}")

        # 輸出總計數和總和
        print(f"{name}_count{base_labels} {summary_data['count']}")
        print(f"{name}_sum{base_labels} {summary_data['sum']}")

    def _aggregate_metrics(self):
        """聚合指標以提高查詢效能"""
        current_time = time.time()

        # 每分鐘執行一次聚合
        if current_time - self.last_aggregation < 60:
            return

        with self.buffer_lock:
            # 這裡可以實作更複雜的聚合邏輯
            # 例如：預計算常用查詢的結果
            self.last_aggregation = current_time

    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取效能統計"""
        with self.buffer_lock:
            current_utilization = len(self.metrics_buffer) / self.buffer_size
            self.performance_stats["buffer_utilization"] = current_utilization

            stats = self.performance_stats.copy()

            # 計算平均處理時間
            if stats["metrics_processed"] > 0:
                stats["avg_processing_time_ms"] = (
                    stats["processing_time_ms"] / stats["metrics_processed"]
                )

            return stats

    def collect_metrics(self) -> Dict[str, Any]:
        """收集所有指標統計"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "performance": self.get_performance_stats(),
            "buffer_size": len(self.metrics_buffer),
            "aggregated_metrics_count": len(self.aggregated_metrics),
        }

    # 便捷方法
    def increment_counter(
        self,
        name: str,
        value: Union[int, float] = 1,
        labels: Optional[Dict[str, str]] = None,
    ):
        """增加計數器"""
        return self.record_metric(name, value, labels, MetricType.COUNTER)

    def set_gauge(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
    ):
        """設定測量器值"""
        return self.record_metric(name, value, labels, MetricType.GAUGE)

    def observe_histogram(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
    ):
        """觀察直方圖值"""
        return self.record_metric(name, value, labels, MetricType.HISTOGRAM)

    def observe_summary(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
    ):
        """觀察摘要值"""
        return self.record_metric(name, value, labels, MetricType.SUMMARY)


# 高效能業務指標管理器
class BusinessMetricsManager:
    """業務指標管理器"""

    def __init__(self):
        self.collector = OptimizedMetricsCollector(
            buffer_size=5000,
            flush_interval=10.0,
            sampling_rate=0.2,  # 業務指標採樣率較高
        )

        # 預定義業務指標
        self.business_metrics_definitions = {
            "video_generation_count": {
                "type": MetricType.COUNTER,
                "description": "Total video generations",
                "labels": ["status", "platform", "user_tier"],
            },
            "user_engagement_rate": {
                "type": MetricType.GAUGE,
                "description": "User engagement rate",
                "labels": ["platform", "content_type"],
            },
            "processing_duration": {
                "type": MetricType.HISTOGRAM,
                "description": "Processing time distribution",
                "labels": ["operation", "service"],
            },
            "api_response_time": {
                "type": MetricType.SUMMARY,
                "description": "API response time summary",
                "labels": ["endpoint", "method", "status_code"],
            },
        }

    def record_video_generation(
        self, status: str, platform: str, user_tier: str = "free"
    ):
        """記錄影片生成指標"""
        return self.collector.increment_counter(
            "video_generation_count",
            labels={
                "status": status,
                "platform": platform,
                "user_tier": user_tier,
            },
        )

    def record_user_engagement(
        self,
        platform: str,
        engagement_rate: float,
        content_type: str = "video",
    ):
        """記錄用戶參與度"""
        return self.collector.set_gauge(
            "user_engagement_rate",
            engagement_rate,
            labels={"platform": platform, "content_type": content_type},
        )

    def record_processing_time(
        self, operation: str, service: str, duration_ms: float
    ):
        """記錄處理時間"""
        return self.collector.observe_histogram(
            "processing_duration",
            duration_ms / 1000,  # 轉換為秒
            labels={"operation": operation, "service": service},
        )

    def record_api_response_time(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
    ):
        """記錄 API 回應時間"""
        return self.collector.observe_summary(
            "api_response_time",
            response_time_ms / 1000,  # 轉換為秒
            labels={
                "endpoint": endpoint,
                "method": method,
                "status_code": str(status_code),
            },
        )

    def get_business_metrics_summary(self) -> Dict[str, Any]:
        """獲取業務指標摘要"""
        return self.collector.collect_metrics()


# 全域實例
optimized_collector = OptimizedMetricsCollector()
business_metrics_manager = BusinessMetricsManager()


# 效能測量裝飾器
def measure_execution_time(
    metric_name: str = None, labels: Dict[str, str] = None
):
    """測量函數執行時間的裝飾器"""

    def decorator(func):
        from functools import wraps

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = metric_name or f"{func.__module__}.{func.__name__}"
            start_time = time.perf_counter()

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000

                optimized_collector.observe_histogram(
                    f"function_execution_time",
                    duration_ms / 1000,
                    labels={
                        **(labels or {}),
                        "function": name,
                        "status": "success",
                    },
                )

                return result

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000

                optimized_collector.observe_histogram(
                    f"function_execution_time",
                    duration_ms / 1000,
                    labels={
                        **(labels or {}),
                        "function": name,
                        "status": "error",
                        "error_type": type(e).__name__,
                    },
                )
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = metric_name or f"{func.__module__}.{func.__name__}"
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000

                optimized_collector.observe_histogram(
                    f"function_execution_time",
                    duration_ms / 1000,
                    labels={
                        **(labels or {}),
                        "function": name,
                        "status": "success",
                    },
                )

                return result

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000

                optimized_collector.observe_histogram(
                    f"function_execution_time",
                    duration_ms / 1000,
                    labels={
                        **(labels or {}),
                        "function": name,
                        "status": "error",
                        "error_type": type(e).__name__,
                    },
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
