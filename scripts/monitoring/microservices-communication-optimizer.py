#!/usr/bin/env python3
"""
Microservices Communication Optimizer
微服務通訊優化器

Features:
- Service mesh performance optimization
- Load balancing strategy optimization
- Circuit breaker tuning
- Connection pooling optimization
- Request/response caching
- Compression and serialization optimization
- Network latency reduction
- Async communication patterns
"""

import asyncio
import gzip
import hashlib
import json
import logging
import statistics
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

import aiohttp
import redis
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""

    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    FASTEST_RESPONSE = "fastest_response"
    RESOURCE_BASED = "resource_based"


class CircuitBreakerState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ServiceInstance:
    """Service instance information"""

    name: str
    host: str
    port: int
    health_endpoint: str
    weight: float = 1.0
    current_connections: int = 0
    avg_response_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    last_health_check: Optional[datetime] = None
    is_healthy: bool = True


@dataclass
class CommunicationMetrics:
    """Communication performance metrics"""

    service_from: str
    service_to: str
    timestamp: datetime
    request_count: int
    total_response_time: float
    error_count: int
    timeout_count: int
    bytes_sent: int
    bytes_received: int
    compression_ratio: float
    cache_hit_rate: float


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    failure_threshold: int = 5
    timeout_duration: int = 60  # seconds
    half_open_max_calls: int = 3
    failure_rate_threshold: float = 0.5


