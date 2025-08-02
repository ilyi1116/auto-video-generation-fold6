#!/usr/bin/env python3
"""
Docker Performance Monitor
Real-time monitoring and optimization for containerized services
"""

import json
import logging
import signal
import sys
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

import docker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("docker-performance.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class ContainerMetrics:
    """Container performance metrics"""

    name: str
    id: str
    status: str
    cpu_percent: float
    memory_usage: int
    memory_limit: int
    memory_percent: float
    network_rx: int
    network_tx: int
    block_read: int
    block_write: int
    pids: int
    timestamp: str


@dataclass
class SystemMetrics:
    """System-wide performance metrics"""

    cpu_percent: float
    memory_total: int
    memory_available: int
    memory_percent: float
    disk_usage_percent: float
    load_average: List[float]
    timestamp: str


@dataclass
class PerformanceAlert:
    """Performance alert definition"""

    type: str
    severity: str
    message: str
    container: Optional[str]
    value: float
    threshold: float
    timestamp: str


class DockerPerformanceMonitor:
    """Advanced Docker performance monitoring and optimization"""

    def __init__(self, config_file: str = "monitor-config.json"):
        self.client = docker.from_env()
        self.config = self._load_config(config_file)
        self.metrics_history: List[Dict] = []
        self.alerts: List[PerformanceAlert] = []
        self.running = False
        self.monitor_thread = None

        # Performance thresholds
        self.cpu_threshold = self.config.get("cpu_threshold", 80.0)
        self.memory_threshold = self.config.get("memory_threshold", 85.0)
        self.disk_threshold = self.config.get("disk_threshold", 90.0)
        self.network_threshold = self.config.get(
            "network_threshold", 100 * 1024 * 1024
        )  # 100MB/s

        # Monitoring intervals
        self.monitor_interval = self.config.get("monitor_interval", 30)
        self.history_retention = self.config.get("history_retention_hours", 24)

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_config(self, config_file: str) -> Dict:
        """Load monitoring configuration"""
        default_config = {
            "services_to_monitor": [
                "frontend",
                "api-gateway",
                "trend-service",
                "video-service",
                "social-service",
                "scheduler-service",
                "postgres",
                "redis",
                "minio",
            ],
            "cpu_threshold": 80.0,
            "memory_threshold": 85.0,
            "disk_threshold": 90.0,
            "network_threshold": 104857600,  # 100MB
            "monitor_interval": 30,
            "history_retention_hours": 24,
            "enable_auto_restart": True,
            "enable_scaling_recommendations": True,
            "alert_webhook_url": None,
        }

        try:
            if Path(config_file).exists():
                with open(config_file, "r") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            logger.warning(f"Could not load config file: {e}")

        return default_config

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop_monitoring()
        sys.exit(0)

    def get_container_metrics(self, container) -> ContainerMetrics:
        """Get comprehensive metrics for a container"""
        try:
            # Get container stats
            stats = container.stats(stream=False)

            # Calculate CPU percentage
            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )

            cpu_percent = 0.0
            if system_delta > 0:
                cpu_percent = (
                    (cpu_delta / system_delta)
                    * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"])
                    * 100.0
                )

            # Memory metrics
            memory_usage = stats["memory_stats"]["usage"]
            memory_limit = stats["memory_stats"]["limit"]
            memory_percent = (memory_usage / memory_limit) * 100.0

            # Network metrics
            network_rx = network_tx = 0
            if "networks" in stats:
                for interface in stats["networks"].values():
                    network_rx += interface.get("rx_bytes", 0)
                    network_tx += interface.get("tx_bytes", 0)

            # Block I/O metrics
            block_read = block_write = 0
            if (
                "blkio_stats" in stats
                and "io_service_bytes_recursive" in stats["blkio_stats"]
            ):
                for entry in stats["blkio_stats"][
                    "io_service_bytes_recursive"
                ]:
                    if entry["op"] == "Read":
                        block_read += entry["value"]
                    elif entry["op"] == "Write":
                        block_write += entry["value"]

            # PIDs count
            pids = stats.get("pids_stats", {}).get("current", 0)

            return ContainerMetrics(
                name=container.name,
                id=container.short_id,
                status=container.status,
                cpu_percent=round(cpu_percent, 2),
                memory_usage=memory_usage,
                memory_limit=memory_limit,
                memory_percent=round(memory_percent, 2),
                network_rx=network_rx,
                network_tx=network_tx,
                block_read=block_read,
                block_write=block_write,
                pids=pids,
                timestamp=datetime.utcnow().isoformat(),
            )

        except Exception as e:
            logger.error(f"Error getting metrics for {container.name}: {e}")
            return None

    def get_system_metrics(self) -> SystemMetrics:
        """Get system-wide performance metrics"""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            # Disk usage for root filesystem
            disk = psutil.disk_usage("/")

            # Load average
            load_avg = list(psutil.getloadavg())

            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_total=memory.total,
                memory_available=memory.available,
                memory_percent=memory.percent,
                disk_usage_percent=disk.percent,
                load_average=load_avg,
                timestamp=datetime.utcnow().isoformat(),
            )

        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return None

    def check_performance_alerts(
        self,
        container_metrics: List[ContainerMetrics],
        system_metrics: SystemMetrics,
    ):
        """Check for performance issues and generate alerts"""
        alerts = []

        # System-level alerts
        if system_metrics.cpu_percent > self.cpu_threshold:
            alerts.append(
                PerformanceAlert(
                    type="system_cpu",
                    severity=(
                        "warning"
                        if system_metrics.cpu_percent < 95
                        else "critical"
                    ),
                    message=f"High system CPU usage: {system_metrics.cpu_percent:.1f}%",
                    container=None,
                    value=system_metrics.cpu_percent,
                    threshold=self.cpu_threshold,
                    timestamp=datetime.utcnow().isoformat(),
                )
            )

        if system_metrics.memory_percent > self.memory_threshold:
            alerts.append(
                PerformanceAlert(
                    type="system_memory",
                    severity=(
                        "warning"
                        if system_metrics.memory_percent < 95
                        else "critical"
                    ),
                    message=f"High system memory usage: {system_metrics.memory_percent:.1f}%",
                    container=None,
                    value=system_metrics.memory_percent,
                    threshold=self.memory_threshold,
                    timestamp=datetime.utcnow().isoformat(),
                )
            )

        if system_metrics.disk_usage_percent > self.disk_threshold:
            alerts.append(
                PerformanceAlert(
                    type="system_disk",
                    severity=(
                        "warning"
                        if system_metrics.disk_usage_percent < 95
                        else "critical"
                    ),
                    message=f"High disk usage: {system_metrics.disk_usage_percent:.1f}%",
                    container=None,
                    value=system_metrics.disk_usage_percent,
                    threshold=self.disk_threshold,
                    timestamp=datetime.utcnow().isoformat(),
                )
            )

        # Container-level alerts
        for metrics in container_metrics:
            if metrics.cpu_percent > self.cpu_threshold:
                alerts.append(
                    PerformanceAlert(
                        type="container_cpu",
                        severity=(
                            "warning"
                            if metrics.cpu_percent < 95
                            else "critical"
                        ),
                        message=f"High CPU usage in {metrics.name}: {metrics.cpu_percent:.1f}%",
                        container=metrics.name,
                        value=metrics.cpu_percent,
                        threshold=self.cpu_threshold,
                        timestamp=datetime.utcnow().isoformat(),
                    )
                )

            if metrics.memory_percent > self.memory_threshold:
                alerts.append(
                    PerformanceAlert(
                        type="container_memory",
                        severity=(
                            "warning"
                            if metrics.memory_percent < 95
                            else "critical"
                        ),
                        message=f"High memory usage in {metrics.name}: {metrics.memory_percent:.1f}%",
                        container=metrics.name,
                        value=metrics.memory_percent,
                        threshold=self.memory_threshold,
                        timestamp=datetime.utcnow().isoformat(),
                    )
                )

        # Add new alerts to the list
        self.alerts.extend(alerts)

        # Log alerts
        for alert in alerts:
            level = (
                logging.WARNING
                if alert.severity == "warning"
                else logging.CRITICAL
            )
            logger.log(level, f"ALERT: {alert.message}")

        return alerts

    def generate_optimization_recommendations(
        self,
        container_metrics: List[ContainerMetrics],
        system_metrics: SystemMetrics,
    ) -> List[str]:
        """Generate performance optimization recommendations"""
        recommendations = []

        # Analyze container resource usage
        high_cpu_containers = [
            m for m in container_metrics if m.cpu_percent > 70
        ]
        high_memory_containers = [
            m for m in container_metrics if m.memory_percent > 70
        ]

        if high_cpu_containers:
            for container in high_cpu_containers:
                recommendations.append(
                    f"Consider increasing CPU limits for {container.name} "
                    f"(current usage: {container.cpu_percent:.1f}%)"
                )

        if high_memory_containers:
            for container in high_memory_containers:
                recommendations.append(
                    f"Consider increasing memory limits for {container.name} "
                    f"(current usage: {container.memory_percent:.1f}%)"
                )

        # System-level recommendations
        if system_metrics.memory_percent > 80:
            recommendations.append(
                "System memory usage is high. Consider adding more RAM or optimizing applications."
            )

        if system_metrics.load_average[0] > psutil.cpu_count():
            recommendations.append(
                f"System load average ({system_metrics.load_average[0]:.2f}) exceeds CPU count. "
                "Consider reducing container concurrency or scaling horizontally."
            )

        return recommendations

    def save_metrics_to_file(
        self,
        container_metrics: List[ContainerMetrics],
        system_metrics: SystemMetrics,
    ):
        """Save metrics to JSON file for analysis"""
        try:
            metrics_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "system": asdict(system_metrics),
                "containers": [asdict(m) for m in container_metrics if m],
            }

            # Add to history
            self.metrics_history.append(metrics_data)

            # Cleanup old data
            cutoff_time = datetime.utcnow() - timedelta(
                hours=self.history_retention
            )
            self.metrics_history = [
                m
                for m in self.metrics_history
                if datetime.fromisoformat(m["timestamp"].replace("Z", ""))
                > cutoff_time
            ]

            # Save to file
            with open("docker-performance-metrics.json", "w") as f:
                json.dump(
                    {
                        "current": metrics_data,
                        "history": self.metrics_history[
                            -100:
                        ],  # Keep last 100 entries
                        "alerts": [
                            asdict(a) for a in self.alerts[-50:]
                        ],  # Keep last 50 alerts
                    },
                    f,
                    indent=2,
                )

        except Exception as e:
            logger.error(f"Error saving metrics: {e}")

    def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting Docker performance monitoring...")

        while self.running:
            try:
                # Get system metrics
                system_metrics = self.get_system_metrics()
                if not system_metrics:
                    time.sleep(self.monitor_interval)
                    continue

                # Get container metrics
                container_metrics = []
                containers = self.client.containers.list()

                for container in containers:
                    # Filter by configured services
                    if container.name in self.config["services_to_monitor"]:
                        metrics = self.get_container_metrics(container)
                        if metrics:
                            container_metrics.append(metrics)

                # Check for alerts
                alerts = self.check_performance_alerts(
                    container_metrics, system_metrics
                )

                # Generate recommendations
                recommendations = self.generate_optimization_recommendations(
                    container_metrics, system_metrics
                )

                # Log recommendations
                if recommendations:
                    logger.info("Performance recommendations:")
                    for rec in recommendations:
                        logger.info(f"  - {rec}")

                # Save metrics
                self.save_metrics_to_file(container_metrics, system_metrics)

                # Print summary
                logger.info(
                    f"Monitored {len(container_metrics)} containers. "
                    f"System: CPU {system_metrics.cpu_percent:.1f}%, "
                    f"Memory {system_metrics.memory_percent:.1f}%, "
                    f"Disk {system_metrics.disk_usage_percent:.1f}%"
                )

                time.sleep(self.monitor_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitor_interval)

    def start_monitoring(self):
        """Start the monitoring process"""
        if self.running:
            logger.warning("Monitoring is already running")
            return

        self.running = True
        self.monitor_thread = threading.Thread(
            target=self.monitor_loop, daemon=True
        )
        self.monitor_thread.start()
        logger.info("Docker performance monitoring started")

    def stop_monitoring(self):
        """Stop the monitoring process"""
        if not self.running:
            return

        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Docker performance monitoring stopped")

    def get_performance_report(self) -> Dict:
        """Generate a comprehensive performance report"""
        if not self.metrics_history:
            return {"error": "No metrics data available"}

        latest_metrics = self.metrics_history[-1]

        # Calculate averages over last hour
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_metrics = [
            m
            for m in self.metrics_history
            if datetime.fromisoformat(m["timestamp"].replace("Z", ""))
            > hour_ago
        ]

        if recent_metrics:
            avg_system_cpu = sum(
                m["system"]["cpu_percent"] for m in recent_metrics
            ) / len(recent_metrics)
            avg_system_memory = sum(
                m["system"]["memory_percent"] for m in recent_metrics
            ) / len(recent_metrics)
        else:
            avg_system_cpu = latest_metrics["system"]["cpu_percent"]
            avg_system_memory = latest_metrics["system"]["memory_percent"]

        return {
            "report_time": datetime.utcnow().isoformat(),
            "monitoring_duration_hours": len(self.metrics_history)
            * self.monitor_interval
            / 3600,
            "current_metrics": latest_metrics,
            "hourly_averages": {
                "system_cpu_percent": round(avg_system_cpu, 2),
                "system_memory_percent": round(avg_system_memory, 2),
            },
            "recent_alerts": [asdict(a) for a in self.alerts[-10:]],
            "total_alerts": len(self.alerts),
        }


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Docker Performance Monitor")
    parser.add_argument(
        "--config",
        default="monitor-config.json",
        help="Configuration file path",
    )
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate and display performance report",
    )

    args = parser.parse_args()

    monitor = DockerPerformanceMonitor(args.config)

    if args.report:
        # Generate and display report
        report = monitor.get_performance_report()
        print(json.dumps(report, indent=2))
        return

    if args.daemon:
        # Run as daemon
        monitor.start_monitoring()
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            monitor.stop_monitoring()
    else:
        # Run once and exit
        monitor.start_monitoring()
        time.sleep(monitor.monitor_interval + 5)  # Wait for one cycle
        monitor.stop_monitoring()

        # Display report
        report = monitor.get_performance_report()
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
