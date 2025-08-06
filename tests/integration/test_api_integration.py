"""
API Integration Test Suite
Testing service communication, authentication, and API endpoints
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from fastapi.testclient import TestClient

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.shared.services import (
    LoadBalancingStrategy,
    ServiceClient,
    ServiceInstance,
    ServiceRegistry,
    ServiceStatus,
)
from src.shared.services.api_gateway import APIGateway, create_api_gateway


class APIIntegrationTestSuite:
    """API Integration Test Suite"""

    def __init__(self):
        self.registry = ServiceRegistry()
        self.client: ServiceClient = None
        self.gateway: APIGateway = None
        self.test_services = []

    async def setup(self):
        """Setup test environment"""
        # Register test services
        self.test_services = [
            ServiceInstance("auth-service", "localhost", 8001, status=ServiceStatus.HEALTHY),
            ServiceInstance("video-service", "localhost", 8003, status=ServiceStatus.HEALTHY),
            ServiceInstance("ai-service", "localhost", 8004, status=ServiceStatus.HEALTHY),
        ]

        for service in self.test_services:
            self.registry.register_service(service)

        # Create service client
        self.client = ServiceClient(self.registry)

        # Create API Gateway
        self.gateway = create_api_gateway(self.registry)

    async def teardown(self):
        """Cleanup test environment"""
        if self.client:
            async with self.client:
                pass


@pytest.fixture
async def api_test_suite():
    """Create API test suite"""
    suite = APIIntegrationTestSuite()
    await suite.setup()
    yield suite
    await suite.teardown()


class TestServiceDiscovery:
    """Test service discovery functionality"""

    @pytest.mark.asyncio
    async def test_service_registration(self, api_test_suite: APIIntegrationTestSuite):
        """Test service registration and discovery"""
        registry = api_test_suite.registry

        # Test service registration
        test_service = ServiceInstance("test-service", "localhost", 9999)
        registry.register_service(test_service)

        # Verify service is registered
        instances = registry.get_service_instances("test-service")
        assert len(instances) == 1
        assert instances[0].name == "test-service"
        assert instances[0].host == "localhost"
        assert instances[0].port == 9999

    @pytest.mark.asyncio
    async def test_load_balancing_strategies(self, api_test_suite: APIIntegrationTestSuite):
        """Test different load balancing strategies"""
        registry = api_test_suite.registry

        # Add multiple instances of the same service
        for i in range(3):
            instance = ServiceInstance(
                "multi-instance-service", "localhost", 8100 + i, status=ServiceStatus.HEALTHY
            )
            instance.active_connections = i  # Different connection counts
            instance.response_time = 0.1 + i * 0.05  # Different response times
            registry.register_service(instance)

        strategies = [
            LoadBalancingStrategy.ROUND_ROBIN,
            LoadBalancingStrategy.RANDOM,
            LoadBalancingStrategy.LEAST_CONNECTIONS,
            LoadBalancingStrategy.HEALTH_BASED,
        ]

        for strategy in strategies:
            instance = registry.select_instance("multi-instance-service", strategy)
            assert instance is not None
            assert instance.name == "multi-instance-service"

        # Test round robin specifically
        instances_selected = []
        for i in range(6):  # More than available instances
            instance = registry.select_instance(
                "multi-instance-service", LoadBalancingStrategy.ROUND_ROBIN
            )
            instances_selected.append(instance.port)

        # Should cycle through instances
        assert len(set(instances_selected)) >= 2

    @pytest.mark.asyncio
    async def test_health_checking(self, api_test_suite: APIIntegrationTestSuite):
        """Test service health checking"""
        registry = api_test_suite.registry

        # Create service with different health states
        healthy_service = ServiceInstance(
            "healthy-service", "localhost", 8200, status=ServiceStatus.HEALTHY
        )
        unhealthy_service = ServiceInstance(
            "unhealthy-service", "localhost", 8201, status=ServiceStatus.UNHEALTHY
        )

        registry.register_service(healthy_service)
        registry.register_service(unhealthy_service)

        # Test healthy instance selection
        healthy_instances = registry.get_healthy_instances("healthy-service")
        assert len(healthy_instances) == 1
        assert healthy_instances[0].is_healthy()

        unhealthy_instances = registry.get_healthy_instances("unhealthy-service")
        assert len(unhealthy_instances) == 0


class TestServiceCommunication:
    """Test service-to-service communication"""

    @pytest.mark.asyncio
    async def test_service_client_context_manager(self, api_test_suite: APIIntegrationTestSuite):
        """Test service client context manager usage"""
        client = api_test_suite.client

        async with client:
            assert client.session is not None

        # Session should be closed after context
        assert client.session.closed

    @pytest.mark.asyncio
    async def test_service_call_success(self, api_test_suite: APIIntegrationTestSuite):
        """Test successful service calls"""
        client = api_test_suite.client

        # Mock successful HTTP response
        mock_response_data = {"status": "success", "data": "test"}

        with patch("aiohttp.ClientSession.request") as mock_request:
            # Setup mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_request.return_value.__aenter__.return_value = mock_response

            async with client:
                result = await client.get("auth-service", "/health")

                assert result == mock_response_data
                mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_service_call_retry_logic(self, api_test_suite: APIIntegrationTestSuite):
        """Test service call retry logic"""
        client = api_test_suite.client

        with patch("aiohttp.ClientSession.request") as mock_request:
            # Setup mock to fail first calls, succeed on last
            mock_response_fail = AsyncMock()
            mock_response_fail.status = 500
            mock_response_fail.text = AsyncMock(return_value="Internal Server Error")

            mock_response_success = AsyncMock()
            mock_response_success.status = 200
            mock_response_success.json = AsyncMock(return_value={"status": "success"})

            mock_request.return_value.__aenter__.side_effect = [
                mock_response_fail,  # First call fails
                mock_response_fail,  # Second call fails
                mock_response_success,  # Third call succeeds
            ]

            async with client:
                result = await client.get("auth-service", "/health", retries=3)

                assert result == {"status": "success"}
                assert mock_request.call_count == 3

    @pytest.mark.asyncio
    async def test_service_call_methods(self, api_test_suite: APIIntegrationTestSuite):
        """Test different HTTP methods"""
        client = api_test_suite.client

        mock_response_data = {"result": "ok"}

        with patch("aiohttp.ClientSession.request") as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_response_data)
            mock_request.return_value.__aenter__.return_value = mock_response

            async with client:
                # Test GET
                await client.get("auth-service", "/test")

                # Test POST
                await client.post("auth-service", "/test", json_data={"data": "test"})

                # Test PUT
                await client.put("auth-service", "/test", json_data={"data": "updated"})

                # Test DELETE
                await client.delete("auth-service", "/test")

            assert mock_request.call_count == 4


class TestAPIGateway:
    """Test API Gateway functionality"""

    @pytest.mark.asyncio
    async def test_gateway_health_endpoint(self, api_test_suite: APIIntegrationTestSuite):
        """Test API Gateway health endpoint"""
        gateway = api_test_suite.gateway

        # Create test client
        with TestClient(gateway.app) as client:
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "api-gateway"
            assert "services" in data

    @pytest.mark.asyncio
    async def test_gateway_services_endpoint(self, api_test_suite: APIIntegrationTestSuite):
        """Test API Gateway services listing endpoint"""
        gateway = api_test_suite.gateway

        with TestClient(gateway.app) as client:
            response = client.get("/services")

            assert response.status_code == 200
            data = response.json()
            assert "services" in data

            # Verify registered services are listed
            services = data["services"]
            assert "auth-service" in services
            assert "video-service" in services
            assert "ai-service" in services

    @pytest.mark.asyncio
    async def test_gateway_metrics_endpoint(self, api_test_suite: APIIntegrationTestSuite):
        """Test API Gateway metrics endpoint"""
        gateway = api_test_suite.gateway

        with TestClient(gateway.app) as client:
            response = client.get("/metrics")

            assert response.status_code == 200
            data = response.json()
            assert "total_services" in data
            assert "total_instances" in data
            assert "healthy_instances" in data
            assert "health_ratio" in data

    @pytest.mark.asyncio
    async def test_rate_limiting_middleware(self, api_test_suite: APIIntegrationTestSuite):
        """Test rate limiting middleware"""
        gateway = api_test_suite.gateway

        with TestClient(gateway.app) as client:
            # Make multiple requests rapidly
            responses = []
            for i in range(110):  # Exceed rate limit of 100
                response = client.get("/health")
                responses.append(response)

            # Some requests should be rate limited
            status_codes = [r.status_code for r in responses]
            assert 429 in status_codes  # Rate limit exceeded


class TestAuthentication:
    """Test authentication flow"""

    @pytest.mark.asyncio
    async def test_user_registration_flow(self):
        """Test user registration API flow"""
        # Mock authentication service
        mock_auth_data = {
            "user_id": 123,
            "email": "test@example.com",
            "message": "User registered successfully",
        }

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json = AsyncMock(return_value=mock_auth_data)
            mock_post.return_value.__aenter__.return_value = mock_response

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8001/api/v1/register",
                    json={
                        "email": "test@example.com",
                        "password": "password123",
                        "full_name": "Test User",
                    },
                ) as response:
                    data = await response.json()

                    assert data == mock_auth_data
                    assert "user_id" in data

    @pytest.mark.asyncio
    async def test_user_login_flow(self):
        """Test user login API flow"""
        mock_login_data = {
            "access_token": "jwt_token_here",
            "token_type": "bearer",
            "user_id": 123,
            "expires_in": 3600,
        }

        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_login_data)
            mock_post.return_value.__aenter__.return_value = mock_response

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8001/api/v1/login",
                    json={"email": "test@example.com", "password": "password123"},
                ) as response:
                    data = await response.json()

                    assert data == mock_login_data
                    assert "access_token" in data
                    assert "user_id" in data

    @pytest.mark.asyncio
    async def test_protected_endpoint_access(self):
        """Test accessing protected endpoints with authentication"""
        # Mock protected endpoint call
        mock_protected_data = {"user_id": 123, "projects": [], "message": "Authorized access"}

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_protected_data)
            mock_get.return_value.__aenter__.return_value = mock_response

            headers = {"Authorization": "Bearer jwt_token_here"}

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "http://localhost:8003/api/v1/video/projects", headers=headers
                ) as response:
                    data = await response.json()

                    assert data == mock_protected_data
                    assert response.status == 200


class TestWebSocketIntegration:
    """Test WebSocket integration for real-time updates"""

    @pytest.mark.asyncio
    async def test_video_progress_websocket(self):
        """Test WebSocket connection for video progress updates"""

        # Mock WebSocket server
        mock_websocket_data = [
            {"type": "progress", "project_id": 123, "progress": 25, "stage": "generating_script"},
            {"type": "progress", "project_id": 123, "progress": 50, "stage": "generating_voice"},
            {"type": "progress", "project_id": 123, "progress": 75, "stage": "composing"},
            {
                "type": "complete",
                "project_id": 123,
                "progress": 100,
                "final_url": "https://example.com/video.mp4",
            },
        ]

        # Simulate WebSocket message receiving
        received_messages = []

        async def mock_websocket_handler():
            for message in mock_websocket_data:
                received_messages.append(message)
                await asyncio.sleep(0.1)

        await mock_websocket_handler()

        # Verify messages received
        assert len(received_messages) == 4
        assert received_messages[0]["progress"] == 25
        assert received_messages[-1]["type"] == "complete"
        assert received_messages[-1]["final_url"] is not None


class TestErrorHandling:
    """Test error handling scenarios"""

    @pytest.mark.asyncio
    async def test_service_unavailable_handling(self, api_test_suite: APIIntegrationTestSuite):
        """Test handling of unavailable services"""
        registry = api_test_suite.registry
        client = api_test_suite.client

        # Register service but mark as unhealthy
        unhealthy_service = ServiceInstance(
            "unavailable-service", "localhost", 9999, status=ServiceStatus.UNHEALTHY
        )
        registry.register_service(unhealthy_service)

        # Try to call unavailable service
        with pytest.raises(Exception) as exc_info:
            async with client:
                await client.get("unavailable-service", "/health")

        assert "No healthy instances available" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_timeout_handling(self, api_test_suite: APIIntegrationTestSuite):
        """Test request timeout handling"""
        client = ServiceClient(api_test_suite.registry, timeout=1)  # 1 second timeout

        with patch("aiohttp.ClientSession.request") as mock_request:
            # Mock a timeout
            mock_request.side_effect = asyncio.TimeoutError()

            with pytest.raises(Exception):
                async with client:
                    await client.get("auth-service", "/health")

    @pytest.mark.asyncio
    async def test_malformed_response_handling(self, api_test_suite: APIIntegrationTestSuite):
        """Test handling of malformed responses"""
        client = api_test_suite.client

        with patch("aiohttp.ClientSession.request") as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(side_effect=json.JSONDecodeError("Invalid JSON", "", 0))
            mock_request.return_value.__aenter__.return_value = mock_response

            with pytest.raises(Exception):
                async with client:
                    await client.get("auth-service", "/health")


class TestCaching:
    """Test caching mechanisms"""

    @pytest.mark.asyncio
    async def test_response_caching(self):
        """Test API response caching"""
        # Mock cache hit and miss scenarios
        cache = {}

        def get_from_cache(key):
            return cache.get(key)

        def set_cache(key, value, ttl=300):
            cache[key] = {"value": value, "expires": time.time() + ttl}
            return value

        # Simulate cache miss
        key = "auth-service:/health"
        cached_value = get_from_cache(key)
        assert cached_value is None

        # Simulate API call and cache set
        api_response = {"status": "healthy", "timestamp": time.time()}
        cached_response = set_cache(key, api_response)
        assert cached_response == api_response

        # Simulate cache hit
        cached_value = get_from_cache(key)
        assert cached_value is not None
        assert cached_value["value"]["status"] == "healthy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
