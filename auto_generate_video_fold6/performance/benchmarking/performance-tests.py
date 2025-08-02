"""
Auto Video System 效能基準測試
包含 API、資料庫、快取和系統整體效能測試
"""

import asyncio
import json
import logging
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import aiohttp
import matplotlib.pyplot as plt
import numpy as np
import psutil
import pytest

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """基準測試結果"""

    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    duration_seconds: float
    requests_per_second: float
    average_response_time: float
    min_response_time: float
    max_response_time: float
    percentile_95: float
    percentile_99: float
    error_rate: float
    timestamp: datetime


class PerformanceBenchmark:
    """效能基準測試器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[BenchmarkResult] = []

    async def run_api_load_test(
        self,
        endpoint: str,
        concurrent_users: int = 10,
        test_duration: int = 60,
        headers: Dict = None,
    ) -> BenchmarkResult:
        """API 負載測試"""
        print(f"🚀 Running API load test: {endpoint}")
        print(f"   Concurrent users: {concurrent_users}")
        print(f"   Test duration: {test_duration}s")

        start_time = time.time()
        end_time = start_time + test_duration

        # 結果收集
        response_times = []
        successful_requests = 0
        failed_requests = 0

        async def make_request(session: aiohttp.ClientSession):
            """發送單個請求"""
            nonlocal successful_requests, failed_requests

            request_start = time.time()
            try:
                async with session.get(
                    f"{self.base_url}{endpoint}", headers=headers
                ) as response:
                    await response.text()
                    request_time = time.time() - request_start
                    response_times.append(request_time)

                    if response.status == 200:
                        successful_requests += 1
                    else:
                        failed_requests += 1

            except Exception as e:
                failed_requests += 1
                logger.error(f"Request failed: {e}")

        async def user_simulation(user_id: int):
            """模擬單個用戶的請求"""
            async with aiohttp.ClientSession() as session:
                while time.time() < end_time:
                    await make_request(session)
                    # 模擬用戶思考時間
                    await asyncio.sleep(0.1)

        # 啟動並發用戶
        tasks = [user_simulation(i) for i in range(concurrent_users)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # 計算統計結果
        total_time = time.time() - start_time
        total_requests = successful_requests + failed_requests

        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            percentile_95 = np.percentile(response_times, 95)
            percentile_99 = np.percentile(response_times, 99)
        else:
            avg_response_time = 0
            min_response_time = 0
            max_response_time = 0
            percentile_95 = 0
            percentile_99 = 0

        result = BenchmarkResult(
            test_name=f"API Load Test - {endpoint}",
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            duration_seconds=total_time,
            requests_per_second=(
                total_requests / total_time if total_time > 0 else 0
            ),
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            percentile_95=percentile_95,
            percentile_99=percentile_99,
            error_rate=(
                failed_requests / total_requests if total_requests > 0 else 0
            ),
            timestamp=datetime.now(),
        )

        self.results.append(result)
        self._print_result(result)
        return result

    async def run_database_benchmark(self, db_connection) -> BenchmarkResult:
        """資料庫效能基準測試"""
        print("🗃️ Running database benchmark...")

        start_time = time.time()
        query_times = []
        successful_queries = 0
        failed_queries = 0

        # 測試查詢集合
        test_queries = [
            "SELECT COUNT(*) FROM auth_users",
            "SELECT * FROM auth_users WHERE is_active = true LIMIT 10",
            "SELECT * FROM audio_files ORDER BY created_at DESC LIMIT 20",
            "SELECT u.email, COUNT(af.id) FROM auth_users u LEFT JOIN audio_files af ON u.id = af.user_id GROUP BY u.id, u.email LIMIT 10",
            "SELECT * FROM training_jobs WHERE status = 'completed' ORDER BY created_at DESC LIMIT 15",
        ]

        # 執行查詢基準測試
        for _ in range(100):  # 每個查詢執行100次
            for query in test_queries:
                query_start = time.time()
                try:
                    cursor = db_connection.cursor()
                    cursor.execute(query)
                    cursor.fetchall()
                    cursor.close()

                    query_time = time.time() - query_start
                    query_times.append(query_time)
                    successful_queries += 1

                except Exception as e:
                    failed_queries += 1
                    logger.error(f"Database query failed: {e}")

        total_time = time.time() - start_time
        total_queries = successful_queries + failed_queries

        result = BenchmarkResult(
            test_name="Database Benchmark",
            total_requests=total_queries,
            successful_requests=successful_queries,
            failed_requests=failed_queries,
            duration_seconds=total_time,
            requests_per_second=total_queries / total_time,
            average_response_time=(
                statistics.mean(query_times) if query_times else 0
            ),
            min_response_time=min(query_times) if query_times else 0,
            max_response_time=max(query_times) if query_times else 0,
            percentile_95=np.percentile(query_times, 95) if query_times else 0,
            percentile_99=np.percentile(query_times, 99) if query_times else 0,
            error_rate=(
                failed_queries / total_queries if total_queries > 0 else 0
            ),
            timestamp=datetime.now(),
        )

        self.results.append(result)
        self._print_result(result)
        return result

    async def run_cache_benchmark(self, redis_client) -> BenchmarkResult:
        """快取效能基準測試"""
        print("🔴 Running cache benchmark...")

        start_time = time.time()
        operation_times = []
        successful_operations = 0
        failed_operations = 0

        # 測試數據
        test_data = {f"key_{i}": f"value_{i}" * 100 for i in range(1000)}

        # SET 操作測試
        for key, value in test_data.items():
            op_start = time.time()
            try:
                await redis_client.set(key, value, ex=3600)
                op_time = time.time() - op_start
                operation_times.append(op_time)
                successful_operations += 1
            except Exception as e:
                failed_operations += 1
                logger.error(f"Redis SET failed: {e}")

        # GET 操作測試
        for key in test_data.keys():
            op_start = time.time()
            try:
                await redis_client.get(key)
                op_time = time.time() - op_start
                operation_times.append(op_time)
                successful_operations += 1
            except Exception as e:
                failed_operations += 1
                logger.error(f"Redis GET failed: {e}")

        # 批次操作測試
        op_start = time.time()
        try:
            await redis_client.mget(list(test_data.keys()))
            op_time = time.time() - op_start
            operation_times.append(op_time)
            successful_operations += 1
        except Exception as e:
            failed_operations += 1
            logger.error(f"Redis MGET failed: {e}")

        total_time = time.time() - start_time
        total_operations = successful_operations + failed_operations

        result = BenchmarkResult(
            test_name="Cache Benchmark",
            total_requests=total_operations,
            successful_requests=successful_operations,
            failed_requests=failed_operations,
            duration_seconds=total_time,
            requests_per_second=total_operations / total_time,
            average_response_time=(
                statistics.mean(operation_times) if operation_times else 0
            ),
            min_response_time=min(operation_times) if operation_times else 0,
            max_response_time=max(operation_times) if operation_times else 0,
            percentile_95=(
                np.percentile(operation_times, 95) if operation_times else 0
            ),
            percentile_99=(
                np.percentile(operation_times, 99) if operation_times else 0
            ),
            error_rate=(
                failed_operations / total_operations
                if total_operations > 0
                else 0
            ),
            timestamp=datetime.now(),
        )

        self.results.append(result)
        self._print_result(result)
        return result

    def run_system_resource_benchmark(self, duration: int = 60) -> Dict:
        """系統資源基準測試"""
        print("💻 Running system resource benchmark...")

        start_time = time.time()
        end_time = start_time + duration

        cpu_usage = []
        memory_usage = []
        disk_io = []
        network_io = []

        while time.time() < end_time:
            # CPU 使用率
            cpu_usage.append(psutil.cpu_percent(interval=1))

            # 記憶體使用率
            memory = psutil.virtual_memory()
            memory_usage.append(memory.percent)

            # 磁碟 I/O
            disk_io_counters = psutil.disk_io_counters()
            if disk_io_counters:
                disk_io.append(
                    {
                        "read_bytes": disk_io_counters.read_bytes,
                        "write_bytes": disk_io_counters.write_bytes,
                    }
                )

            # 網路 I/O
            network_io_counters = psutil.net_io_counters()
            if network_io_counters:
                network_io.append(
                    {
                        "bytes_sent": network_io_counters.bytes_sent,
                        "bytes_recv": network_io_counters.bytes_recv,
                    }
                )

            time.sleep(1)

        # 計算統計結果
        system_stats = {
            "cpu": {
                "average": statistics.mean(cpu_usage) if cpu_usage else 0,
                "max": max(cpu_usage) if cpu_usage else 0,
                "min": min(cpu_usage) if cpu_usage else 0,
            },
            "memory": {
                "average": (
                    statistics.mean(memory_usage) if memory_usage else 0
                ),
                "max": max(memory_usage) if memory_usage else 0,
                "min": min(memory_usage) if memory_usage else 0,
            },
            "disk_io": {"samples": len(disk_io)},
            "network_io": {"samples": len(network_io)},
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
        }

        print("📊 System Resource Results:")
        print(f"   CPU Average: {system_stats['cpu']['average']:.2f}%")
        print(f"   Memory Average: {system_stats['memory']['average']:.2f}%")
        print(f"   Test Duration: {duration}s")

        return system_stats

    def _print_result(self, result: BenchmarkResult):
        """列印測試結果"""
        print(f"\n📊 {result.test_name} Results:")
        print(f"   Total Requests: {result.total_requests}")
        print(f"   Successful: {result.successful_requests}")
        print(f"   Failed: {result.failed_requests}")
        print(f"   Duration: {result.duration_seconds:.2f}s")
        print(f"   RPS: {result.requests_per_second:.2f}")
        print(
            f"   Avg Response Time: {result.average_response_time * 1000:.2f}ms"
        )
        print(f"   95th Percentile: {result.percentile_95 * 1000:.2f}ms")
        print(f"   99th Percentile: {result.percentile_99 * 1000:.2f}ms")
        print(f"   Error Rate: {result.error_rate * 100:.2f}%")

    def generate_report(self, output_file: str = "performance_report.json"):
        """生成效能報告"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "test_summary": {
                "total_tests": len(self.results),
                "tests_completed": len(
                    [r for r in self.results if r.error_rate < 0.05]
                ),
            },
            "results": [],
        }

        for result in self.results:
            report["results"].append(
                {
                    "test_name": result.test_name,
                    "total_requests": result.total_requests,
                    "successful_requests": result.successful_requests,
                    "failed_requests": result.failed_requests,
                    "duration_seconds": result.duration_seconds,
                    "requests_per_second": result.requests_per_second,
                    "average_response_time_ms": result.average_response_time
                    * 1000,
                    "percentile_95_ms": result.percentile_95 * 1000,
                    "percentile_99_ms": result.percentile_99 * 1000,
                    "error_rate_percent": result.error_rate * 100,
                    "timestamp": result.timestamp.isoformat(),
                }
            )

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📄 Performance report saved to: {output_file}")
        return report

    def plot_results(self, output_dir: str = "performance_plots"):
        """生成效能圖表"""
        import os

        os.makedirs(output_dir, exist_ok=True)

        if not self.results:
            print("⚠️ No results to plot")
            return

        # RPS 比較圖
        test_names = [r.test_name for r in self.results]
        rps_values = [r.requests_per_second for r in self.results]

        plt.figure(figsize=(12, 6))
        plt.bar(test_names, rps_values)
        plt.title("Requests Per Second Comparison")
        plt.xlabel("Test Name")
        plt.ylabel("Requests Per Second")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(f"{output_dir}/rps_comparison.png")
        plt.close()

        # 回應時間分佈圖
        avg_times = [r.average_response_time * 1000 for r in self.results]
        p95_times = [r.percentile_95 * 1000 for r in self.results]
        p99_times = [r.percentile_99 * 1000 for r in self.results]

        x = np.arange(len(test_names))
        width = 0.25

        plt.figure(figsize=(12, 6))
        plt.bar(x - width, avg_times, width, label="Average")
        plt.bar(x, p95_times, width, label="95th Percentile")
        plt.bar(x + width, p99_times, width, label="99th Percentile")

        plt.title("Response Time Distribution")
        plt.xlabel("Test Name")
        plt.ylabel("Response Time (ms)")
        plt.xticks(x, test_names, rotation=45, ha="right")
        plt.legend()
        plt.tight_layout()
        plt.savefig(f"{output_dir}/response_time_distribution.png")
        plt.close()

        print(f"📈 Performance plots saved to: {output_dir}/")


