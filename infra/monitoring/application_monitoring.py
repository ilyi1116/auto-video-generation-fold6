"""
應用程式整合監控套件
整合 Prometheus、OpenTelemetry 和結構化日誌記錄
"""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict

import asyncpg
import psutil
import redis.asyncio as redis
import structlog
from fastapi import FastAPI, HTTPException
from opentelemetry import trace
from prometheus_client import Counter, Gauge, Info

from .middleware.prometheus_middleware import PrometheusMiddleware


class ApplicationMonitoring:
    """應用程式監控整合類"""

    def __init__(
        self,
        service_name: str,
        service_version: str = "1.0.0",
        environment: str = "production",
        enable_tracing: bool = True,
        enable_metrics: bool = True,
        enable_logging: bool = True,
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment

        # 初始化日誌記錄
        if enable_logging:
            self._setup_structured_logging()

        # 初始化指標收集
        self.metrics_middleware = None
        if enable_metrics:
            self.metrics_middleware = PrometheusMiddleware(service_name)

        # 初始化追蹤
        self.tracing_middleware = None
        if enable_tracing:
            self.tracing_middleware = None  # 將在 setup_app 中初始化

        # 服務健康狀態
        self.health_checks = {}
        self.startup_time = time.time()

        # 業務指標
        self.business_metrics = {
            "user_registrations": Counter(
                "user_registrations_total",
                "Total user registrations",
                ["service"],
            ),
            "video_generations": Counter(
                "video_generations_total",
                "Total video generations",
                ["platform", "status", "service"],
            ),
            "ai_requests": Counter(
                "ai_requests_total",
                "Total AI service requests",
                ["request_type", "status", "service"],
            ),
            "user_sessions": Gauge(
                "active_user_sessions",
                "Number of active user sessions",
                ["service"],
            ),
            "processing_queue_size": Gauge(
                "processing_queue_size",
                "Number of items in processing queue",
                ["queue_type", "service"],
            ),
        }

        self.logger = structlog.get_logger()

    def _setup_structured_logging(self):
        """設定結構化日誌記錄"""
        logging.basicConfig(
            format="%(message)s",
            stream=os.sys.stdout,
            level=logging.INFO,
        )

        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    def setup_app(self, app: FastAPI) -> FastAPI:
        """設定 FastAPI 應用程式監控"""
        # 設定指標中介軟體
        if self.metrics_middleware:
            app.middleware("http")(self.metrics_middleware)
            from .middleware.prometheus_middleware import (
                setup_metrics_endpoint,
            )

            setup_metrics_endpoint(app, self.metrics_middleware)

        # 設定追蹤中介軟體
        if self.tracing_middleware is None:
            self.tracing_middleware = setup_tracing(
                app=app,
                service_name=self.service_name,
                service_version=self.service_version,
                environment=self.environment,
            )

        # 添加健康檢查端點
        self._setup_health_endpoints(app)

        # 添加啟動和關閉事件
        self._setup_lifecycle_events(app)

        return app

    def _setup_health_endpoints(self, app: FastAPI):
        """設定健康檢查端點"""

        @app.get("/health")
        async def health_check():
            """基本健康檢查"""
            return {
                "status": "healthy",
                "service": self.service_name,
                "version": self.service_version,
                "environment": self.environment,
                "uptime": time.time() - self.startup_time,
                "timestamp": time.time(),
            }

        @app.get("/health/ready")
        async def readiness_check():
            """就緒檢查 - 檢查依賴服務"""
            checks = {}
            overall_status = "ready"

            for name, check_func in self.health_checks.items():
                try:
                    result = (
                        await check_func()
                        if asyncio.iscoroutinefunction(check_func)
                        else check_func()
                    )
                    checks[name] = {
                        "status": "healthy" if result else "unhealthy",
                        "timestamp": time.time(),
                    }
                    if not result:
                        overall_status = "not_ready"
                except Exception as e:
                    checks[name] = {
                        "status": "error",
                        "error": str(e),
                        "timestamp": time.time(),
                    }
                    overall_status = "not_ready"

            response = {
                "status": overall_status,
                "service": self.service_name,
                "checks": checks,
                "timestamp": time.time(),
            }

            if overall_status != "ready":
                raise HTTPException(status_code=503, detail=response)

            return response

        @app.get("/health/live")
        async def liveness_check():
            """存活檢查"""
            return {
                "status": "alive",
                "service": self.service_name,
                "uptime": time.time() - self.startup_time,
                "timestamp": time.time(),
            }

    def _setup_lifecycle_events(self, app: FastAPI):
        """設定應用程式生命週期事件"""

        @app.on_event("startup")
        async def startup_event():
            self.logger.info(
                "Service starting",
                service=self.service_name,
                version=self.service_version,
                environment=self.environment,
            )

            # 記錄服務資訊指標
            service_info = Info("service_info", "Service information")
            service_info.info(
                {
                    "version": self.service_version,
                    "environment": self.environment,
                    "start_time": str(self.startup_time),
                }
            )

        @app.on_event("shutdown")
        async def shutdown_event():
            self.logger.info(
                "Service shutting down",
                service=self.service_name,
                uptime=time.time() - self.startup_time,
            )

    def add_health_check(self, name: str, check_func: Callable):
        """添加健康檢查函數"""
        self.health_checks[name] = check_func

    def create_database_health_check(self, database_url: str):
        """創建資料庫健康檢查"""

        async def check_database():
            try:
                conn = await asyncpg.connect(database_url)
                await conn.fetchval("SELECT 1")
                await conn.close()
                return True
            except Exception as e:
                self.logger.error("Database health check failed", error=str(e))
                return False

        return check_database

    def create_redis_health_check(self, redis_url: str):
        """創建 Redis 健康檢查"""

        async def check_redis():
            try:
                r = redis.from_url(redis_url)
                await r.ping()
                await r.close()
                return True
            except Exception as e:
                self.logger.error("Redis health check failed", error=str(e))
                return False

        return check_redis

    def record_business_metric(
        self, metric_name: str, labels: Dict[str, str] = None, value: float = 1
    ):
        """記錄業務指標"""
        if metric_name in self.business_metrics:
            metric = self.business_metrics[metric_name]
            labels = labels or {}
            labels["service"] = self.service_name

            if hasattr(metric, "inc"):
                metric.labels(**labels).inc(value)
            elif hasattr(metric, "set"):
                metric.labels(**labels).set(value)
            elif hasattr(metric, "observe"):
                metric.labels(**labels).observe(value)

    @asynccontextmanager
    async def monitor_operation(
        self, operation_name: str, labels: Dict[str, str] = None
    ):
        """監控操作的上下文管理器"""
        labels = labels or {}
        labels.update(
            {"operation": operation_name, "service": self.service_name}
        )

        start_time = time.time()

        # 開始追蹤 span
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(operation_name) as span:
            span.set_attributes(labels)

            try:
                self.logger.info("Operation started", **labels)
                yield span

                # 記錄成功指標
                duration = time.time() - start_time
                self.metrics_middleware.record_ai_request(
                    operation_name, "success", duration
                )

                self.logger.info(
                    "Operation completed successfully",
                    duration=duration,
                    **labels,
                )

            except Exception as e:
                # 記錄錯誤
                duration = time.time() - start_time
                self.metrics_middleware.record_error(type(e).__name__)

                span.record_exception(e)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))

                self.logger.error(
                    "Operation failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    duration=duration,
                    **labels,
                )
                raise

    def get_system_metrics(self) -> Dict[str, Any]:
        """獲取系統指標"""
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage("/")

            return {
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used,
                },
                "cpu": {"percent": cpu, "cores": psutil.cpu_count()},
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100,
                },
                "uptime": time.time() - self.startup_time,
            }
        except Exception as e:
            self.logger.error("Failed to collect system metrics", error=str(e))
            return {}


