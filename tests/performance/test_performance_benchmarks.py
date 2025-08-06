"""
Performance and Load Testing Framework
Comprehensive performance testing for video generation system
"""

import asyncio
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.shared.database import AsyncSessionLocal
from src.shared.services import ServiceClient, ServiceRegistry


@dataclass
class PerformanceMetrics:
    """Performance metrics container"""

    response_times: List[float] = field(default_factory=list)
    success_count: int = 0
    error_count: int = 0
    total_requests: int = 0
    start_time: float = 0
    end_time: float = 0

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.success_count / self.total_requests

    @property
    def requests_per_second(self) -> float:
        if self.duration == 0:
            return 0.0
        return self.total_requests / self.duration

    @property
    def average_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)

    @property
    def p95_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return statistics.quantiles(self.response_times, n=20)[18]  # 95th percentile

    @property
    def p99_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(0.99 * len(sorted_times))
        return sorted_times[index] if index < len(sorted_times) else sorted_times[-1]


class LoadTestClient:
    """Load testing client for API endpoints"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session: aiohttp.ClientSession = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def execute_load_test(
        self,
        endpoint: str,
        method: str = "GET",
        payload: Dict = None,
        headers: Dict = None,
        concurrent_users: int = 10,
        requests_per_user: int = 10,
        ramp_up_time: int = 5,
    ) -> PerformanceMetrics:
        """Execute load test against an endpoint"""

        metrics = PerformanceMetrics()
        metrics.start_time = time.time()

        # Calculate delay between user spawns
        user_spawn_delay = ramp_up_time / concurrent_users if concurrent_users > 0 else 0

        # Create tasks for concurrent users
        tasks = []
        for user_id in range(concurrent_users):
            # Stagger user start times
            start_delay = user_id * user_spawn_delay
            task = asyncio.create_task(
                self._user_session(
                    user_id,
                    endpoint,
                    method,
                    payload,
                    headers,
                    requests_per_user,
                    start_delay,
                    metrics,
                )
            )
            tasks.append(task)

        # Wait for all users to complete
        await asyncio.gather(*tasks, return_exceptions=True)

        metrics.end_time = time.time()
        return metrics

    async def _user_session(
        self,
        user_id: int,
        endpoint: str,
        method: str,
        payload: Dict,
        headers: Dict,
        requests_count: int,
        start_delay: float,
        metrics: PerformanceMetrics,
    ):
        """Simulate a single user session"""

        # Wait for staggered start
        await asyncio.sleep(start_delay)

        for request_id in range(requests_count):
            try:
                start_time = time.time()

                async with self.session.request(
                    method, f"{self.base_url}{endpoint}", json=payload, headers=headers
                ) as response:
                    await response.read()  # Consume response

                    end_time = time.time()
                    response_time = end_time - start_time

                    metrics.response_times.append(response_time)
                    metrics.total_requests += 1

                    if 200 <= response.status < 400:
                        metrics.success_count += 1
                    else:
                        metrics.error_count += 1

            except Exception:
                metrics.error_count += 1
                metrics.total_requests += 1
                # Add timeout as response time for failed requests
                metrics.response_times.append(30.0)

            # Small delay between requests from same user
            await asyncio.sleep(0.1)


class DatabasePerformanceTest:
    """Database performance testing"""

    @staticmethod
    async def test_database_connection_pool():
        """Test database connection pool performance"""
        metrics = PerformanceMetrics()
        metrics.start_time = time.time()

        async def single_query():
            start = time.time()
            try:
                async with AsyncSessionLocal() as db:
                    await db.execute("SELECT 1")
                    end = time.time()
                    return end - start, True
            except Exception:
                end = time.time()
                return end - start, False

        # Run concurrent database queries
        tasks = [single_query() for _ in range(50)]
        results = await asyncio.gather(*tasks)

        for response_time, success in results:
            metrics.response_times.append(response_time)
            metrics.total_requests += 1
            if success:
                metrics.success_count += 1
            else:
                metrics.error_count += 1

        metrics.end_time = time.time()
        return metrics

    @staticmethod
    async def test_complex_query_performance():
        """Test complex query performance"""
        from sqlalchemy import func, select

        from src.shared.database import User, Video, VideoAsset

        metrics = PerformanceMetrics()
        metrics.start_time = time.time()

        async def complex_query():
            start = time.time()
            try:
                async with AsyncSessionLocal() as db:
                    # Complex query with joins and aggregations
                    query = (
                        select(
                            User.id,
                            User.email,
                            func.count(Video.id).label("video_count"),
                            func.count(VideoAsset.id).label("asset_count"),
                        )
                        .outerjoin(Video, User.id == Video.user_id)
                        .outerjoin(VideoAsset, Video.id == VideoAsset.video_id)
                        .group_by(User.id, User.email)
                        .limit(100)
                    )

                    result = await db.execute(query)
                    await result.fetchall()

                    end = time.time()
                    return end - start, True
            except Exception:
                end = time.time()
                return end - start, False

        # Run multiple complex queries
        tasks = [complex_query() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        for response_time, success in results:
            metrics.response_times.append(response_time)
            metrics.total_requests += 1
            if success:
                metrics.success_count += 1
            else:
                metrics.error_count += 1

        metrics.end_time = time.time()
        return metrics


class ServiceCommunicationPerformanceTest:
    """Test service communication performance"""

    @staticmethod
    async def test_service_discovery_performance():
        """Test service discovery performance"""
        registry = ServiceRegistry()

        # Register many services
        for i in range(100):
            from src.shared.services import ServiceInstance, ServiceStatus

            instance = ServiceInstance(
                f"service-{i}", "localhost", 8000 + i, status=ServiceStatus.HEALTHY
            )
            registry.register_service(instance)

        metrics = PerformanceMetrics()
        metrics.start_time = time.time()

        # Test service selection performance
        async def select_service():
            start = time.time()
            try:
                from src.shared.services import LoadBalancingStrategy

                instance = registry.select_instance(
                    "service-50", LoadBalancingStrategy.ROUND_ROBIN  # Middle service
                )
                end = time.time()
                return end - start, instance is not None
            except Exception:
                end = time.time()
                return end - start, False

        # Run many service selections
        tasks = [select_service() for _ in range(1000)]
        results = await asyncio.gather(*tasks)

        for response_time, success in results:
            metrics.response_times.append(response_time)
            metrics.total_requests += 1
            if success:
                metrics.success_count += 1
            else:
                metrics.error_count += 1

        metrics.end_time = time.time()
        return metrics

    @staticmethod
    async def test_service_client_performance():
        """Test service client communication performance"""
        registry = ServiceRegistry()

        # Register test service
        from src.shared.services import ServiceInstance, ServiceStatus

        test_service = ServiceInstance(
            "test-service", "localhost", 8999, status=ServiceStatus.HEALTHY
        )
        registry.register_service(test_service)

        client = ServiceClient(registry)
        metrics = PerformanceMetrics()
        metrics.start_time = time.time()

        # Mock successful HTTP calls
        mock_response_data = {"status": "ok", "timestamp": time.time()}

        with patch("aiohttp.ClientSession.request") as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_request.return_value.__aenter__.return_value = mock_response

            async def service_call():
                start = time.time()
                try:
                    await client.get("test-service", "/health")
                    end = time.time()
                    return end - start, True
                except Exception:
                    end = time.time()
                    return end - start, False

            async with client:
                tasks = [service_call() for _ in range(100)]
                results = await asyncio.gather(*tasks)

        for response_time, success in results:
            metrics.response_times.append(response_time)
            metrics.total_requests += 1
            if success:
                metrics.success_count += 1
            else:
                metrics.error_count += 1

        metrics.end_time = time.time()
        return metrics


class PerformanceTestSuite:
    """Comprehensive performance test suite"""

    @pytest.mark.asyncio
    async def test_api_gateway_performance(self):
        """Test API Gateway performance under load"""
        async with LoadTestClient() as client:
            # Test health endpoint performance
            health_metrics = await client.execute_load_test(
                endpoint="/health", concurrent_users=20, requests_per_user=50, ramp_up_time=10
            )

            assert health_metrics.success_rate >= 0.95
            assert health_metrics.average_response_time <= 1.0
            assert health_metrics.p95_response_time <= 2.0

            print(f"Health Endpoint Performance:")
            print(f"  Success Rate: {health_metrics.success_rate:.2%}")
            print(f"  Average Response Time: {health_metrics.average_response_time:.3f}s")
            print(f"  95th Percentile: {health_metrics.p95_response_time:.3f}s")
            print(f"  Requests/Second: {health_metrics.requests_per_second:.2f}")

    @pytest.mark.asyncio
    async def test_video_creation_performance(self):
        """Test video creation endpoint performance"""

        # Mock authentication
        mock_headers = {"Authorization": "Bearer test_token"}

        video_payload = {
            "title": "Performance Test Video",
            "theme": "testing",
            "duration": 30,
            "target_platform": "youtube",
        }

        async with LoadTestClient() as client:
            with patch("src.services.video_service.auth.verify_token", return_value=123):
                metrics = await client.execute_load_test(
                    endpoint="/api/v1/video/generate",
                    method="POST",
                    payload=video_payload,
                    headers=mock_headers,
                    concurrent_users=5,  # Lower concurrency for complex operations
                    requests_per_user=10,
                    ramp_up_time=5,
                )

                assert metrics.success_rate >= 0.90
                assert metrics.average_response_time <= 10.0

                print(f"Video Creation Performance:")
                print(f"  Success Rate: {metrics.success_rate:.2%}")
                print(f"  Average Response Time: {metrics.average_response_time:.3f}s")
                print(f"  95th Percentile: {metrics.p95_response_time:.3f}s")

    @pytest.mark.asyncio
    async def test_database_performance(self):
        """Test database performance"""

        # Connection pool performance
        pool_metrics = await DatabasePerformanceTest.test_database_connection_pool()

        assert pool_metrics.success_rate >= 0.95
        assert pool_metrics.average_response_time <= 0.1

        print(f"Database Connection Pool Performance:")
        print(f"  Success Rate: {pool_metrics.success_rate:.2%}")
        print(f"  Average Query Time: {pool_metrics.average_response_time:.3f}s")

        # Complex query performance
        query_metrics = await DatabasePerformanceTest.test_complex_query_performance()

        assert query_metrics.success_rate >= 0.90
        assert query_metrics.average_response_time <= 1.0

        print(f"Complex Query Performance:")
        print(f"  Success Rate: {query_metrics.success_rate:.2%}")
        print(f"  Average Query Time: {query_metrics.average_response_time:.3f}s")

    @pytest.mark.asyncio
    async def test_service_communication_performance(self):
        """Test service communication performance"""

        # Service discovery performance
        discovery_metrics = (
            await ServiceCommunicationPerformanceTest.test_service_discovery_performance()
        )

        assert discovery_metrics.success_rate >= 0.99
        assert discovery_metrics.average_response_time <= 0.001

        print(f"Service Discovery Performance:")
        print(f"  Success Rate: {discovery_metrics.success_rate:.2%}")
        print(f"  Average Selection Time: {discovery_metrics.average_response_time:.6f}s")

        # Service client performance
        client_metrics = await ServiceCommunicationPerformanceTest.test_service_client_performance()

        assert client_metrics.success_rate >= 0.95
        assert client_metrics.average_response_time <= 0.1

        print(f"Service Client Performance:")
        print(f"  Success Rate: {client_metrics.success_rate:.2%}")
        print(f"  Average Call Time: {client_metrics.average_response_time:.3f}s")

    @pytest.mark.asyncio
    async def test_memory_usage_during_load(self):
        """Test memory usage during load testing"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run load test
        async with LoadTestClient() as client:
            await client.execute_load_test(
                endpoint="/health", concurrent_users=50, requests_per_user=100, ramp_up_time=5
            )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        print(f"Memory Usage:")
        print(f"  Initial: {initial_memory:.2f} MB")
        print(f"  Final: {final_memory:.2f} MB")
        print(f"  Increase: {memory_increase:.2f} MB")

        # Memory increase should be reasonable
        assert memory_increase <= 100  # Less than 100MB increase

    @pytest.mark.asyncio
    async def test_concurrent_video_generation_performance(self):
        """Test performance with concurrent video generation"""

        # Simulate multiple users creating videos simultaneously
        mock_headers = {"Authorization": "Bearer test_token"}

        video_payloads = [
            {
                "title": f"Concurrent Video {i}",
                "theme": f"theme_{i}",
                "duration": 30,
                "target_platform": "youtube",
            }
            for i in range(10)
        ]

        metrics = PerformanceMetrics()
        metrics.start_time = time.time()

        async with LoadTestClient() as client:
            with patch("src.services.video_service.auth.verify_token", return_value=123):

                async def create_video(payload):
                    start = time.time()
                    try:
                        async with client.session.post(
                            f"{client.base_url}/api/v1/video/generate",
                            json=payload,
                            headers=mock_headers,
                        ) as response:
                            await response.json()
                            end = time.time()
                            return end - start, response.status < 400
                    except Exception:
                        end = time.time()
                        return end - start, False

                tasks = [create_video(payload) for payload in video_payloads]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in results:
                    if isinstance(result, tuple):
                        response_time, success = result
                        metrics.response_times.append(response_time)
                        metrics.total_requests += 1
                        if success:
                            metrics.success_count += 1
                        else:
                            metrics.error_count += 1

        metrics.end_time = time.time()

        print(f"Concurrent Video Generation Performance:")
        print(f"  Success Rate: {metrics.success_rate:.2%}")
        print(f"  Average Response Time: {metrics.average_response_time:.3f}s")
        print(f"  Total Requests: {metrics.total_requests}")

        assert metrics.success_rate >= 0.80  # 80% success rate for concurrent operations


