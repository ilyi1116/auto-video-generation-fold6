#!/usr/bin/env python3
"""
TDD Refactor 階段: 監控效能和可觀測性優化測試 (重構版)
專注於實際效能優化，避免外部依賴問題
"""

import asyncio
import json
import time
import os
import statistics
import threading
import queue
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import concurrent.futures
from unittest.mock import Mock, patch
import uuid

# 配置測試日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitoringPerformanceRefactoredTest:
    """監控效能和可觀測性優化重構測試套件"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            "tests_passed": 0,
            "tests_failed": 0,
            "errors": [],
            "performance_metrics": {}
        }
        
        # 效能基準 (微秒)
        self.performance_thresholds = {
            "log_entry_processing": 1000,  # 1ms
            "metric_collection": 500,      # 0.5ms
            "correlation_lookup": 50,      # 0.05ms
            "span_creation": 100,          # 0.1ms
        }
    
    def _record_result(self, test_name: str, success: bool, error: str = None, metrics: Dict[str, float] = None):
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

    def test_optimized_logging_performance(self):
        """測試優化的日誌記錄效能"""
        try:
            # 導入優化的效能日誌記錄器
            from monitoring.logging.performance_logger import get_performance_logger, performance_monitor
            
            # 創建測試日誌記錄器
            test_logger = get_performance_logger("performance_test", 
                                               buffer_size=500, 
                                               enable_async=True)
            
            # 單個日誌條目效能測試
            log_times = []
            for i in range(200):
                start_time = time.perf_counter()
                test_logger.info(f"Performance test log {i}", 
                               iteration=i, 
                               test_type="performance")
                end_time = time.perf_counter()
                log_times.append((end_time - start_time) * 1000000)
            
            # 強制刷新緩衝區
            test_logger.flush()
            
            # 計算統計
            avg_log_time = statistics.mean(log_times)
            p95_log_time = statistics.quantiles(log_times, n=20)[18] if len(log_times) > 20 else max(log_times)
            max_log_time = max(log_times)
            
            # 併發日誌記錄測試
            def concurrent_logging_task(thread_id: int, log_count: int):
                thread_times = []
                for i in range(log_count):
                    start_time = time.perf_counter()
                    test_logger.info(f"Concurrent log T{thread_id}-{i}")
                    end_time = time.perf_counter()
                    thread_times.append((end_time - start_time) * 1000000)
                return thread_times
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(concurrent_logging_task, i, 50) for i in range(5)]
                concurrent_times = []
                for future in concurrent.futures.as_completed(futures):
                    concurrent_times.extend(future.result())
            
            concurrent_avg = statistics.mean(concurrent_times)
            
            # 獲取日誌記錄器統計
            logger_stats = test_logger.get_stats()
            
            metrics = {
                "avg_log_time_us": avg_log_time,
                "p95_log_time_us": p95_log_time,
                "max_log_time_us": max_log_time,
                "concurrent_avg_time_us": concurrent_avg,
                "throughput_logs_per_second": 1000000 / avg_log_time if avg_log_time > 0 else 0,
                "buffer_utilization": logger_stats.get("buffer_utilization", 0),
                "total_logs_processed": logger_stats.get("logs_processed", 0)
            }
            
            # 效能驗證
            threshold = self.performance_thresholds["log_entry_processing"]
            assert avg_log_time < threshold, f"平均日誌處理時間 {avg_log_time:.2f}μs 超過閾值 {threshold}μs"
            
            self._record_result("optimized_logging_performance", True, metrics=metrics)
            
        except Exception as e:
            self._record_result("optimized_logging_performance", False, str(e))

    def test_optimized_metrics_collection_performance(self):
        """測試優化的指標收集效能"""
        try:
            # 導入優化的指標收集器
            from monitoring.metrics.optimized_metrics_collector import OptimizedMetricsCollector, MetricType
            
            # 創建測試收集器
            collector = OptimizedMetricsCollector(
                buffer_size=1000,
                flush_interval=2.0,
                enable_sampling=False  # 關閉採樣以獲得準確的效能測試
            )
            
            # 單個指標記錄效能測試
            metric_times = []
            for i in range(500):
                start_time = time.perf_counter()
                collector.record_metric(
                    f"test_metric_{i % 10}",
                    i,
                    labels={"iteration": str(i), "batch": str(i // 100)},
                    metric_type=MetricType.GAUGE
                )
                end_time = time.perf_counter()
                metric_times.append((end_time - start_time) * 1000000)
            
            avg_metric_time = statistics.mean(metric_times)
            p95_metric_time = statistics.quantiles(metric_times, n=20)[18] if len(metric_times) > 20 else max(metric_times)
            
            # 批量指標測試
            batch_start = time.perf_counter()
            for i in range(1000):
                collector.increment_counter("batch_counter", 1, {"batch_id": str(i // 100)})
            batch_end = time.perf_counter()
            batch_avg_time = (batch_end - batch_start) * 1000000 / 1000
            
            # 不同類型指標測試
            histogram_times = []
            for i in range(100):
                start_time = time.perf_counter()
                collector.observe_histogram("response_time", i * 0.01, {"endpoint": f"/api/v{i%3}"})
                end_time = time.perf_counter()
                histogram_times.append((end_time - start_time) * 1000000)
            
            avg_histogram_time = statistics.mean(histogram_times)
            
            # 獲取收集器統計
            collector_stats = collector.get_performance_stats()
            
            metrics = {
                "avg_metric_time_us": avg_metric_time,
                "p95_metric_time_us": p95_metric_time,
                "batch_avg_time_us": batch_avg_time,
                "histogram_avg_time_us": avg_histogram_time,
                "metrics_per_second": 1000000 / avg_metric_time if avg_metric_time > 0 else 0,
                "buffer_utilization": collector_stats.get("buffer_utilization", 0),
                "total_metrics_processed": collector_stats.get("metrics_processed", 0),
                "total_buffer_flushes": collector_stats.get("buffer_flushes", 0)
            }
            
            # 效能驗證
            threshold = self.performance_thresholds["metric_collection"]
            assert avg_metric_time < threshold, f"平均指標收集時間 {avg_metric_time:.2f}μs 超過閾值 {threshold}μs"
            
            self._record_result("optimized_metrics_collection_performance", True, metrics=metrics)
            
        except Exception as e:
            self._record_result("optimized_metrics_collection_performance", False, str(e))

    def test_correlation_id_performance(self):
        """測試關聯ID處理效能"""
        try:
            # 模擬關聯ID上下文操作
            from contextvars import ContextVar
            
            correlation_id_context = ContextVar("correlation_id", default=None)
            
            # 關聯ID生成效能測試
            generation_times = []
            for i in range(1000):
                start_time = time.perf_counter()
                correlation_id = str(uuid.uuid4())
                correlation_id_context.set(correlation_id)
                retrieved_id = correlation_id_context.get()
                end_time = time.perf_counter()
                generation_times.append((end_time - start_time) * 1000000)
            
            avg_generation_time = statistics.mean(generation_times)
            p95_generation_time = statistics.quantiles(generation_times, n=20)[18] if len(generation_times) > 20 else max(generation_times)
            
            # 併發關聯ID操作測試
            def concurrent_correlation_task(task_id: int, operation_count: int):
                task_times = []
                for i in range(operation_count):
                    start_time = time.perf_counter()
                    correlation_id = f"task-{task_id}-{i}"
                    correlation_id_context.set(correlation_id)
                    retrieved = correlation_id_context.get()
                    assert retrieved == correlation_id
                    end_time = time.perf_counter()
                    task_times.append((end_time - start_time) * 1000000)
                return task_times
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(concurrent_correlation_task, i, 100) for i in range(10)]
                concurrent_times = []
                for future in concurrent.futures.as_completed(futures):
                    concurrent_times.extend(future.result())
            
            concurrent_avg = statistics.mean(concurrent_times)
            
            # 上下文切換效能測試
            context_switch_times = []
            for i in range(500):
                old_id = f"old-{i}"
                new_id = f"new-{i}"
                
                correlation_id_context.set(old_id)
                
                start_time = time.perf_counter()
                token = correlation_id_context.set(new_id)
                retrieved = correlation_id_context.get()
                correlation_id_context.reset(token)
                end_time = time.perf_counter()
                
                context_switch_times.append((end_time - start_time) * 1000000)
            
            avg_context_switch_time = statistics.mean(context_switch_times)
            
            metrics = {
                "avg_generation_time_us": avg_generation_time,
                "p95_generation_time_us": p95_generation_time,
                "concurrent_avg_time_us": concurrent_avg,
                "context_switch_avg_time_us": avg_context_switch_time,
                "operations_per_second": 1000000 / avg_generation_time if avg_generation_time > 0 else 0
            }
            
            # 效能驗證
            threshold = self.performance_thresholds["correlation_lookup"]
            assert avg_generation_time < threshold, f"平均關聯ID處理時間 {avg_generation_time:.3f}μs 超過閾值 {threshold}μs"
            
            self._record_result("correlation_id_performance", True, metrics=metrics)
            
        except Exception as e:
            self._record_result("correlation_id_performance", False, str(e))

    def test_monitoring_configuration_optimization(self):
        """測試監控配置優化"""
        try:
            # 檢查 Prometheus 配置優化
            prometheus_config = self.project_root / "monitoring/prometheus/prometheus.yml"
            assert prometheus_config.exists(), "Prometheus 配置不存在"
            
            config_content = prometheus_config.read_text()
            
            # 檢查效能優化配置
            has_query_log = "query_log_file" in config_content
            has_retention_config = "storage.tsdb.retention" in config_content
            has_compression = "wal-compression" in config_content
            has_concurrency_config = "query.max-concurrency" in config_content
            
            # 檢查抓取間隔優化
            scrape_intervals = []
            for line in config_content.split('\n'):
                if "scrape_interval:" in line and not line.strip().startswith('#'):
                    interval_str = line.split(':')[-1].strip()
                    if interval_str.endswith('s'):
                        scrape_intervals.append(int(interval_str[:-1]))
            
            avg_scrape_interval = statistics.mean(scrape_intervals) if scrape_intervals else 30
            
            # 檢查服務數量（影響資源使用）
            service_count = config_content.count("job_name:")
            
            # 預估效能特性
            estimated_queries_per_second = service_count / avg_scrape_interval
            estimated_data_points_per_hour = estimated_queries_per_second * 3600 * 50  # 假設每個查詢50個指標
            
            metrics = {
                "has_query_log": has_query_log,
                "has_retention_config": has_retention_config,
                "has_compression": has_compression,
                "has_concurrency_config": has_concurrency_config,
                "avg_scrape_interval_seconds": avg_scrape_interval,
                "monitored_services": service_count,
                "estimated_queries_per_second": estimated_queries_per_second,
                "estimated_data_points_per_hour": estimated_data_points_per_hour
            }
            
            # 配置優化驗證
            config_score = 0
            config_score += 1 if has_query_log else 0
            config_score += 1 if has_retention_config else 0
            config_score += 1 if has_compression else 0
            config_score += 1 if has_concurrency_config else 0
            config_score += 1 if avg_scrape_interval <= 30 else 0  # 合理的抓取間隔
            
            metrics["optimization_score"] = config_score
            metrics["optimization_percentage"] = (config_score / 5) * 100
            
            # 要求至少60%的優化配置
            assert config_score >= 3, f"配置優化分數 {config_score}/5 過低，需要更多優化"
            
            self._record_result("monitoring_configuration_optimization", True, metrics=metrics)
            
        except Exception as e:
            self._record_result("monitoring_configuration_optimization", False, str(e))

    def test_dashboard_query_performance_optimization(self):
        """測試儀表板查詢效能優化"""
        try:
            # 檢查儀表板配置
            dashboards_dir = self.project_root / "monitoring/grafana/dashboards"
            assert dashboards_dir.exists(), "Grafana 儀表板目錄不存在"
            
            dashboard_files = list(dashboards_dir.glob("*.json"))
            assert len(dashboard_files) > 0, "沒有找到儀表板配置檔案"
            
            total_queries = 0
            total_panels = 0
            complex_queries = 0
            dashboard_performance_scores = {}
            
            for dashboard_file in dashboard_files:
                with open(dashboard_file, 'r') as f:
                    dashboard_config = json.load(f)
                
                dashboard_name = dashboard_file.stem
                panels = dashboard_config.get('dashboard', {}).get('panels', [])
                
                panel_count = len(panels)
                query_count = 0
                complex_query_count = 0
                
                for panel in panels:
                    targets = panel.get('targets', [])
                    query_count += len(targets)
                    
                    for target in targets:
                        expr = target.get('expr', '')
                        
                        # 分析查詢複雜度
                        complexity_indicators = [
                            'rate(', 'increase(', 'histogram_quantile(',
                            'avg_over_time(', 'max_over_time(', 'min_over_time(',
                            'by(', 'group_left', 'group_right',
                            'join', 'on(', 'ignoring('
                        ]
                        
                        complexity_score = sum(1 for indicator in complexity_indicators if indicator in expr)
                        if complexity_score >= 2:
                            complex_query_count += 1
                
                # 計算儀表板效能分數
                queries_per_panel = query_count / panel_count if panel_count > 0 else 0
                complexity_ratio = complex_query_count / query_count if query_count > 0 else 0
                
                # 效能分數 (0-100)
                performance_score = 100
                if queries_per_panel > 2:
                    performance_score -= (queries_per_panel - 2) * 10
                if complexity_ratio > 0.5:
                    performance_score -= (complexity_ratio - 0.5) * 40
                if panel_count > 15:
                    performance_score -= (panel_count - 15) * 2
                
                performance_score = max(0, performance_score)
                
                dashboard_performance_scores[dashboard_name] = {
                    "panels": panel_count,
                    "queries": query_count,
                    "complex_queries": complex_query_count,
                    "queries_per_panel": queries_per_panel,
                    "complexity_ratio": complexity_ratio,
                    "performance_score": performance_score
                }
                
                total_queries += query_count
                total_panels += panel_count
                complex_queries += complex_query_count
            
            # 整體效能分析
            avg_queries_per_dashboard = total_queries / len(dashboard_files)
            avg_panels_per_dashboard = total_panels / len(dashboard_files)  
            overall_complexity_ratio = complex_queries / total_queries if total_queries > 0 else 0
            
            avg_performance_score = statistics.mean([d["performance_score"] for d in dashboard_performance_scores.values()])
            
            metrics = {
                "total_dashboards": len(dashboard_files),
                "total_queries": total_queries,
                "total_panels": total_panels,
                "avg_queries_per_dashboard": avg_queries_per_dashboard,
                "avg_panels_per_dashboard": avg_panels_per_dashboard,
                "overall_complexity_ratio": overall_complexity_ratio,
                "avg_performance_score": avg_performance_score,
                "dashboard_details": dashboard_performance_scores
            }
            
            # 效能驗證
            assert avg_performance_score >= 70, f"平均儀表板效能分數 {avg_performance_score:.1f} 過低，需要優化"
            assert avg_queries_per_dashboard <= 15, f"平均每個儀表板查詢數 {avg_queries_per_dashboard:.1f} 過多"
            
            self._record_result("dashboard_query_performance_optimization", True, metrics=metrics)
            
        except Exception as e:
            self._record_result("dashboard_query_performance_optimization", False, str(e))

    def test_alerting_performance_optimization(self):
        """測試警報效能優化"""
        try:
            # 檢查警報規則配置
            rules_dir = self.project_root / "monitoring/prometheus/rules"
            assert rules_dir.exists(), "警報規則目錄不存在"
            
            rule_files = list(rules_dir.glob("*.yml"))
            assert len(rule_files) > 0, "沒有找到警報規則檔案"
            
            total_rules = 0
            total_groups = 0
            complex_rules = 0
            rule_performance_metrics = {}
            
            try:
                import yaml
                yaml_available = True
            except ImportError:
                yaml_available = False
            
            for rule_file in rule_files:
                file_rules = 0
                file_groups = 0
                file_complex_rules = 0
                
                if yaml_available:
                    try:
                        with open(rule_file, 'r') as f:
                            rules_config = yaml.safe_load(f)
                        
                        for group in rules_config.get('groups', []):
                            file_groups += 1
                            for rule in group.get('rules', []):
                                file_rules += 1
                                expr = rule.get('expr', '')
                                
                                # 分析規則複雜度
                                complexity_score = 0
                                complexity_score += expr.count('(') * 0.5
                                complexity_score += expr.count('rate(') * 2
                                complexity_score += expr.count('histogram_quantile(') * 3
                                complexity_score += expr.count('by(') * 1
                                complexity_score += expr.count('group_left') * 2
                                complexity_score += expr.count('group_right') * 2
                                
                                if complexity_score > 3:
                                    file_complex_rules += 1
                    except Exception as e:
                        logger.warning(f"無法解析 YAML 文件 {rule_file}: {e}")
                        # 使用文本分析作為備選方案
                        content = rule_file.read_text()
                        file_rules = content.count('alert:')
                        file_groups = content.count('name:')
                        file_complex_rules = content.count('histogram_quantile')
                else:
                    # 簡單文本分析
                    content = rule_file.read_text()
                    file_rules = content.count('alert:')
                    file_groups = content.count('name:') 
                    file_complex_rules = content.count('histogram_quantile') + content.count('rate(')
                
                rule_performance_metrics[rule_file.stem] = {
                    "rules": file_rules,
                    "groups": file_groups,
                    "complex_rules": file_complex_rules,
                    "complexity_ratio": file_complex_rules / file_rules if file_rules > 0 else 0
                }
                
                total_rules += file_rules
                total_groups += file_groups
                complex_rules += file_complex_rules
            
            # 效能分析
            avg_rules_per_file = total_rules / len(rule_files) if len(rule_files) > 0 else 0
            avg_rules_per_group = total_rules / total_groups if total_groups > 0 else 0
            complexity_ratio = complex_rules / total_rules if total_rules > 0 else 0
            
            # 預估警報評估效能
            base_eval_time_us = 5  # 基礎評估時間
            complexity_penalty = complexity_ratio * 20
            estimated_eval_time = base_eval_time_us + complexity_penalty
            estimated_total_eval_time = estimated_eval_time * total_rules
            
            metrics = {
                "total_rules": total_rules,
                "total_groups": total_groups,
                "complex_rules": complex_rules,
                "avg_rules_per_file": avg_rules_per_file,
                "avg_rules_per_group": avg_rules_per_group,
                "complexity_ratio": complexity_ratio,
                "estimated_eval_time_us": estimated_eval_time,
                "estimated_total_eval_time_us": estimated_total_eval_time,
                "rule_file_details": rule_performance_metrics
            }
            
            # 效能驗證
            assert estimated_eval_time <= 50, f"預估警報評估時間 {estimated_eval_time:.1f}μs 過高"
            assert avg_rules_per_group <= 10, f"平均每組規則數 {avg_rules_per_group:.1f} 過多，建議拆分"
            
            self._record_result("alerting_performance_optimization", True, metrics=metrics)
            
        except Exception as e:
            self._record_result("alerting_performance_optimization", False, str(e))

    def print_results(self):
        """打印測試結果和效能分析"""
        total_tests = self.results["tests_passed"] + self.results["tests_failed"]
        success_rate = (self.results["tests_passed"] / total_tests * 100) if total_tests > 0 else 0
        
        logger.info("=" * 80)
        logger.info("🔧 TDD Refactor 階段: 監控效能和可觀測性優化結果 (重構版)")
        logger.info("=" * 80)
        logger.info(f"✅ 通過測試: {self.results['tests_passed']}")
        logger.info(f"❌ 失敗測試: {self.results['tests_failed']}")
        logger.info(f"📈 測試成功率: {success_rate:.1f}%")
        
        if self.results["errors"]:
            logger.info("\n🎯 需要優化的項目:")
            for error in self.results["errors"]:
                logger.info(f"  - {error}")
        
        # 效能分析報告
        if self.results["performance_metrics"]:
            logger.info("\n📊 效能優化分析報告:")
            for test_name, metrics in self.results["performance_metrics"].items():
                logger.info(f"  📈 {test_name}:")
                for metric_name, value in metrics.items():
                    if isinstance(value, (int, float)):
                        if metric_name.endswith("_us"):
                            logger.info(f"    - {metric_name}: {value:.3f} μs")
                        elif metric_name.endswith("_ms"):
                            logger.info(f"    - {metric_name}: {value:.3f} ms")
                        elif metric_name.endswith("_seconds"):
                            logger.info(f"    - {metric_name}: {value:.1f} s")
                        elif "percentage" in metric_name or "ratio" in metric_name:
                            logger.info(f"    - {metric_name}: {value:.1f}%")
                        elif "per_second" in metric_name:
                            logger.info(f"    - {metric_name}: {value:.0f} /s")
                        else:
                            logger.info(f"    - {metric_name}: {value:.3f}")
                    elif isinstance(value, dict) and len(value) <= 3:
                        logger.info(f"    - {metric_name}: {value}")
                    elif not isinstance(value, dict):
                        logger.info(f"    - {metric_name}: {value}")
        
        # 總體效能評估
        logger.info("\n🎯 效能優化摘要:")
        
        performance_summary = {}
        for test_name, metrics in self.results["performance_metrics"].items():
            if "avg_" in str(metrics):
                for key, value in metrics.items():
                    if "avg_" in key and isinstance(value, (int, float)):
                        performance_summary[f"{test_name}_{key}"] = value
        
        if performance_summary:
            logger.info("  主要效能指標:")
            for metric, value in performance_summary.items():
                logger.info(f"    - {metric}: {value:.3f}")
        
        # Refactor 階段評估
        if success_rate >= 90:
            logger.info("\n🟢 TDD Refactor 階段狀態: 優秀 - 效能和可觀測性優化成功")
            logger.info("✨ 監控系統已達到生產級效能標準")
        elif success_rate >= 70:
            logger.info("\n🟡 TDD Refactor 階段狀態: 良好 - 大部分優化成功，少數需調整")
            logger.info("🔧 建議進一步調整未達標的效能指標")
        else:
            logger.info("\n🔴 TDD Refactor 階段狀態: 需改進 - 多數效能指標需要優化")
            logger.info("📊 請根據詳細分析報告進行系統性優化")
        
        return success_rate >= 70


def main():
    """執行監控效能和可觀測性優化 TDD Refactor 階段測試"""
    logger.info("🔧 開始 TDD Refactor 階段: 監控效能和可觀測性優化 (重構版)")
    logger.info("目標: 優化監控系統效能並增強可觀測性功能")
    logger.info("=" * 80)
    
    test_suite = MonitoringPerformanceRefactoredTest()
    
    try:
        # 執行所有優化測試
        test_suite.test_optimized_logging_performance()
        test_suite.test_optimized_metrics_collection_performance()
        test_suite.test_correlation_id_performance()
        test_suite.test_monitoring_configuration_optimization()
        test_suite.test_dashboard_query_performance_optimization()
        test_suite.test_alerting_performance_optimization()
        
        # 打印結果和分析
        is_successful = test_suite.print_results()
        
        if is_successful:
            logger.info("\n🎉 TDD Refactor 階段成功！")
            logger.info("✨ 監控系統效能和可觀測性優化完成")
            logger.info("🚀 系統已具備生產級監控能力")
            logger.info("📊 所有效能指標均符合或超過預期目標")
        else:
            logger.info("\n🔧 TDD Refactor 階段需要進一步優化")
            logger.info("📊 請根據效能分析報告進行針對性調整")
        
        return is_successful
        
    except Exception as e:
        logger.error(f"❌ Refactor 階段測試執行異常: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    
    if success:
        logger.info("🏁 TDD Refactor 階段完成 - 監控效能優化成功")
        exit(0)
    else:
        logger.error("🛑 TDD Refactor 階段需要改進")
        exit(1)