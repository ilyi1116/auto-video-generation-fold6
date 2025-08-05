#!/usr/bin/env python3
"""
分散式快取系統
達到 AWS ElastiCache / Google Cloud Memorystore 級別的快取效能
支援 Redis Cluster、一致性哈希、智能預取、多層快取
"""

import asyncio
import hashlib
import json
import logging
import pickle
import threading
import time
import zlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import numpy as np
import rediscluster

logger = logging.getLogger(__name__)


class CacheType(Enum):
    MEMORY = "memory"
    REDIS = "redis"
    REDIS_CLUSTER = "redis_cluster"
    REDIS_SENTINEL = "redis_sentinel"
    MULTI_TIER = "multi_tier"


class EvictionPolicy(Enum):
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    RANDOM = "random"
    CUSTOM = "custom"


class CacheStrategy(Enum):
    CACHE_ASIDE = "cache_aside"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"
    REFRESH_AHEAD = "refresh_ahead"


@dataclass
class CacheEntry:
    """快取條目"""

    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl: Optional[int]
    size_bytes: int
    tags: List[str]
    metadata: Dict[str, Any]


@dataclass
class CacheStats:
    """快取統計"""

    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_ratio: float
    avg_response_time: float
    memory_usage: int
    evictions: int
    errors: int


class ConsistentHash:
    """一致性哈希算法"""

    def __init__(self, nodes: List[str], replicas: int = 3):
        self.replicas = replicas
        self.ring = {}
        self.sorted_keys = []

        for node in nodes:
            self.add_node(node)

    def _hash(self, key: str) -> int:
        """計算哈希值"""
        return int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)

    def add_node(self, node: str):
        """添加節點"""
        for i in range(self.replicas):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            self.ring[hash_value] = node

        self._update_sorted_keys()

    def remove_node(self, node: str):
        """移除節點"""
        for i in range(self.replicas):
            virtual_key = f"{node}:{i}"
            hash_value = self._hash(virtual_key)
            if hash_value in self.ring:
                del self.ring[hash_value]

        self._update_sorted_keys()

    def _update_sorted_keys(self):
        """更新排序的鍵列表"""
        self.sorted_keys = sorted(self.ring.keys())

    def get_node(self, key: str) -> str:
        """獲取鍵應該分配到的節點"""
        if not self.ring:
            return None

        hash_value = self._hash(key)

        # 找到第一個大於等於 hash_value 的節點
        for ring_key in self.sorted_keys:
            if hash_value <= ring_key:
                return self.ring[ring_key]

        # 如果沒找到，返回第一個節點（環形結構）
        return self.ring[self.sorted_keys[0]]


