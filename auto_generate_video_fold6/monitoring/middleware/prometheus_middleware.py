"""
Prometheus 指標收集中介軟體
為 FastAPI 應用程式提供自動指標收集功能
"""

import asyncio
import time
from typing import Callable

import psutil
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)


class PrometheusMiddleware:
    """Prometheus 指標收集中介軟體"""

    def __init__(self, app_name: str = "auto_video_service"):
        self.app_name = app_name

        # 基礎指標
        self.request_count = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status_code", "service"],
        )

        self.request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request duration in seconds",
            ["method", "endpoint", "service"],
            buckets=(
                0.005,
                0.01,
                0.025,
                0.05,
                0.075,
                0.1,
                0.25,
                0.5,
                0.75,
                1.0,
                2.5,
                5.0,
                7.5,
                10.0,
                float("inf"),
            ),
        )

        self.active_requests = Gauge(
            "http_requests_active",
            "Number of active HTTP requests",
            ["service"],
        )

        # 業務指標
        self.video_generation_count = Counter(
            "video_generation_total",
            "Total video generation requests",
            ["status", "platform", "service"],
        )

        self.video_generation_duration = Histogram(
            "video_generation_duration_seconds",
            "Video generation duration in seconds",
            ["platform", "service"],
            buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1200, float("inf")),
        )

        self.ai_request_count = Counter(
            "ai_requests_total",
            "Total AI service requests",
            ["request_type", "status", "service"],
        )

        self.ai_request_duration = Histogram(
            "ai_request_duration_seconds",
            "AI request duration in seconds",
            ["request_type", "service"],
            buckets=(0.1, 0.5, 1, 2, 5, 10, 20, 30, 60, float("inf")),
        )

        # 系統指標
        self.memory_usage = Gauge(
            "memory_usage_bytes", "Memory usage in bytes", ["service"]
        )

        self.cpu_usage = Gauge(
            "cpu_usage_percent", "CPU usage percentage", ["service"]
        )

        # 資料庫指標
        self.db_connections = Gauge(
            "database_connections_active",
            "Number of active database connections",
            ["service"],
        )

        self.db_query_duration = Histogram(
            "database_query_duration_seconds",
            "Database query duration in seconds",
            ["operation", "service"],
            buckets=(
                0.001,
                0.005,
                0.01,
                0.05,
                0.1,
                0.25,
                0.5,
                1.0,
                2.5,
                5.0,
                float("inf"),
            ),
        )

        # 快取指標
        self.cache_operations = Counter(
            "cache_operations_total",
            "Total cache operations",
            ["operation", "result", "service"],
        )

        # 錯誤指標
        self.error_count = Counter(
            "application_errors_total",
            "Total application errors",
            ["error_type", "service"],
        )

        # 啟動背景任務收集系統指標
        asyncio.create_task(self._collect_system_metrics())

    async def _collect_system_metrics(self):
        """背景任務：收集系統指標"""
        while True:
            try:
                # 記憶體使用量
                memory_info = psutil.virtual_memory()
                self.memory_usage.labels(service=self.app_name).set(
                    memory_info.used
                )

                # CPU 使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_usage.labels(service=self.app_name).set(cpu_percent)

                await asyncio.sleep(30)  # 每 30 秒收集一次
            except Exception as e:
                print(f"Error collecting system metrics: {e}")
                await asyncio.sleep(60)

    async def __call__(
        self, request: Request, call_next: Callable
    ) -> Response:
        """中介軟體主要邏輯"""
        # 記錄請求開始時間
        start_time = time.time()

        # 增加活躍請求計數
        self.active_requests.labels(service=self.app_name).inc()

        # 提取請求資訊
        method = request.method
        path = request.url.path

        # 簡化路徑以避免高基數問題
        endpoint = self._normalize_path(path)

        try:
            # 執行請求
            response = await call_next(request)
            status_code = response.status_code

        except Exception as e:
            # 記錄錯誤
            self.error_count.labels(
                error_type=type(e).__name__, service=self.app_name
            ).inc()

            status_code = 500
            raise

        finally:
            # 減少活躍請求計數
            self.active_requests.labels(service=self.app_name).dec()

            # 計算請求持續時間
            duration = time.time() - start_time

            # 記錄指標
            self.request_count.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                service=self.app_name,
            ).inc()

            self.request_duration.labels(
                method=method, endpoint=endpoint, service=self.app_name
            ).observe(duration)

        return response

    def _normalize_path(self, path: str) -> str:
        """標準化路徑以減少基數"""
        # 移除查詢參數
        path = path.split("?")[0]

        # 替換常見的動態部分
        import re

        # UUID 模式
        path = re.sub(
            r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
            "/{uuid}",
            path,
        )

        # 數字 ID 模式
        path = re.sub(r"/\d+", "/{id}", path)

        # 常見的動態路徑
        patterns = [
            (r"/users/[^/]+", "/users/{user_id}"),
            (r"/projects/[^/]+", "/projects/{project_id}"),
            (r"/videos/[^/]+", "/videos/{video_id}"),
            (r"/generations/[^/]+", "/generations/{generation_id}"),
        ]

        for pattern, replacement in patterns:
            path = re.sub(pattern, replacement, path)

        return path

    def record_video_generation(
        self, status: str, platform: str, duration: float = None
    ):
        """記錄影片生成指標"""
        self.video_generation_count.labels(
            status=status, platform=platform, service=self.app_name
        ).inc()

        if duration is not None:
            self.video_generation_duration.labels(
                platform=platform, service=self.app_name
            ).observe(duration)

    def record_ai_request(
        self, request_type: str, status: str, duration: float
    ):
        """記錄 AI 請求指標"""
        self.ai_request_count.labels(
            request_type=request_type, status=status, service=self.app_name
        ).inc()

        self.ai_request_duration.labels(
            request_type=request_type, service=self.app_name
        ).observe(duration)

    def record_db_query(self, operation: str, duration: float):
        """記錄資料庫查詢指標"""
        self.db_query_duration.labels(
            operation=operation, service=self.app_name
        ).observe(duration)

    def record_cache_operation(self, operation: str, result: str):
        """記錄快取操作指標"""
        self.cache_operations.labels(
            operation=operation, result=result, service=self.app_name
        ).inc()

    def record_error(self, error_type: str):
        """記錄錯誤指標"""
        self.error_count.labels(
            error_type=error_type, service=self.app_name
        ).inc()


def setup_metrics_endpoint(app: FastAPI, middleware: PrometheusMiddleware):
    """設定指標端點"""

    @app.get("/metrics", response_class=PlainTextResponse)
    async def get_metrics():
        """Prometheus 指標端點"""
        return generate_latest()

    @app.get("/health")
    async def health_check():
        """健康檢查端點"""
        return {
            "status": "healthy",
            "service": middleware.app_name,
            "timestamp": time.time(),
        }


# 使用範例
def create_app_with_monitoring(
    app_name: str = "auto_video_service",
) -> tuple[FastAPI, PrometheusMiddleware]:
    """創建帶監控的 FastAPI 應用程式"""
    app = FastAPI(title=f"{app_name} API")

    # 創建監控中介軟體
    metrics_middleware = PrometheusMiddleware(app_name)

    # 添加中介軟體
    app.middleware("http")(metrics_middleware)

    # 設定指標端點
    setup_metrics_endpoint(app, metrics_middleware)

    return app, metrics_middleware
