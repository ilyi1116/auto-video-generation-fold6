"""
健康監控與告警系統
提供全面的系統健康監控、告警和自動恢復功能
"""

import asyncio
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import aiohttp
import psutil

from ..celery_app import celery_app
from ..database import SessionLocal
from ..logging_system import AuditLogger
from ..models import SystemLog

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警級別"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class HealthStatus(Enum):
    """健康狀態"""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class HealthMetric:
    """健康指標"""

    name: str
    value: Any
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def get_status(self) -> HealthStatus:
        """獲取指標狀態"""
        if isinstance(self.value, (int, float)):
            if self.threshold_critical and self.value >= self.threshold_critical:
                return HealthStatus.CRITICAL
            elif self.threshold_warning and self.value >= self.threshold_warning:
                return HealthStatus.WARNING
            else:
                return HealthStatus.HEALTHY
        return HealthStatus.UNKNOWN


@dataclass
class HealthCheck:
    """健康檢查結果"""

    component: str
    status: HealthStatus
    metrics: List[HealthMetric]
    message: str
    timestamp: datetime = None
    execution_time_ms: int = 0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class Alert:
    """告警"""

    id: str
    level: AlertLevel
    title: str
    message: str
    component: str
    metric_name: Optional[str] = None
    metric_value: Optional[Any] = None
    threshold: Optional[float] = None
    timestamp: datetime = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class HealthMonitor:
    """健康監控器"""

    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.health_history: List[Dict] = []
        self.alert_handlers: List[Callable] = []
        self.check_interval = 60  # 檢查間隔（秒）
        self.running = False

        # 預設閾值配置
        self.thresholds = {
            "cpu_usage": {"warning": 70, "critical": 85},
            "memory_usage": {"warning": 80, "critical": 90},
            "disk_usage": {"warning": 80, "critical": 90},
            "response_time": {"warning": 5000, "critical": 10000},  # ms
            "error_rate": {"warning": 5, "critical": 10},  # %
            "queue_size": {"warning": 100, "critical": 500},
        }

    async def start_monitoring(self):
        """開始監控"""
        self.running = True
        logger.info("健康監控系統啟動")

        while self.running:
            try:
                await self.run_health_checks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"健康監控執行錯誤: {e}")
                await asyncio.sleep(self.check_interval)

    def stop_monitoring(self):
        """停止監控"""
        self.running = False
        logger.info("健康監控系統停止")

    async def run_health_checks(self):
        """執行所有健康檢查"""
        checks = []

        # 系統資源檢查
        checks.append(await self.check_system_resources())

        # 資料庫檢查
        checks.append(await self.check_database())

        # Celery 檢查
        checks.append(await self.check_celery())

        # API 端點檢查
        checks.append(await self.check_api_endpoints())

        # 服務依賴檢查
        checks.append(await self.check_dependencies())

        # 處理檢查結果
        await self.process_health_checks(checks)

    async def check_system_resources(self) -> HealthCheck:
        """檢查系統資源"""
        start_time = time.time()
        metrics = []

        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(
                HealthMetric(
                    name="cpu_usage",
                    value=cpu_percent,
                    threshold_warning=self.thresholds["cpu_usage"]["warning"],
                    threshold_critical=self.thresholds["cpu_usage"]["critical"],
                    unit="%",
                    description="CPU 使用率",
                )
            )

            # 記憶體使用率
            memory = psutil.virtual_memory()
            metrics.append(
                HealthMetric(
                    name="memory_usage",
                    value=memory.percent,
                    threshold_warning=self.thresholds["memory_usage"]["warning"],
                    threshold_critical=self.thresholds["memory_usage"]["critical"],
                    unit="%",
                    description="記憶體使用率",
                )
            )

            # 磁碟使用率
            disk = psutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            metrics.append(
                HealthMetric(
                    name="disk_usage",
                    value=disk_percent,
                    threshold_warning=self.thresholds["disk_usage"]["warning"],
                    threshold_critical=self.thresholds["disk_usage"]["critical"],
                    unit="%",
                    description="磁碟使用率",
                )
            )

            # 系統負載
            try:
                load_avg = psutil.getloadavg()
                metrics.append(
                    HealthMetric(
                        name="load_average_1m",
                        value=load_avg[0],
                        threshold_warning=psutil.cpu_count() * 0.7,
                        threshold_critical=psutil.cpu_count() * 0.9,
                        description="1分鐘平均負載",
                    )
                )
            except (OSError, AttributeError):
                pass

            # 確定整體狀態
            critical_metrics = [m for m in metrics if m.get_status() == HealthStatus.CRITICAL]
            warning_metrics = [m for m in metrics if m.get_status() == HealthStatus.WARNING]

            if critical_metrics:
                status = HealthStatus.CRITICAL
                message = f"發現 {len(critical_metrics)} 個嚴重問題"
            elif warning_metrics:
                status = HealthStatus.WARNING
                message = f"發現 {len(warning_metrics)} 個警告"
            else:
                status = HealthStatus.HEALTHY
                message = "系統資源正常"

            return HealthCheck(
                component="system_resources",
                status=status,
                metrics=metrics,
                message=message,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            return HealthCheck(
                component="system_resources",
                status=HealthStatus.CRITICAL,
                metrics=[],
                message=f"系統資源檢查失敗: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

    async def check_database(self) -> HealthCheck:
        """檢查資料庫連接"""
        start_time = time.time()

        try:
            db = SessionLocal()

            # 測試基本連接
            db.execute("SELECT 1")

            # 檢查連接池狀態
            pool_info = db.get_bind().pool.status()

            # 測試寫入操作
            test_log = SystemLog(
                action="health_check",
                resource_type="database",
                message="資料庫健康檢查",
                level="info",
            )
            db.add(test_log)
            db.commit()
            db.delete(test_log)
            db.commit()
            db.close()

            metrics = [
                HealthMetric(name="db_connection", value="connected", description="資料庫連接狀態"),
                HealthMetric(
                    name="db_pool_size",
                    value=pool_info.split()[1] if pool_info else 0,
                    description="連接池大小",
                ),
            ]

            return HealthCheck(
                component="database",
                status=HealthStatus.HEALTHY,
                metrics=metrics,
                message="資料庫連接正常",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            return HealthCheck(
                component="database",
                status=HealthStatus.CRITICAL,
                metrics=[],
                message=f"資料庫檢查失敗: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

    async def check_celery(self) -> HealthCheck:
        """檢查 Celery 狀態"""
        start_time = time.time()

        try:
            from ..celery_app import celery_monitor

            # 檢查工作器狀態
            active_tasks = celery_monitor.get_active_tasks()
            scheduled_tasks = celery_monitor.get_scheduled_tasks()
            worker_stats = celery_monitor.get_worker_stats()

            # 計算指標
            total_active = sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0
            total_scheduled = (
                sum(len(tasks) for tasks in scheduled_tasks.values()) if scheduled_tasks else 0
            )
            worker_count = len(worker_stats) if worker_stats else 0

            metrics = [
                HealthMetric(
                    name="celery_workers",
                    value=worker_count,
                    threshold_warning=0,  # 至少要有1個工作器
                    description="Celery 工作器數量",
                ),
                HealthMetric(
                    name="active_tasks",
                    value=total_active,
                    threshold_warning=self.thresholds["queue_size"]["warning"],
                    threshold_critical=self.thresholds["queue_size"]["critical"],
                    description="活躍任務數量",
                ),
                HealthMetric(
                    name="scheduled_tasks", value=total_scheduled, description="計劃任務數量"
                ),
            ]

            if worker_count == 0:
                status = HealthStatus.CRITICAL
                message = "沒有可用的 Celery 工作器"
            elif total_active > self.thresholds["queue_size"]["critical"]:
                status = HealthStatus.CRITICAL
                message = f"任務隊列過載: {total_active} 個活躍任務"
            elif total_active > self.thresholds["queue_size"]["warning"]:
                status = HealthStatus.WARNING
                message = f"任務隊列繁忙: {total_active} 個活躍任務"
            else:
                status = HealthStatus.HEALTHY
                message = "Celery 服務正常"

            return HealthCheck(
                component="celery",
                status=status,
                metrics=metrics,
                message=message,
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

        except Exception as e:
            return HealthCheck(
                component="celery",
                status=HealthStatus.CRITICAL,
                metrics=[],
                message=f"Celery 檢查失敗: {str(e)}",
                execution_time_ms=int((time.time() - start_time) * 1000),
            )

    async def check_api_endpoints(self) -> HealthCheck:
        """檢查 API 端點"""
        start_time = time.time()

        endpoints = [
            {"url": "http://localhost:8000/health", "name": "main_api"},
            {"url": "http://localhost:8000/admin/logs", "name": "admin_api"},
        ]

        metrics = []
        failed_endpoints = 0

        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    endpoint_start = time.time()
                    async with session.get(endpoint["url"], timeout=10) as response:
                        response_time = int((time.time() - endpoint_start) * 1000)

                        metrics.append(
                            HealthMetric(
                                name=f"{endpoint['name']}_response_time",
                                value=response_time,
                                threshold_warning=self.thresholds["response_time"]["warning"],
                                threshold_critical=self.thresholds["response_time"]["critical"],
                                unit="ms",
                                description=f"{endpoint['name']} 響應時間",
                            )
                        )

                        metrics.append(
                            HealthMetric(
                                name=f"{endpoint['name']}_status_code",
                                value=response.status,
                                description=f"{endpoint['name']} 狀態碼",
                            )
                        )

                        if response.status >= 400:
                            failed_endpoints += 1

                except Exception as e:
                    failed_endpoints += 1
                    metrics.append(
                        HealthMetric(
                            name=f"{endpoint['name']}_error",
                            value=str(e),
                            description=f"{endpoint['name']} 錯誤",
                        )
                    )

        if failed_endpoints > 0:
            status = (
                HealthStatus.CRITICAL
                if failed_endpoints == len(endpoints)
                else HealthStatus.WARNING
            )
            message = f"{failed_endpoints}/{len(endpoints)} 個端點不可用"
        else:
            status = HealthStatus.HEALTHY
            message = "所有 API 端點正常"

        return HealthCheck(
            component="api_endpoints",
            status=status,
            metrics=metrics,
            message=message,
            execution_time_ms=int((time.time() - start_time) * 1000),
        )

    async def check_dependencies(self) -> HealthCheck:
        """檢查外部依賴"""
        start_time = time.time()

        dependencies = [
            {"name": "redis", "host": "localhost", "port": 6379},
            {"name": "postgres", "host": "localhost", "port": 5432},
        ]

        metrics = []
        failed_deps = 0

        for dep in dependencies:
            try:
                # 簡單的端口連接測試
                import socket

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((dep["host"], dep["port"]))
                sock.close()

                if result == 0:
                    metrics.append(
                        HealthMetric(
                            name=f"{dep['name']}_connection",
                            value="connected",
                            description=f"{dep['name']} 連接狀態",
                        )
                    )
                else:
                    failed_deps += 1
                    metrics.append(
                        HealthMetric(
                            name=f"{dep['name']}_connection",
                            value="disconnected",
                            description=f"{dep['name']} 連接狀態",
                        )
                    )

            except Exception as e:
                failed_deps += 1
                metrics.append(
                    HealthMetric(
                        name=f"{dep['name']}_error", value=str(e), description=f"{dep['name']} 錯誤"
                    )
                )

        if failed_deps > 0:
            status = HealthStatus.WARNING
            message = f"{failed_deps}/{len(dependencies)} 個依賴不可用"
        else:
            status = HealthStatus.HEALTHY
            message = "所有依賴正常"

        return HealthCheck(
            component="dependencies",
            status=status,
            metrics=metrics,
            message=message,
            execution_time_ms=int((time.time() - start_time) * 1000),
        )

    async def process_health_checks(self, checks: List[HealthCheck]):
        """處理健康檢查結果"""
        # 計算整體健康狀態
        critical_count = sum(1 for check in checks if check.status == HealthStatus.CRITICAL)
        warning_count = sum(1 for check in checks if check.status == HealthStatus.WARNING)

        if critical_count > 0:
            overall_status = HealthStatus.CRITICAL
        elif warning_count > 0:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY

        # 生成告警
        for check in checks:
            await self.process_component_alerts(check)

        # 記錄健康檢查結果
        health_summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status.value,
            "components": {
                check.component: {
                    "status": check.status.value,
                    "message": check.message,
                    "execution_time_ms": check.execution_time_ms,
                    "metrics": [asdict(metric) for metric in check.metrics],
                }
                for check in checks
            },
        }

        # 保存到歷史記錄
        self.health_history.append(health_summary)

        # 清理舊的歷史記錄（保留最近24小時）
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        self.health_history = [
            record
            for record in self.health_history
            if datetime.fromisoformat(record["timestamp"]) > cutoff_time
        ]

        # 記錄到系統日誌
        await AuditLogger.log_system_event(
            action="health_check",
            message=f"系統健康檢查完成: {overall_status.value}",
            details=health_summary,
            level="info" if overall_status == HealthStatus.HEALTHY else "warning",
        )

    async def process_component_alerts(self, check: HealthCheck):
        """處理組件告警"""
        for metric in check.metrics:
            metric_status = metric.get_status()
            alert_key = f"{check.component}:{metric.name}"

            if metric_status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                # 生成或更新告警
                level = (
                    AlertLevel.WARNING
                    if metric_status == HealthStatus.WARNING
                    else AlertLevel.CRITICAL
                )
                threshold = (
                    metric.threshold_warning
                    if metric_status == HealthStatus.WARNING
                    else metric.threshold_critical
                )

                alert = Alert(
                    id=alert_key,
                    level=level,
                    title=f"{check.component} {metric.name} 異常",
                    message=f"{metric.description}: {metric.value}{metric.unit or ''} (閾值: {threshold})",
                    component=check.component,
                    metric_name=metric.name,
                    metric_value=metric.value,
                    threshold=threshold,
                )

                # 如果是新告警或級別升級，發送通知
                if (
                    alert_key not in self.active_alerts
                    or self.active_alerts[alert_key].level != level
                ):
                    await self.send_alert(alert)

                self.active_alerts[alert_key] = alert

            else:
                # 檢查是否需要解除告警
                if alert_key in self.active_alerts:
                    resolved_alert = self.active_alerts[alert_key]
                    resolved_alert.resolved = True
                    resolved_alert.resolved_at = datetime.utcnow()

                    # 發送解除通知
                    await self.send_alert_resolved(resolved_alert)

                    # 從活躍告警中移除
                    del self.active_alerts[alert_key]

    async def send_alert(self, alert: Alert):
        """發送告警"""
        logger.warning(f"告警: {alert.title} - {alert.message}")

        # 調用所有告警處理器
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"告警處理器執行失敗: {e}")

        # 記錄到系統日誌
        await AuditLogger.log_system_event(
            action="alert_triggered",
            message=f"觸發告警: {alert.title}",
            details=asdict(alert),
            level=alert.level.value,
        )

    async def send_alert_resolved(self, alert: Alert):
        """發送告警解除通知"""
        logger.info(f"告警解除: {alert.title}")

        # 記錄到系統日誌
        await AuditLogger.log_system_event(
            action="alert_resolved",
            message=f"告警已解除: {alert.title}",
            details=asdict(alert),
            level="info",
        )

    def add_alert_handler(self, handler: Callable):
        """添加告警處理器"""
        self.alert_handlers.append(handler)

    def get_health_status(self) -> Dict:
        """獲取當前健康狀態"""
        if not self.health_history:
            return {"status": "unknown", "message": "尚未執行健康檢查"}

        return self.health_history[-1]

    def get_active_alerts(self) -> List[Dict]:
        """獲取活躍告警"""
        return [asdict(alert) for alert in self.active_alerts.values()]


# 全局健康監控實例
health_monitor = HealthMonitor()


# 告警處理器示例
async def email_alert_handler(alert: Alert):
    """電子郵件告警處理器"""
    # 這裡可以實現電子郵件發送邏輯


async def slack_alert_handler(alert: Alert):
    """Slack 告警處理器"""
    # 這裡可以實現 Slack 通知邏輯


async def webhook_alert_handler(alert: Alert):
    """Webhook 告警處理器"""
    # 這裡可以實現 Webhook 通知邏輯


# Celery 任務
@celery_app.task(bind=True)
def start_health_monitoring_task(self):
    """啟動健康監控任務"""
    import asyncio

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(health_monitor.start_monitoring())
    loop.close()
