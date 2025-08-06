#!/usr/bin/env python3
"""
Log Analysis Dashboard
日誌分析儀表板

Real-time log analysis and visualization dashboard
for the centralized logging system.
"""

import asyncio
import json
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis


@dataclass
class LogAnalytics:
    """Log analytics result"""

    time_range: str
    total_logs: int
    logs_by_service: Dict[str, int]
    logs_by_level: Dict[str, int]
    error_rate: float
    avg_response_time: float
    top_errors: List[Dict]
    service_health: Dict[str, float]
    performance_trends: Dict[str, List[float]]


@dataclass
class RealTimeMetrics:
    """Real-time metrics"""

    timestamp: datetime
    logs_per_second: float
    error_rate: float
    avg_response_time: float
    active_services: int
    critical_alerts: int


class LogAnalyticsDashboard:
    """Real-time log analytics dashboard"""

    def __init__(self, config_path: str = "config/logging-config.yaml"):
        self.redis_client = None
        self.metrics_history = []
        self.analysis_cache = {}

    async def initialize(self):
        """Initialize dashboard"""
        try:
            # Connect to Redis
            self.redis_client = redis.Redis(
                host="localhost", port=6379, db=2, decode_responses=True
            )

            # Test connection
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.ping
            )

            print("📊 Log Analytics Dashboard initialized")

        except Exception as e:
            print(f"❌ Failed to initialize dashboard: {e}")
            raise

    async def get_real_time_metrics(self) -> RealTimeMetrics:
        """Get real-time metrics"""
        try:
            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)

            # Get recent log batches
            batches = await self._get_recent_batches(1)  # Last minute

            # Calculate metrics
            total_logs = sum(batch.get("batch_size", 0) for batch in batches)
            logs_per_second = total_logs / 60.0  # Per second over last minute

            # Get error rate
            error_count = sum(batch.get("error_count", 0) for batch in batches)
            error_rate = (
                (error_count / total_logs * 100) if total_logs > 0 else 0
            )

            # Get active services
            all_services = set()
            for batch in batches:
                all_services.update(batch.get("services", []))

            # Mock response time and alerts (would come from actual analysis)
            avg_response_time = 150.0  # ms
            critical_alerts = 0

            return RealTimeMetrics(
                timestamp=now,
                logs_per_second=logs_per_second,
                error_rate=error_rate,
                avg_response_time=avg_response_time,
                active_services=len(all_services),
                critical_alerts=critical_alerts,
            )

        except Exception as e:
            print(f"Error getting real-time metrics: {e}")
            return RealTimeMetrics(
                timestamp=datetime.now(),
                logs_per_second=0,
                error_rate=0,
                avg_response_time=0,
                active_services=0,
                critical_alerts=0,
            )

    async def analyze_logs(self, time_range_hours: int = 1) -> LogAnalytics:
        """Comprehensive log analysis"""
        try:
            print(
                f"🔍 Analyzing logs for the last {time_range_hours} hour(s)..."
            )

            # Get all log streams
            stream_keys = await self._get_all_log_streams()

            # Collect logs from all streams
            all_logs = []
            logs_by_service = defaultdict(int)
            logs_by_level = defaultdict(int)
            response_times = []
            errors = []

            cutoff_time = datetime.now() - timedelta(hours=time_range_hours)

            for stream_key in stream_keys:
                try:
                    # Parse service and level from stream key
                    parts = stream_key.split(":")
                    if len(parts) >= 3:
                        service_name = parts[1]
                        log_level = parts[2]

                        # Get entries from stream
                        entries = await self._get_stream_entries(
                            stream_key, cutoff_time
                        )

                        for entry_id, fields in entries:
                            logs_by_service[service_name] += 1
                            logs_by_level[log_level] += 1

                            # Extract response time if available
                            if "duration_ms" in fields:
                                try:
                                    response_times.append(
                                        float(fields["duration_ms"])
                                    )
                                except Exception:
                                    pass

                            # Collect errors
                            if log_level in ["error", "critical"]:
                                error_data = {
                                    "service": service_name,
                                    "message": fields.get("message", ""),
                                    "timestamp": fields.get("timestamp", ""),
                                    "error_type": fields.get(
                                        "error_details", {}
                                    ).get("type", "Unknown"),
                                }
                                errors.append(error_data)

                            all_logs.append(fields)

                except Exception as e:
                    print(
                        f"Warning: Error processing stream {stream_key}: {e}"
                    )

            # Calculate analytics
            total_logs = len(all_logs)
            error_count = logs_by_level.get("error", 0) + logs_by_level.get(
                "critical", 0
            )
            error_rate = (
                (error_count / total_logs * 100) if total_logs > 0 else 0
            )
            avg_response_time = (
                statistics.mean(response_times) if response_times else 0
            )

            # Analyze top errors
            error_counter = Counter()
            for error in errors:
                error_key = f"{error['service']}: {error['error_type']}"
                error_counter[error_key] += 1

            top_errors = [
                {"error": error, "count": count}
                for error, count in error_counter.most_common(10)
            ]

            # Calculate service health scores
            service_health = {}
            for service in logs_by_service:
                service_errors = len(
                    [e for e in errors if e["service"] == service]
                )
                service_total = logs_by_service[service]
                service_error_rate = (
                    (service_errors / service_total)
                    if service_total > 0
                    else 0
                )
                service_health[service] = max(
                    0, 100 - (service_error_rate * 100)
                )

            # Mock performance trends (would be calculated from historical data)
            performance_trends = {
                "response_time": (
                    response_times[-20:]
                    if len(response_times) > 20
                    else response_times
                ),
                "error_rate": [error_rate]
                * 10,  # Would be historical error rates
                "throughput": [total_logs / time_range_hours]
                * 10,  # Logs per hour
            }

            return LogAnalytics(
                time_range=f"Last {time_range_hours} hour(s)",
                total_logs=total_logs,
                logs_by_service=dict(logs_by_service),
                logs_by_level=dict(logs_by_level),
                error_rate=error_rate,
                avg_response_time=avg_response_time,
                top_errors=top_errors,
                service_health=service_health,
                performance_trends=performance_trends,
            )

        except Exception as e:
            print(f"Error analyzing logs: {e}")
            return LogAnalytics(
                time_range=f"Last {time_range_hours} hour(s)",
                total_logs=0,
                logs_by_service={},
                logs_by_level={},
                error_rate=0,
                avg_response_time=0,
                top_errors=[],
                service_health={},
                performance_trends={},
            )

    async def _get_all_log_streams(self) -> List[str]:
        """Get all log stream keys"""
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.redis_client.keys("logs:*")
            )
        except Exception:
            return []

    async def _get_stream_entries(
        self, stream_key: str, cutoff_time: datetime
    ) -> List:
        """Get entries from a Redis stream"""
        try:
            cutoff_timestamp = int(cutoff_time.timestamp() * 1000)

            entries = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.xrange(
                    stream_key, min=cutoff_timestamp
                ),
            )

            return entries

        except Exception as e:
            print(f"Error getting stream entries from {stream_key}: {e}")
            return []

    async def _get_recent_batches(self, minutes: int) -> List[Dict]:
        """Get recent log batches"""
        try:
            batch_data = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.redis_client.lrange("log_batches", 0, -1)
            )

            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            recent_batches = []

            for batch_json in batch_data:
                try:
                    batch = json.loads(batch_json)
                    batch_time = datetime.fromisoformat(batch["timestamp"])

                    if batch_time >= cutoff_time:
                        recent_batches.append(batch)

                except Exception:
                    continue

            return recent_batches

        except Exception:
            return []

    def print_dashboard(
        self, analytics: LogAnalytics, real_time_metrics: RealTimeMetrics
    ):
        """Print formatted dashboard"""
        print("\n" + "=" * 80)
        print("📊 CENTRALIZED LOGGING DASHBOARD")
        print("=" * 80)

        # Real-time metrics
        print(
            f"\n🔴 REAL-TIME METRICS ({real_time_metrics.timestamp.strftime('%H:%M:%S')})"
        )
        print(f"  • Logs/Second: {real_time_metrics.logs_per_second:.1f}")
        print(f"  • Error Rate: {real_time_metrics.error_rate:.1f}%")
        print(
            f"  • Avg Response Time: {real_time_metrics.avg_response_time:.1f}ms"
        )
        print(f"  • Active Services: {real_time_metrics.active_services}")
        print(f"  • Critical Alerts: {real_time_metrics.critical_alerts}")

        # Overview
        print(f"\n📈 OVERVIEW ({analytics.time_range})")
        print(f"  • Total Logs: {analytics.total_logs:,}")
        print(f"  • Error Rate: {analytics.error_rate:.2f}%")
        print(f"  • Avg Response Time: {analytics.avg_response_time:.1f}ms")

        # Services
        print(f"\n🚀 SERVICES ({len(analytics.logs_by_service)} active)")
        for service, count in sorted(
            analytics.logs_by_service.items(), key=lambda x: x[1], reverse=True
        ):
            health = analytics.service_health.get(service, 0)
            health_icon = (
                "🟢" if health > 90 else "🟡" if health > 70 else "🔴"
            )
            print(
                f"  {health_icon} {service}: {count:,} logs (Health: {health:.1f}%)"
            )

        # Log levels
        print("\n📊 LOG LEVELS")
        level_icons = {
            "debug": "🔵",
            "info": "🟢",
            "warning": "🟡",
            "error": "🔴",
            "critical": "🚨",
        }

        for level, count in sorted(
            analytics.logs_by_level.items(), key=lambda x: x[1], reverse=True
        ):
            icon = level_icons.get(level, "⚪")
            percentage = (
                (count / analytics.total_logs * 100)
                if analytics.total_logs > 0
                else 0
            )
            print(f"  {icon} {level.upper()}: {count:,} ({percentage:.1f}%)")

        # Top errors
        if analytics.top_errors:
            print("\n🚨 TOP ERRORS")
            for i, error in enumerate(analytics.top_errors[:5], 1):
                print(
                    f"  {i}. {error['error']} ({error['count']} occurrences)"
                )

        # Performance trends
        if analytics.performance_trends.get("response_time"):
            response_times = analytics.performance_trends["response_time"]
            if len(response_times) >= 2:
                trend = (
                    "📈" if response_times[-1] > response_times[-2] else "📉"
                )
                print("\n⚡ PERFORMANCE TRENDS")
                print(
                    f"  {trend} Response Time Trend: {response_times[-1]:.1f}ms"
                )
                print(
                    f"  📊 Min/Max Response Time: {min(response_times):.1f}ms / {max(response_times):.1f}ms"
                )

        print("\n" + "=" * 80)

    async def start_real_time_dashboard(self, refresh_interval: int = 10):
        """Start real-time dashboard"""
        print("🚀 Starting Real-Time Log Analytics Dashboard")
        print(f"📱 Refresh interval: {refresh_interval} seconds")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                # Clear screen (works on most terminals)
                print("\033[2J\033[H", end="")

                # Get metrics and analytics
                real_time_metrics = await self.get_real_time_metrics()
                analytics = await self.analyze_logs(time_range_hours=1)

                # Display dashboard
                self.print_dashboard(analytics, real_time_metrics)

                # Store metrics for trending
                self.metrics_history.append(real_time_metrics)

                # Keep only last 100 metrics
                if len(self.metrics_history) > 100:
                    self.metrics_history = self.metrics_history[-100:]

                # Wait for next refresh
                await asyncio.sleep(refresh_interval)

        except KeyboardInterrupt:
            print("\n👋 Dashboard stopped by user")
        except Exception as e:
            print(f"\n❌ Dashboard error: {e}")

    async def generate_report(self, time_range_hours: int = 24) -> Dict:
        """Generate comprehensive log report"""
        print(
            f"📋 Generating log report for the last {time_range_hours} hours..."
        )

        analytics = await self.analyze_logs(time_range_hours)

        report = {
            "report_generated": datetime.now().isoformat(),
            "time_range_hours": time_range_hours,
            "summary": {
                "total_logs": analytics.total_logs,
                "error_rate": analytics.error_rate,
                "avg_response_time": analytics.avg_response_time,
                "services_monitored": len(analytics.logs_by_service),
            },
            "service_breakdown": analytics.logs_by_service,
            "log_level_distribution": analytics.logs_by_level,
            "service_health_scores": analytics.service_health,
            "top_errors": analytics.top_errors,
            "recommendations": self._generate_recommendations(analytics),
        }

        return report

    def _generate_recommendations(self, analytics: LogAnalytics) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        # Error rate recommendations
        if analytics.error_rate > 5:
            recommendations.append(
                f"High error rate detected ({analytics.error_rate:.1f}%). "
                "Review top errors and implement fixes."
            )

        # Response time recommendations
        if analytics.avg_response_time > 1000:
            recommendations.append(
                f"High average response time ({analytics.avg_response_time:.1f}ms). "
                "Consider performance optimization."
            )

        # Service health recommendations
        unhealthy_services = [
            service
            for service, health in analytics.service_health.items()
            if health < 80
        ]

        if unhealthy_services:
            recommendations.append(
                f"Services with low health scores: {', '.join(unhealthy_services)}. "
                "Investigate and resolve issues."
            )

        # Log volume recommendations
        if analytics.total_logs < 100:
            recommendations.append(
                "Low log volume detected. Verify logging configuration and service connectivity."
            )

        if not recommendations:
            recommendations.append(
                "System is operating within normal parameters."
            )

        return recommendations


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Log Analytics Dashboard")
    parser.add_argument(
        "--mode",
        choices=["dashboard", "report", "analyze"],
        default="dashboard",
        help="Operation mode",
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=10,
        help="Dashboard refresh interval in seconds",
    )
    parser.add_argument(
        "--hours", type=int, default=1, help="Time range in hours for analysis"
    )

    args = parser.parse_args()

    dashboard = LogAnalyticsDashboard()
    await dashboard.initialize()

    try:
        if args.mode == "dashboard":
            await dashboard.start_real_time_dashboard(args.refresh)

        elif args.mode == "report":
            report = await dashboard.generate_report(args.hours)
            print(json.dumps(report, indent=2, default=str))

        elif args.mode == "analyze":
            analytics = await dashboard.analyze_logs(args.hours)
            real_time_metrics = await dashboard.get_real_time_metrics()
            dashboard.print_dashboard(analytics, real_time_metrics)

    except KeyboardInterrupt:
        print("\n👋 Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
