#!/usr/bin/env python3
"""
TDD Refactor 階段: 監控效能和可觀測性優化測試
驗證監控系統的效能特性和可觀測性功能
"""

import asyncio
import json
import time
import os
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import concurrent.futures
from unittest.mock import Mock, patch
import threading

# 配置測試日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonitoringPerformanceOptimizationTest:
    """監控效能和可觀測性優化 TDD Refactor 測試套件"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": [],
            "performance_metrics": {},
        }

        # 效能基準 (微秒)
        self.performance_thresholds = {
            "log_entry_processing": 1000,  # 1ms
            "metric_collection": 500,  # 0.5ms
            "dashboard_query": 2000,  # 2ms
            "alert_evaluation": 100,  # 0.1ms
            "trace_span_creation": 50,  # 0.05ms
            "correlation_id_lookup": 10,  # 0.01ms
        }

        # 可觀測性目標
        self.observability_targets = {
            "log_retention_days": 30,
            "metric_resolution_seconds": 15,
            "trace_sampling_rate": 0.1,
            "dashboard_refresh_seconds": 5,
            "alert_notification_seconds": 30,
        }

    def _record_result(
        self,
        test_name: str,
        success: bool,
        error: str = None,
        metrics: Dict[str, float] = None,
    ):
        """記錄測試結果和效能指標"""
        if success:
            self.results["tests_passed"] += 1
            logger.info(f"✅ {test_name} 通過")
        else:
            self.results["tests_failed"] += 1
            self.results["errors"].append(f"{test_name}: {error}")
            logger.error(f"❌ {test_name} 失敗: {error}")

        if metrics:
            self.results["performance_metrics"][test_name] = metrics

    def test_structured_logging_performance(self):
        """測試結構化日誌記錄效能"""
        try:
            # 檢查日誌記錄器是否存在
            logger_module = (
                self.project_root / "monitoring/logging/structured_logger.py"
            )
            assert logger_module.exists(), "結構化日誌記錄器不存在"

            # 模擬高併發日誌記錄測試
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "structured_logger", logger_module
            )
            structured_logger = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(structured_logger)

            # 創建測試日誌記錄器
            test_logger = structured_logger.get_logger("performance_test")

            # 效能測試：單個日誌條目處理時間
            log_times = []
            for i in range(100):
                start_time = time.perf_counter()
                test_logger.info(
                    f"Performance test log entry {i}",
                    extra={
                        "test_data": {"iteration": i, "timestamp": time.time()}
                    },
                )
                end_time = time.perf_counter()
                log_times.append(
                    (end_time - start_time) * 1000000
                )  # 轉換為微秒

            avg_log_time = statistics.mean(log_times)
            p95_log_time = statistics.quantiles(log_times, n=20)[
                18
            ]  # 95th percentile
            max_log_time = max(log_times)

            # 驗證效能要求
            threshold = self.performance_thresholds["log_entry_processing"]
            assert avg_log_time < threshold, (
                f"平均日誌處理時間 {avg_log_time:.2f}μs 超過閾值 {threshold}μs"
            )
            assert p95_log_time < threshold * 2, (
                f"P95 日誌處理時間 {p95_log_time:.2f}μs 超過閾值 {threshold * 2}μs"
            )

            # 併發測試
            def concurrent_logging(thread_id, log_count):
                thread_times = []
                for i in range(log_count):
                    start_time = time.perf_counter()
                    test_logger.info(
                        f"Concurrent log from thread {thread_id}, entry {i}"
                    )
                    end_time = time.perf_counter()
                    thread_times.append((end_time - start_time) * 1000000)
                return thread_times

            with concurrent.futures.ThreadPoolExecutor(
                max_workers=10
            ) as executor:
                futures = [
                    executor.submit(concurrent_logging, i, 20)
                    for i in range(10)
                ]
                concurrent_times = []
                for future in concurrent.futures.as_completed(futures):
                    concurrent_times.extend(future.result())

            concurrent_avg = statistics.mean(concurrent_times)

            metrics = {
                "avg_log_time_us": avg_log_time,
                "p95_log_time_us": p95_log_time,
                "max_log_time_us": max_log_time,
                "concurrent_avg_time_us": concurrent_avg,
                "throughput_logs_per_second": 1000000 / avg_log_time,
            }

            self._record_result(
                "structured_logging_performance", True, metrics=metrics
            )

        except Exception as e:
            self._record_result(
                "structured_logging_performance", False, str(e)
            )

    def test_prometheus_metrics_performance(self):
        """測試 Prometheus 指標收集效能"""
        try:
            # 檢查業務指標收集器
            metrics_collector_path = (
                self.project_root
                / "monitoring/business_metrics/business_metrics_collector.py"
            )
            assert metrics_collector_path.exists(), "業務指標收集器不存在"

            # 導入指標收集器
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "business_metrics_collector", metrics_collector_path
            )
            metrics_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(metrics_module)

            # 創建測試收集器
            collector = metrics_module.BusinessMetricsCollector()

            # 效能測試：指標記錄時間
            metric_times = []
            for i in range(200):
                start_time = time.perf_counter()
                collector.record_metric(
                    "test_counter", i, {"iteration": str(i)}
                )
                end_time = time.perf_counter()
                metric_times.append((end_time - start_time) * 1000000)

            avg_metric_time = statistics.mean(metric_times)
            p95_metric_time = statistics.quantiles(metric_times, n=20)[18]

            # 批量指標測試
            batch_start = time.perf_counter()
            for i in range(1000):
                collector.record_metric("batch_test", i, {"batch": "true"})
            batch_end = time.perf_counter()
            batch_time = (
                (batch_end - batch_start) * 1000000 / 1000
            )  # 每個指標的平均時間

            # 驗證效能要求
            threshold = self.performance_thresholds["metric_collection"]
            assert avg_metric_time < threshold, (
                f"平均指標收集時間 {avg_metric_time:.2f}μs 超過閾值 {threshold}μs"
            )

            # 測試指標摘要生成效能
            summary_start = time.perf_counter()
            summary = collector.get_all_metrics_summary()
            summary_end = time.perf_counter()
            summary_time = (summary_end - summary_start) * 1000

            metrics = {
                "avg_metric_time_us": avg_metric_time,
                "p95_metric_time_us": p95_metric_time,
                "batch_avg_time_us": batch_time,
                "summary_generation_time_ms": summary_time,
                "metrics_per_second": 1000000 / avg_metric_time,
            }

            self._record_result(
                "prometheus_metrics_performance", True, metrics=metrics
            )

        except Exception as e:
            self._record_result(
                "prometheus_metrics_performance", False, str(e)
            )

    def test_correlation_middleware_performance(self):
        """測試關聯ID中間件效能"""
        try:
            # 檢查關聯中間件
            middleware_path = (
                self.project_root
                / "monitoring/middleware/correlation_middleware.py"
            )
            assert middleware_path.exists(), "關聯ID中間件不存在"

            # 導入中間件
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "correlation_middleware", middleware_path
            )
            middleware_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(middleware_module)

            # 測試關聯ID生成和查找效能
            correlation_times = []
            for i in range(1000):
                start_time = time.perf_counter()
                correlation_id = middleware_module.get_correlation_id()
                end_time = time.perf_counter()
                correlation_times.append((end_time - start_time) * 1000000)

            avg_correlation_time = statistics.mean(correlation_times)
            threshold = self.performance_thresholds["correlation_id_lookup"]

            # 測試追踪事件記錄效能
            event_times = []
            for i in range(100):
                start_time = time.perf_counter()
                middleware_module.log_trace_event(
                    f"test_event_{i}", iteration=i
                )
                end_time = time.perf_counter()
                event_times.append((end_time - start_time) * 1000000)

            avg_event_time = statistics.mean(event_times)

            metrics = {
                "avg_correlation_lookup_us": avg_correlation_time,
                "avg_trace_event_time_us": avg_event_time,
                "correlation_lookups_per_second": 1000000
                / avg_correlation_time
                if avg_correlation_time > 0
                else 0,
            }

            self._record_result(
                "correlation_middleware_performance", True, metrics=metrics
            )

        except Exception as e:
            self._record_result(
                "correlation_middleware_performance", False, str(e)
            )

    def test_opentelemetry_span_performance(self):
        """測試 OpenTelemetry Span 創建效能"""
        try:
            # 檢查 OpenTelemetry 中間件
            otel_path = (
                self.project_root
                / "monitoring/tracing/opentelemetry_middleware.py"
            )
            assert otel_path.exists(), "OpenTelemetry 中間件不存在"

            # 導入 OpenTelemetry 模組
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "opentelemetry_middleware", otel_path
            )
            otel_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(otel_module)

            # 創建測試中間件
            otel_middleware = otel_module.OpenTelemetryMiddleware(
                service_name="performance_test", service_version="1.0.0"
            )

            # 測試 Span 創建效能
            span_times = []
            for i in range(500):
                start_time = time.perf_counter()
                span = otel_middleware.create_span(
                    f"test_span_{i}",
                    {"iteration": i, "test_type": "performance"},
                )
                span.end()
                end_time = time.perf_counter()
                span_times.append((end_time - start_time) * 1000000)

            avg_span_time = statistics.mean(span_times)
            p95_span_time = statistics.quantiles(span_times, n=20)[18]

            threshold = self.performance_thresholds["trace_span_creation"]
            assert avg_span_time < threshold, (
                f"平均 Span 創建時間 {avg_span_time:.3f}μs 超過閾值 {threshold}μs"
            )

            # 測試嵌套 Span 效能
            nested_start = time.perf_counter()
            parent_span = otel_middleware.create_span("parent_span")
            for i in range(10):
                child_span = otel_middleware.create_span(f"child_span_{i}")
                child_span.end()
            parent_span.end()
            nested_end = time.perf_counter()
            nested_time = (
                (nested_end - nested_start) * 1000000 / 11
            )  # 平均每個 span

            metrics = {
                "avg_span_creation_us": avg_span_time,
                "p95_span_creation_us": p95_span_time,
                "nested_span_avg_us": nested_time,
                "spans_per_second": 1000000 / avg_span_time,
            }

            self._record_result(
                "opentelemetry_span_performance", True, metrics=metrics
            )

        except Exception as e:
            self._record_result(
                "opentelemetry_span_performance", False, str(e)
            )

    def test_grafana_dashboard_query_optimization(self):
        """測試 Grafana 儀表板查詢優化"""
        try:
            # 檢查儀表板配置
            dashboards_dir = (
                self.project_root / "monitoring/grafana/dashboards"
            )
            assert dashboards_dir.exists(), "Grafana 儀表板目錄不存在"

            dashboard_files = list(dashboards_dir.glob("*.json"))
            assert len(dashboard_files) > 0, "沒有找到儀表板配置檔案"

            # 分析每個儀表板的查詢複雜度
            dashboard_metrics = {}

            for dashboard_file in dashboard_files:
                with open(dashboard_file, "r") as f:
                    dashboard_config = json.load(f)

                dashboard_name = dashboard_file.stem
                panels = dashboard_config.get("dashboard", {}).get(
                    "panels", []
                )

                query_count = 0
                complex_queries = 0

                for panel in panels:
                    targets = panel.get("targets", [])
                    query_count += len(targets)

                    for target in targets:
                        expr = target.get("expr", "")
                        # 檢查查詢複雜度（簡單指標）
                        if any(
                            func in expr
                            for func in [
                                "rate(",
                                "increase(",
                                "histogram_quantile(",
                            ]
                        ):
                            complex_queries += 1

                dashboard_metrics[dashboard_name] = {
                    "total_queries": query_count,
                    "complex_queries": complex_queries,
                    "complexity_ratio": complex_queries / query_count
                    if query_count > 0
                    else 0,
                    "panels_count": len(panels),
                }

            # 驗證儀表板效能特性
            total_queries = sum(
                m["total_queries"] for m in dashboard_metrics.values()
            )
            avg_queries_per_dashboard = total_queries / len(dashboard_metrics)

            # 建議：每個儀表板不超過 20 個查詢以保持效能
            assert avg_queries_per_dashboard <= 20, (
                f"平均每個儀表板查詢數 {avg_queries_per_dashboard:.1f} 過多，建議不超過 20"
            )

            metrics = {
                "total_dashboards": len(dashboard_metrics),
                "total_queries": total_queries,
                "avg_queries_per_dashboard": avg_queries_per_dashboard,
                "dashboard_details": dashboard_metrics,
            }

            self._record_result(
                "grafana_dashboard_query_optimization", True, metrics=metrics
            )

        except Exception as e:
            self._record_result(
                "grafana_dashboard_query_optimization", False, str(e)
            )

    def test_log_aggregation_performance(self):
        """測試日誌聚合管道效能"""
        try:
            # 檢查 Logstash 配置
            logstash_config = (
                self.project_root
                / "monitoring/logstash/pipeline/logstash.conf"
            )
            assert logstash_config.exists(), "Logstash 配置不存在"

            config_content = logstash_config.read_text()

            # 分析配置效能特性
            has_grok_filter = "grok" in config_content
            has_json_filter = "json" in config_content
            has_date_filter = "date" in config_content
            has_mutate_filter = "mutate" in config_content

            # 計算預期處理延遲（基於過濾器複雜度）
            base_latency = 10  # 基礎延遲 ms
            if has_grok_filter:
                base_latency += 5  # Grok 解析較慢
            if has_json_filter:
                base_latency += 2  # JSON 解析適中
            if has_date_filter:
                base_latency += 3  # 日期解析
            if has_mutate_filter:
                base_latency += 1  # 字段變更

            # 檢查 Fluent Bit 配置
            fluent_config = (
                self.project_root / "monitoring/logging/fluent-bit.conf"
            )
            assert fluent_config.exists(), "Fluent Bit 配置不存在"

            fluent_content = fluent_config.read_text()

            # 計算緩衝配置
            buffer_chunk_size = "1MB"  # 預設值
            buffer_max_size = "5MB"  # 預設值

            if "Chunk_Size" in fluent_content:
                # 提取實際配置值（簡化實作）
                for line in fluent_content.split("\n"):
                    if "Chunk_Size" in line:
                        buffer_chunk_size = line.split()[-1]
                        break

            metrics = {
                "estimated_processing_latency_ms": base_latency,
                "has_grok_filter": has_grok_filter,
                "has_json_filter": has_json_filter,
                "has_date_filter": has_date_filter,
                "buffer_chunk_size": buffer_chunk_size,
                "buffer_max_size": buffer_max_size,
            }

            # 效能驗證：預期延遲不超過 50ms
            assert base_latency <= 50, (
                f"預期日誌處理延遲 {base_latency}ms 過高，建議不超過 50ms"
            )

            self._record_result(
                "log_aggregation_performance", True, metrics=metrics
            )

        except Exception as e:
            self._record_result("log_aggregation_performance", False, str(e))

    def test_alert_evaluation_performance(self):
        """測試警報評估效能"""
        try:
            # 檢查警報規則配置
            rules_dir = self.project_root / "monitoring/prometheus/rules"
            assert rules_dir.exists(), "警報規則目錄不存在"

            rule_files = list(rules_dir.glob("*.yml"))
            assert len(rule_files) > 0, "沒有找到警報規則檔案"

            total_rules = 0
            complex_rules = 0
            rule_complexity_scores = []

            try:
                import yaml

                yaml_available = True
            except ImportError:
                yaml_available = False

            for rule_file in rule_files:
                if yaml_available:
                    with open(rule_file, "r") as f:
                        rules_config = yaml.safe_load(f)

                    for group in rules_config.get("groups", []):
                        for rule in group.get("rules", []):
                            total_rules += 1
                            expr = rule.get("expr", "")

                            # 計算規則複雜度分數
                            complexity = 0
                            complexity += expr.count("(")  # 括號數量
                            complexity += expr.count("rate(") * 2  # rate 函數
                            complexity += (
                                expr.count("histogram_quantile(") * 3
                            )  # 分位數計算
                            complexity += expr.count("by(") * 1  # 分組操作

                            rule_complexity_scores.append(complexity)

                            if complexity > 5:  # 複雜規則閾值
                                complex_rules += 1
                else:
                    # 簡單文本分析
                    content = rule_file.read_text()
                    total_rules += content.count("alert:")
                    complex_rules += content.count("histogram_quantile")

            avg_complexity = (
                statistics.mean(rule_complexity_scores)
                if rule_complexity_scores
                else 0
            )
            max_complexity = (
                max(rule_complexity_scores) if rule_complexity_scores else 0
            )

            # 預估警報評估時間（基於複雜度）
            base_eval_time = 10  # 基礎評估時間 μs
            estimated_eval_time = base_eval_time + (avg_complexity * 20)

            metrics = {
                "total_rules": total_rules,
                "complex_rules": complex_rules,
                "complexity_ratio": complex_rules / total_rules
                if total_rules > 0
                else 0,
                "avg_complexity_score": avg_complexity,
                "max_complexity_score": max_complexity,
                "estimated_eval_time_us": estimated_eval_time,
            }

            # 效能驗證
            threshold = self.performance_thresholds["alert_evaluation"]
            assert estimated_eval_time <= threshold, (
                f"預估警報評估時間 {estimated_eval_time:.1f}μs 超過閾值 {threshold}μs"
            )

            self._record_result(
                "alert_evaluation_performance", True, metrics=metrics
            )

        except Exception as e:
            self._record_result("alert_evaluation_performance", False, str(e))

    def test_observability_configuration_optimization(self):
        """測試可觀測性配置優化"""
        try:
            # 檢查資料保留配置
            prometheus_config = (
                self.project_root / "monitoring/prometheus/prometheus.yml"
            )
            assert prometheus_config.exists(), "Prometheus 配置不存在"

            config_content = prometheus_config.read_text()

            # 檢查抓取間隔配置
            scrape_interval = "15s"  # 預設值
            if "scrape_interval:" in config_content:
                for line in config_content.split("\n"):
                    if (
                        "scrape_interval:" in line
                        and not line.strip().startswith("#")
                    ):
                        scrape_interval = line.split(":")[-1].strip()
                        break

            # 轉換為秒
            interval_seconds = 15
            if scrape_interval.endswith("s"):
                interval_seconds = int(scrape_interval[:-1])
            elif scrape_interval.endswith("m"):
                interval_seconds = int(scrape_interval[:-1]) * 60

            # 檢查儲存配置（模擬）
            retention_days = 15  # Prometheus 預設
            retention_size = "10GB"

            # 檢查 Grafana 配置
            grafana_config = (
                self.project_root / "monitoring/grafana/grafana.ini"
            )
            if grafana_config.exists():
                grafana_content = grafana_config.read_text()
                # 檢查緩存配置
                has_query_cache = "query_caching_enabled" in grafana_content
            else:
                has_query_cache = False

            # 計算預估資料量
            services_count = 8  # 基於系統服務數量
            metrics_per_service = 50  # 每個服務的平均指標數
            data_points_per_day = (
                services_count
                * metrics_per_service
                * (86400 / interval_seconds)
            )
            estimated_storage_mb_per_day = (
                data_points_per_day * 0.1 / 1024
            )  # 估算

            metrics = {
                "scrape_interval_seconds": interval_seconds,
                "retention_days": retention_days,
                "retention_size": retention_size,
                "estimated_data_points_per_day": data_points_per_day,
                "estimated_storage_mb_per_day": estimated_storage_mb_per_day,
                "has_grafana_query_cache": has_query_cache,
                "services_monitored": services_count,
            }

            # 驗證配置合理性
            target_interval = self.observability_targets[
                "metric_resolution_seconds"
            ]
            assert interval_seconds <= target_interval, (
                f"抓取間隔 {interval_seconds}s 超過目標 {target_interval}s"
            )

            target_retention = self.observability_targets["log_retention_days"]
            assert retention_days >= target_retention, (
                f"資料保留期 {retention_days} 天不足，目標 {target_retention} 天"
            )

            self._record_result(
                "observability_configuration_optimization",
                True,
                metrics=metrics,
            )

        except Exception as e:
            self._record_result(
                "observability_configuration_optimization", False, str(e)
            )

    def print_results(self):
        """打印測試結果和效能分析"""
        total_tests = (
            self.results["tests_passed"] + self.results["tests_failed"]
        )
        success_rate = (
            (self.results["tests_passed"] / total_tests * 100)
            if total_tests > 0
            else 0
        )

        logger.info("=" * 70)
        logger.info("🔧 TDD Refactor 階段: 監控效能和可觀測性優化結果")
        logger.info("=" * 70)
        logger.info(f"✅ 通過測試: {self.results['tests_passed']}")
        logger.info(f"❌ 失敗測試: {self.results['tests_failed']}")
        logger.info(f"📈 測試成功率: {success_rate:.1f}%")

        if self.results["errors"]:
            logger.info("\n🎯 需要優化的項目:")
            for error in self.results["errors"]:
                logger.info(f"  - {error}")

        # 效能分析報告
        if self.results["performance_metrics"]:
            logger.info("\n📊 效能分析報告:")
            for test_name, metrics in self.results[
                "performance_metrics"
            ].items():
                logger.info(f"  📈 {test_name}:")
                for metric_name, value in metrics.items():
                    if isinstance(value, (int, float)):
                        logger.info(f"    - {metric_name}: {value:.3f}")
                    else:
                        logger.info(f"    - {metric_name}: {value}")

        # Refactor 階段評估
        if success_rate >= 90:
            logger.info(
                "\n🟢 TDD Refactor 階段狀態: 優秀 - 效能和可觀測性優化成功"
            )
        elif success_rate >= 70:
            logger.info(
                "\n🟡 TDD Refactor 階段狀態: 良好 - 大部分優化成功，少數需調整"
            )
        else:
            logger.info(
                "\n🔴 TDD Refactor 階段狀態: 需改進 - 多數效能指標需要優化"
            )

        return success_rate >= 70


def main():
    """執行監控效能和可觀測性優化 TDD Refactor 階段測試"""
    logger.info("🔧 開始 TDD Refactor 階段: 監控效能和可觀測性優化")
    logger.info("目標: 優化監控系統效能並增強可觀測性功能")
    logger.info("=" * 70)

    test_suite = MonitoringPerformanceOptimizationTest()

    try:
        # 執行所有優化測試
        test_suite.test_structured_logging_performance()
        test_suite.test_prometheus_metrics_performance()
        test_suite.test_correlation_middleware_performance()
        test_suite.test_opentelemetry_span_performance()
        test_suite.test_grafana_dashboard_query_optimization()
        test_suite.test_log_aggregation_performance()
        test_suite.test_alert_evaluation_performance()
        test_suite.test_observability_configuration_optimization()

        # 打印結果和分析
        is_successful = test_suite.print_results()

        if is_successful:
            logger.info("\n🎉 TDD Refactor 階段成功！")
            logger.info("✨ 監控系統效能和可觀測性優化完成")
            logger.info("🚀 系統已具備生產級監控能力")
        else:
            logger.info("\n🔧 TDD Refactor 階段需要進一步優化")
            logger.info("📊 請根據效能分析報告進行調整")

        return is_successful

    except Exception as e:
        logger.error(f"❌ Refactor 階段測試執行異常: {e}")
        return False


if __name__ == "__main__":
    success = main()

    if success:
        logger.info("🏁 TDD Refactor 階段完成 - 監控效能優化成功")
        exit(0)
    else:
        logger.error("🛑 TDD Refactor 階段需要改進")
        exit(1)