# 便利函數
def create_monitored_app(
    app_name: str,
    service_name: str,
    service_version: str = "1.0.0",
    environment: str = None,
    database_url: str = None,
    redis_url: str = None,
) -> tuple[FastAPI, ApplicationMonitoring]:
    """創建帶監控的 FastAPI 應用程式"""
    environment = environment or os.getenv("ENVIRONMENT", "production")

    app = FastAPI(
        title=f"{app_name} API",
        version=service_version,
        description=f"{app_name} - Auto Video Generation System",
    )

    # 創建監控實例
    monitoring = ApplicationMonitoring(
        service_name=service_name,
        service_version=service_version,
        environment=environment,
    )

    # 設定應用程式監控
    monitoring.setup_app(app)

    # 添加資料庫健康檢查
    if database_url:
        monitoring.add_health_check(
            "database", monitoring.create_database_health_check(database_url)
        )

    # 添加 Redis 健康檢查
    if redis_url:
        monitoring.add_health_check(
            "redis", monitoring.create_redis_health_check(redis_url)
        )

    return app, monitoring


# 裝飾器
def monitor_endpoint(
    operation_name: str = None, labels: Dict[str, str] = None
):
    """端點監控裝飾器"""

    def decorator(func):
        from functools import wraps

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 獲取監控實例 (假設已注入到應用程式狀態中)
            monitoring = getattr(func, "_monitoring", None)
            if not monitoring:
                return await func(*args, **kwargs)

            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            async with monitoring.monitor_operation(op_name, labels):
                return await func(*args, **kwargs)

        return wrapper

    return decorator
