"""
服務發現和通訊模組
提供服務註冊、發現和負載均衡功能
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服務狀態"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class LoadBalancingStrategy(Enum):
    """負載均衡策略"""

    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    HEALTH_BASED = "health_based"


@dataclass
class ServiceInstance:
    """服務實例"""

    name: str
    host: str
    port: int
    protocol: str = "http"
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_health_check: float = field(default_factory=time.time)
    response_time: float = 0.0
    active_connections: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def base_url(self) -> str:
        return f"{self.protocol}://{self.host}:{self.port}"

    @property
    def health_url(self) -> str:
        return urljoin(self.base_url, "/health")

    def is_healthy(self) -> bool:
        return self.status == ServiceStatus.HEALTHY


class ServiceRegistry:
    """服務註冊中心"""

    def __init__(self):
        self._services: Dict[str, List[ServiceInstance]] = {}
        self._round_robin_counters: Dict[str, int] = {}

    def register_service(self, instance: ServiceInstance) -> None:
        """註冊服務實例"""
        service_name = instance.name

        if service_name not in self._services:
            self._services[service_name] = []
            self._round_robin_counters[service_name] = 0

        # 檢查是否已存在相同的實例
        existing = self._find_instance(service_name, instance.host, instance.port)
        if existing:
            # 更新現有實例
            existing.status = instance.status
            existing.metadata.update(instance.metadata)
        else:
            # 添加新實例
            self._services[service_name].append(instance)

        logger.info(f"Registered service instance: {service_name} at {instance.base_url}")

    def deregister_service(self, service_name: str, host: str, port: int) -> bool:
        """註銷服務實例"""
        if service_name not in self._services:
            return False

        instance = self._find_instance(service_name, host, port)
        if instance:
            self._services[service_name].remove(instance)
            logger.info(f"Deregistered service instance: {service_name} at {instance.base_url}")
            return True

        return False

    def get_service_instances(self, service_name: str) -> List[ServiceInstance]:
        """獲取服務的所有實例"""
        return self._services.get(service_name, [])

    def get_healthy_instances(self, service_name: str) -> List[ServiceInstance]:
        """獲取健康的服務實例"""
        instances = self._services.get(service_name, [])
        return [instance for instance in instances if instance.is_healthy()]

    def select_instance(
        self, service_name: str, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    ) -> Optional[ServiceInstance]:
        """根據負載均衡策略選擇服務實例"""
        healthy_instances = self.get_healthy_instances(service_name)

        if not healthy_instances:
            logger.warning(f"No healthy instances found for service: {service_name}")
            return None

        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(service_name, healthy_instances)
        elif strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(healthy_instances)
        elif strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return min(healthy_instances, key=lambda x: x.active_connections)
        elif strategy == LoadBalancingStrategy.HEALTH_BASED:
            return min(healthy_instances, key=lambda x: x.response_time)
        else:
            return healthy_instances[0]

    def _find_instance(self, service_name: str, host: str, port: int) -> Optional[ServiceInstance]:
        """尋找特定的服務實例"""
        instances = self._services.get(service_name, [])
        for instance in instances:
            if instance.host == host and instance.port == port:
                return instance
        return None

    def _round_robin_select(
        self, service_name: str, instances: List[ServiceInstance]
    ) -> ServiceInstance:
        """輪詢選擇實例"""
        counter = self._round_robin_counters[service_name]
        instance = instances[counter % len(instances)]
        self._round_robin_counters[service_name] = (counter + 1) % len(instances)
        return instance


class ServiceClient:
    """服務客戶端 - 提供服務間通訊功能"""

    def __init__(self, registry: ServiceRegistry, timeout: int = 30):
        self.registry = registry
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def call_service(
        self,
        service_name: str,
        method: str,
        path: str,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN,
        retries: int = 3,
    ) -> Dict[str, Any]:
        """調用服務API"""

        if not self.session:
            raise RuntimeError("ServiceClient must be used as async context manager")

        last_error = None

        for attempt in range(retries + 1):
            instance = self.registry.select_instance(service_name, strategy)
            if not instance:
                raise Exception(f"No healthy instances available for service: {service_name}")

            url = urljoin(instance.base_url, path)

            try:
                # 增加活動連接計數
                instance.active_connections += 1
                start_time = time.time()

                async with self.session.request(
                    method, url, data=data, json=json_data, headers=headers
                ) as response:
                    response_time = time.time() - start_time
                    instance.response_time = response_time

                    if response.status >= 200 and response.status < 300:
                        result = await response.json()
                        logger.debug(f"Service call successful: {service_name} {method} {path}")
                        return result
                    else:
                        error_text = await response.text()
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=error_text,
                        )

            except Exception as e:
                last_error = e
                instance.status = ServiceStatus.UNHEALTHY
                logger.warning(
                    f"Service call failed (attempt {attempt + 1}): {service_name} {method} {path} - {str(e)}"
                )

                if attempt < retries:
                    await asyncio.sleep(0.5 * (attempt + 1))  # 指數退避

            finally:
                instance.active_connections = max(0, instance.active_connections - 1)

        raise Exception(f"Service call failed after {retries + 1} attempts: {last_error}")

    async def get(self, service_name: str, path: str, **kwargs) -> Dict[str, Any]:
        """GET請求"""
        return await self.call_service(service_name, "GET", path, **kwargs)

    async def post(self, service_name: str, path: str, **kwargs) -> Dict[str, Any]:
        """POST請求"""
        return await self.call_service(service_name, "POST", path, **kwargs)

    async def put(self, service_name: str, path: str, **kwargs) -> Dict[str, Any]:
        """PUT請求"""
        return await self.call_service(service_name, "PUT", path, **kwargs)

    async def delete(self, service_name: str, path: str, **kwargs) -> Dict[str, Any]:
        """DELETE請求"""
        return await self.call_service(service_name, "DELETE", path, **kwargs)


class HealthChecker:
    """健康檢查器"""

    def __init__(self, registry: ServiceRegistry, check_interval: int = 30):
        self.registry = registry
        self.check_interval = check_interval
        self.running = False

    async def start_health_checks(self):
        """開始健康檢查"""
        self.running = True

        async with aiohttp.ClientSession() as session:
            while self.running:
                await self._check_all_services(session)
                await asyncio.sleep(self.check_interval)

    def stop_health_checks(self):
        """停止健康檢查"""
        self.running = False

    async def _check_all_services(self, session: aiohttp.ClientSession):
        """檢查所有服務的健康狀態"""
        tasks = []

        for service_name, instances in self.registry._services.items():
            for instance in instances:
                tasks.append(self._check_instance_health(session, instance))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_instance_health(
        self, session: aiohttp.ClientSession, instance: ServiceInstance
    ):
        """檢查單個服務實例的健康狀態"""
        try:
            start_time = time.time()
            async with session.get(
                instance.health_url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    instance.status = ServiceStatus.HEALTHY
                    instance.response_time = response_time
                    instance.last_health_check = time.time()

                    # 嘗試解析健康檢查回應以獲取更多資訊
                    try:
                        health_data = await response.json()
                        if isinstance(health_data, dict):
                            instance.metadata.update(health_data)
                    except:
                        pass
                else:
                    instance.status = ServiceStatus.UNHEALTHY

        except Exception as e:
            instance.status = ServiceStatus.UNHEALTHY
            logger.debug(f"Health check failed for {instance.base_url}: {str(e)}")


# 全域服務註冊表
global_registry = ServiceRegistry()


def get_service_registry() -> ServiceRegistry:
    """獲取全域服務註冊表"""
    return global_registry


async def register_default_services():
    """註冊預設的微服務實例"""
    services = [
        ServiceInstance("api-gateway", "localhost", 8000),
        ServiceInstance("auth-service", "localhost", 8001),
        ServiceInstance("user-service", "localhost", 8002),
        ServiceInstance("video-service", "localhost", 8003),
        ServiceInstance("ai-service", "localhost", 8004),
        ServiceInstance("upload-service", "localhost", 8005),
        ServiceInstance("analytics-service", "localhost", 8006),
        ServiceInstance("social-service", "localhost", 8007),
        ServiceInstance("notification-service", "localhost", 8008),
        ServiceInstance("storage-service", "localhost", 8009),
        ServiceInstance("payment-service", "localhost", 8010),
        ServiceInstance("search-service", "localhost", 8011),
        ServiceInstance("recommendation-service", "localhost", 8012),
        ServiceInstance("cache-service", "localhost", 8013),
        ServiceInstance("queue-service", "localhost", 8014),
        ServiceInstance("monitoring-service", "localhost", 8015),
        ServiceInstance("compliance-service", "localhost", 8016),
    ]

    registry = get_service_registry()
    for service in services:
        registry.register_service(service)

    logger.info("Registered all default microservices")


# 便利函數
async def create_service_client() -> ServiceClient:
    """創建服務客戶端"""
    return ServiceClient(get_service_registry())