class MemoryCache:
    """記憶體快取"""

    def __init__(
        self,
        max_size: int = 1000,
        eviction_policy: EvictionPolicy = EvictionPolicy.LRU,
    ):
        self.max_size = max_size
        self.eviction_policy = eviction_policy
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []  # LRU 順序
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """獲取快取值"""
        with self.lock:
            if key not in self.cache:
                return None

            entry = self.cache[key]

            # 檢查是否過期
            if self._is_expired(entry):
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
                return None

            # 更新訪問資訊
            entry.last_accessed = datetime.utcnow()
            entry.access_count += 1

            # 更新 LRU 順序
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)

            return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: List[str] = None,
    ):
        """設置快取值"""
        with self.lock:
            # 如果快取已滿，執行淘汰策略
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict()

            size_bytes = len(pickle.dumps(value))

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                access_count=1,
                ttl=ttl,
                size_bytes=size_bytes,
                tags=tags or [],
                metadata={},
            )

            self.cache[key] = entry

            # 更新 LRU 順序
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)

    def delete(self, key: str) -> bool:
        """刪除快取值"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
                return True
            return False

    def _is_expired(self, entry: CacheEntry) -> bool:
        """檢查條目是否過期"""
        if entry.ttl is None:
            return False

        age = (datetime.utcnow() - entry.created_at).total_seconds()
        return age > entry.ttl

    def _evict(self):
        """執行淘汰策略"""
        if not self.cache:
            return

        if self.eviction_policy == EvictionPolicy.LRU:
            # 淘汰最少使用的
            if self.access_order:
                key_to_evict = self.access_order[0]
                del self.cache[key_to_evict]
                self.access_order.remove(key_to_evict)

        elif self.eviction_policy == EvictionPolicy.LFU:
            # 淘汰訪問次數最少的
            min_access_key = min(self.cache.keys(), key=lambda k: self.cache[k].access_count)
            del self.cache[min_access_key]
            if min_access_key in self.access_order:
                self.access_order.remove(min_access_key)

        elif self.eviction_policy == EvictionPolicy.TTL:
            # 淘汰即將過期的
            datetime.utcnow()
            min_ttl_key = min(
                self.cache.keys(),
                key=lambda k: (
                    self.cache[k].created_at + timedelta(seconds=self.cache[k].ttl or 0)
                ),
            )
            del self.cache[min_ttl_key]
            if min_ttl_key in self.access_order:
                self.access_order.remove(min_ttl_key)


class RedisClusterCache:
    """Redis 集群快取"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.nodes = config.get("nodes", [])
        self.password = config.get("password")
        self.decode_responses = config.get("decode_responses", True)

        # 創建 Redis 集群連接
        startup_nodes = [
            {"host": node.split(":")[0], "port": int(node.split(":")[1])} for node in self.nodes
        ]

        self.cluster = rediscluster.RedisCluster(
            startup_nodes=startup_nodes,
            password=self.password,
            decode_responses=self.decode_responses,
            skip_full_coverage_check=True,
            health_check_interval=30,
            retry_on_timeout=True,
            max_connections_per_node=20,
        )

        self.stats = {"hits": 0, "misses": 0, "errors": 0}

    async def get(self, key: str) -> Optional[Any]:
        """獲取快取值"""
        try:
            value = self.cluster.get(key)
            if value is not None:
                self.stats["hits"] += 1
                # 如果值是序列化的，進行反序列化
                if isinstance(value, (bytes, str)) and value.startswith(b"pickle:"):
                    return pickle.loads(value[7:])  # 去掉 'pickle:' 前綴
                return value
            else:
                self.stats["misses"] += 1
                return None
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Redis 集群獲取錯誤: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        compress: bool = False,
        serialize: bool = True,
    ):
        """設置快取值"""
        try:
            # 序列化複雜對象
            if serialize and not isinstance(value, (str, int, float, bool, bytes)):
                serialized_value = b"pickle:" + pickle.dumps(value)
                if compress:
                    serialized_value = b"compressed:" + zlib.compress(serialized_value)
                value = serialized_value

            if ttl:
                self.cluster.setex(key, ttl, value)
            else:
                self.cluster.set(key, value)

            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Redis 集群設置錯誤: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """刪除快取值"""
        try:
            result = self.cluster.delete(key)
            return result > 0
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Redis 集群刪除錯誤: {e}")
            return False

    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """批量獲取"""
        try:
            values = self.cluster.mget(keys)
            results = []
            for value in values:
                if value is not None:
                    self.stats["hits"] += 1
                    if isinstance(value, (bytes, str)) and value.startswith(b"pickle:"):
                        results.append(pickle.loads(value[7:]))
                    else:
                        results.append(value)
                else:
                    self.stats["misses"] += 1
                    results.append(None)
            return results
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Redis 集群批量獲取錯誤: {e}")
            return [None] * len(keys)

    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None):
        """批量設置"""
        try:
            # 序列化所有值
            serialized_mapping = {}
            for key, value in mapping.items():
                if not isinstance(value, (str, int, float, bool, bytes)):
                    serialized_mapping[key] = b"pickle:" + pickle.dumps(value)
                else:
                    serialized_mapping[key] = value

            pipe = self.cluster.pipeline()
            for key, value in serialized_mapping.items():
                if ttl:
                    pipe.setex(key, ttl, value)
                else:
                    pipe.set(key, value)
            pipe.execute()

            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Redis 集群批量設置錯誤: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """獲取統計資訊"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_ratio = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "total_requests": total_requests,
            "cache_hits": self.stats["hits"],
            "cache_misses": self.stats["misses"],
            "hit_ratio": hit_ratio,
            "errors": self.stats["errors"],
            "cluster_info": self.cluster.info(),
        }


class IntelligentPreloader:
    """智能預載器"""

    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.access_patterns = {}  # 記錄訪問模式
        self.prediction_model = None
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def record_access(self, key: str, context: Dict[str, Any] = None):
        """記錄訪問模式"""
        timestamp = datetime.utcnow()

        if key not in self.access_patterns:
            self.access_patterns[key] = {
                "access_times": [],
                "contexts": [],
                "frequency": 0,
            }

        self.access_patterns[key]["access_times"].append(timestamp)
        self.access_patterns[key]["contexts"].append(context or {})
        self.access_patterns[key]["frequency"] += 1

        # 保留最近的 100 次記錄
        if len(self.access_patterns[key]["access_times"]) > 100:
            self.access_patterns[key]["access_times"] = self.access_patterns[key]["access_times"][
                -100:
            ]
            self.access_patterns[key]["contexts"] = self.access_patterns[key]["contexts"][-100:]

    async def predict_next_access(self, current_key: str) -> List[str]:
        """預測下一個可能訪問的鍵"""

        # 基於關聯性的簡單預測
        related_keys = []

        # 查找經常一起訪問的鍵
        current_pattern = self.access_patterns.get(current_key, {})
        current_contexts = current_pattern.get("contexts", [])

        for key, pattern in self.access_patterns.items():
            if key == current_key:
                continue

            # 計算上下文相似性
            similarity = self._calculate_context_similarity(
                current_contexts, pattern.get("contexts", [])
            )

            if similarity > 0.5:  # 相似度閾值
                related_keys.append((key, similarity))

        # 按相似度排序
        related_keys.sort(key=lambda x: x[1], reverse=True)

        return [key for key, _ in related_keys[:10]]  # 返回前 10 個

    def _calculate_context_similarity(self, contexts1: List[Dict], contexts2: List[Dict]) -> float:
        """計算上下文相似性"""
        if not contexts1 or not contexts2:
            return 0.0

        # 簡化的相似性計算
        common_keys = set()
        for ctx1 in contexts1[-10:]:  # 只比較最近的上下文
            for ctx2 in contexts2[-10:]:
                common_keys.update(set(ctx1.keys()) & set(ctx2.keys()))

        if not common_keys:
            return 0.0

        similarity_score = len(common_keys) / max(
            len(set().union(*[ctx.keys() for ctx in contexts1[-10:]])),
            len(set().union(*[ctx.keys() for ctx in contexts2[-10:]])),
        )

        return similarity_score

    async def preload_related_data(self, key: str, data_loader: Callable):
        """預載相關數據"""
        try:
            # 預測相關鍵
            related_keys = await self.predict_next_access(key)

            # 異步預載數據
            for related_key in related_keys[:5]:  # 限制預載數量
                if not await self.cache_manager.exists(related_key):
                    # 在後台載入數據
                    self.executor.submit(self._background_load, related_key, data_loader)

        except Exception as e:
            logger.error(f"預載錯誤: {e}")

    def _background_load(self, key: str, data_loader: Callable):
        """後台載入數據"""
        try:
            data = data_loader(key)
            if data is not None:
                asyncio.run(self.cache_manager.set(key, data))
                logger.info(f"預載成功: {key}")
        except Exception as e:
            logger.warning(f"預載失敗 {key}: {e}")


class MultiTierCache:
    """多層快取系統"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

        # L1: 記憶體快取
        self.l1_cache = MemoryCache(
            max_size=config.get("l1_max_size", 1000),
            eviction_policy=EvictionPolicy(config.get("l1_eviction", "lru")),
        )

        # L2: Redis 快取
        self.l2_cache = RedisClusterCache(config.get("redis", {}))

        # 統計資訊
        self.stats = {"l1_hits": 0, "l2_hits": 0, "total_misses": 0}

    async def get(self, key: str) -> Optional[Any]:
        """多層獲取"""

        # L1 快取
        value = self.l1_cache.get(key)
        if value is not None:
            self.stats["l1_hits"] += 1
            return value

        # L2 快取
        value = await self.l2_cache.get(key)
        if value is not None:
            self.stats["l2_hits"] += 1
            # 提升到 L1
            self.l1_cache.set(key, value)
            return value

        self.stats["total_misses"] += 1
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """多層設置"""
        # 同時設置到兩層
        self.l1_cache.set(key, value, ttl)
        await self.l2_cache.set(key, value, ttl)

    async def delete(self, key: str) -> bool:
        """多層刪除"""
        l1_result = self.l1_cache.delete(key)
        l2_result = await self.l2_cache.delete(key)
        return l1_result or l2_result


