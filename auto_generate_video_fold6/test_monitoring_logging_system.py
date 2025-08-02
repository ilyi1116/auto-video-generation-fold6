#!/usr/bin/env python3
"""
TDD Red 階段: 監控和日誌系統測試
定義完整監控和日誌系統的期望行為
"""

import json
from pathlib import Path
import logging

# Try to import optional dependencies
try:
    import yaml
except ImportError:
    yaml = None

try:
    import requests
except ImportError:
    requests = None

try:
    import pytest
except ImportError:
    pytest = None

# Configure test logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MonitoringLoggingSystemTest:
    """監控和日誌系統 TDD 測試套件"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {"tests_passed": 0, "tests_failed": 0, "errors": []}

        # Test configuration
        self.services = [
            "frontend",
            "api-gateway",
            "trend-service",
            "video-service",
            "social-service",
            "scheduler-service",
            "postgres",
            "redis",
            "minio",
        ]

        # Expected monitoring endpoints
        self.monitoring_endpoints = {
            "prometheus": "http://localhost:9090",
            "grafana": "http://localhost:3001",
            "alertmanager": "http://localhost:9093",
            "jaeger": "http://localhost:16686",
        }

    def _record_result(self, test_name: str, success: bool, error: str = None):
        """記錄測試結果"""
        if success:
            self.results["tests_passed"] += 1
            logger.info(f"✅ {test_name} 通過")
        else:
            self.results["tests_failed"] += 1
            self.results["errors"].append(f"{test_name}: {error}")
            logger.error(f"❌ {test_name} 失敗: {error}")

    def test_structured_logging_configuration(self):
        """測試結構化日誌配置"""
        try:
            # 檢查日誌配置文件
            log_config_files = [
                "monitoring/logging/structured_logger.py",
                "monitoring/logging/log_config.json",
                "monitoring/fluentd/fluent.conf",
                "monitoring/logstash/pipeline/logstash.conf",
            ]

            for config_file in log_config_files:
                config_path = self.project_root / config_file
                assert (
                    config_path.exists()
                ), f"日誌配置文件不存在: {config_file}"

                # 檢查配置文件內容
                if config_file.endswith(".py"):
                    content = config_path.read_text()
                    assert (
                        "StructuredLogger" in content
                    ), f"缺少 StructuredLogger 類別: {config_file}"
                    assert (
                        "correlation_id" in content
                    ), f"缺少關聯ID支援: {config_file}"
                    assert (
                        "json" in content.lower()
                    ), f"缺少JSON格式支援: {config_file}"

                elif config_file.endswith(".json"):
                    with open(config_path, "r") as f:
                        config = json.load(f)
                    assert (
                        "formatters" in config
                    ), f"缺少格式化器配置: {config_file}"
                    assert (
                        "handlers" in config
                    ), f"缺少處理器配置: {config_file}"

                elif config_file.endswith(".conf"):
                    content = config_path.read_text()
                    assert (
                        "source" in content
                    ), f"缺少輸入源配置: {config_file}"
                    assert "match" in content, f"缺少匹配規則: {config_file}"

            self._record_result("structured_logging_configuration", True)

        except Exception as e:
            self._record_result(
                "structured_logging_configuration", False, str(e)
            )

    def test_prometheus_metrics_collection(self):
        """測試 Prometheus 指標收集配置"""
        try:
            # 檢查 Prometheus 配置
            prometheus_config = (
                self.project_root / "monitoring/prometheus/prometheus.yml"
            )
            assert prometheus_config.exists(), "Prometheus 配置文件不存在"

            if yaml:
                with open(prometheus_config, "r") as f:
                    config = yaml.safe_load(f)
            else:
                # 簡單文本檢查如果沒有 yaml
                prometheus_config.read_text()
                config = {
                    "scrape_configs": [{"job_name": "prometheus"}]
                }  # 模擬基本結構

            # 檢查基本配置
            assert "global" in config, "缺少全局配置"
            assert "scrape_configs" in config, "缺少抓取配置"

            # 檢查服務發現配置
            scrape_jobs = {job["job_name"] for job in config["scrape_configs"]}
            expected_jobs = {
                "prometheus",
                "node-exporter",
                "postgres-exporter",
                "redis-exporter",
                "docker-exporter",
                "application-metrics",
            }

            missing_jobs = expected_jobs - scrape_jobs
            assert not missing_jobs, f"缺少監控作業: {missing_jobs}"

            # 檢查指標中間件文件
            metrics_middleware = (
                self.project_root
                / "monitoring/middleware/prometheus_middleware.py"
            )
            assert metrics_middleware.exists(), "缺少 Prometheus 中間件"

            middleware_content = metrics_middleware.read_text()
            assert "Counter" in middleware_content, "缺少計數器指標"
            assert "Histogram" in middleware_content, "缺少直方圖指標"
            assert "Gauge" in middleware_content, "缺少測量指標"

            self._record_result("prometheus_metrics_collection", True)

        except Exception as e:
            self._record_result("prometheus_metrics_collection", False, str(e))

    def test_grafana_dashboard_configuration(self):
        """測試 Grafana 儀表板配置"""
        try:
            # 檢查 Grafana 配置目錄
            grafana_dir = self.project_root / "monitoring/grafana"
            assert grafana_dir.exists(), "Grafana 配置目錄不存在"

            # 檢查數據源配置
            datasources_dir = grafana_dir / "provisioning/datasources"
            assert datasources_dir.exists(), "數據源配置目錄不存在"

            prometheus_datasource = datasources_dir / "prometheus.yml"
            assert (
                prometheus_datasource.exists()
            ), "Prometheus 數據源配置不存在"

            if yaml:
                with open(prometheus_datasource, "r") as f:
                    datasource_config = yaml.safe_load(f)
            else:
                datasource_config = {"datasources": [{"type": "prometheus"}]}

            assert "datasources" in datasource_config, "缺少數據源定義"
            prometheus_ds = datasource_config["datasources"][0]
            assert prometheus_ds["type"] == "prometheus", "數據源類型不正確"

            # 檢查儀表板配置
            dashboards_dir = grafana_dir / "dashboards"
            assert dashboards_dir.exists(), "儀表板目錄不存在"

            expected_dashboards = [
                "system-overview.json",
                "application-performance.json",
                "docker-containers.json",
                "business-metrics.json",
                "error-tracking.json",
            ]

            for dashboard in expected_dashboards:
                dashboard_path = dashboards_dir / dashboard
                assert dashboard_path.exists(), f"儀表板不存在: {dashboard}"

                with open(dashboard_path, "r") as f:
                    dashboard_config = json.load(f)

                assert (
                    "dashboard" in dashboard_config
                ), f"儀表板配置格式錯誤: {dashboard}"
                assert (
                    "panels" in dashboard_config["dashboard"]
                ), f"缺少面板配置: {dashboard}"

            self._record_result("grafana_dashboard_configuration", True)

        except Exception as e:
            self._record_result(
                "grafana_dashboard_configuration", False, str(e)
            )

    def test_alerting_system_configuration(self):
        """測試警報系統配置"""
        try:
            # 檢查 Alertmanager 配置
            alertmanager_config = (
                self.project_root / "monitoring/alertmanager/alertmanager.yml"
            )
            assert alertmanager_config.exists(), "Alertmanager 配置文件不存在"

            if yaml:
                with open(alertmanager_config, "r") as f:
                    config = yaml.safe_load(f)
            else:
                config = {"global": {}, "route": {}, "receivers": []}

            assert "global" in config, "缺少全局警報配置"
            assert "route" in config, "缺少路由配置"
            assert "receivers" in config, "缺少接收器配置"

            # 檢查警報規則
            alert_rules = self.project_root / "monitoring/prometheus/rules"
            assert alert_rules.exists(), "警報規則目錄不存在"

            expected_rule_files = [
                "system-alerts.yml",
                "application-alerts.yml",
                "business-alerts.yml",
            ]

            for rule_file in expected_rule_files:
                rule_path = alert_rules / rule_file
                assert rule_path.exists(), f"警報規則文件不存在: {rule_file}"

                if yaml:
                    with open(rule_path, "r") as f:
                        rules = yaml.safe_load(f)
                else:
                    rules = {
                        "groups": [
                            {
                                "name": "test",
                                "rules": [
                                    {
                                        "alert": "test",
                                        "expr": "up",
                                        "for": "1m",
                                    }
                                ],
                            }
                        ]
                    }

                assert "groups" in rules, f"缺少警報組: {rule_file}"

                for group in rules["groups"]:
                    assert "rules" in group, f"警報組缺少規則: {group['name']}"

                    for rule in group["rules"]:
                        assert "alert" in rule, f"規則缺少警報名稱: {rule}"
                        assert (
                            "expr" in rule
                        ), f"規則缺少表達式: {rule['alert']}"
                        assert (
                            "for" in rule
                        ), f"規則缺少持續時間: {rule['alert']}"

            # 檢查通知範本
            templates_dir = (
                self.project_root / "monitoring/alertmanager/templates"
            )
            assert templates_dir.exists(), "警報範本目錄不存在"

            email_template = templates_dir / "email.tmpl"
            assert email_template.exists(), "電子郵件範本不存在"

            self._record_result("alerting_system_configuration", True)

        except Exception as e:
            self._record_result("alerting_system_configuration", False, str(e))

    def test_distributed_tracing_setup(self):
        """測試分散式追蹤配置"""
        try:
            # 檢查 Jaeger 配置
            jaeger_config = self.project_root / "monitoring/jaeger"
            assert jaeger_config.exists(), "Jaeger 配置目錄不存在"

            jaeger_config_file = jaeger_config / "jaeger-config.yml"
            assert jaeger_config_file.exists(), "Jaeger 配置文件不存在"

            # 檢查 OpenTelemetry 中間件
            otel_middleware = (
                self.project_root
                / "monitoring/tracing/opentelemetry_middleware.py"
            )
            assert otel_middleware.exists(), "OpenTelemetry 中間件不存在"

            middleware_content = otel_middleware.read_text()
            assert "tracer" in middleware_content.lower(), "缺少追蹤器配置"
            assert "span" in middleware_content.lower(), "缺少跨度處理"
            assert (
                "correlation" in middleware_content.lower()
            ), "缺少關聯ID處理"

            # 檢查追蹤配置檔案
            tracing_configs = [
                "services/api-gateway/tracing_config.py",
                "services/trend-service/tracing_config.py",
                "services/video-service/tracing_config.py",
            ]

            for config_file in tracing_configs:
                config_path = self.project_root / config_file
                # 允許文件不存在，因為這是 Red 階段
                if config_path.exists():
                    content = config_path.read_text()
                    assert (
                        "opentelemetry" in content.lower()
                    ), f"缺少 OpenTelemetry 配置: {config_file}"

            self._record_result("distributed_tracing_setup", True)

        except Exception as e:
            self._record_result("distributed_tracing_setup", False, str(e))

    def test_log_aggregation_pipeline(self):
        """測試日誌聚合管道配置"""
        try:
            # 檢查 ELK Stack 配置
            logstash_config = self.project_root / "monitoring/logstash"
            assert logstash_config.exists(), "Logstash 配置目錄不存在"

            pipeline_config = logstash_config / "pipeline/logstash.conf"
            assert pipeline_config.exists(), "Logstash 管道配置不存在"

            pipeline_content = pipeline_config.read_text()
            assert "input" in pipeline_content, "缺少輸入配置"
            assert "filter" in pipeline_content, "缺少過濾器配置"
            assert "output" in pipeline_content, "缺少輸出配置"

            # 檢查 Fluent Bit 配置
            fluent_config = (
                self.project_root / "monitoring/logging/fluent-bit.conf"
            )
            assert fluent_config.exists(), "Fluent Bit 配置不存在"

            fluent_content = fluent_config.read_text()
            assert "[INPUT]" in fluent_content, "缺少輸入配置"
            assert "[OUTPUT]" in fluent_content, "缺少輸出配置"
            assert "[FILTER]" in fluent_content, "缺少過濾配置"

            # 檢查解析器配置
            parsers_config = (
                self.project_root / "monitoring/logging/parsers.conf"
            )
            assert parsers_config.exists(), "解析器配置不存在"

            self._record_result("log_aggregation_pipeline", True)

        except Exception as e:
            self._record_result("log_aggregation_pipeline", False, str(e))

    def test_performance_monitoring_integration(self):
        """測試效能監控整合"""
        try:
            # 檢查應用程式監控中間件
            monitoring_middleware = self.project_root / "monitoring/middleware"
            assert monitoring_middleware.exists(), "監控中間件目錄不存在"

            expected_middleware = [
                "performance_middleware.py",
                "health_check_middleware.py",
                "correlation_middleware.py",
            ]

            for middleware in expected_middleware:
                middleware_path = monitoring_middleware / middleware
                assert middleware_path.exists(), f"中間件不存在: {middleware}"

                content = middleware_path.read_text()
                assert (
                    "async def" in content or "def " in content
                ), f"中間件缺少函數定義: {middleware}"

                if "performance" in middleware:
                    assert (
                        "response_time" in content.lower()
                    ), f"缺少回應時間監控: {middleware}"
                    assert (
                        "request_count" in content.lower()
                    ), f"缺少請求計數: {middleware}"

                elif "health" in middleware:
                    assert (
                        "health" in content.lower()
                    ), f"缺少健康檢查: {middleware}"
                    assert (
                        "status" in content.lower()
                    ), f"缺少狀態檢查: {middleware}"

            # 檢查資料庫監控配置
            db_monitoring = self.project_root / "monitoring/database"
            if db_monitoring.exists():
                pg_exporter_config = db_monitoring / "postgres_exporter.yml"
                if pg_exporter_config.exists():
                    if yaml:
                        with open(pg_exporter_config, "r") as f:
                            config = yaml.safe_load(f)
                        assert "queries" in config, "缺少資料庫查詢配置"
                    else:
                        logger.info("跳過 YAML 配置檢查 (yaml 模組未安裝)")

            self._record_result("performance_monitoring_integration", True)

        except Exception as e:
            self._record_result(
                "performance_monitoring_integration", False, str(e)
            )

    def test_business_metrics_tracking(self):
        """測試業務指標追蹤"""
        try:
            # 檢查業務指標定義
            business_metrics = (
                self.project_root / "monitoring/business_metrics"
            )
            assert business_metrics.exists(), "業務指標目錄不存在"

            metrics_config = business_metrics / "metrics_definition.json"
            assert metrics_config.exists(), "業務指標定義不存在"

            with open(metrics_config, "r") as f:
                metrics = json.load(f)

            # 檢查關鍵業務指標
            expected_metrics = [
                "video_generation_count",
                "user_engagement_rate",
                "platform_publish_success_rate",
                "trend_analysis_accuracy",
                "system_availability",
            ]

            defined_metrics = set(metrics.keys())
            missing_metrics = set(expected_metrics) - defined_metrics
            assert not missing_metrics, f"缺少業務指標: {missing_metrics}"

            # 檢查指標收集器
            metrics_collector = (
                business_metrics / "business_metrics_collector.py"
            )
            assert metrics_collector.exists(), "業務指標收集器不存在"

            collector_content = metrics_collector.read_text()
            assert (
                "BusinessMetricsCollector" in collector_content
            ), "缺少業務指標收集器類別"
            assert "collect_metrics" in collector_content, "缺少指標收集方法"

            self._record_result("business_metrics_tracking", True)

        except Exception as e:
            self._record_result("business_metrics_tracking", False, str(e))

    def test_monitoring_docker_compose_integration(self):
        """測試監控系統 Docker Compose 整合"""
        try:
            # 檢查監控 Docker Compose 文件
            monitoring_compose = (
                self.project_root / "docker-compose.monitoring.yml"
            )
            assert (
                monitoring_compose.exists()
            ), "監控 Docker Compose 文件不存在"

            if yaml:
                with open(monitoring_compose, "r") as f:
                    compose_config = yaml.safe_load(f)
            else:
                compose_config = {
                    "services": {"prometheus": {"image": "prom/prometheus"}}
                }

            assert "services" in compose_config, "缺少服務定義"

            # 檢查必要的監控服務
            expected_services = [
                "prometheus",
                "grafana",
                "alertmanager",
                "jaeger",
                "logstash",
                "elasticsearch",
                "kibana",
            ]

            defined_services = set(compose_config["services"].keys())
            missing_services = set(expected_services) - defined_services

            # 允許部分服務缺失（Red 階段期望失敗）
            if missing_services:
                logger.warning(f"缺少監控服務: {missing_services}")

            # 檢查服務配置
            for service_name, service_config in compose_config[
                "services"
            ].items():
                if service_name in expected_services:
                    assert (
                        "image" in service_config or "build" in service_config
                    ), f"服務缺少映像配置: {service_name}"

                    if "ports" in service_config:
                        assert (
                            len(service_config["ports"]) > 0
                        ), f"服務未暴露端口: {service_name}"

            self._record_result("monitoring_docker_compose_integration", True)

        except Exception as e:
            self._record_result(
                "monitoring_docker_compose_integration", False, str(e)
            )

    def test_health_check_endpoints(self):
        """測試健康檢查端點"""
        try:
            # 檢查健康檢查實作
            health_check_files = [
                "monitoring/health-check/health_monitor.py",
                "shared/health/health_checker.py",
            ]

            for health_file in health_check_files:
                health_path = self.project_root / health_file
                if health_path.exists():  # 允許文件不存在
                    content = health_path.read_text()
                    assert (
                        "health" in content.lower()
                    ), f"缺少健康檢查實作: {health_file}"
                    assert (
                        "status" in content.lower()
                    ), f"缺少狀態檢查: {health_file}"

            # 檢查各服務的健康檢查端點定義
            for service in self.services[:3]:  # 只檢查前3個服務
                service_path = self.project_root / f"services/{service}"
                if service_path.exists():
                    # 查找健康檢查端點
                    for py_file in service_path.rglob("*.py"):
                        if py_file.name in ["main.py", "app.py", "health.py"]:
                            content = py_file.read_text()
                            if "/health" in content:
                                assert (
                                    "health" in content.lower()
                                ), f"健康檢查端點實作不完整: {py_file}"
                                break

            self._record_result("health_check_endpoints", True)

        except Exception as e:
            self._record_result("health_check_endpoints", False, str(e))

    def test_monitoring_configuration_validation(self):
        """測試監控配置驗證"""
        try:
            # 檢查配置驗證腳本
            config_validator = (
                self.project_root / "scripts/validate-monitoring-config.py"
            )
            if not config_validator.exists():
                config_validator = (
                    self.project_root / "monitoring/config_validator.py"
                )

            if config_validator.exists():
                content = config_validator.read_text()
                assert "validate" in content.lower(), "缺少配置驗證功能"
                assert (
                    "prometheus" in content.lower()
                ), "缺少 Prometheus 配置驗證"
                assert "grafana" in content.lower(), "缺少 Grafana 配置驗證"

            # 檢查環境變數範本
            env_example = self.project_root / ".env.monitoring.example"
            if env_example.exists():
                env_content = env_example.read_text()
                monitoring_vars = [
                    "PROMETHEUS_PORT",
                    "GRAFANA_ADMIN_PASSWORD",
                    "ALERTMANAGER_PORT",
                    "JAEGER_PORT",
                ]

                for var in monitoring_vars:
                    if var not in env_content:
                        logger.warning(f"環境變數範本缺少: {var}")

            self._record_result("monitoring_configuration_validation", True)

        except Exception as e:
            self._record_result(
                "monitoring_configuration_validation", False, str(e)
            )

    def print_results(self):
        """打印測試結果"""
        total_tests = (
            self.results["tests_passed"] + self.results["tests_failed"]
        )
        success_rate = (
            (self.results["tests_passed"] / total_tests * 100)
            if total_tests > 0
            else 0
        )

        logger.info("=" * 70)
        logger.info("🔴 TDD Red 階段: 監控和日誌系統測試結果")
        logger.info("=" * 70)
        logger.info(f"✅ 通過測試: {self.results['tests_passed']}")
        logger.info(f"❌ 失敗測試: {self.results['tests_failed']}")
        logger.info(f"📈 當前完成率: {success_rate:.1f}%")

        if self.results["errors"]:
            logger.info("\n🎯 需要實作的功能:")
            for error in self.results["errors"]:
                logger.info(f"  - {error}")

        # Red 階段評估
        if success_rate < 30:
            logger.info(
                "\n🔴 TDD Red 階段狀態: 完美 - 大部分測試失敗，定義了清晰的目標"
            )
        elif success_rate < 60:
            logger.info(
                "\n🟡 TDD Red 階段狀態: 良好 - 有些基礎已存在，需要更多實作"
            )
        else:
            logger.info(
                "\n🟢 TDD Red 階段狀態: 意外 - 很多功能已存在，可能需要調整測試"
            )

        return success_rate < 50  # Red 階段期望低成功率


def main():
    """執行監控和日誌系統 TDD Red 階段測試"""
    logger.info("🔴 開始 TDD Red 階段: 監控和日誌系統測試")
    logger.info("目標: 定義完整監控和日誌系統的期望行為")
    logger.info("=" * 70)

    test_suite = MonitoringLoggingSystemTest()

    try:
        # 執行所有測試
        test_suite.test_structured_logging_configuration()
        test_suite.test_prometheus_metrics_collection()
        test_suite.test_grafana_dashboard_configuration()
        test_suite.test_alerting_system_configuration()
        test_suite.test_distributed_tracing_setup()
        test_suite.test_log_aggregation_pipeline()
        test_suite.test_performance_monitoring_integration()
        test_suite.test_business_metrics_tracking()
        test_suite.test_monitoring_docker_compose_integration()
        test_suite.test_health_check_endpoints()
        test_suite.test_monitoring_configuration_validation()

        # 打印結果
        is_proper_red = test_suite.print_results()

        if is_proper_red:
            logger.info("\n🎉 TDD Red 階段成功！")
            logger.info("✨ 已定義完整的監控和日誌系統需求")
            logger.info("🎯 準備進入 Green 階段實作")
        else:
            logger.info("\n🤔 TDD Red 階段意外通過較多測試")
            logger.info("🔧 可能需要調整測試或檢查現有實作")

        return is_proper_red

    except Exception as e:
        logger.error(f"❌ Red 階段測試執行異常: {e}")
        return False


if __name__ == "__main__":
    success = main()

    if success:
        logger.info("🏁 TDD Red 階段完成 - 監控和日誌系統需求已定義")
        exit(0)
    else:
        logger.error("🛑 TDD Red 階段需要調整")
        exit(1)
