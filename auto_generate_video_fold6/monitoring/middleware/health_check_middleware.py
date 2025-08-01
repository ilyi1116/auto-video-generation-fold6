#!/usr/bin/env python3
"""
健康檢查中間件
提供系統健康狀態檢查和依賴性驗證
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum

# Database connectivity checks
try:
    import psycopg2

    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ..logging.structured_logger import get_logger

logger = get_logger(__name__)


class HealthStatus(Enum):
    """健康狀態枚舉"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """健康檢查結果"""

    name: str
    status: HealthStatus
    timestamp: datetime
    duration_ms: float
    message: str = ""
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


@dataclass
class SystemHealth:
    """系統整體健康狀態"""

    status: HealthStatus
    timestamp: datetime
    checks: List[HealthCheckResult]
    uptime_seconds: float
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "uptime_seconds": self.uptime_seconds,
            "version": self.version,
            "checks": {
                check.name: {
                    "status": check.status.value,
                    "timestamp": check.timestamp.isoformat(),
                    "duration_ms": check.duration_ms,
                    "message": check.message,
                    "details": check.details,
                }
                for check in self.checks
            },
        }


class HealthChecker:
    """健康檢查執行器"""

    def __init__(self):
        self.start_time = time.time()
        self.checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, HealthCheckResult] = {}

    def register_check(
        self, name: str, check_func: Callable, timeout: float = 5.0
    ):
        """註冊健康檢查函數"""
        self.checks[name] = {"func": check_func, "timeout": timeout}

    async def run_check(self, name: str) -> HealthCheckResult:
        """執行單個健康檢查"""
        if name not in self.checks:
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                timestamp=datetime.utcnow(),
                duration_ms=0,
                message=f"Check '{name}' not registered",
            )

        check_config = self.checks[name]
        start_time = time.time()

        try:
            # 執行健康檢查，帶超時控制
            result = await asyncio.wait_for(
                check_config["func"](), timeout=check_config["timeout"]
            )

            duration_ms = (time.time() - start_time) * 1000

            if isinstance(result, HealthCheckResult):
                result.duration_ms = duration_ms
                return result
            elif isinstance(result, bool):
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY
                    if result
                    else HealthStatus.UNHEALTHY,
                    timestamp=datetime.utcnow(),
                    duration_ms=duration_ms,
                    message="OK" if result else "Check failed",
                )
            else:  # Assume dict or other data
                return HealthCheckResult(
                    name=name,
                    status=HealthStatus.HEALTHY,
                    timestamp=datetime.utcnow(),
                    duration_ms=duration_ms,
                    message="OK",
                    details=result
                    if isinstance(result, dict)
                    else {"result": str(result)},
                )

        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                message=f"Check timeout after {check_config['timeout']}s",
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheckResult(
                name=name,
                status=HealthStatus.UNHEALTHY,
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                message=f"Check failed: {str(e)}",
            )

    async def run_all_checks(self) -> SystemHealth:
        """執行所有健康檢查"""
        results = []

        # 並行執行所有檢查
        check_tasks = [self.run_check(name) for name in self.checks.keys()]

        if check_tasks:
            results = await asyncio.gather(
                *check_tasks, return_exceptions=True
            )

            # 處理異常結果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    check_name = list(self.checks.keys())[i]
                    processed_results.append(
                        HealthCheckResult(
                            name=check_name,
                            status=HealthStatus.UNHEALTHY,
                            timestamp=datetime.utcnow(),
                            duration_ms=0,
                            message=f"Exception: {str(result)}",
                        )
                    )
                else:
                    processed_results.append(result)

            results = processed_results

        # 儲存結果供後續使用
        for result in results:
            self.last_results[result.name] = result

        # 計算整體健康狀態
        overall_status = self._calculate_overall_status(results)
        uptime = time.time() - self.start_time

        return SystemHealth(
            status=overall_status,
            timestamp=datetime.utcnow(),
            checks=results,
            uptime_seconds=uptime,
        )

    def _calculate_overall_status(
        self, results: List[HealthCheckResult]
    ) -> HealthStatus:
        """計算整體健康狀態"""
        if not results:
            return HealthStatus.HEALTHY

        unhealthy_count = sum(
            1 for r in results if r.status == HealthStatus.UNHEALTHY
        )
        degraded_count = sum(
            1 for r in results if r.status == HealthStatus.DEGRADED
        )

        if unhealthy_count > 0:
            # 如果有超過一半的檢查失敗，系統不健康
            if unhealthy_count > len(results) // 2:
                return HealthStatus.UNHEALTHY
            else:
                return HealthStatus.DEGRADED
        elif degraded_count > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY


# 預定義健康檢查函數
async def check_database_connectivity(
    host: str = "localhost",
    port: int = 5432,
    database: str = "postgres",
    user: str = "postgres",
    password: str = "password",
) -> HealthCheckResult:
    """檢查 PostgreSQL 資料庫連接"""
    if not POSTGRES_AVAILABLE:
        return HealthCheckResult(
            name="database",
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.utcnow(),
            duration_ms=0,
            message="psycopg2 not available",
        )

    try:
        start_time = time.time()
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            connect_timeout=3,
        )

        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            result = cur.fetchone()

        conn.close()
        duration_ms = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name="database",
            status=HealthStatus.HEALTHY,
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            message="Database connection successful",
            details={"query_result": result[0] if result else None},
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        return HealthCheckResult(
            name="database",
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            message=f"Database connection failed: {str(e)}",
        )


async def check_redis_connectivity(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: str = None,
) -> HealthCheckResult:
    """檢查 Redis 連接"""
    if not REDIS_AVAILABLE:
        return HealthCheckResult(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.utcnow(),
            duration_ms=0,
            message="redis library not available",
        )

    try:
        start_time = time.time()
        r = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            socket_timeout=3,
            socket_connect_timeout=3,
        )

        # 測試連接
        ping_result = r.ping()
        info = r.info("memory")

        duration_ms = (time.time() - start_time) * 1000

        return HealthCheckResult(
            name="redis",
            status=HealthStatus.HEALTHY,
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            message="Redis connection successful",
            details={
                "ping": ping_result,
                "used_memory": info.get("used_memory", 0),
                "max_memory": info.get("maxmemory", 0),
            },
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        return HealthCheckResult(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            message=f"Redis connection failed: {str(e)}",
        )


async def check_disk_space(
    threshold_percent: float = 90.0,
) -> HealthCheckResult:
    """檢查磁碟空間"""
    import shutil

    try:
        start_time = time.time()
        total, used, free = shutil.disk_usage("/")

        used_percent = (used / total) * 100
        duration_ms = (time.time() - start_time) * 1000

        if used_percent > threshold_percent:
            status = HealthStatus.UNHEALTHY
            message = f"Disk usage critical: {used_percent:.1f}%"
        elif used_percent > threshold_percent - 10:
            status = HealthStatus.DEGRADED
            message = f"Disk usage warning: {used_percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Disk usage normal: {used_percent:.1f}%"

        return HealthCheckResult(
            name="disk_space",
            status=status,
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            message=message,
            details={
                "total_bytes": total,
                "used_bytes": used,
                "free_bytes": free,
                "used_percent": used_percent,
            },
        )

    except Exception as e:
        return HealthCheckResult(
            name="disk_space",
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.utcnow(),
            duration_ms=0,
            message=f"Disk space check failed: {str(e)}",
        )


async def check_memory_usage(
    threshold_percent: float = 90.0,
) -> HealthCheckResult:
    """檢查記憶體使用量"""
    import psutil

    try:
        start_time = time.time()
        memory = psutil.virtual_memory()

        used_percent = memory.percent
        duration_ms = (time.time() - start_time) * 1000

        if used_percent > threshold_percent:
            status = HealthStatus.UNHEALTHY
            message = f"Memory usage critical: {used_percent:.1f}%"
        elif used_percent > threshold_percent - 10:
            status = HealthStatus.DEGRADED
            message = f"Memory usage warning: {used_percent:.1f}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Memory usage normal: {used_percent:.1f}%"

        return HealthCheckResult(
            name="memory_usage",
            status=status,
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
            message=message,
            details={
                "total_bytes": memory.total,
                "available_bytes": memory.available,
                "used_bytes": memory.used,
                "used_percent": used_percent,
            },
        )

    except ImportError:
        return HealthCheckResult(
            name="memory_usage",
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.utcnow(),
            duration_ms=0,
            message="psutil library not available",
        )
    except Exception as e:
        return HealthCheckResult(
            name="memory_usage",
            status=HealthStatus.UNHEALTHY,
            timestamp=datetime.utcnow(),
            duration_ms=0,
            message=f"Memory check failed: {str(e)}",
        )


# 全域健康檢查器實例
health_checker = HealthChecker()


class HealthCheckMiddleware:
    """健康檢查中間件"""

    def __init__(self, app, health_endpoint: str = "/health"):
        self.app = app
        self.health_endpoint = health_endpoint
        self.detailed_endpoint = f"{health_endpoint}/detailed"
        self.logger = get_logger("health_check")

        # 註冊預設健康檢查
        self._register_default_checks()

    def _register_default_checks(self):
        """註冊預設健康檢查"""
        # 磁碟空間檢查
        health_checker.register_check("disk_space", check_disk_space)

        # 記憶體使用檢查 (如果 psutil 可用)
        try:
            import psutil

            health_checker.register_check("memory_usage", check_memory_usage)
        except ImportError:
            pass

        # 資料庫檢查 (如果配置可用)
        if POSTGRES_AVAILABLE:
            health_checker.register_check(
                "database", check_database_connectivity
            )

        # Redis 檢查 (如果配置可用)
        if REDIS_AVAILABLE:
            health_checker.register_check("redis", check_redis_connectivity)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]

        # 健康檢查端點
        if path == self.health_endpoint:
            await self._handle_health_check(
                scope, receive, send, detailed=False
            )
            return
        elif path == self.detailed_endpoint:
            await self._handle_health_check(
                scope, receive, send, detailed=True
            )
            return

        # 正常請求處理
        await self.app(scope, receive, send)

    async def _handle_health_check(
        self, scope, receive, send, detailed: bool = False
    ):
        """處理健康檢查請求"""
        try:
            system_health = await health_checker.run_all_checks()

            if detailed:
                response_data = system_health.to_dict()
            else:
                # 簡化回應
                response_data = {
                    "status": system_health.status.value,
                    "timestamp": system_health.timestamp.isoformat(),
                    "uptime_seconds": system_health.uptime_seconds,
                }

            # 根據健康狀態設定 HTTP 狀態碼
            if system_health.status == HealthStatus.HEALTHY:
                status_code = 200
            elif system_health.status == HealthStatus.DEGRADED:
                status_code = 200  # 仍可服務但有警告
            else:
                status_code = 503  # 服務不可用

            response_body = json.dumps(response_data, indent=2).encode()

            await send(
                {
                    "type": "http.response.start",
                    "status": status_code,
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"content-length", str(len(response_body)).encode()],
                    ],
                }
            )

            await send(
                {
                    "type": "http.response.body",
                    "body": response_body,
                }
            )

            # 記錄健康檢查
            self.logger.info(
                f"Health check completed: {system_health.status.value}",
                status=system_health.status.value,
                checks_count=len(system_health.checks),
                uptime_seconds=system_health.uptime_seconds,
                detailed=detailed,
            )

        except Exception as e:
            # 健康檢查本身失敗
            error_response = {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            }

            response_body = json.dumps(error_response).encode()

            await send(
                {
                    "type": "http.response.start",
                    "status": 500,
                    "headers": [
                        [b"content-type", b"application/json"],
                        [b"content-length", str(len(response_body)).encode()],
                    ],
                }
            )

            await send(
                {
                    "type": "http.response.body",
                    "body": response_body,
                }
            )

            self.logger.error("Health check middleware failed", exception=e)


# 便捷函數
def register_health_check(
    name: str, check_func: Callable, timeout: float = 5.0
):
    """註冊健康檢查的便捷函數"""
    health_checker.register_check(name, check_func, timeout)


async def get_system_health() -> SystemHealth:
    """獲取系統健康狀態的便捷函數"""
    return await health_checker.run_all_checks()