class DistributedCacheManager:
    """分散式快取管理器"""

    def __init__(self, config_file: str = "config/cache-config.json"):
        self.config = self._load_config(config_file)

        # 選擇快取類型
        cache_type = CacheType(self.config.get("cache_type", "redis_cluster"))

        if cache_type == CacheType.MEMORY:
            self.cache = MemoryCache(**self.config.get("memory", {}))
        elif cache_type == CacheType.REDIS_CLUSTER:
            self.cache = RedisClusterCache(self.config.get("redis_cluster", {}))
        elif cache_type == CacheType.MULTI_TIER:
            self.cache = MultiTierCache(self.config.get("multi_tier", {}))
        else:
            raise ValueError(f"不支持的快取類型: {cache_type}")

        # 智能預載器
        self.preloader = IntelligentPreloader(self)

        # 性能監控
        self.performance_monitor = CachePerformanceMonitor()

        # 一致性哈希環（用於分片）
        nodes = self.config.get("sharding", {}).get("nodes", [])
        if nodes:
            self.hash_ring = ConsistentHash(nodes)
        else:
            self.hash_ring = None

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """載入配置"""
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"配置檔案不存在: {config_file}，使用預設配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            "cache_type": "redis_cluster",
            "redis_cluster": {
                "nodes": [
                    "localhost:7000",
                    "localhost:7001",
                    "localhost:7002",
                ],
                "password": None,
                "decode_responses": True,
            },
            "multi_tier": {
                "l1_max_size": 1000,
                "l1_eviction": "lru",
                "redis": {
                    "nodes": [
                        "localhost:7000",
                        "localhost:7001",
                        "localhost:7002",
                    ]
                },
            },
            "sharding": {"enabled": False, "nodes": []},
            "compression": {
                "enabled": True,
                "threshold_bytes": 1024,
                "algorithm": "zlib",
            },
            "monitoring": {"enabled": True, "metrics_interval": 60},
        }

    def _get_shard_key(self, key: str) -> str:
        """獲取分片鍵"""
        if self.hash_ring:
            node = self.hash_ring.get_node(key)
            return f"{node}:{key}"
        return key

    async def get(self, key: str, default: Any = None) -> Any:
        """獲取快取值"""
        start_time = time.time()

        try:
            # 記錄訪問模式
            await self.preloader.record_access(key)

            # 獲取值
            shard_key = self._get_shard_key(key)
            value = await self.cache.get(shard_key)

            # 記錄性能指標
            self.performance_monitor.record_get(time.time() - start_time, value is not None)

            return value if value is not None else default

        except Exception as e:
            logger.error(f"快取獲取錯誤: {e}")
            self.performance_monitor.record_error()
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: List[str] = None,
    ) -> bool:
        """設置快取值"""
        start_time = time.time()

        try:
            shard_key = self._get_shard_key(key)

            # 壓縮大值
            if self.config.get("compression", {}).get("enabled", False):
                value_size = len(pickle.dumps(value))
                threshold = self.config.get("compression", {}).get("threshold_bytes", 1024)
                if value_size > threshold:
                    value = self._compress_value(value)

            result = await self.cache.set(shard_key, value, ttl)

            # 記錄性能指標
            self.performance_monitor.record_set(time.time() - start_time, result)

            return result

        except Exception as e:
            logger.error(f"快取設置錯誤: {e}")
            self.performance_monitor.record_error()
            return False

    async def delete(self, key: str) -> bool:
        """刪除快取值"""
        try:
            shard_key = self._get_shard_key(key)
            return await self.cache.delete(shard_key)
        except Exception as e:
            logger.error(f"快取刪除錯誤: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        value = await self.get(key)
        return value is not None

    async def mget(self, keys: List[str]) -> List[Optional[Any]]:
        """批量獲取"""
        if hasattr(self.cache, "mget"):
            shard_keys = [self._get_shard_key(key) for key in keys]
            return await self.cache.mget(shard_keys)
        else:
            # 並發獲取
            tasks = [self.get(key) for key in keys]
            return await asyncio.gather(*tasks)

    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """批量設置"""
        if hasattr(self.cache, "mset"):
            shard_mapping = {self._get_shard_key(k): v for k, v in mapping.items()}
            return await self.cache.mset(shard_mapping, ttl)
        else:
            # 並發設置
            tasks = [self.set(key, value, ttl) for key, value in mapping.items()]
            results = await asyncio.gather(*tasks)
            return all(results)

    def _compress_value(self, value: Any) -> bytes:
        """壓縮值"""
        algorithm = self.config.get("compression", {}).get("algorithm", "zlib")
        serialized = pickle.dumps(value)

        if algorithm == "zlib":
            compressed = zlib.compress(serialized)
        else:
            compressed = serialized  # 不支持的算法不壓縮

        return b"compressed:" + compressed

    def _decompress_value(self, compressed_value: bytes) -> Any:
        """解壓縮值"""
        if compressed_value.startswith(b"compressed:"):
            algorithm = self.config.get("compression", {}).get("algorithm", "zlib")
            compressed_data = compressed_value[11:]  # 去掉前綴

            if algorithm == "zlib":
                serialized = zlib.decompress(compressed_data)
            else:
                serialized = compressed_data

            return pickle.loads(serialized)

        return pickle.loads(compressed_value)

    async def invalidate_by_tags(self, tags: List[str]):
        """按標籤失效快取"""
        # 這需要維護標籤到鍵的映射
        # 實現複雜，這裡提供介面

    def get_stats(self) -> Dict[str, Any]:
        """獲取統計資訊"""
        stats = {}

        if hasattr(self.cache, "get_stats"):
            stats.update(self.cache.get_stats())

        stats.update(self.performance_monitor.get_stats())

        return stats


class CachePerformanceMonitor:
    """快取性能監控器"""

    def __init__(self):
        self.metrics = {
            "total_gets": 0,
            "total_sets": 0,
            "total_hits": 0,
            "total_misses": 0,
            "total_errors": 0,
            "get_times": [],
            "set_times": [],
        }
        self.lock = threading.Lock()

    def record_get(self, response_time: float, hit: bool):
        """記錄獲取操作"""
        with self.lock:
            self.metrics["total_gets"] += 1
            self.metrics["get_times"].append(response_time)

            if hit:
                self.metrics["total_hits"] += 1
            else:
                self.metrics["total_misses"] += 1

            # 只保留最近的 1000 次記錄
            if len(self.metrics["get_times"]) > 1000:
                self.metrics["get_times"] = self.metrics["get_times"][-1000:]

    def record_set(self, response_time: float, success: bool):
        """記錄設置操作"""
        with self.lock:
            self.metrics["total_sets"] += 1
            self.metrics["set_times"].append(response_time)

            if len(self.metrics["set_times"]) > 1000:
                self.metrics["set_times"] = self.metrics["set_times"][-1000:]

    def record_error(self):
        """記錄錯誤"""
        with self.lock:
            self.metrics["total_errors"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """獲取統計資訊"""
        with self.lock:
            total_requests = self.metrics["total_gets"] + self.metrics["total_sets"]
            hit_ratio = (
                self.metrics["total_hits"] / self.metrics["total_gets"]
                if self.metrics["total_gets"] > 0
                else 0
            )

            avg_get_time = np.mean(self.metrics["get_times"]) if self.metrics["get_times"] else 0
            avg_set_time = np.mean(self.metrics["set_times"]) if self.metrics["set_times"] else 0

            return {
                "total_requests": total_requests,
                "total_gets": self.metrics["total_gets"],
                "total_sets": self.metrics["total_sets"],
                "cache_hits": self.metrics["total_hits"],
                "cache_misses": self.metrics["total_misses"],
                "hit_ratio": hit_ratio,
                "total_errors": self.metrics["total_errors"],
                "avg_get_time_ms": avg_get_time * 1000,
                "avg_set_time_ms": avg_set_time * 1000,
                "p95_get_time_ms": (
                    np.percentile(self.metrics["get_times"], 95) * 1000
                    if self.metrics["get_times"]
                    else 0
                ),
                "p99_get_time_ms": (
                    np.percentile(self.metrics["get_times"], 99) * 1000
                    if self.metrics["get_times"]
                    else 0
                ),
            }


# 使用示例
async def main():
    """分散式快取系統使用示例"""

    cache_manager = DistributedCacheManager()

    # 基本操作
    await cache_manager.set("user:123", {"name": "John", "age": 30}, ttl=3600)
    user_data = await cache_manager.get("user:123")
    print(f"用戶數據: {user_data}")

    # 批量操作
    users = {
        "user:124": {"name": "Alice", "age": 25},
        "user:125": {"name": "Bob", "age": 35},
    }
    await cache_manager.mset(users, ttl=3600)

    batch_users = await cache_manager.mget(["user:124", "user:125", "user:126"])
    print(f"批量獲取: {batch_users}")

    # 性能統計
    stats = cache_manager.get_stats()
    print(f"快取統計: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
