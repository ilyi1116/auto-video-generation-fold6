"""
追蹤資料分析器
提供追蹤資料的分析、聚合和洞察功能
"""

import logging
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .collector import trace_collector

logger = logging.getLogger(__name__)


class TraceAnalyzer:
    """追蹤資料分析器"""

    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5分鐘快取

    async def analyze_performance(
        self,
        service_name: Optional[str] = None,
        operation_category: Optional[str] = None,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """分析性能指標"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            # 獲取追蹤資料
            traces = await trace_collector.get_traces(
                service_name=service_name,
                operation_category=operation_category,
                start_time=start_time,
                end_time=end_time,
                limit=10000,
            )

            if not traces:
                return {"error": "沒有找到追蹤資料"}

            # 計算性能指標
            durations = []
            error_count = 0
            total_count = len(traces)

            for trace in traces:
                if trace.get("duration_ms"):
                    durations.append(trace["duration_ms"])

                if trace.get("status") == "error" or trace.get("error"):
                    error_count += 1

            if not durations:
                return {"error": "沒有有效的持續時間資料"}

            # 計算統計指標
            analysis = {
                "total_requests": total_count,
                "error_rate": round((error_count / total_count) * 100, 2),
                "performance_metrics": {
                    "avg_duration_ms": round(statistics.mean(durations), 2),
                    "median_duration_ms": round(statistics.median(durations), 2),
                    "p95_duration_ms": round(self._percentile(durations, 95), 2),
                    "p99_duration_ms": round(self._percentile(durations, 99), 2),
                    "min_duration_ms": round(min(durations), 2),
                    "max_duration_ms": round(max(durations), 2),
                },
                "throughput": {
                    "requests_per_hour": round(total_count / hours, 2),
                    "requests_per_minute": round(total_count / (hours * 60), 2),
                },
                "analysis_period": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_hours": hours,
                },
            }

            return analysis

        except Exception as e:
            logger.error(f"性能分析失敗: {e}")
            return {"error": str(e)}

    async def analyze_errors(self, hours: int = 24) -> Dict[str, Any]:
        """分析錯誤模式"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            # 獲取追蹤資料
            traces = await trace_collector.get_traces(
                start_time=start_time, end_time=end_time, limit=10000
            )

            # 篩選錯誤追蹤
            error_traces = [
                trace for trace in traces if trace.get("status") == "error" or trace.get("error")
            ]

            if not error_traces:
                return {"message": "沒有發現錯誤"}

            # 分析錯誤模式
            error_types = Counter()
            error_services = Counter()
            error_operations = Counter()
            error_timeline = defaultdict(int)

            for trace in error_traces:
                # 錯誤類型
                error_type = trace.get("error_type", "unknown")
                error_types[error_type] += 1

                # 錯誤服務
                service = trace.get("service_name", "unknown")
                error_services[service] += 1

                # 錯誤操作
                operation = trace.get("operation_category", "unknown")
                error_operations[operation] += 1

                # 錯誤時間線 (按小時分組)
                collected_at = trace.get("collected_at", "")
                if collected_at:
                    try:
                        dt = datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
                        hour_key = dt.strftime("%Y-%m-%d %H:00")
                        error_timeline[hour_key] += 1
                    except Exception:
                        pass

            analysis = {
                "total_errors": len(error_traces),
                "error_types": dict(error_types.most_common(10)),
                "error_services": dict(error_services.most_common(10)),
                "error_operations": dict(error_operations.most_common(10)),
                "error_timeline": dict(sorted(error_timeline.items())),
                "top_errors": self._get_top_error_details(error_traces),
            }

            return analysis

        except Exception as e:
            logger.error(f"錯誤分析失敗: {e}")
            return {"error": str(e)}

    async def analyze_services(self, hours: int = 24) -> Dict[str, Any]:
        """分析服務間的互動和依賴"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            traces = await trace_collector.get_traces(
                start_time=start_time, end_time=end_time, limit=10000
            )

            # 服務統計
            service_stats = defaultdict(
                lambda: {
                    "request_count": 0,
                    "error_count": 0,
                    "total_duration": 0,
                    "operations": set(),
                }
            )

            # 服務依賴圖
            service_dependencies = defaultdict(set)

            for trace in traces:
                service = trace.get("service_name", "unknown")
                stats = service_stats[service]

                stats["request_count"] += 1

                if trace.get("status") == "error":
                    stats["error_count"] += 1

                if trace.get("duration_ms"):
                    stats["total_duration"] += trace["duration_ms"]

                operation = trace.get("operation_name", "")
                if operation:
                    stats["operations"].add(operation)

                # 分析服務依賴 (基於 parent_span_id)
                parent_span_id = trace.get("parent_span_id")
                if parent_span_id:
                    # 查找父級服務
                    parent_trace = await trace_collector.get_trace_by_id(parent_span_id)
                    if parent_trace:
                        parent_service = parent_trace.get("service_name")
                        if parent_service and parent_service != service:
                            service_dependencies[parent_service].add(service)

            # 計算服務指標
            services_analysis = {}
            for service, stats in service_stats.items():
                avg_duration = (
                    stats["total_duration"] / stats["request_count"]
                    if stats["request_count"] > 0
                    else 0
                )
                error_rate = (
                    stats["error_count"] / stats["request_count"] * 100
                    if stats["request_count"] > 0
                    else 0
                )

                services_analysis[service] = {
                    "request_count": stats["request_count"],
                    "error_count": stats["error_count"],
                    "error_rate": round(error_rate, 2),
                    "avg_duration_ms": round(avg_duration, 2),
                    "operation_count": len(stats["operations"]),
                    "dependencies": list(service_dependencies.get(service, [])),
                }

            return {
                "services": services_analysis,
                "dependency_graph": {
                    service: list(deps) for service, deps in service_dependencies.items()
                },
                "total_services": len(service_stats),
                "analysis_period": f"{hours} hours",
            }

        except Exception as e:
            logger.error(f"服務分析失敗: {e}")
            return {"error": str(e)}

    async def analyze_trends(self, hours: int = 24, interval_minutes: int = 60) -> Dict[str, Any]:
        """分析趨勢資料"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            traces = await trace_collector.get_traces(
                start_time=start_time, end_time=end_time, limit=10000
            )

            # 時間序列分析
            timeline = defaultdict(
                lambda: {
                    "request_count": 0,
                    "error_count": 0,
                    "total_duration": 0,
                    "services": set(),
                }
            )

            for trace in traces:
                collected_at = trace.get("collected_at", "")
                if not collected_at:
                    continue

                try:
                    dt = datetime.fromisoformat(collected_at.replace("Z", "+00:00"))
                    # 按間隔分組
                    interval_key = self._round_to_interval(dt, interval_minutes)
                    stats = timeline[interval_key]

                    stats["request_count"] += 1

                    if trace.get("status") == "error":
                        stats["error_count"] += 1

                    if trace.get("duration_ms"):
                        stats["total_duration"] += trace["duration_ms"]

                    service = trace.get("service_name")
                    if service:
                        stats["services"].add(service)

                except Exception:
                    continue

            # 轉換為時間序列
            time_series = []
            for time_key in sorted(timeline.keys()):
                stats = timeline[time_key]
                avg_duration = (
                    stats["total_duration"] / stats["request_count"]
                    if stats["request_count"] > 0
                    else 0
                )
                error_rate = (
                    stats["error_count"] / stats["request_count"] * 100
                    if stats["request_count"] > 0
                    else 0
                )

                time_series.append(
                    {
                        "timestamp": time_key,
                        "request_count": stats["request_count"],
                        "error_count": stats["error_count"],
                        "error_rate": round(error_rate, 2),
                        "avg_duration_ms": round(avg_duration, 2),
                        "active_services": len(stats["services"]),
                    }
                )

            return {
                "time_series": time_series,
                "interval_minutes": interval_minutes,
                "analysis_period": f"{hours} hours",
                "data_points": len(time_series),
            }

        except Exception as e:
            logger.error(f"趨勢分析失敗: {e}")
            return {"error": str(e)}

    async def get_slow_operations(self, limit: int = 10, hours: int = 24) -> List[Dict[str, Any]]:
        """獲取最慢的操作"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            traces = await trace_collector.get_traces(
                start_time=start_time, end_time=end_time, limit=10000
            )

            # 按操作分組統計
            operation_stats = defaultdict(
                lambda: {
                    "durations": [],
                    "service_name": "",
                    "operation_name": "",
                    "error_count": 0,
                    "total_count": 0,
                }
            )

            for trace in traces:
                operation_name = trace.get("operation_name", "unknown")
                service_name = trace.get("service_name", "unknown")
                key = f"{service_name}::{operation_name}"

                stats = operation_stats[key]
                stats["service_name"] = service_name
                stats["operation_name"] = operation_name
                stats["total_count"] += 1

                if trace.get("status") == "error":
                    stats["error_count"] += 1

                if trace.get("duration_ms"):
                    stats["durations"].append(trace["duration_ms"])

            # 計算平均時間並排序
            slow_operations = []
            for key, stats in operation_stats.items():
                if stats["durations"]:
                    avg_duration = statistics.mean(stats["durations"])
                    p95_duration = self._percentile(stats["durations"], 95)
                    error_rate = stats["error_count"] / stats["total_count"] * 100

                    slow_operations.append(
                        {
                            "service_name": stats["service_name"],
                            "operation_name": stats["operation_name"],
                            "avg_duration_ms": round(avg_duration, 2),
                            "p95_duration_ms": round(p95_duration, 2),
                            "total_requests": stats["total_count"],
                            "error_rate": round(error_rate, 2),
                        }
                    )

            # 按平均持續時間排序
            slow_operations.sort(key=lambda x: x["avg_duration_ms"], reverse=True)

            return slow_operations[:limit]

        except Exception as e:
            logger.error(f"慢操作分析失敗: {e}")
            return []

    async def get_health_score(
        self, service_name: Optional[str] = None, hours: int = 1
    ) -> Dict[str, Any]:
        """計算服務健康評分"""
        try:
            performance = await self.analyze_performance(service_name=service_name, hours=hours)

            if "error" in performance:
                return {"health_score": 0, "status": "unknown", "details": performance}

            # 計算健康評分 (0-100)
            error_rate = performance.get("error_rate", 0)
            avg_duration = performance["performance_metrics"]["avg_duration_ms"]

            # 錯誤率評分 (錯誤率越低分數越高)
            error_score = max(0, 100 - (error_rate * 10))

            # 性能評分 (響應時間越快分數越高)
            # 假設 100ms 以下為滿分，1000ms 以上為0分
            performance_score = max(0, 100 - (avg_duration / 10))

            # 綜合評分
            health_score = round((error_score * 0.6 + performance_score * 0.4), 1)

            # 確定狀態
            if health_score >= 80:
                status = "healthy"
            elif health_score >= 60:
                status = "warning"
            else:
                status = "critical"

            return {
                "health_score": health_score,
                "status": status,
                "details": {
                    "error_score": round(error_score, 1),
                    "performance_score": round(performance_score, 1),
                    "error_rate": error_rate,
                    "avg_duration_ms": avg_duration,
                    "total_requests": performance["total_requests"],
                },
            }

        except Exception as e:
            logger.error(f"健康評分計算失敗: {e}")
            return {"health_score": 0, "status": "error", "error": str(e)}

    def _percentile(self, data: List[float], percentile: int) -> float:
        """計算百分位數"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index == int(index):
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))

    def _get_top_error_details(self, error_traces: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """獲取主要錯誤詳情"""
        error_messages = Counter()

        for trace in error_traces:
            error_msg = trace.get("error", "")
            if isinstance(error_msg, dict):
                error_msg = error_msg.get("message", str(error_msg))

            if error_msg:
                error_messages[str(error_msg)[:200]] += 1  # 限制長度

        top_errors = []
        for error_msg, count in error_messages.most_common(5):
            top_errors.append({"error_message": error_msg, "occurrence_count": count})

        return top_errors

    def _round_to_interval(self, dt: datetime, interval_minutes: int) -> str:
        """將時間四捨五入到指定間隔"""
        minutes = (dt.minute // interval_minutes) * interval_minutes
        rounded_dt = dt.replace(minute=minutes, second=0, microsecond=0)
        return rounded_dt.isoformat()


# 全域分析器實例
trace_analyzer = TraceAnalyzer()