class StressTestSuite:
    """Stress testing to find system limits"""

    @pytest.mark.asyncio
    async def test_breaking_point_analysis(self):
        """Find the breaking point of the system"""

        async with LoadTestClient() as client:
            # Gradually increase load until system breaks
            concurrent_users_levels = [10, 25, 50, 100, 200]
            results = {}

            for users in concurrent_users_levels:
                print(f"Testing with {users} concurrent users...")

                metrics = await client.execute_load_test(
                    endpoint="/health",
                    concurrent_users=users,
                    requests_per_user=20,
                    ramp_up_time=min(users // 10, 10),
                )

                results[users] = {
                    "success_rate": metrics.success_rate,
                    "avg_response_time": metrics.average_response_time,
                    "p95_response_time": metrics.p95_response_time,
                    "requests_per_second": metrics.requests_per_second,
                }

                # If success rate drops below 90%, we've found the breaking point
                if metrics.success_rate < 0.90:
                    print(f"Breaking point found at {users} concurrent users")
                    break

                # Small delay between tests
                await asyncio.sleep(2)

            print("\nStress Test Results:")
            for users, data in results.items():
                print(
                    f"  {users} users: "
                    f"Success={data['success_rate']:.2%}, "
                    f"AvgTime={data['avg_response_time']:.3f}s, "
                    f"RPS={data['requests_per_second']:.2f}"
                )


if __name__ == "__main__":
    # Run specific performance tests
    pytest.main([__file__, "-v", "-s"])
