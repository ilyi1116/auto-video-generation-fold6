#!/usr/bin/env python3
"""
實際部署測試驗證腳本
Phase 4-6: 完整部署流程測試和驗證
"""

import asyncio
import aiohttp
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List
import argparse
from datetime import datetime


class DeploymentTester:
    """部署測試器"""

    def __init__(self, project_root: Path, environment: str = "development"):
        self.project_root = project_root
        self.environment = environment
        self.test_results = []
        self.services = {
            "api-gateway": "http://localhost:8000",
            "auth-service": "http://localhost:8001",
            "video-service": "http://localhost:8004",
            "frontend": "http://localhost:3000",
        }

    async def test_service_health(
        self, service_name: str, base_url: str
    ) -> Dict:
        """測試服務健康狀態"""
        health_endpoint = (
            f"{base_url}/health" if service_name != "frontend" else base_url
        )

        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(health_endpoint) as response:
                    status_code = response.status
                    response_text = await response.text()

                    return {
                        "service": service_name,
                        "status": (
                            "healthy" if status_code == 200 else "unhealthy"
                        ),
                        "status_code": status_code,
                        "response": response_text[:200],
                        "response_time_ms": 0,  # 將在外部計算
                    }

        except Exception as e:
            return {
                "service": service_name,
                "status": "error",
                "error": str(e),
                "status_code": 0,
                "response": "",
                "response_time_ms": 0,
            }

    async def test_api_endpoints(self) -> List[Dict]:
        """測試 API 端點"""
        test_cases = [
            {
                "name": "API Gateway Health Check",
                "method": "GET",
                "url": f"{self.services['api-gateway']}/health",
                "expected_status": 200,
            },
            {
                "name": "Auth Service Health Check",
                "method": "GET",
                "url": f"{self.services['auth-service']}/health",
                "expected_status": 200,
            },
            {
                "name": "Video Service Health Check",
                "method": "GET",
                "url": f"{self.services['video-service']}/health",
                "expected_status": 200,
            },
            {
                "name": "API Documentation",
                "method": "GET",
                "url": f"{self.services['api-gateway']}/docs",
                "expected_status": 200,
            },
        ]

        results = []
        timeout = aiohttp.ClientTimeout(total=15)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            for test_case in test_cases:
                start_time = time.time()

                try:
                    if test_case["method"] == "GET":
                        async with session.get(test_case["url"]) as response:
                            status_code = response.status
                            response_text = await response.text()
                    elif test_case["method"] == "POST":
                        async with session.post(
                            test_case["url"], json=test_case.get("data", {})
                        ) as response:
                            status_code = response.status
                            response_text = await response.text()

                    response_time = (time.time() - start_time) * 1000

                    results.append(
                        {
                            "test_name": test_case["name"],
                            "status": (
                                "pass"
                                if status_code == test_case["expected_status"]
                                else "fail"
                            ),
                            "status_code": status_code,
                            "expected_status": test_case["expected_status"],
                            "response_time_ms": round(response_time, 2),
                            "response": (
                                response_text[:100] + "..."
                                if len(response_text) > 100
                                else response_text
                            ),
                        }
                    )

                except Exception as e:
                    results.append(
                        {
                            "test_name": test_case["name"],
                            "status": "error",
                            "error": str(e),
                            "response_time_ms": (time.time() - start_time)
                            * 1000,
                        }
                    )

        return results

    def test_docker_services(self) -> Dict:
        """測試 Docker 服務狀態"""
        try:
            # 檢查 Docker 是否運行
            result = subprocess.run(
                ["docker", "info"], capture_output=True, text=True
            )
            if result.returncode != 0:
                return {"status": "error", "message": "Docker is not running"}

            # 獲取容器狀態
            result = subprocess.run(
                ["docker", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
            )

            containers = []
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n"):
                    container_info = json.loads(line)
                    containers.append(
                        {
                            "name": container_info.get("Names", ""),
                            "image": container_info.get("Image", ""),
                            "status": container_info.get("Status", ""),
                            "ports": container_info.get("Ports", ""),
                        }
                    )

            # 檢查 Docker Compose 服務
            compose_result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.unified.yml", "ps"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            return {
                "status": "success",
                "total_containers": len(containers),
                "containers": containers,
                "compose_status": (
                    compose_result.stdout
                    if compose_result.returncode == 0
                    else "Error getting compose status"
                ),
            }

        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "message": f"Docker command failed: {e}",
            }
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {e}"}

    def test_database_connectivity(self) -> Dict:
        """測試資料庫連接"""
        results = {
            "postgresql": {"status": "unknown"},
            "redis": {"status": "unknown"},
        }

        # 測試 PostgreSQL
        try:
            result = subprocess.run(
                ["pg_isready", "-h", "localhost", "-p", "5432"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            results["postgresql"] = {
                "status": (
                    "available" if result.returncode == 0 else "unavailable"
                ),
                "message": result.stdout.strip() or result.stderr.strip(),
            }
        except Exception as e:
            results["postgresql"] = {"status": "error", "message": str(e)}

        # 測試 Redis
        try:
            result = subprocess.run(
                ["redis-cli", "-h", "localhost", "-p", "6379", "ping"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            results["redis"] = {
                "status": (
                    "available" if "PONG" in result.stdout else "unavailable"
                ),
                "message": result.stdout.strip(),
            }
        except Exception as e:
            results["redis"] = {"status": "error", "message": str(e)}

        return results

    def test_monitoring_services(self) -> Dict:
        """測試監控服務"""
        monitoring_services = {
            "prometheus": "http://localhost:9090/-/healthy",
            "grafana": "http://localhost:3001/api/health",
            "alertmanager": "http://localhost:9093/-/healthy",
        }

        results = {}

        for service_name, health_url in monitoring_services.items():
            try:
                result = subprocess.run(
                    ["curl", "-f", "-s", "-m", "5", health_url],
                    capture_output=True,
                    text=True,
                )

                results[service_name] = {
                    "status": (
                        "available"
                        if result.returncode == 0
                        else "unavailable"
                    ),
                    "response": (
                        result.stdout[:100]
                        if result.stdout
                        else result.stderr[:100]
                    ),
                }
            except Exception as e:
                results[service_name] = {"status": "error", "message": str(e)}

        return results

    async def run_load_test(
        self, target_url: str, duration_seconds: int = 30
    ) -> Dict:
        """運行簡單的負載測試"""
        print(f"🚀 開始負載測試: {target_url} ({duration_seconds}秒)")

        results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": [],
        }

        start_time = time.time()

        # 創建並發請求任務
        async def make_request(session):
            try:
                request_start = time.time()
                async with session.get(target_url) as response:
                    response_time = (time.time() - request_start) * 1000
                    results["response_times"].append(response_time)
                    results["total_requests"] += 1

                    if response.status == 200:
                        results["successful_requests"] += 1
                    else:
                        results["failed_requests"] += 1

            except Exception as e:
                results["failed_requests"] += 1
                results["errors"].append(str(e))

        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            while time.time() - start_time < duration_seconds:
                # 每秒發送 10 個並發請求
                batch_tasks = [make_request(session) for _ in range(10)]
                await asyncio.gather(*batch_tasks, return_exceptions=True)
                await asyncio.sleep(0.1)  # 100ms 間隔

        # 計算統計資訊
        if results["response_times"]:
            results["avg_response_time"] = sum(
                results["response_times"]
            ) / len(results["response_times"])
            results["max_response_time"] = max(results["response_times"])
            results["min_response_time"] = min(results["response_times"])

        results["requests_per_second"] = (
            results["total_requests"] / duration_seconds
        )
        results["success_rate"] = (
            results["successful_requests"] / max(results["total_requests"], 1)
        ) * 100

        return results

    async def run_comprehensive_test(self) -> Dict:
        """運行綜合測試"""
        print("🧪 開始綜合部署測試...")

        test_results = {
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "tests": {},
        }

        # 1. Docker 服務測試
        print("📦 測試 Docker 服務...")
        test_results["tests"]["docker"] = self.test_docker_services()

        # 2. 資料庫連接測試
        print("🗄️ 測試資料庫連接...")
        test_results["tests"]["databases"] = self.test_database_connectivity()

        # 3. 服務健康檢查
        print("🏥 測試服務健康狀態...")
        health_results = []
        for service_name, base_url in self.services.items():
            health_result = await self.test_service_health(
                service_name, base_url
            )
            health_results.append(health_result)
        test_results["tests"]["service_health"] = health_results

        # 4. API 端點測試
        print("🔗 測試 API 端點...")
        test_results["tests"][
            "api_endpoints"
        ] = await self.test_api_endpoints()

        # 5. 監控服務測試
        print("📊 測試監控服務...")
        test_results["tests"]["monitoring"] = self.test_monitoring_services()

        # 6. 負載測試 (可選)
        if self.services.get("api-gateway"):
            print("⚡ 運行負載測試...")
            load_test_url = f"{self.services['api-gateway']}/health"
            test_results["tests"]["load_test"] = await self.run_load_test(
                load_test_url, 15
            )

        # 計算整體測試結果
        test_results["summary"] = self._calculate_test_summary(
            test_results["tests"]
        )

        return test_results

    def _calculate_test_summary(self, tests: Dict) -> Dict:
        """計算測試總結"""
        summary = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "error_tests": 0,
            "overall_status": "unknown",
        }

        # 計算服務健康檢查
        if "service_health" in tests:
            for health_test in tests["service_health"]:
                summary["total_tests"] += 1
                if health_test["status"] == "healthy":
                    summary["passed_tests"] += 1
                elif health_test["status"] == "error":
                    summary["error_tests"] += 1
                else:
                    summary["failed_tests"] += 1

        # 計算 API 端點測試
        if "api_endpoints" in tests:
            for api_test in tests["api_endpoints"]:
                summary["total_tests"] += 1
                if api_test["status"] == "pass":
                    summary["passed_tests"] += 1
                elif api_test["status"] == "error":
                    summary["error_tests"] += 1
                else:
                    summary["failed_tests"] += 1

        # 計算整體狀態
        if summary["total_tests"] == 0:
            summary["overall_status"] = "no_tests"
        elif summary["failed_tests"] == 0 and summary["error_tests"] == 0:
            summary["overall_status"] = "all_passed"
        elif (
            summary["passed_tests"]
            > summary["failed_tests"] + summary["error_tests"]
        ):
            summary["overall_status"] = "mostly_passed"
        else:
            summary["overall_status"] = "failed"

        return summary

    def generate_report(self, test_results: Dict) -> str:
        """生成測試報告"""
        report = [
            "# 部署測試報告",
            f"**測試時間**: {test_results['timestamp']}",
            f"**測試環境**: {test_results['environment']}",
            "",
        ]

        # 測試總結
        summary = test_results["summary"]
        report.extend(
            [
                "## 測試總結",
                f"- **總測試數**: {summary['total_tests']}",
                f"- **通過**: {summary['passed_tests']} ✅",
                f"- **失敗**: {summary['failed_tests']} ❌",
                f"- **錯誤**: {summary['error_tests']} ⚠️",
                f"- **整體狀態**: {summary['overall_status']}",
                "",
            ]
        )

        # Docker 服務狀態
        docker_tests = test_results["tests"].get("docker", {})
        if docker_tests:
            report.extend(
                [
                    "## Docker 服務狀態",
                    f"- **狀態**: {docker_tests.get('status', 'unknown')}",
                    f"- **運行中容器**: {docker_tests.get('total_containers', 0)}",
                    "",
                ]
            )

            if docker_tests.get("containers"):
                report.append("### 容器列表")
                report.append("| 名稱 | 映像 | 狀態 |")
                report.append("|------|------|------|")
                for container in docker_tests["containers"][:10]:
                    report.append(
                        f"| {container['name']} | {container['image']} | {container['status']} |"
                    )
                report.append("")

        # 資料庫連接狀態
        db_tests = test_results["tests"].get("databases", {})
        if db_tests:
            report.extend(
                [
                    "## 資料庫連接狀態",
                    f"- **PostgreSQL**: {db_tests.get('postgresql', {}).get('status', 'unknown')} "
                    f"{' ✅' if db_tests.get('postgresql', {}).get('status') == 'available' else ' ❌'}",
                    f"- **Redis**: {db_tests.get('redis', {}).get('status', 'unknown')} "
                    f"{' ✅' if db_tests.get('redis', {}).get('status') == 'available' else ' ❌'}",
                    "",
                ]
            )

        # 服務健康檢查
        health_tests = test_results["tests"].get("service_health", [])
        if health_tests:
            report.extend(
                [
                    "## 服務健康檢查",
                    "| 服務 | 狀態 | 狀態碼 | 回應時間 |",
                    "|------|------|--------|----------|",
                ]
            )

            for health_test in health_tests:
                status_emoji = (
                    "✅" if health_test["status"] == "healthy" else "❌"
                )
                report.append(
                    f"| {health_test['service']} | {health_test['status']} {status_emoji} | "
                    f"{health_test.get('status_code', 'N/A')} | {health_test.get('response_time_ms', 0):.1f}ms |"
                )
            report.append("")

        # API 端點測試
        api_tests = test_results["tests"].get("api_endpoints", [])
        if api_tests:
            report.extend(
                [
                    "## API 端點測試",
                    "| 測試名稱 | 狀態 | 狀態碼 | 預期狀態碼 | 回應時間 |",
                    "|----------|------|--------|------------|----------|",
                ]
            )

            for api_test in api_tests:
                status_emoji = "✅" if api_test["status"] == "pass" else "❌"
                report.append(
                    f"| {api_test['test_name']} | {api_test['status']} {status_emoji} | "
                    f"{api_test.get('status_code', 'N/A')} | {api_test.get('expected_status', 'N/A')} | "
                    f"{api_test.get('response_time_ms', 0):.1f}ms |"
                )
            report.append("")

        # 負載測試結果
        load_test = test_results["tests"].get("load_test")
        if load_test:
            report.extend(
                [
                    "## 負載測試結果",
                    f"- **總請求數**: {load_test['total_requests']}",
                    f"- **成功請求**: {load_test['successful_requests']}",
                    f"- **失敗請求**: {load_test['failed_requests']}",
                    f"- **成功率**: {load_test.get('success_rate', 0):.1f}%",
                    f"- **請求/秒**: {load_test.get('requests_per_second', 0):.1f}",
                    f"- **平均回應時間**: {load_test.get('avg_response_time', 0):.1f}ms",
                    f"- **最大回應時間**: {load_test.get('max_response_time', 0):.1f}ms",
                    "",
                ]
            )

        # 建議
        report.extend(
            ["## 建議", self._generate_recommendations(test_results), ""]
        )

        return "\n".join(report)

    def _generate_recommendations(self, test_results: Dict) -> str:
        """生成建議"""
        recommendations = []

        summary = test_results["summary"]

        if summary["overall_status"] == "all_passed":
            recommendations.append("🎉 所有測試通過！系統部署成功。")
        elif summary["overall_status"] == "mostly_passed":
            recommendations.append("⚠️ 大部分測試通過，但有部分問題需要關注。")
        elif summary["overall_status"] == "failed":
            recommendations.append("❌ 多項測試失敗，需要檢查部署配置。")

        # 基於測試結果的具體建議
        docker_tests = test_results["tests"].get("docker", {})
        if docker_tests.get("status") != "success":
            recommendations.append("- 檢查 Docker 服務是否正常運行")

        db_tests = test_results["tests"].get("databases", {})
        if db_tests.get("postgresql", {}).get("status") != "available":
            recommendations.append("- 檢查 PostgreSQL 資料庫連接")
        if db_tests.get("redis", {}).get("status") != "available":
            recommendations.append("- 檢查 Redis 連接")

        load_test = test_results["tests"].get("load_test")
        if load_test and load_test.get("success_rate", 0) < 95:
            recommendations.append("- 負載測試成功率偏低，檢查服務穩定性")

        recommendations.extend(
            [
                "- 定期執行部署測試確保系統穩定性",
                "- 監控服務日誌排查問題",
                "- 設置自動化健康檢查",
            ]
        )

        return "\n".join(recommendations)


async def main():
    parser = argparse.ArgumentParser(description="部署測試工具")
    parser.add_argument(
        "--env",
        help="測試環境",
        default="development",
        choices=["development", "staging", "production"],
    )
    parser.add_argument(
        "--output",
        help="輸出報告文件路徑",
        default="deployment-test-report.md",
    )
    parser.add_argument(
        "--json", help="同時輸出 JSON 格式", action="store_true"
    )
    parser.add_argument(
        "--load-test", help="是否執行負載測試", action="store_true"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    tester = DeploymentTester(project_root, args.env)

    print("🚀 部署測試工具")
    print("=" * 50)

    # 運行綜合測試
    test_results = await tester.run_comprehensive_test()

    # 生成報告
    print("📝 生成測試報告...")
    report = tester.generate_report(test_results)

    # 輸出報告
    output_path = Path(args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"📊 測試報告已生成: {output_path}")

    # 輸出 JSON 格式 (如果請求)
    if args.json:
        json_path = output_path.with_suffix(".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        print(f"📄 JSON 數據已輸出: {json_path}")

    # 檢查測試結果
    summary = test_results["summary"]
    print(
        f"\n📊 測試結果: {summary['passed_tests']}/{summary['total_tests']} 通過"
    )

    if summary["overall_status"] == "all_passed":
        print("✅ 所有測試通過！")
        return 0
    elif summary["overall_status"] == "mostly_passed":
        print("⚠️ 大部分測試通過")
        return 0
    else:
        print("❌ 測試失敗")
        return 1


if __name__ == "__main__":
    import asyncio

    sys.exit(asyncio.run(main()))
