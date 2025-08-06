"""
統一服務發現和負載均衡系統
提供服務註冊、發現、健康檢查和負載均衡功能
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
    """服務狀態枚舉"""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class LoadBalanceStrategy(Enum):
    """負載均衡策略"""

    ROUND_ROBIN = "round_robin"
    RANDOM = "random"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"


@dataclass
class ServiceInstance:
    """服務實例"""

    service_name: str
    host: str
    port: int
    weight: int = 1
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_health_check: float = field(default_factory=time.time)
    connections: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def url(self) -> str:
        """獲取服務 URL"""
        return f"http://{self.host}:{self.port}"

    @property
    def health_url(self) -> str:
        """獲取健康檢查 URL"""
        return urljoin(self.url, "/health")

    def __hash__(self) -> int:
        return hash(f"{self.service_name}:{self.host}:{self.port}")


class ServiceRegistry:
    """服務註冊表"""

    def __init__(self) -> None:
        self._services: Dict[str, List[ServiceInstance]] = {}
        self._lock = asyncio.Lock()

    async def register(self, instance: ServiceInstance) -> bool:
        """註冊服務實例"""
        async with self._lock:
            if instance.service_name not in self._services:
                self._services[instance.service_name] = []

            # 檢查是否已存在相同實例
            existing = self._find_instance(instance.service_name, instance.host, instance.port)
            if existing:
                # 更新現有實例
                existing.weight = instance.weight
                existing.metadata = instance.metadata
                logger.info(
                    f"Updated service instance: {instance.service_name}@{instance.host}:{instance.port}"
                )
                return True
            else:
                # 添加新實例
                self._services[instance.service_name].append(instance)
                logger.info(
                    f"Registered service instance: {instance.service_name}@{instance.host}:{instance.port}"
                )
                return True

    async def deregister(self, service_name: str, host: str, port: int) -> bool:
        """取消註冊服務實例"""
        async with self._lock:
            if service_name not in self._services:
                return False

            instance = self._find_instance(service_name, host, port)
            if instance:
                self._services[service_name].remove(instance)
                logger.info(f"Deregistered service instance: {service_name}@{host}:{port}")
                return True
            return False

    async def get_healthy_instances(self, service_name: str) -> List[ServiceInstance]:
        """獲取健康的服務實例"""
        async with self._lock:
            if service_name not in self._services:
                return []

            return [
                instance
                for instance in self._services[service_name]
                if instance.status == ServiceStatus.HEALTHY
            ]

    async def get_all_instances(self, service_name: str) -> List[ServiceInstance]:
        """獲取所有服務實例"""
        async with self._lock:
            return self._services.get(service_name, []).copy()

    async def get_service_names(self) -> List[str]:
        """獲取所有服務名稱"""
        async with self._lock:
            return list(self._services.keys())

    def _find_instance(self, service_name: str, host: str, port: int) -> Optional[ServiceInstance]:
        """查找服務實例"""
        if service_name not in self._services:
            return None

        for instance in self._services[service_name]:
            if instance.host == host and instance.port == port:
                return instance
        return None


class HealthChecker:
    """健康檢查器"""

    def __init__(self, registry: ServiceRegistry, check_interval: int = 30) -> None:
        self.registry = registry
        self.check_interval = check_interval
        self._running = False
        self._session: Optional[aiohttp.ClientSession] = None

    async def start(self) -> None:
        """開始健康檢查"""
        if self._running:
            return

        self._running = True
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5))

        asyncio.create_task(self._health_check_loop())
        logger.info("Health checker started")

    async def stop(self) -> None:
        """停止健康檢查"""
        self._running = False
        if self._session:
            await self._session.close()
        logger.info("Health checker stopped")

    async def _health_check_loop(self) -> None:
        """健康檢查循環"""
        while self._running:
            try:
                service_names = await self.registry.get_service_names()
                for service_name in service_names:
                    instances = await self.registry.get_all_instances(service_name)
                    for instance in instances:
                        await self._check_instance_health(instance)

                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.check_interval)

    async def _check_instance_health(self, instance: ServiceInstance) -> None:
        """檢查單個實例健康狀態"""
        if not self._session:
            return
        try:
            async with self._session.get(instance.health_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "healthy":
                        instance.status = ServiceStatus.HEALTHY
                    else:
                        instance.status = ServiceStatus.UNHEALTHY
                else:
                    instance.status = ServiceStatus.UNHEALTHY
        except Exception as e:
            logger.warning(
                f"Health check failed for {instance.service_name}@{instance.host}:{instance.port}: {e}"
            )
            instance.status = ServiceStatus.UNHEALTHY

        instance.last_health_check = time.time()


class LoadBalancer:
    """負載均衡器"""

    def __init__(self, strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self._round_robin_counters: Dict[str, int] = {}

    async def select_instance(self, instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """選擇服務實例"""
        if not instances:
            return None

        healthy_instances = [
            instance for instance in instances if instance.status == ServiceStatus.HEALTHY
        ]

        if not healthy_instances:
            logger.warning("No healthy instances available, falling back to all instances")
            healthy_instances = instances

        if self.strategy == LoadBalanceStrategy.ROUND_ROBIN:
            return self._round_robin_select(healthy_instances)
        elif self.strategy == LoadBalanceStrategy.RANDOM:
            return self._random_select(healthy_instances)
        elif self.strategy == LoadBalanceStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(healthy_instances)
        elif self.strategy == LoadBalanceStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(healthy_instances)
        else:
            return healthy_instances[0]

    def _round_robin_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """輪詢選擇"""
        service_name = instances[0].service_name
        counter = self._round_robin_counters.get(service_name, 0)
        selected = instances[counter % len(instances)]
        self._round_robin_counters[service_name] = counter + 1
        return selected

    def _random_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """隨機選擇"""
        return random.choice(instances)

    def _least_connections_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """最少連接選擇"""
        return min(instances, key=lambda x: x.connections)

    def _weighted_round_robin_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """加權輪詢選擇"""
        # 創建權重列表
        weighted_instances = []
        for instance in instances:
            weighted_instances.extend([instance] * instance.weight)

        if not weighted_instances:
            return instances[0]

        service_name = instances[0].service_name
        counter = self._round_robin_counters.get(service_name, 0)
        selected = weighted_instances[counter % len(weighted_instances)]
        self._round_robin_counters[service_name] = counter + 1
        return selected


class ServiceDiscovery:
    """服務發現主類"""

    def __init__(
        self,
        load_balance_strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN,
    ) -> None:
        self.registry = ServiceRegistry()
        self.health_checker = HealthChecker(self.registry)
        self.load_balancer = LoadBalancer(load_balance_strategy)
        self._started = False

    async def start(self) -> None:
        """啟動服務發現"""
        if self._started:
            return

        await self.health_checker.start()
        self._started = True
        logger.info("Service discovery started")

    async def stop(self) -> None:
        """停止服務發現"""
        if not self._started:
            return

        await self.health_checker.stop()
        self._started = False
        logger.info("Service discovery stopped")

    async def register_service(
        self,
        service_name: str,
        host: str,
        port: int,
        weight: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """註冊服務"""
        instance = ServiceInstance(
            service_name=service_name,
            host=host,
            port=port,
            weight=weight,
            metadata=metadata or {},
        )
        return await self.registry.register(instance)

    async def deregister_service(self, service_name: str, host: str, port: int) -> bool:
        """取消註冊服務"""
        return await self.registry.deregister(service_name, host, port)

    async def get_service_url(self, service_name: str) -> Optional[str]:
        """獲取服務 URL（通過負載均衡）"""
        instances = await self.registry.get_healthy_instances(service_name)
        selected = await self.load_balancer.select_instance(instances)

        if selected:
            selected.connections += 1
            return selected.url
        return None

    async def get_service_instance(self, service_name: str) -> Optional[ServiceInstance]:
        """獲取服務實例（通過負載均衡）"""
        instances = await self.registry.get_healthy_instances(service_name)
        selected = await self.load_balancer.select_instance(instances)

        if selected:
            selected.connections += 1
        return selected

    async def release_connection(self, instance: ServiceInstance) -> None:
        """釋放連接"""
        if instance.connections > 0:
            instance.connections -= 1

    async def get_service_stats(self, service_name: str) -> Dict[str, Any]:
        """獲取服務統計信息"""
        instances = await self.registry.get_all_instances(service_name)

        total_instances = len(instances)
        healthy_instances = len([i for i in instances if i.status == ServiceStatus.HEALTHY])

        return {
            "service_name": service_name,
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "unhealthy_instances": total_instances - healthy_instances,
            "instances": [
                {
                    "host": instance.host,
                    "port": instance.port,
                    "status": instance.status.value,
                    "connections": instance.connections,
                    "weight": instance.weight,
                    "last_health_check": instance.last_health_check,
                }
                for instance in instances
            ],
        }


# 全局服務發現實例
_service_discovery: Optional[ServiceDiscovery] = None


async def get_service_discovery() -> ServiceDiscovery:
    """獲取全局服務發現實例"""
    global _service_discovery
    if _service_discovery is None:
        _service_discovery = ServiceDiscovery()
        await _service_discovery.start()
    return _service_discovery


async def register_service(
    service_name: str,
    host: str,
    port: int,
    weight: int = 1,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """註冊服務的便捷函數"""
    discovery = await get_service_discovery()
    return await discovery.register_service(service_name, host, port, weight, metadata)


async def get_service_url(service_name: str) -> Optional[str]:
    """獲取服務 URL 的便捷函數"""
    discovery = await get_service_discovery()
    return await discovery.get_service_url(service_name)


async def get_service_instance(service_name: str) -> Optional[ServiceInstance]:
    """獲取服務實例的便捷函數"""
    discovery = await get_service_discovery()
    return await discovery.get_service_instance(service_name)
