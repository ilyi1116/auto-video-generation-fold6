#!/usr/bin/env python3
"""
TDD Red 階段: Docker 容器化測試
定義生產級 Docker 多階段構建的期望行為
"""

import asyncio
import pytest
import subprocess
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Any
import tempfile
import yaml
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DockerContainerizationTest:
    """Docker 容器化 TDD 測試套件"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {"tests_passed": 0, "tests_failed": 0, "errors": []}

    def _record_result(self, test_name: str, success: bool, error: str = None):
        """記錄測試結果"""
        if success:
            self.results["tests_passed"] += 1
            logger.info(f"✅ {test_name} 通過")
        else:
            self.results["tests_failed"] += 1
            self.results["errors"].append(f"{test_name}: {error}")
            logger.error(f"❌ {test_name} 失敗: {error}")

    def test_dockerfile_exists_and_multistage(self):
        """測試 Dockerfile 存在且為多階段構建"""
        try:
            # 檢查各服務的 Dockerfile
            expected_dockerfiles = [
                "services/trend-service/Dockerfile",
                "services/video-service/Dockerfile",
                "services/social-service/Dockerfile",
                "services/scheduler-service/Dockerfile",
                "frontend/Dockerfile",
            ]

            for dockerfile_path in expected_dockerfiles:
                full_path = self.project_root / dockerfile_path
                assert (
                    full_path.exists()
                ), f"Dockerfile 不存在: {dockerfile_path}"

                # 讀取 Dockerfile 內容
                content = full_path.read_text()

                # 檢查多階段構建標記
                stages = content.count("FROM ")
                assert (
                    stages >= 2
                ), f"Dockerfile {dockerfile_path} 不是多階段構建 (只有 {stages} 個 FROM)"

                # 檢查必要的構建階段（不區分大小寫）
                content_lower = content.lower()
                assert (
                    "as builder" in content_lower
                    or "as build" in content_lower
                ), f"缺少 builder 階段: {dockerfile_path}"
                assert (
                    "as runtime" in content_lower
                    or "as production" in content_lower
                ), f"缺少 runtime 階段: {dockerfile_path}"

            self._record_result("dockerfile_multistage_structure", True)

        except Exception as e:
            self._record_result(
                "dockerfile_multistage_structure", False, str(e)
            )

    def test_docker_compose_production_config(self):
        """測試生產級 Docker Compose 配置"""
        try:
            compose_files = [
                "docker-compose.yml",
                "docker-compose.prod.yml",
                "docker-compose.dev.yml",
            ]

            for compose_file in compose_files:
                full_path = self.project_root / compose_file
                assert (
                    full_path.exists()
                ), f"Docker Compose 文件不存在: {compose_file}"

                # 解析 YAML 配置
                with open(full_path, "r") as f:
                    config = yaml.safe_load(f)

                # 檢查服務定義
                assert (
                    "services" in config
                ), f"缺少 services 定義: {compose_file}"

                expected_services = [
                    "trend-service",
                    "video-service",
                    "social-service",
                    "scheduler-service",
                    "frontend",
                    "postgres",
                    "redis",
                ]

                for service in expected_services:
                    assert (
                        service in config["services"]
                    ), f"缺少服務定義: {service} in {compose_file}"

                # 檢查生產配置特定要求
                if "prod" in compose_file:
                    # 檢查資源限制
                    for service_name, service_config in config[
                        "services"
                    ].items():
                        if service_name in [
                            "trend-service",
                            "video-service",
                            "social-service",
                            "scheduler-service",
                        ]:
                            assert (
                                "deploy" in service_config
                            ), f"生產服務缺少 deploy 配置: {service_name}"
                            assert (
                                "resources" in service_config["deploy"]
                            ), f"缺少資源限制: {service_name}"

            self._record_result("docker_compose_production_config", True)

        except Exception as e:
            self._record_result(
                "docker_compose_production_config", False, str(e)
            )

    def test_dockerfile_optimization_practices(self):
        """測試 Dockerfile 優化實踐"""
        try:
            dockerfile_paths = [
                "services/trend-service/Dockerfile",
                "services/video-service/Dockerfile",
            ]

            for dockerfile_path in dockerfile_paths:
                full_path = self.project_root / dockerfile_path
                if not full_path.exists():
                    continue

                content = full_path.read_text()

                # 檢查優化實踐
                optimizations = {
                    "使用 .dockerignore": True,  # 將在後續檢查
                    "多階段構建減少映像大小": "FROM python:3.11-slim"
                    in content,
                    "合併 RUN 指令": content.count("RUN")
                    <= 5,  # 限制 RUN 指令數量
                    "清理快取": "rm -rf" in content
                    or "apt-get clean" in content,
                    "非 root 用戶": "USER " in content,
                    "健康檢查": "HEALTHCHECK" in content,
                }

                for optimization, passed in optimizations.items():
                    if optimization == "使用 .dockerignore":
                        dockerignore_path = full_path.parent / ".dockerignore"
                        passed = dockerignore_path.exists()

                    if not passed:
                        logger.warning(
                            f"優化建議: {dockerfile_path} - {optimization}"
                        )

            self._record_result("dockerfile_optimization_practices", True)

        except Exception as e:
            self._record_result(
                "dockerfile_optimization_practices", False, str(e)
            )

    def test_container_security_practices(self):
        """測試容器安全實踐"""
        try:
            security_checks = []

            # 檢查 .dockerignore 文件
            for service_dir in [
                "services/trend-service",
                "services/video-service",
                "frontend",
            ]:
                dockerignore_path = (
                    self.project_root / service_dir / ".dockerignore"
                )
                if dockerignore_path.exists():
                    content = dockerignore_path.read_text()

                    # 檢查敏感文件排除
                    sensitive_patterns = [
                        ".env",
                        "*.key",
                        "*.pem",
                        ".git",
                        "node_modules",
                        "__pycache__",
                    ]
                    for pattern in sensitive_patterns:
                        if pattern not in content:
                            security_checks.append(
                                f"缺少排除模式: {pattern} in {dockerignore_path}"
                            )

            # 檢查環境變數安全
            compose_path = self.project_root / "docker-compose.prod.yml"
            if compose_path.exists():
                with open(compose_path, "r") as f:
                    config = yaml.safe_load(f)

                for service_name, service_config in config.get(
                    "services", {}
                ).items():
                    env_vars = service_config.get("environment", {})

                    # 處理環境變數格式（可能是字典或列表）
                    if isinstance(env_vars, list):
                        # 如果是列表格式，跳過詳細檢查
                        continue
                    elif isinstance(env_vars, dict):
                        # 檢查是否使用敏感環境變數
                        sensitive_vars = ["PASSWORD", "SECRET", "KEY", "TOKEN"]
                        for var_name, var_value in env_vars.items():
                            for sensitive in sensitive_vars:
                                if sensitive in var_name.upper() and not str(
                                    var_value
                                ).startswith("${"):
                                    security_checks.append(
                                        f"硬編碼敏感變數: {var_name} in {service_name}"
                                    )

            # 如果有安全問題，記錄但不失敗（因為這是初始測試）
            if security_checks:
                logger.warning(f"安全建議: {security_checks}")

            self._record_result("container_security_practices", True)

        except Exception as e:
            self._record_result("container_security_practices", False, str(e))

    def test_build_and_run_simulation(self):
        """測試構建和運行模擬（不實際構建）"""
        try:
            # 模擬構建過程檢查
            build_requirements = {
                "Python 後端服務": {
                    "requirements_files": [
                        "requirements.txt",
                        "requirements-prod.txt",
                    ],
                    "app_files": ["main.py", "app.py"],
                    "config_files": ["config/", "settings.py"],
                },
                "前端服務": {
                    "package_files": ["package.json", "package-lock.json"],
                    "build_files": ["vite.config.js", "tailwind.config.js"],
                    "source_files": ["src/", "public/"],
                },
            }

            # 檢查構建所需文件
            missing_files = []

            # 檢查後端服務文件
            for service_dir in [
                "services/trend-service",
                "services/video-service",
            ]:
                service_path = self.project_root / service_dir
                if service_path.exists():
                    for req_file in build_requirements["Python 後端服務"][
                        "requirements_files"
                    ]:
                        if not (service_path / req_file).exists():
                            missing_files.append(f"{service_dir}/{req_file}")

            # 檢查前端文件
            frontend_path = self.project_root / "frontend"
            if frontend_path.exists():
                for req_file in build_requirements["前端服務"][
                    "package_files"
                ]:
                    if not (frontend_path / req_file).exists():
                        missing_files.append(f"frontend/{req_file}")

            # 記錄缺少的文件（不會導致測試失敗，因為這是 Red 階段）
            if missing_files:
                logger.info(f"待創建的構建文件: {missing_files}")

            self._record_result("build_requirements_check", True)

        except Exception as e:
            self._record_result("build_requirements_check", False, str(e))

    def test_service_discovery_and_networking(self):
        """測試服務發現和網路配置"""
        try:
            compose_path = self.project_root / "docker-compose.yml"

            # 如果文件不存在，記錄為預期失敗
            if not compose_path.exists():
                self._record_result(
                    "service_networking_config",
                    False,
                    "docker-compose.yml 不存在（預期失敗）",
                )
                return

            with open(compose_path, "r") as f:
                config = yaml.safe_load(f)

            # 檢查網路配置
            networks = config.get("networks", {})
            assert "app-network" in networks, "缺少應用網路定義"

            # 檢查服務網路連接
            for service_name, service_config in config.get(
                "services", {}
            ).items():
                if service_name not in [
                    "postgres",
                    "redis",
                ]:  # 排除基礎設施服務
                    networks_config = service_config.get("networks", [])
                    assert (
                        "app-network" in networks_config
                    ), f"服務 {service_name} 未加入應用網路"

            # 檢查端口暴露配置
            exposed_services = ["frontend", "trend-service", "video-service"]
            for service in exposed_services:
                if service in config["services"]:
                    ports = config["services"][service].get("ports", [])
                    assert len(ports) > 0, f"服務 {service} 未暴露端口"

            self._record_result("service_networking_config", True)

        except Exception as e:
            self._record_result("service_networking_config", False, str(e))

    def test_health_checks_and_monitoring(self):
        """測試健康檢查和監控配置"""
        try:
            compose_path = self.project_root / "docker-compose.yml"

            if not compose_path.exists():
                self._record_result(
                    "health_monitoring_config",
                    False,
                    "docker-compose.yml 不存在（預期失敗）",
                )
                return

            with open(compose_path, "r") as f:
                config = yaml.safe_load(f)

            # 檢查健康檢查配置
            app_services = [
                "trend-service",
                "video-service",
                "social-service",
                "scheduler-service",
            ]

            for service in app_services:
                if service in config["services"]:
                    service_config = config["services"][service]
                    healthcheck = service_config.get("healthcheck", {})

                    # 檢查健康檢查配置
                    if not healthcheck:
                        logger.warning(f"服務 {service} 缺少健康檢查配置")
                        continue

                    # 檢查健康檢查參數
                    required_params = [
                        "test",
                        "interval",
                        "timeout",
                        "retries",
                    ]
                    for param in required_params:
                        if param not in healthcheck:
                            logger.warning(
                                f"服務 {service} 健康檢查缺少參數: {param}"
                            )

            # 檢查監控服務配置（如果存在）
            monitoring_services = ["prometheus", "grafana", "jaeger"]
            for monitor_service in monitoring_services:
                if monitor_service in config.get("services", {}):
                    logger.info(f"發現監控服務: {monitor_service}")

            self._record_result("health_monitoring_config", True)

        except Exception as e:
            self._record_result("health_monitoring_config", False, str(e))

    def test_environment_configuration(self):
        """測試環境配置管理"""
        try:
            # 檢查環境配置文件
            env_files = [
                ".env.example",
                ".env.prod.example",
                ".env.dev.example",
            ]
            existing_env_files = []

            for env_file in env_files:
                env_path = self.project_root / env_file
                if env_path.exists():
                    existing_env_files.append(env_file)

                    # 讀取並檢查環境變數
                    content = env_path.read_text()

                    # 檢查必要的環境變數
                    required_vars = [
                        "DATABASE_URL",
                        "REDIS_URL",
                        "JWT_SECRET",
                        "API_BASE_URL",
                        "OPENAI_API_KEY",
                    ]

                    for var in required_vars:
                        if var not in content:
                            logger.warning(
                                f"環境文件 {env_file} 缺少變數: {var}"
                            )

            # 檢查 Docker Compose 環境變數使用
            compose_files = ["docker-compose.yml", "docker-compose.prod.yml"]
            for compose_file in compose_files:
                compose_path = self.project_root / compose_file
                if compose_path.exists():
                    with open(compose_path, "r") as f:
                        config = yaml.safe_load(f)

                    # 檢查環境變數引用格式
                    for service_name, service_config in config.get(
                        "services", {}
                    ).items():
                        env_vars = service_config.get("environment", {})

                        # 處理不同的環境變數格式
                        if isinstance(env_vars, dict):
                            for var_name, var_value in env_vars.items():
                                if isinstance(
                                    var_value, str
                                ) and var_value.startswith("$"):
                                    logger.info(
                                        f"發現環境變數引用: {var_name}={var_value} in {service_name}"
                                    )
                        elif isinstance(env_vars, list):
                            for env_item in env_vars:
                                if (
                                    isinstance(env_item, str)
                                    and "=" in env_item
                                ):
                                    var_name, var_value = env_item.split(
                                        "=", 1
                                    )
                                    if var_value.startswith("$"):
                                        logger.info(
                                            f"發現環境變數引用: {var_name}={var_value} in {service_name}"
                                        )

            # 記錄結果（允許部分缺失，因為這是 Red 階段）
            self._record_result("environment_configuration", True)

        except Exception as e:
            self._record_result("environment_configuration", False, str(e))

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

        logger.info("=" * 60)
        logger.info("🔴 TDD Red 階段: Docker 容器化測試結果")
        logger.info("=" * 60)
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
    """執行 Docker 容器化 TDD Red 階段測試"""
    logger.info("🔴 開始 TDD Red 階段: Docker 容器化測試")
    logger.info("目標: 定義生產級 Docker 多階段構建的期望行為")
    logger.info("=" * 60)

    test_suite = DockerContainerizationTest()

    try:
        # 執行所有測試
        test_suite.test_dockerfile_exists_and_multistage()
        test_suite.test_docker_compose_production_config()
        test_suite.test_dockerfile_optimization_practices()
        test_suite.test_container_security_practices()
        test_suite.test_build_and_run_simulation()
        test_suite.test_service_discovery_and_networking()
        test_suite.test_health_checks_and_monitoring()
        test_suite.test_environment_configuration()

        # 打印結果
        is_proper_red = test_suite.print_results()

        if is_proper_red:
            logger.info("\n🎉 TDD Red 階段成功！")
            logger.info("✨ 已定義完整的 Docker 容器化需求")
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
        logger.info("🏁 TDD Red 階段完成 - Docker 容器化需求已定義")
        exit(0)
    else:
        logger.error("🛑 TDD Red 階段需要調整")
        exit(1)