class CircuitBreaker:
    """Circuit breaker implementation"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        self.success_count = 0
        self.total_calls = 0

    def can_execute(self) -> bool:
        """Check if request can be executed"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        elif self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                self.half_open_calls = 0
                return True
            return False
        else:  # HALF_OPEN
            return self.half_open_calls < self.config.half_open_max_calls

    def record_success(self):
        """Record successful call"""
        self.success_count += 1
        self.total_calls += 1
        self.failure_count = 0

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.config.half_open_max_calls:
                self.state = CircuitBreakerState.CLOSED

    def record_failure(self):
        """Record failed call"""
        self.failure_count += 1
        self.total_calls += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
        elif self.state == CircuitBreakerState.CLOSED:
            failure_rate = self.failure_count / max(self.total_calls, 1)
            if (
                self.failure_count >= self.config.failure_threshold
                or failure_rate >= self.config.failure_rate_threshold
            ):
                self.state = CircuitBreakerState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset"""
        if not self.last_failure_time:
            return False

        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.config.timeout_duration


class ConnectionPool:
    """Advanced connection pool"""

    def __init__(self, max_connections: int = 100, max_idle_time: int = 300):
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.connections: Dict[str, deque] = defaultdict(deque)
        self.connection_metrics: Dict[str, Dict] = defaultdict(dict)
        self.lock = asyncio.Lock()

    async def get_session(self, service_key: str) -> aiohttp.ClientSession:
        """Get or create HTTP session for service"""
        async with self.lock:
            now = time.time()

            # Clean up idle connections
            if service_key in self.connections:
                while self.connections[service_key]:
                    session, last_used = self.connections[service_key][0]
                    if now - last_used > self.max_idle_time:
                        self.connections[service_key].popleft()
                        await session.close()
                    else:
                        break

            # Try to reuse existing connection
            if self.connections[service_key]:
                session, _ = self.connections[service_key].popleft()
                self.connection_metrics[service_key]["reused"] = (
                    self.connection_metrics[service_key].get("reused", 0) + 1
                )
                return session

            # Create new connection
            connector = aiohttp.TCPConnector(
                limit=10,  # Max connections per host
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True,
            )

            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=10)

            session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"Connection": "keep-alive"},
            )

            self.connection_metrics[service_key]["created"] = (
                self.connection_metrics[service_key].get("created", 0) + 1
            )

            return session

    async def return_session(self, service_key: str, session: aiohttp.ClientSession):
        """Return session to pool"""
        async with self.lock:
            if len(self.connections[service_key]) < self.max_connections:
                self.connections[service_key].append((session, time.time()))
            else:
                await session.close()


class ResponseCache:
    """Intelligent response caching"""

    def __init__(self, redis_client: redis.Redis, default_ttl: int = 300):
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.cache_stats = {"hits": 0, "misses": 0, "sets": 0, "errors": 0}

    def _generate_cache_key(
        self, method: str, url: str, params: Dict = None, headers: Dict = None
    ) -> str:
        """Generate cache key for request"""
        cache_data = {
            "method": method,
            "url": url,
            "params": params or {},
            "cache_headers": {
                k: v
                for k, v in (headers or {}).items()
                if k.lower() in ("authorization", "content-type")
            },
        }

        cache_string = json.dumps(cache_data, sort_keys=True)
        return f"cache:api:{hashlib.md5(cache_string.encode()).hexdigest()}"

    async def get(self, cache_key: str) -> Optional[Dict]:
        """Get cached response"""
        try:
            cached_data = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.get, cache_key
            )

            if cached_data:
                self.cache_stats["hits"] += 1
                return json.loads(cached_data)
            else:
                self.cache_stats["misses"] += 1
                return None

        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            self.cache_stats["errors"] += 1
            return None

    async def set(self, cache_key: str, data: Dict, ttl: int = None):
        """Set cached response"""
        try:
            ttl = ttl or self.default_ttl
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.setex(cache_key, ttl, json.dumps(data, default=str)),
            )
            self.cache_stats["sets"] += 1

        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            self.cache_stats["errors"] += 1

    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0

        return {
            **self.cache_stats,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
        }


class MicroservicesCommunicationOptimizer:
    """Microservices communication optimizer"""

    def __init__(self, config_path: str = "config/communication-optimizer.yaml"):
        self.config = self._load_config(config_path)
        self.services: Dict[str, List[ServiceInstance]] = {}
        self.load_balancing_strategy = LoadBalancingStrategy(
            self.config.get("load_balancing_strategy", "round_robin")
        )
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.connection_pool = ConnectionPool(
            max_connections=self.config.get("max_connections", 100)
        )
        self.response_cache = None
        self.metrics: Dict[str, List[CommunicationMetrics]] = defaultdict(list)
        self.round_robin_counters: Dict[str, int] = defaultdict(int)

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration"""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._default_config()

    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            "load_balancing_strategy": "fastest_response",
            "max_connections": 100,
            "cache_enabled": True,
            "cache_ttl": 300,
            "compression_enabled": True,
            "compression_threshold": 1024,  # bytes
            "circuit_breaker": {
                "failure_threshold": 5,
                "timeout_duration": 60,
                "half_open_max_calls": 3,
                "failure_rate_threshold": 0.5,
            },
            "services": {
                "api-gateway": [{"host": "localhost", "port": 8000, "weight": 1.0}],
                "auth-service": [{"host": "localhost", "port": 8001, "weight": 1.0}],
                "ai-service": [{"host": "localhost", "port": 8002, "weight": 1.0}],
                "video-service": [{"host": "localhost", "port": 8003, "weight": 1.0}],
                "storage-service": [{"host": "localhost", "port": 8004, "weight": 1.0}],
            },
            "redis": {"host": "localhost", "port": 6379, "db": 1},
        }

    async def initialize(self):
        """Initialize optimizer"""
        # Initialize services
        for service_name, instances in self.config.get("services", {}).items():
            self.services[service_name] = []
            for instance_config in instances:
                instance = ServiceInstance(
                    name=service_name,
                    host=instance_config["host"],
                    port=instance_config["port"],
                    health_endpoint=f"http://{instance_config['host']}:{instance_config['port']}/health",
                    weight=instance_config.get("weight", 1.0),
                )
                self.services[service_name].append(instance)

                # Initialize circuit breaker for each service
                cb_config = CircuitBreakerConfig(**self.config.get("circuit_breaker", {}))
                self.circuit_breakers[f"{service_name}:{instance.host}:{instance.port}"] = (
                    CircuitBreaker(cb_config)
                )

        # Initialize cache if enabled
        if self.config.get("cache_enabled", True):
            redis_config = self.config.get("redis", {})
            redis_client = redis.Redis(
                host=redis_config.get("host", "localhost"),
                port=redis_config.get("port", 6379),
                db=redis_config.get("db", 1),
                decode_responses=True,
            )
            self.response_cache = ResponseCache(redis_client, self.config.get("cache_ttl", 300))

        logger.info("Microservices communication optimizer initialized")
        logger.info(f"Registered services: {list(self.services.keys())}")
        logger.info(f"Load balancing strategy: {self.load_balancing_strategy.value}")

    async def select_service_instance(self, service_name: str) -> Optional[ServiceInstance]:
        """Select optimal service instance using load balancing strategy"""
        if service_name not in self.services:
            logger.error(f"Service {service_name} not found")
            return None

        instances = [inst for inst in self.services[service_name] if inst.is_healthy]
        if not instances:
            logger.warning(f"No healthy instances for service {service_name}")
            return None

        if self.load_balancing_strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(service_name, instances)
        elif self.load_balancing_strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(service_name, instances)
        elif self.load_balancing_strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return min(instances, key=lambda x: x.current_connections)
        elif self.load_balancing_strategy == LoadBalancingStrategy.FASTEST_RESPONSE:
            return min(instances, key=lambda x: x.avg_response_time or float("in"))
        elif self.load_balancing_strategy == LoadBalancingStrategy.RESOURCE_BASED:
            return self._resource_based_select(instances)
        else:
            return instances[0]  # Fallback

    def _round_robin_select(
        self, service_name: str, instances: List[ServiceInstance]
    ) -> ServiceInstance:
        """Round robin selection"""
        index = self.round_robin_counters[service_name] % len(instances)
        self.round_robin_counters[service_name] += 1
        return instances[index]

    def _weighted_round_robin_select(
        self, service_name: str, instances: List[ServiceInstance]
    ) -> ServiceInstance:
        """Weighted round robin selection"""
        total_weight = sum(inst.weight for inst in instances)
        if total_weight == 0:
            return instances[0]

        # Create weighted list
        weighted_instances = []
        for instance in instances:
            weight_count = max(1, int(instance.weight * 10))
            weighted_instances.extend([instance] * weight_count)

        index = self.round_robin_counters[service_name] % len(weighted_instances)
        self.round_robin_counters[service_name] += 1
        return weighted_instances[index]

    def _resource_based_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Resource-based selection considering CPU and memory"""

        def resource_score(instance: ServiceInstance) -> float:
            # Lower score is better
            cpu_score = instance.cpu_usage / 100.0
            memory_score = instance.memory_usage / 100.0
            connection_score = instance.current_connections / 100.0
            response_time_score = (instance.avg_response_time or 0) / 1000.0

            return cpu_score + memory_score + connection_score + response_time_score

        return min(instances, key=resource_score)

    async def make_request(
        self,
        from_service: str,
        to_service: str,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> Tuple[Optional[Dict], CommunicationMetrics]:
        """Make optimized request between services"""
        start_time = time.time()
        instance = await self.select_service_instance(to_service)

        metrics = CommunicationMetrics(
            service_from=from_service,
            service_to=to_service,
            timestamp=datetime.now(),
            request_count=1,
            total_response_time=0,
            error_count=0,
            timeout_count=0,
            bytes_sent=0,
            bytes_received=0,
            compression_ratio=1.0,
            cache_hit_rate=0.0,
        )

        if not instance:
            metrics.error_count = 1
            return None, metrics

        # Circuit breaker check
        cb_key = f"{to_service}:{instance.host}:{instance.port}"
        circuit_breaker = self.circuit_breakers.get(cb_key)

        if circuit_breaker and not circuit_breaker.can_execute():
            logger.warning(f"Circuit breaker OPEN for {cb_key}")
            metrics.error_count = 1
            return None, metrics

        # Build URL
        url = f"http://{instance.host}:{instance.port}{endpoint}"

        # Check cache if GET request
        cache_key = None
        cached_response = None
        if method.upper() == "GET" and self.response_cache:
            cache_key = self.response_cache._generate_cache_key(
                method, url, kwargs.get("params"), kwargs.get("headers")
            )
            cached_response = await self.response_cache.get(cache_key)

            if cached_response:
                metrics.cache_hit_rate = 1.0
                metrics.total_response_time = time.time() - start_time
                return cached_response, metrics

        # Make request
        session = await self.connection_pool.get_session(cb_key)

        try:
            # Prepare request data
            request_data = {}
            if "json" in kwargs:
                request_data["json"] = kwargs["json"]
                if self.config.get("compression_enabled", True):
                    json_str = json.dumps(kwargs["json"])
                    if len(json_str) > self.config.get("compression_threshold", 1024):
                        # Use compression
                        compressed_data = gzip.compress(json_str.encode())
                        request_data["data"] = compressed_data
                        request_data.pop("json")
                        kwargs.setdefault("headers", {})["Content-Encoding"] = "gzip"
                        kwargs["headers"]["Content-Type"] = "application/json"
                        metrics.compression_ratio = len(compressed_data) / len(json_str)

            # Update connection count
            instance.current_connections += 1

            # Make request
            async with session.request(method, url, **request_data, **kwargs) as response:
                response_data = (
                    await response.json()
                    if response.content_type == "application/json"
                    else await response.text()
                )

                # Record success
                if circuit_breaker:
                    circuit_breaker.record_success()

                # Update metrics
                response_time = time.time() - start_time
                metrics.total_response_time = response_time
                metrics.bytes_received = len(str(response_data))

                # Update instance metrics
                instance.avg_response_time = (
                    ((instance.avg_response_time * 0.9) + (response_time * 1000 * 0.1))
                    if instance.avg_response_time
                    else response_time * 1000
                )

                # Cache successful GET responses
                if (
                    method.upper() == "GET"
                    and response.status == 200
                    and self.response_cache
                    and cache_key
                ):
                    await self.response_cache.set(
                        cache_key,
                        {
                            "data": response_data,
                            "status": response.status,
                            "headers": dict(response.headers),
                        },
                    )

                await self.connection_pool.return_session(cb_key, session)

                return {
                    "data": response_data,
                    "status": response.status,
                    "headers": dict(response.headers),
                }, metrics

        except asyncio.TimeoutError:
            metrics.timeout_count = 1
            if circuit_breaker:
                circuit_breaker.record_failure()
            logger.warning(f"Request timeout to {url}")
            await session.close()  # Don't return timed out session
            return None, metrics

        except Exception as e:
            metrics.error_count = 1
            if circuit_breaker:
                circuit_breaker.record_failure()
            logger.error(f"Request error to {url}: {e}")
            await session.close()  # Don't return errored session
            return None, metrics

        finally:
            instance.current_connections = max(0, instance.current_connections - 1)

    async def health_check_services(self):
        """Perform health checks on all service instances"""
        for service_name, instances in self.services.items():
            for instance in instances:
                try:
                    start_time = time.time()

                    session = await self.connection_pool.get_session(
                        f"health:{instance.host}:{instance.port}"
                    )

                    async with session.get(
                        instance.health_endpoint,
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as response:
                        is_healthy = response.status == 200
                        response_time = (time.time() - start_time) * 1000

                        instance.is_healthy = is_healthy
                        instance.last_health_check = datetime.now()

                        if is_healthy:
                            # Update response time moving average
                            instance.avg_response_time = (
                                ((instance.avg_response_time * 0.8) + (response_time * 0.2))
                                if instance.avg_response_time
                                else response_time
                            )

                            # Try to get resource metrics
                            try:
                                health_data = await response.json()
                                if isinstance(health_data, dict):
                                    instance.cpu_usage = health_data.get(
                                        "cpu_usage", instance.cpu_usage
                                    )
                                    instance.memory_usage = health_data.get(
                                        "memory_usage", instance.memory_usage
                                    )
                            except Exception:
                                pass

                    await self.connection_pool.return_session(
                        f"health:{instance.host}:{instance.port}", session
                    )

                except Exception as e:
                    instance.is_healthy = False
                    instance.last_health_check = datetime.now()
                    logger.warning(
                        f"Health check failed for {instance.name} at {instance.host}:{instance.port}: {e}"
                    )
                    await session.close()  # Don't return failed session

    async def optimize_communication_patterns(self):
        """Analyze and optimize communication patterns"""
        # Analyze recent metrics
        optimization_report = {
            "timestamp": datetime.now().isoformat(),
            "recommendations": [],
            "service_performance": {},
            "cache_performance": {},
            "circuit_breaker_status": {},
        }

        # Service performance analysis
        for service_name, instances in self.services.items():
            healthy_instances = [inst for inst in instances if inst.is_healthy]
            if not healthy_instances:
                optimization_report["recommendations"].append(
                    f"Critical: No healthy instances for {service_name}"
                )
                continue

            avg_response_time = statistics.mean(
                [inst.avg_response_time or 0 for inst in healthy_instances]
            )
            max_response_time = max([inst.avg_response_time or 0 for inst in healthy_instances])

            optimization_report["service_performance"][service_name] = {
                "healthy_instances": len(healthy_instances),
                "total_instances": len(instances),
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "load_distribution": [inst.current_connections for inst in healthy_instances],
            }

            # Generate recommendations
            if avg_response_time > 1000:  # 1 second
                optimization_report["recommendations"].append(
                    f"High average response time for {service_name}: {avg_response_time:.1f}ms. Consider scaling or optimization."
                )

            if max_response_time > avg_response_time * 2:
                optimization_report["recommendations"].append(
                    f"Uneven performance in {service_name}. Consider load balancing adjustment."
                )

        # Cache performance analysis
        if self.response_cache:
            cache_stats = self.response_cache.get_cache_stats()
            optimization_report["cache_performance"] = cache_stats

            if cache_stats["hit_rate"] < 20:  # Less than 20% hit rate
                optimization_report["recommendations"].append(
                    f"Low cache hit rate ({cache_stats['hit_rate']:.1f}%). Review caching strategy."
                )

        # Circuit breaker analysis
        for cb_key, circuit_breaker in self.circuit_breakers.items():
            optimization_report["circuit_breaker_status"][cb_key] = {
                "state": circuit_breaker.state.value,
                "failure_count": circuit_breaker.failure_count,
                "success_count": circuit_breaker.success_count,
                "total_calls": circuit_breaker.total_calls,
            }

            if circuit_breaker.state == CircuitBreakerState.OPEN:
                optimization_report["recommendations"].append(
                    f"Circuit breaker OPEN for {cb_key}. Service may be experiencing issues."
                )

        return optimization_report

    async def start_monitoring(self, monitoring_interval: int = 30):
        """Start continuous monitoring and optimization"""
        await self.initialize()

        logger.info(
            f"Starting communication optimizer monitoring (interval: {monitoring_interval}s)"
        )

        while True:
            try:
                # Health check all services
                await self.health_check_services()

                # Generate optimization report
                report = await self.optimize_communication_patterns()

                # Log summary
                total_healthy = sum(
                    len([inst for inst in instances if inst.is_healthy])
                    for instances in self.services.values()
                )
                total_instances = sum(len(instances) for instances in self.services.values())

                logger.info(
                    f"Health check completed - {total_healthy}/{total_instances} instances healthy"
                )

                # Log recommendations
                for recommendation in report["recommendations"]:
                    logger.warning(f"RECOMMENDATION: {recommendation}")

                # Cache performance
                if self.response_cache:
                    cache_stats = self.response_cache.get_cache_stats()
                    logger.info(
                        f"Cache performance - Hit rate: {cache_stats['hit_rate']:.1f}%, Total requests: {cache_stats['total_requests']}"
                    )

                await asyncio.sleep(monitoring_interval)

            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(monitoring_interval)


# Example usage function
async def example_usage():
    """Example of how to use the optimizer"""
    optimizer = MicroservicesCommunicationOptimizer()
    await optimizer.initialize()

    # Make optimized request
    response, metrics = await optimizer.make_request(
        from_service="frontend",
        to_service="api-gateway",
        method="GET",
        endpoint="/api/v1/status",
    )

    print(f"Response: {response}")
    print(f"Metrics: {asdict(metrics)}")

    # Generate optimization report
    report = await optimizer.optimize_communication_patterns()
    print(json.dumps(report, indent=2, default=str))


async def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Microservices Communication Optimizer")
    parser.add_argument(
        "--config",
        default="config/communication-optimizer.yaml",
        help="Configuration file",
    )
    parser.add_argument("--monitor", action="store_true", help="Start monitoring mode")
    parser.add_argument("--example", action="store_true", help="Run example usage")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Monitoring interval in seconds",
    )

    args = parser.parse_args()

    if args.example:
        await example_usage()
    elif args.monitor:
        optimizer = MicroservicesCommunicationOptimizer(args.config)
        await optimizer.start_monitoring(args.interval)
    else:
        print("Use --monitor to start monitoring or --example to run example")


if __name__ == "__main__":
    asyncio.run(main())