# 主要測試套件
class AutoVideoPerformanceTests:
    """Auto Video 系統效能測試套件"""

    def __init__(self):
        self.benchmark = PerformanceBenchmark()

    async def run_full_benchmark_suite(self):
        """執行完整的效能基準測試套件"""
        print("🏁 Starting Auto Video Performance Benchmark Suite")
        print("=" * 60)

        # API 端點測試
        api_endpoints = [
            "/api/health",
            "/api/auth/login",
            "/api/user/profile",
            "/api/audio/list",
            "/api/video/projects",
            "/api/trends/current",
        ]

        for endpoint in api_endpoints:
            try:
                await self.benchmark.run_api_load_test(
                    endpoint=endpoint,
                    concurrent_users=5,  # 減少並發用戶數
                    test_duration=30,  # 減少測試時間
                )
            except Exception as e:
                print(f"❌ Failed to test {endpoint}: {e}")

        # 系統資源測試
        self.benchmark.run_system_resource_benchmark(duration=30)

        # 生成報告
        self.benchmark.generate_report()
        self.benchmark.plot_results()

        print("\n🎉 Performance benchmark suite completed!")


# 使用範例和主程式
async def main():
    """主程式"""
    benchmark_suite = AutoVideoPerformanceTests()
    await benchmark_suite.run_full_benchmark_suite()


if __name__ == "__main__":
    # 設定日誌
    logging.basicConfig(level=logging.INFO)

    # 執行效能測試
    asyncio.run(main())
