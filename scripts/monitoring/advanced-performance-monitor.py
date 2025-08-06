#!/usr/bin/env python3
"""
Advanced Performance Monitoring and Analysis System
企業級效能監控與分析系統

Features:
- Real-time system metrics collection
- Microservices performance tracking
- Database query optimization analysis
- Memory and CPU usage profiling
- Network latency monitoring
- Automated alert system
- Performance regression detection
"""

import asyncio
import json
import logging
import platform
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import docker
import psutil
import redis
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class SystemMetrics:
    """System performance metrics"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available: int
    disk_usage: float
    network_io: Dict[str, int]
    load_average: List[float]
    docker_stats: Dict[str, Any]


@dataclass
class ServiceMetrics:
    """Microservice performance metrics"""

    service_name: str
    timestamp: datetime
    response_time: float
    requests_per_second: float
    error_rate: float
    memory_usage: int
    cpu_usage: float
    active_connections: int
    status_code: int


@dataclass
class DatabaseMetrics:
    """Database performance metrics"""

    timestamp: datetime
    active_connections: int
    queries_per_second: float
    slow_queries: int
    cache_hit_ratio: float
    table_locks: int
    deadlocks: int


@dataclass
class PerformanceAlert:
    """Performance alert"""

    timestamp: datetime
    severity: str  # critical, warning, info
    service: str
    metric: str
    current_value: float
    threshold: float
    message: str


class AdvancedPerformanceMonitor:
    """Advanced performance monitoring system"""

    def __init__(self, config_path: str = "config/monitoring-config.yaml"):
        self.config = self._load_config(config_path)
        self.redis_client = None
        self.docker_client = None
        self.metrics_history: Dict[str, List] = {
            "system": [],
            "services": [],
            "database": [],
            "alerts": [],
        }
        self.thresholds = self.config.get("thresholds", {})
        self.services = self.config.get("services", [])
        self.monitoring_interval = self.config.get("interval", 30)
        self.retention_days = self.config.get("retention_days", 7)

    def _load_config(self, config_path: str) -> Dict:
        """Load monitoring configuration"""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._default_config()

    def _default_config(self) -> Dict:
        """Default monitoring configuration"""
        return {
            "interval": 30,
            "retention_days": 7,
            "services": [
                {
                    "name": "api-gateway",
                    "url": "http://localhost:8000/health",
                    "port": 8000,
                },
                {
                    "name": "auth-service",
                    "url": "http://localhost:8001/health",
                    "port": 8001,
                },
                {
                    "name": "ai-service",
                    "url": "http://localhost:8002/health",
                    "port": 8002,
                },
                {
                    "name": "video-service",
                    "url": "http://localhost:8003/health",
                    "port": 8003,
                },
                {
                    "name": "storage-service",
                    "url": "http://localhost:8004/health",
                    "port": 8004,
                },
            ],
            "thresholds": {
                "cpu_percent": 80.0,
                "memory_percent": 85.0,
                "disk_usage": 90.0,
                "response_time": 1000.0,  # ms
                "error_rate": 5.0,  # %
                "database_connections": 80,
            },
            "redis": {"host": "localhost", "port": 6379, "db": 0},
            "database": {
                "host": "localhost",
                "port": 5432,
                "database": "auto_video_db",
            },
        }

    async def initialize(self):
        """Initialize monitoring connections"""
        try:
            # Initialize Redis
            redis_config = self.config.get("redis", {})
            self.redis_client = redis.Redis(
                host=redis_config.get("host", "localhost"),
                port=redis_config.get("port", 6379),
                db=redis_config.get("db", 0),
                decode_responses=True,
            )

            # Initialize Docker client
            self.docker_client = docker.from_env()

            logger.info("Performance monitor initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize performance monitor: {e}")

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect system performance metrics"""
        try:
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # Disk usage
            disk = psutil.disk_usage("/")
            disk_usage = (disk.used / disk.total) * 100

            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            }

            # Load average (Unix systems)
            try:
                load_avg = list(psutil.getloadavg())
            except AttributeError:
                load_avg = [0.0, 0.0, 0.0]  # Windows doesn't have load average

            # Docker stats
            docker_stats = await self._collect_docker_stats()

            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available=memory.available,
                disk_usage=disk_usage,
                network_io=network_io,
                load_average=load_avg,
                docker_stats=docker_stats,
            )

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return None

    async def _collect_docker_stats(self) -> Dict[str, Any]:
        """Collect Docker container statistics"""
        if not self.docker_client:
            return {}

        try:
            stats = {}
            containers = self.docker_client.containers.list(all=True)

            for container in containers:
                try:
                    container_stats = container.stats(stream=False)
                    stats[container.name] = {
                        "status": container.status,
                        "cpu_usage": self._calculate_cpu_percent(
                            container_stats
                        ),
                        "memory_usage": container_stats["memory_stats"].get(
                            "usage", 0
                        ),
                        "memory_limit": container_stats["memory_stats"].get(
                            "limit", 0
                        ),
                        "network_rx": container_stats["networks"]
                        .get("eth0", {})
                        .get("rx_bytes", 0),
                        "network_tx": container_stats["networks"]
                        .get("eth0", {})
                        .get("tx_bytes", 0),
                    }
                except Exception as e:
                    logger.warning(
                        f"Failed to get stats for container {container.name}: {e}"
                    )

            return stats

        except Exception as e:
            logger.error(f"Failed to collect Docker stats: {e}")
            return {}

    def _calculate_cpu_percent(self, stats: Dict) -> float:
        """Calculate CPU usage percentage from Docker stats"""
        try:
            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_cpu_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )

            if system_cpu_delta > 0 and cpu_delta > 0:
                cpu_percent = (
                    (cpu_delta / system_cpu_delta)
                    * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"])
                    * 100.0
                )
                return round(cpu_percent, 2)

        except (KeyError, ZeroDivisionError):
            pass

        return 0.0

    async def collect_service_metrics(self) -> List[ServiceMetrics]:
        """Collect microservice performance metrics"""
        service_metrics = []

        async with aiohttp.ClientSession() as session:
            for service in self.services:
                try:
                    start_time = time.time()

                    async with session.get(
                        service["url"], timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        response_time = (time.time() - start_time) * 1000  # ms

                        # Get additional metrics from service
                        service_data = await self._get_service_stats(
                            service, session
                        )

                        metrics = ServiceMetrics(
                            service_name=service["name"],
                            timestamp=datetime.now(),
                            response_time=response_time,
                            requests_per_second=service_data.get("rps", 0),
                            error_rate=service_data.get("error_rate", 0),
                            memory_usage=service_data.get("memory_usage", 0),
                            cpu_usage=service_data.get("cpu_usage", 0),
                            active_connections=service_data.get(
                                "active_connections", 0
                            ),
                            status_code=response.status,
                        )

                        service_metrics.append(metrics)

                except Exception as e:
                    logger.warning(
                        f"Failed to collect metrics for {service['name']}: {e}"
                    )
                    # Create error metric
                    error_metric = ServiceMetrics(
                        service_name=service["name"],
                        timestamp=datetime.now(),
                        response_time=0,
                        requests_per_second=0,
                        error_rate=100.0,
                        memory_usage=0,
                        cpu_usage=0,
                        active_connections=0,
                        status_code=0,
                    )
                    service_metrics.append(error_metric)

        return service_metrics

    async def _get_service_stats(
        self, service: Dict, session: aiohttp.ClientSession
    ) -> Dict:
        """Get detailed service statistics"""
        try:
            stats_url = f"http://localhost:{service['port']}/metrics"
            async with session.get(
                stats_url, timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception:
            pass

        return {}

    async def collect_database_metrics(self) -> Optional[DatabaseMetrics]:
        """Collect database performance metrics"""
        # This would integrate with your specific database
        # For now, return mock data
        return DatabaseMetrics(
            timestamp=datetime.now(),
            active_connections=15,
            queries_per_second=125.5,
            slow_queries=2,
            cache_hit_ratio=0.95,
            table_locks=0,
            deadlocks=0,
        )

    def analyze_performance(
        self, metrics: SystemMetrics, service_metrics: List[ServiceMetrics]
    ) -> List[PerformanceAlert]:
        """Analyze performance and generate alerts"""
        alerts = []

        # System alerts
        if metrics.cpu_percent > self.thresholds.get("cpu_percent", 80):
            alerts.append(
                PerformanceAlert(
                    timestamp=datetime.now(),
                    severity=(
                        "warning" if metrics.cpu_percent < 90 else "critical"
                    ),
                    service="system",
                    metric="cpu_percent",
                    current_value=metrics.cpu_percent,
                    threshold=self.thresholds["cpu_percent"],
                    message=f"High CPU usage: {metrics.cpu_percent:.1f}%",
                )
            )

        if metrics.memory_percent > self.thresholds.get("memory_percent", 85):
            alerts.append(
                PerformanceAlert(
                    timestamp=datetime.now(),
                    severity=(
                        "warning"
                        if metrics.memory_percent < 95
                        else "critical"
                    ),
                    service="system",
                    metric="memory_percent",
                    current_value=metrics.memory_percent,
                    threshold=self.thresholds["memory_percent"],
                    message=f"High memory usage: {metrics.memory_percent:.1f}%",
                )
            )

        if metrics.disk_usage > self.thresholds.get("disk_usage", 90):
            alerts.append(
                PerformanceAlert(
                    timestamp=datetime.now(),
                    severity="critical",
                    service="system",
                    metric="disk_usage",
                    current_value=metrics.disk_usage,
                    threshold=self.thresholds["disk_usage"],
                    message=f"High disk usage: {metrics.disk_usage:.1f}%",
                )
            )

        # Service alerts
        for service_metric in service_metrics:
            if service_metric.response_time > self.thresholds.get(
                "response_time", 1000
            ):
                alerts.append(
                    PerformanceAlert(
                        timestamp=datetime.now(),
                        severity="warning",
                        service=service_metric.service_name,
                        metric="response_time",
                        current_value=service_metric.response_time,
                        threshold=self.thresholds["response_time"],
                        message=f"High response time: {service_metric.response_time:.1f}ms",
                    )
                )

            if service_metric.error_rate > self.thresholds.get(
                "error_rate", 5
            ):
                alerts.append(
                    PerformanceAlert(
                        timestamp=datetime.now(),
                        severity="critical",
                        service=service_metric.service_name,
                        metric="error_rate",
                        current_value=service_metric.error_rate,
                        threshold=self.thresholds["error_rate"],
                        message=f"High error rate: {service_metric.error_rate:.1f}%",
                    )
                )

        return alerts

    async def store_metrics(
        self,
        system_metrics: SystemMetrics,
        service_metrics: List[ServiceMetrics],
        alerts: List[PerformanceAlert],
    ):
        """Store metrics in Redis for real-time access"""
        if not self.redis_client:
            return

        try:
            timestamp = datetime.now().isoformat()

            # Store system metrics
            await self._store_redis_metric(
                "system", timestamp, asdict(system_metrics)
            )

            # Store service metrics
            for service_metric in service_metrics:
                await self._store_redis_metric(
                    f"service:{service_metric.service_name}",
                    timestamp,
                    asdict(service_metric),
                )

            # Store alerts
            for alert in alerts:
                await self._store_redis_metric(
                    "alerts", timestamp, asdict(alert)
                )

            # Store summary metrics
            summary = {
                "timestamp": timestamp,
                "system_health": self._calculate_system_health(
                    system_metrics, service_metrics
                ),
                "total_services": len(service_metrics),
                "healthy_services": len(
                    [s for s in service_metrics if s.status_code == 200]
                ),
                "alerts_count": len(alerts),
                "critical_alerts": len(
                    [a for a in alerts if a.severity == "critical"]
                ),
            }

            await self._store_redis_metric("summary", timestamp, summary)

        except Exception as e:
            logger.error(f"Failed to store metrics in Redis: {e}")

    async def _store_redis_metric(self, key: str, timestamp: str, data: Dict):
        """Store metric in Redis with TTL"""
        try:
            metric_key = f"metrics:{key}:{timestamp}"
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.setex(
                    metric_key,
                    timedelta(days=self.retention_days),
                    json.dumps(data, default=str),
                ),
            )

            # Also store in time series for easy querying
            list_key = f"metrics:timeseries:{key}"
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.lpush(
                    list_key, json.dumps(data, default=str)
                ),
            )

            # Trim list to keep only recent entries
            max_entries = (
                self.retention_days * 24 * 60 * 60
            ) // self.monitoring_interval
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.ltrim(list_key, 0, max_entries - 1),
            )

        except Exception as e:
            logger.error(f"Failed to store Redis metric {key}: {e}")

    def _calculate_system_health(
        self,
        system_metrics: SystemMetrics,
        service_metrics: List[ServiceMetrics],
    ) -> float:
        """Calculate overall system health score (0-100)"""
        health_score = 100.0

        # System health factors
        if system_metrics.cpu_percent > 80:
            health_score -= (system_metrics.cpu_percent - 80) * 2

        if system_metrics.memory_percent > 85:
            health_score -= (system_metrics.memory_percent - 85) * 3

        if system_metrics.disk_usage > 90:
            health_score -= (system_metrics.disk_usage - 90) * 5

        # Service health factors
        healthy_services = len(
            [s for s in service_metrics if s.status_code == 200]
        )
        total_services = len(service_metrics)

        if total_services > 0:
            service_health_ratio = healthy_services / total_services
            health_score *= service_health_ratio

        return max(0.0, min(100.0, health_score))

    async def generate_performance_report(self) -> Dict:
        """Generate comprehensive performance report"""
        if not self.redis_client:
            return {}

        try:
            # Get recent metrics
            system_metrics = await self._get_recent_metrics(
                "system", 24
            )  # Last 24 hours
            service_metrics = {}

            for service in self.services:
                service_name = service["name"]
                service_metrics[service_name] = await self._get_recent_metrics(
                    f"service:{service_name}", 24
                )

            alerts = await self._get_recent_metrics("alerts", 24)

            # Calculate trends and insights
            report = {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "monitoring_period_hours": 24,
                    "total_services_monitored": len(self.services),
                    "total_alerts": len(alerts),
                    "critical_alerts": len(
                        [a for a in alerts if a.get("severity") == "critical"]
                    ),
                },
                "system_performance": self._analyze_system_trends(
                    system_metrics
                ),
                "service_performance": {
                    service: self._analyze_service_trends(metrics)
                    for service, metrics in service_metrics.items()
                },
                "top_issues": self._identify_top_issues(alerts),
                "recommendations": self._generate_recommendations(
                    system_metrics, service_metrics, alerts
                ),
            }

            return report

        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            return {}

    async def _get_recent_metrics(self, key: str, hours: int) -> List[Dict]:
        """Get recent metrics from Redis"""
        try:
            list_key = f"metrics:timeseries:{key}"
            # Get all entries and filter by time
            entries = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.redis_client.lrange(list_key, 0, -1)
            )

            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_metrics = []

            for entry in entries:
                try:
                    data = json.loads(entry)
                    entry_time = datetime.fromisoformat(
                        data.get("timestamp", "")
                    )
                    if entry_time >= cutoff_time:
                        recent_metrics.append(data)
                except Exception:
                    continue

            return recent_metrics

        except Exception as e:
            logger.error(f"Failed to get recent metrics for {key}: {e}")
            return []

    def _analyze_system_trends(self, metrics: List[Dict]) -> Dict:
        """Analyze system performance trends"""
        if not metrics:
            return {}

        cpu_values = [
            m.get("cpu_percent", 0) for m in metrics if "cpu_percent" in m
        ]
        memory_values = [
            m.get("memory_percent", 0)
            for m in metrics
            if "memory_percent" in m
        ]

        return {
            "avg_cpu_percent": (
                statistics.mean(cpu_values) if cpu_values else 0
            ),
            "max_cpu_percent": max(cpu_values) if cpu_values else 0,
            "avg_memory_percent": (
                statistics.mean(memory_values) if memory_values else 0
            ),
            "max_memory_percent": max(memory_values) if memory_values else 0,
            "cpu_trend": self._calculate_trend(cpu_values),
            "memory_trend": self._calculate_trend(memory_values),
            "sample_count": len(metrics),
        }

    def _analyze_service_trends(self, metrics: List[Dict]) -> Dict:
        """Analyze service performance trends"""
        if not metrics:
            return {}

        response_times = [
            m.get("response_time", 0) for m in metrics if "response_time" in m
        ]
        error_rates = [
            m.get("error_rate", 0) for m in metrics if "error_rate" in m
        ]

        return {
            "avg_response_time": (
                statistics.mean(response_times) if response_times else 0
            ),
            "max_response_time": max(response_times) if response_times else 0,
            "avg_error_rate": (
                statistics.mean(error_rates) if error_rates else 0
            ),
            "max_error_rate": max(error_rates) if error_rates else 0,
            "response_time_trend": self._calculate_trend(response_times),
            "error_rate_trend": self._calculate_trend(error_rates),
            "sample_count": len(metrics),
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from values"""
        if len(values) < 2:
            return "stable"

        # Simple trend calculation using first and last quartile
        first_quartile = (
            values[: len(values) // 4] if len(values) >= 4 else values[:1]
        )
        last_quartile = (
            values[-len(values) // 4 :] if len(values) >= 4 else values[-1:]
        )

        avg_first = statistics.mean(first_quartile)
        avg_last = statistics.mean(last_quartile)

        change_percent = (
            ((avg_last - avg_first) / avg_first * 100) if avg_first > 0 else 0
        )

        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"

    def _identify_top_issues(self, alerts: List[Dict]) -> List[Dict]:
        """Identify top performance issues"""
        # Group alerts by service and metric
        issue_counts = {}

        for alert in alerts:
            service = alert.get("service", "unknown")
            metric = alert.get("metric", "unknown")
            key = f"{service}:{metric}"

            if key not in issue_counts:
                issue_counts[key] = {
                    "service": service,
                    "metric": metric,
                    "count": 0,
                    "severity": alert.get("severity", "info"),
                    "latest_value": alert.get("current_value", 0),
                }

            issue_counts[key]["count"] += 1

            # Update with latest values
            if alert.get("current_value"):
                issue_counts[key]["latest_value"] = alert["current_value"]

        # Sort by count and severity
        top_issues = sorted(
            issue_counts.values(),
            key=lambda x: (
                x["count"],
                1 if x["severity"] == "critical" else 0,
            ),
            reverse=True,
        )

        return top_issues[:10]  # Top 10 issues

    def _generate_recommendations(
        self,
        system_metrics: List[Dict],
        service_metrics: Dict[str, List[Dict]],
        alerts: List[Dict],
    ) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []

        # Analyze system metrics
        if system_metrics:
            cpu_values = [
                m.get("cpu_percent", 0) for m in system_metrics[-10:]
            ]  # Last 10 samples
            memory_values = [
                m.get("memory_percent", 0) for m in system_metrics[-10:]
            ]

            avg_cpu = statistics.mean(cpu_values) if cpu_values else 0
            avg_memory = statistics.mean(memory_values) if memory_values else 0

            if avg_cpu > 70:
                recommendations.append(
                    f"System CPU usage is high ({avg_cpu:.1f}%). Consider scaling horizontally or optimizing CPU-intensive operations."
                )

            if avg_memory > 80:
                recommendations.append(
                    f"System memory usage is high ({avg_memory:.1f}%). Consider increasing memory or optimizing memory-intensive processes."
                )

        # Analyze service metrics
        for service_name, metrics in service_metrics.items():
            if not metrics:
                continue

            response_times = [m.get("response_time", 0) for m in metrics[-10:]]
            error_rates = [m.get("error_rate", 0) for m in metrics[-10:]]

            avg_response_time = (
                statistics.mean(response_times) if response_times else 0
            )
            avg_error_rate = statistics.mean(error_rates) if error_rates else 0

            if avg_response_time > 500:
                recommendations.append(
                    f"{service_name} has high response times ({avg_response_time:.1f}ms). Consider optimization or caching."
                )

            if avg_error_rate > 1:
                recommendations.append(
                    f"{service_name} has elevated error rates ({avg_error_rate:.1f}%). Review logs and fix underlying issues."
                )

        # Analyze alert patterns
        critical_alerts = [
            a for a in alerts if a.get("severity") == "critical"
        ]
        if len(critical_alerts) > 5:
            recommendations.append(
                f"High number of critical alerts ({len(critical_alerts)}). Immediate attention required for system stability."
            )

        return recommendations

    async def run_monitoring_cycle(self):
        """Run a single monitoring cycle"""
        try:
            logger.info("Starting monitoring cycle")

            # Collect metrics
            system_metrics = await self.collect_system_metrics()
            service_metrics = await self.collect_service_metrics()
            database_metrics = await self.collect_database_metrics()

            if not system_metrics:
                logger.error("Failed to collect system metrics")
                return

            # Analyze performance and generate alerts
            alerts = self.analyze_performance(system_metrics, service_metrics)

            # Store metrics
            await self.store_metrics(system_metrics, service_metrics, alerts)

            # Log summary
            healthy_services = len(
                [s for s in service_metrics if s.status_code == 200]
            )
            logger.info(
                f"Monitoring cycle completed - System Health: {self._calculate_system_health(system_metrics, service_metrics):.1f}%, "
                f"Services: {healthy_services}/{len(service_metrics)} healthy, "
                f"Alerts: {len(alerts)} ({len([a for a in alerts if a.severity == 'critical'])} critical)"
            )

            # Print alerts to console
            for alert in alerts:
                log_level = (
                    logging.CRITICAL
                    if alert.severity == "critical"
                    else logging.WARNING
                )
                logger.log(
                    log_level,
                    f"ALERT [{alert.severity.upper()}] {alert.service}: {alert.message}",
                )

        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")

    async def start_monitoring(self):
        """Start continuous monitoring"""
        await self.initialize()

        logger.info(
            f"Starting advanced performance monitoring (interval: {self.monitoring_interval}s)"
        )
        logger.info(f"Monitoring {len(self.services)} services")
        logger.info(f"Platform: {platform.system()} {platform.release()}")

        while True:
            try:
                await self.run_monitoring_cycle()
                await asyncio.sleep(self.monitoring_interval)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Advanced Performance Monitor"
    )
    parser.add_argument(
        "--config",
        default="config/monitoring-config.yaml",
        help="Configuration file path",
    )
    parser.add_argument(
        "--once", action="store_true", help="Run once and exit"
    )
    parser.add_argument(
        "--report", action="store_true", help="Generate performance report"
    )

    args = parser.parse_args()

    monitor = AdvancedPerformanceMonitor(args.config)

    if args.report:
        await monitor.initialize()
        report = await monitor.generate_performance_report()
        print(json.dumps(report, indent=2, default=str))
    elif args.once:
        await monitor.initialize()
        await monitor.run_monitoring_cycle()
    else:
        await monitor.start_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
