#!/usr/bin/env python3
"""
綜合健康檢查監控系統
實時監控所有服務的健康狀態並提供告警機制
"""

import asyncio
import aiohttp
import json
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import yaml
import psutil
import docker
import redis
import sqlalchemy as sa
from sqlalchemy import create_engine
from prometheus_client import CollectorRegistry, Gauge, Counter, start_http_server
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


@dataclass
class HealthStatus:
    """健康狀態資料結構"""
    service_name: str
    status: str  # healthy, unhealthy, degraded, unknown
    response_time: float
    timestamp: datetime
    details: Dict[str, Any]
    dependencies: List[str]
    error_message: Optional[str] = None


@dataclass
class SystemMetrics:
    """系統指標資料結構"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_connections: int
    uptime: float


class HealthMonitor:
    """健康檢查監控器"""
    
    def __init__(self, config_path: str = "./monitoring/health-check/config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.logger = self._setup_logging()
        
        # Prometheus 指標
        self.registry = CollectorRegistry()
        self.health_gauge = Gauge(
            'service_health_status',
            'Service health status (1=healthy, 0=unhealthy)',
            ['service_name'],
            registry=self.registry
        )
        self.response_time_gauge = Gauge(
            'service_response_time_seconds',
            'Service response time in seconds',
            ['service_name'],
            registry=self.registry
        )
        self.dependency_gauge = Gauge(
            'service_dependency_status',
            'Service dependency status',
            ['service_name', 'dependency'],
            registry=self.registry
        )
        self.alert_counter = Counter(
            'health_alerts_total',
            'Total number of health alerts',
            ['service_name', 'alert_type'],
            registry=self.registry
        )
        
        # 狀態追蹤
        self.service_states = {}
        self.alert_history = []
        self.downtime_tracker = {}
        
        # 外部連接
        self.docker_client = None
        self.redis_client = None
        self.db_engine = None
        
    def _load_config(self) -> Dict[str, Any]:
        """載入配置檔案"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            "monitoring": {
                "interval": 30,
                "timeout": 10,
                "retries": 3,
                "alert_threshold": 3
            },
            "services": [
                {
                    "name": "api-gateway",
                    "type": "http",
                    "url": "http://localhost:8080/health",
                    "critical": True,
                    "dependencies": ["auth-service", "data-service"]
                },
                {
                    "name": "auth-service",
                    "type": "http",
                    "url": "http://localhost:8001/health",
                    "critical": True,
                    "dependencies": ["postgresql", "redis"]
                },
                {
                    "name": "data-service",
                    "type": "http",
                    "url": "http://localhost:8002/health",
                    "critical": True,
                    "dependencies": ["postgresql", "s3"]
                },
                {
                    "name": "ai-service",
                    "type": "http",
                    "url": "http://localhost:8003/health",
                    "critical": True,
                    "dependencies": ["gpu-resources"]
                },
                {
                    "name": "video-service",
                    "type": "http",
                    "url": "http://localhost:8004/health",
                    "critical": True,
                    "dependencies": ["storage", "ffmpeg"]
                },
                {
                    "name": "postgresql",
                    "type": "database",
                    "connection": "postgresql://user:pass@localhost:5432/autovideo",
                    "critical": True
                },
                {
                    "name": "redis",
                    "type": "redis",
                    "connection": "redis://localhost:6379",
                    "critical": True
                }
            ],
            "alerts": {
                "email": {
                    "enabled": True,
                    "smtp_server": "localhost:587",
                    "from": "health@auto-video-system.com",
                    "to": ["ops@auto-video-system.com"]
                },
                "webhook": {
                    "enabled": True,
                    "url": "http://alertmanager:9093/api/v1/alerts"
                }
            }
        }
    
    def _setup_logging(self) -> logging.Logger:
        """設定日誌記錄"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('./logs/health_monitor.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    async def start_monitoring(self):
        """開始監控"""
        self.logger.info("Starting health monitoring system")
        
        # 啟動 Prometheus 指標伺服器
        start_http_server(8090, registry=self.registry)
        
        # 初始化外部連接
        await self._initialize_connections()
        
        # 主監控循環
        while True:
            try:
                await self._run_health_checks()
                await asyncio.sleep(self.config["monitoring"]["interval"])
            except KeyboardInterrupt:
                self.logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)
    
    async def _initialize_connections(self):
        """初始化外部連接"""
        try:
            # Docker 連接
            self.docker_client = docker.from_env()
            
            # Redis 連接
            redis_config = next((s for s in self.config["services"] if s["name"] == "redis"), None)
            if redis_config:
                self.redis_client = redis.from_url(redis_config["connection"])
            
            # 資料庫連接
            db_config = next((s for s in self.config["services"] if s["name"] == "postgresql"), None)
            if db_config:
                self.db_engine = create_engine(db_config["connection"])
                
        except Exception as e:
            self.logger.error(f"Failed to initialize connections: {e}")
    
    async def _run_health_checks(self):
        """執行健康檢查"""
        check_tasks = []
        
        for service_config in self.config["services"]:
            task = asyncio.create_task(
                self._check_service_health(service_config)
            )
            check_tasks.append(task)
        
        # 系統指標檢查
        system_task = asyncio.create_task(self._check_system_metrics())
        check_tasks.append(system_task)
        
        # 等待所有檢查完成
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # 處理結果
        health_statuses = []
        for i, result in enumerate(results[:-1]):  # 排除系統指標
            if isinstance(result, HealthStatus):
                health_statuses.append(result)
                await self._update_service_state(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Health check failed: {result}")
        
        # 系統指標處理
        if isinstance(results[-1], SystemMetrics):
            await self._update_system_metrics(results[-1])
        
        # 檢查依賴關係
        await self._check_dependencies(health_statuses)
        
        # 評估整體系統健康
        await self._evaluate_system_health(health_statuses)
    
    async def _check_service_health(self, service_config: Dict[str, Any]) -> HealthStatus:
        """檢查單個服務健康狀態"""
        service_name = service_config["name"]
        service_type = service_config["type"]
        start_time = time.time()
        
        try:
            if service_type == "http":
                status = await self._check_http_service(service_config)
            elif service_type == "database":
                status = await self._check_database_service(service_config)
            elif service_type == "redis":
                status = await self._check_redis_service(service_config)
            elif service_type == "docker":
                status = await self._check_docker_service(service_config)
            else:
                status = HealthStatus(
                    service_name=service_name,
                    status="unknown",
                    response_time=0,
                    timestamp=datetime.now(),
                    details={"error": f"Unknown service type: {service_type}"},
                    dependencies=service_config.get("dependencies", [])
                )
            
            response_time = time.time() - start_time
            status.response_time = response_time
            
            # 更新 Prometheus 指標
            self.health_gauge.labels(service_name=service_name).set(
                1 if status.status == "healthy" else 0
            )
            self.response_time_gauge.labels(service_name=service_name).set(response_time)
            
            return status
            
        except Exception as e:
            self.logger.error(f"Health check failed for {service_name}: {e}")
            return HealthStatus(
                service_name=service_name,
                status="unhealthy",
                response_time=time.time() - start_time,
                timestamp=datetime.now(),
                details={"error": str(e)},
                dependencies=service_config.get("dependencies", []),
                error_message=str(e)
            )
    
    async def _check_http_service(self, service_config: Dict[str, Any]) -> HealthStatus:
        """檢查 HTTP 服務"""
        url = service_config["url"]
        timeout = self.config["monitoring"]["timeout"]
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        return HealthStatus(
                            service_name=service_config["name"],
                            status="healthy",
                            response_time=0,  # 將在上層設定
                            timestamp=datetime.now(),
                            details=response_data,
                            dependencies=service_config.get("dependencies", [])
                        )
                    else:
                        return HealthStatus(
                            service_name=service_config["name"],
                            status="unhealthy",
                            response_time=0,
                            timestamp=datetime.now(),
                            details={"http_status": response.status},
                            dependencies=service_config.get("dependencies", []),
                            error_message=f"HTTP {response.status}"
                        )
            except asyncio.TimeoutError:
                return HealthStatus(
                    service_name=service_config["name"],
                    status="unhealthy",
                    response_time=0,
                    timestamp=datetime.now(),
                    details={"error": "timeout"},
                    dependencies=service_config.get("dependencies", []),
                    error_message="Request timeout"
                )
    
    async def _check_database_service(self, service_config: Dict[str, Any]) -> HealthStatus:
        """檢查資料庫服務"""
        try:
            if self.db_engine:
                with self.db_engine.connect() as conn:
                    result = conn.execute(sa.text("SELECT 1"))
                    result.fetchone()
                    
                return HealthStatus(
                    service_name=service_config["name"],
                    status="healthy",
                    response_time=0,
                    timestamp=datetime.now(),
                    details={"connection": "active"},
                    dependencies=[]
                )
            else:
                raise Exception("Database engine not initialized")
                
        except Exception as e:
            return HealthStatus(
                service_name=service_config["name"],
                status="unhealthy",
                response_time=0,
                timestamp=datetime.now(),
                details={"error": str(e)},
                dependencies=[],
                error_message=str(e)
            )
    
    async def _check_redis_service(self, service_config: Dict[str, Any]) -> HealthStatus:
        """檢查 Redis 服務"""
        try:
            if self.redis_client:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.ping
                )
                
                return HealthStatus(
                    service_name=service_config["name"],
                    status="healthy",
                    response_time=0,
                    timestamp=datetime.now(),
                    details={"connection": "active"},
                    dependencies=[]
                )
            else:
                raise Exception("Redis client not initialized")
                
        except Exception as e:
            return HealthStatus(
                service_name=service_config["name"],
                status="unhealthy",
                response_time=0,
                timestamp=datetime.now(),
                details={"error": str(e)},
                dependencies=[],
                error_message=str(e)
            )
    
    async def _check_docker_service(self, service_config: Dict[str, Any]) -> HealthStatus:
        """檢查 Docker 容器服務"""
        try:
            container_name = service_config.get("container_name", service_config["name"])
            
            if self.docker_client:
                container = self.docker_client.containers.get(container_name)
                
                status = "healthy" if container.status == "running" else "unhealthy"
                
                return HealthStatus(
                    service_name=service_config["name"],
                    status=status,
                    response_time=0,
                    timestamp=datetime.now(),
                    details={
                        "container_status": container.status,
                        "container_id": container.id[:12]
                    },
                    dependencies=service_config.get("dependencies", [])
                )
            else:
                raise Exception("Docker client not initialized")
                
        except Exception as e:
            return HealthStatus(
                service_name=service_config["name"],
                status="unhealthy",
                response_time=0,
                timestamp=datetime.now(),
                details={"error": str(e)},
                dependencies=service_config.get("dependencies", []),
                error_message=str(e)
            )
    
    async def _check_system_metrics(self) -> SystemMetrics:
        """檢查系統指標"""
        try:
            # CPU 使用率
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # 記憶體使用率
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # 磁碟使用率
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # 網路 I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv
            }
            
            # 活躍連接數
            connections = len(psutil.net_connections())
            
            # 系統運行時間
            uptime = time.time() - psutil.boot_time()
            
            return SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                active_connections=connections,
                uptime=uptime
            )
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics(0, 0, 0, {}, 0, 0)
    
    async def _update_service_state(self, health_status: HealthStatus):
        """更新服務狀態並檢查告警條件"""
        service_name = health_status.service_name
        current_time = datetime.now()
        
        # 初始化服務狀態追蹤
        if service_name not in self.service_states:
            self.service_states[service_name] = {
                "status": health_status.status,
                "last_change": current_time,
                "failure_count": 0,
                "last_alert": None
            }
        
        previous_state = self.service_states[service_name]
        
        # 檢查狀態變化
        if previous_state["status"] != health_status.status:
            self.service_states[service_name]["status"] = health_status.status
            self.service_states[service_name]["last_change"] = current_time
            
            if health_status.status == "healthy":
                # 服務恢復
                self.service_states[service_name]["failure_count"] = 0
                await self._send_recovery_alert(health_status)
            else:
                # 服務故障
                self.service_states[service_name]["failure_count"] += 1
        
        # 檢查告警條件
        if health_status.status != "healthy":
            failure_count = self.service_states[service_name]["failure_count"]
            alert_threshold = self.config["monitoring"]["alert_threshold"]
            
            if failure_count >= alert_threshold:
                last_alert = previous_state.get("last_alert")
                if not last_alert or (current_time - last_alert).seconds > 300:  # 5分鐘間隔
                    await self._send_alert(health_status, failure_count)
                    self.service_states[service_name]["last_alert"] = current_time
    
    async def _check_dependencies(self, health_statuses: List[HealthStatus]):
        """檢查服務依賴關係"""
        status_map = {status.service_name: status for status in health_statuses}
        
        for status in health_statuses:
            for dependency in status.dependencies:
                if dependency in status_map:
                    dep_status = status_map[dependency]
                    self.dependency_gauge.labels(
                        service_name=status.service_name,
                        dependency=dependency
                    ).set(1 if dep_status.status == "healthy" else 0)
    
    async def _evaluate_system_health(self, health_statuses: List[HealthStatus]):
        """評估整體系統健康"""
        total_services = len(health_statuses)
        healthy_services = sum(1 for s in health_statuses if s.status == "healthy")
        critical_services = [
            s for s in health_statuses 
            if s.status != "healthy" and self._is_critical_service(s.service_name)
        ]
        
        system_health_score = healthy_services / total_services if total_services > 0 else 0
        
        # 記錄系統健康狀態
        self.logger.info(
            f"System Health: {healthy_services}/{total_services} services healthy "
            f"({system_health_score:.2%})"
        )
        
        # 如果有關鍵服務故障，發送系統級告警
        if critical_services:
            await self._send_system_alert(critical_services, system_health_score)
    
    def _is_critical_service(self, service_name: str) -> bool:
        """檢查是否為關鍵服務"""
        service_config = next(
            (s for s in self.config["services"] if s["name"] == service_name),
            {}
        )
        return service_config.get("critical", False)
    
    async def _update_system_metrics(self, metrics: SystemMetrics):
        """更新系統指標到 Prometheus"""
        # 可以在這裡添加系統指標的 Prometheus 更新
        pass
    
    async def _send_alert(self, health_status: HealthStatus, failure_count: int):
        """發送告警"""
        alert_data = {
            "service": health_status.service_name,
            "status": health_status.status,
            "error": health_status.error_message,
            "failure_count": failure_count,
            "timestamp": health_status.timestamp.isoformat(),
            "details": health_status.details
        }
        
        # 更新告警計數器
        self.alert_counter.labels(
            service_name=health_status.service_name,
            alert_type="service_down"
        ).inc()
        
        # 發送 email 告警
        if self.config["alerts"]["email"]["enabled"]:
            await self._send_email_alert(alert_data)
        
        # 發送 webhook 告警
        if self.config["alerts"]["webhook"]["enabled"]:
            await self._send_webhook_alert(alert_data)
        
        self.logger.warning(f"Alert sent for {health_status.service_name}: {health_status.status}")
    
    async def _send_recovery_alert(self, health_status: HealthStatus):
        """發送恢復告警"""
        recovery_data = {
            "service": health_status.service_name,
            "status": "recovered",
            "timestamp": health_status.timestamp.isoformat(),
            "details": health_status.details
        }
        
        self.logger.info(f"Service recovered: {health_status.service_name}")
    
    async def _send_system_alert(self, critical_services: List[HealthStatus], health_score: float):
        """發送系統級告警"""
        system_alert = {
            "alert_type": "system_health",
            "health_score": health_score,
            "critical_services_down": [s.service_name for s in critical_services],
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.critical(f"System health degraded: {health_score:.2%}")
    
    async def _send_email_alert(self, alert_data: Dict[str, Any]):
        """發送電子郵件告警"""
        try:
            # 這裡實作電子郵件發送邏輯
            pass
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
    async def _send_webhook_alert(self, alert_data: Dict[str, Any]):
        """發送 webhook 告警"""
        try:
            webhook_url = self.config["alerts"]["webhook"]["url"]
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=alert_data) as response:
                    if response.status != 200:
                        self.logger.error(f"Webhook alert failed: {response.status}")
        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")


async def main():
    """主函數"""
    monitor = HealthMonitor()
    await monitor.start_monitoring()


if __name__ == "__main__":
    asyncio.run(main())