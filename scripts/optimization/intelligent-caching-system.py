#!/usr/bin/env python3
"""
Intelligent Caching System
智能缓存策略系统

Features:
- Multi-level caching (Memory, Redis, Disk)
- Intelligent cache invalidation
- Predictive pre-caching
- Cache performance analytics
- Dynamic TTL optimization
- Cache warming strategies
- Memory-aware caching
- Distributed cache coordination
"""

import asyncio
import gzip
import hashlib
import json
import logging
import pickle
import platform
import sqlite3
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import aiohttp
import lru
import psutil
import redis
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache levels"""

    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_DISK = "l3_disk"


class CachePolicy(Enum):
    """Cache eviction policies"""

    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL_BASED = "ttl_based"
    ADAPTIVE = "adaptive"


@dataclass
class CacheEntry:
    """Cache entry metadata"""

    key: str
    size: int
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl: Optional[int]
    level: CacheLevel
    tags: List[str]
    compressed: bool = False
    metadata: Dict[str, Any] = None


@dataclass
class CacheMetrics:
    """Cache performance metrics"""

    cache_level: CacheLevel
    hits: int
    misses: int
    evictions: int
    memory_usage: int
    avg_access_time: float
    hit_rate: float
    throughput: float


@dataclass
class CachePattern:
    """Cache access pattern"""

    key_pattern: str
    access_frequency: float
    avg_size: int
    optimal_ttl: int
    access_times: List[datetime]
    prediction_score: float


class IntelligentCache:
    """Multi-level intelligent caching system"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.l1_cache = {}  # In-memory cache
        self.l1_metadata = {}  # L1 cache metadata
        self.l1_access_order = deque()  # For LRU
        self.l1_lock = threading.RLock()

        # Redis L2 cache
        self.redis_client = None

        # Disk L3 cache
        self.disk_cache_dir = Path(config.get("disk_cache_dir", "cache/disk"))
        self.disk_cache_dir.mkdir(parents=True, exist_ok=True)

        # Cache analytics
        self.metrics = {
            CacheLevel.L1_MEMORY: CacheMetrics(
                CacheLevel.L1_MEMORY, 0, 0, 0, 0, 0.0, 0.0, 0.0
            ),
            CacheLevel.L2_REDIS: CacheMetrics(
                CacheLevel.L2_REDIS, 0, 0, 0, 0, 0.0, 0.0, 0.0
            ),
            CacheLevel.L3_DISK: CacheMetrics(
                CacheLevel.L3_DISK, 0, 0, 0, 0, 0.0, 0.0, 0.0
            ),
        }

        # Pattern analysis
        self.access_patterns = {}
        self.pattern_analysis_interval = config.get(
            "pattern_analysis_interval", 300
        )  # 5 minutes

        # Configuration
        self.l1_max_size = config.get(
            "l1_max_size", 100 * 1024 * 1024
        )  # 100MB
        self.l1_max_entries = config.get("l1_max_entries", 10000)
        self.compression_threshold = config.get(
            "compression_threshold", 1024
        )  # 1KB
        self.default_ttl = config.get("default_ttl", 3600)  # 1 hour

        # Predictive caching
        self.prediction_model = None
        self.preload_queue = deque()

        # Performance monitoring
        self.performance_history = deque(maxlen=1000)

    async def initialize(self):
        """Initialize cache system"""
        # Initialize Redis connection
        redis_config = self.config.get("redis", {})
        if redis_config.get("enabled", True):
            try:
                self.redis_client = redis.Redis(
                    host=redis_config.get("host", "localhost"),
                    port=redis_config.get("port", 6379),
                    db=redis_config.get("db", 2),
                    decode_responses=False,  # Keep binary data
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )

                # Test connection
                self.redis_client.ping()
                logger.info("Redis L2 cache initialized")

            except Exception as e:
                logger.warning(f"Failed to initialize Redis cache: {e}")
                self.redis_client = None

        # Initialize disk cache database
        await self._init_disk_cache()

        # Start background tasks
        asyncio.create_task(self._pattern_analysis_task())
        asyncio.create_task(self._cache_maintenance_task())
        asyncio.create_task(self._predictive_caching_task())

        logger.info("Intelligent caching system initialized")

    async def _init_disk_cache(self):
        """Initialize disk cache with SQLite index"""
        db_path = self.disk_cache_dir / "cache_index.db"

        def init_db():
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    file_path TEXT,
                    size INTEGER,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    access_count INTEGER,
                    ttl INTEGER,
                    tags TEXT,
                    compressed BOOLEAN
                )
            """
            )

            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_created_at ON cache_entries(created_at)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_tags ON cache_entries(tags)"
            )

            conn.commit()
            conn.close()

        await asyncio.get_event_loop().run_in_executor(None, init_db)

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with intelligent multi-level lookup"""
        start_time = time.time()

        try:
            # L1 Memory cache
            value = await self._get_l1(key)
            if value is not None:
                self._record_hit(
                    CacheLevel.L1_MEMORY, time.time() - start_time
                )
                return value

            # L2 Redis cache
            if self.redis_client:
                value = await self._get_l2(key)
                if value is not None:
                    # Promote to L1
                    await self._set_l1(key, value, promote=True)
                    self._record_hit(
                        CacheLevel.L2_REDIS, time.time() - start_time
                    )
                    return value

            # L3 Disk cache
            value = await self._get_l3(key)
            if value is not None:
                # Promote to higher levels
                await self._set_l1(key, value, promote=True)
                if self.redis_client:
                    await self._set_l2(key, value, promote=True)
                self._record_hit(CacheLevel.L3_DISK, time.time() - start_time)
                return value

            # Cache miss
            self._record_miss_all_levels(time.time() - start_time)
            return default

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: List[str] = None,
        force_level: Optional[CacheLevel] = None,
    ) -> bool:
        """Set value in cache with intelligent level selection"""
        try:
            ttl = ttl or self.default_ttl
            tags = tags or []

            # Determine optimal cache level
            if force_level:
                target_level = force_level
            else:
                target_level = await self._select_optimal_level(
                    key, value, ttl
                )

            # Set in target level and potentially lower levels
            success = False

            if (
                target_level == CacheLevel.L1_MEMORY
                or target_level == CacheLevel.L2_REDIS
            ):
                success = await self._set_l1(key, value, ttl, tags)

            if (
                target_level == CacheLevel.L2_REDIS
                or target_level == CacheLevel.L3_DISK
            ):
                if self.redis_client:
                    await self._set_l2(key, value, ttl, tags)
                    success = True

            if target_level == CacheLevel.L3_DISK:
                success = await self._set_l3(key, value, ttl, tags)

            # Update access patterns
            self._update_access_pattern(key, len(pickle.dumps(value)))

            return success

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete from all cache levels"""
        success_count = 0

        # Delete from L1
        if await self._delete_l1(key):
            success_count += 1

        # Delete from L2
        if self.redis_client and await self._delete_l2(key):
            success_count += 1

        # Delete from L3
        if await self._delete_l3(key):
            success_count += 1

        return success_count > 0

    async def invalidate_by_tags(self, tags: List[str]) -> int:
        """Invalidate cache entries by tags"""
        invalidated_count = 0

        # L1 invalidation
        keys_to_delete = []
        with self.l1_lock:
            for key, metadata in self.l1_metadata.items():
                if any(tag in metadata.tags for tag in tags):
                    keys_to_delete.append(key)

        for key in keys_to_delete:
            if await self._delete_l1(key):
                invalidated_count += 1

        # L2 invalidation (Redis)
        if self.redis_client:
            try:
                # Use Redis SCAN to find keys with tags
                for tag in tags:
                    pattern = f"*tag:{tag}*"
                    for key in self.redis_client.scan_iter(match=pattern):
                        if self.redis_client.delete(key):
                            invalidated_count += 1
            except Exception as e:
                logger.error(f"Redis tag invalidation error: {e}")

        # L3 invalidation (Disk)
        try:
            db_path = self.disk_cache_dir / "cache_index.db"

            def invalidate_disk():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()

                count = 0
                for tag in tags:
                    cursor.execute(
                        "SELECT key, file_path FROM cache_entries WHERE tags LIKE ?",
                        (f"%{tag}%",),
                    )
                    entries = cursor.fetchall()

                    for key, file_path in entries:
                        # Delete file
                        file_path_obj = Path(file_path)
                        if file_path_obj.exists():
                            file_path_obj.unlink()

                        # Delete from index
                        cursor.execute(
                            "DELETE FROM cache_entries WHERE key = ?", (key,)
                        )
                        count += 1

                conn.commit()
                conn.close()
                return count

            disk_invalidated = await asyncio.get_event_loop().run_in_executor(
                None, invalidate_disk
            )
            invalidated_count += disk_invalidated

        except Exception as e:
            logger.error(f"Disk cache tag invalidation error: {e}")

        logger.info(
            f"Invalidated {invalidated_count} cache entries for tags: {tags}"
        )
        return invalidated_count

    async def _get_l1(self, key: str) -> Any:
        """Get from L1 memory cache"""
        with self.l1_lock:
            if key in self.l1_cache:
                # Update metadata
                metadata = self.l1_metadata[key]
                metadata.last_accessed = datetime.now()
                metadata.access_count += 1

                # Update LRU order
                if key in self.l1_access_order:
                    self.l1_access_order.remove(key)
                self.l1_access_order.append(key)

                return self.l1_cache[key]

        return None

    async def _set_l1(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: List[str] = None,
        promote: bool = False,
    ) -> bool:
        """Set in L1 memory cache"""
        try:
            # Serialize value to check size
            serialized = pickle.dumps(value)
            entry_size = len(serialized)

            # Check if should compress
            if entry_size > self.compression_threshold:
                try:
                    compressed = gzip.compress(serialized)
                    if (
                        len(compressed) < entry_size * 0.8
                    ):  # Only if 20% reduction
                        serialized = compressed
                        is_compressed = True
                    else:
                        is_compressed = False
                except:
                    is_compressed = False
            else:
                is_compressed = False

            with self.l1_lock:
                # Evict if necessary
                while (
                    len(self.l1_cache) >= self.l1_max_entries
                    or self._get_l1_memory_usage() + entry_size
                    > self.l1_max_size
                ):
                    if not self.l1_access_order:
                        break

                    oldest_key = self.l1_access_order.popleft()
                    if oldest_key in self.l1_cache:
                        del self.l1_cache[oldest_key]
                        del self.l1_metadata[oldest_key]
                        self.metrics[CacheLevel.L1_MEMORY].evictions += 1

                # Store value
                self.l1_cache[key] = value
                self.l1_metadata[key] = CacheEntry(
                    key=key,
                    size=entry_size,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    access_count=1,
                    ttl=ttl,
                    level=CacheLevel.L1_MEMORY,
                    tags=tags or [],
                    compressed=is_compressed,
                )

                # Update access order
                if key in self.l1_access_order:
                    self.l1_access_order.remove(key)
                self.l1_access_order.append(key)

            return True

        except Exception as e:
            logger.error(f"L1 cache set error: {e}")
            return False

    async def _delete_l1(self, key: str) -> bool:
        """Delete from L1 memory cache"""
        with self.l1_lock:
            if key in self.l1_cache:
                del self.l1_cache[key]
                del self.l1_metadata[key]

                if key in self.l1_access_order:
                    self.l1_access_order.remove(key)

                return True

        return False

    def _get_l1_memory_usage(self) -> int:
        """Get L1 memory usage"""
        return sum(metadata.size for metadata in self.l1_metadata.values())

    async def _get_l2(self, key: str) -> Any:
        """Get from L2 Redis cache"""
        if not self.redis_client:
            return None

        try:
            data = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.get, key
            )

            if data:
                # Check if compressed
                try:
                    # Try to decompress first
                    decompressed = gzip.decompress(data)
                    value = pickle.loads(decompressed)
                except:
                    # Not compressed or different format
                    try:
                        value = pickle.loads(data)
                    except:
                        # JSON fallback
                        value = json.loads(data.decode())

                return value

        except Exception as e:
            logger.error(f"L2 cache get error: {e}")

        return None

    async def _set_l2(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: List[str] = None,
        promote: bool = False,
    ) -> bool:
        """Set in L2 Redis cache"""
        if not self.redis_client:
            return False

        try:
            # Serialize and potentially compress
            serialized = pickle.dumps(value)

            if len(serialized) > self.compression_threshold:
                try:
                    compressed = gzip.compress(serialized)
                    if len(compressed) < len(serialized) * 0.8:
                        data = compressed
                    else:
                        data = serialized
                except:
                    data = serialized
            else:
                data = serialized

            # Set with TTL
            ttl = ttl or self.default_ttl

            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.redis_client.setex(key, ttl, data)
            )

            # Store tags for invalidation
            if tags:
                for tag in tags:
                    tag_key = f"tag:{tag}:{key}"
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.redis_client.setex(tag_key, ttl, "1"),
                    )

            return True

        except Exception as e:
            logger.error(f"L2 cache set error: {e}")
            return False

    async def _delete_l2(self, key: str) -> bool:
        """Delete from L2 Redis cache"""
        if not self.redis_client:
            return False

        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.delete, key
            )
            return result > 0

        except Exception as e:
            logger.error(f"L2 cache delete error: {e}")
            return False

    async def _get_l3(self, key: str) -> Any:
        """Get from L3 disk cache"""
        try:
            db_path = self.disk_cache_dir / "cache_index.db"

            def get_from_disk():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT file_path, compressed, ttl, created_at 
                    FROM cache_entries 
                    WHERE key = ?
                """,
                    (key,),
                )

                result = cursor.fetchone()
                if not result:
                    conn.close()
                    return None

                file_path, compressed, ttl, created_at = result

                # Check TTL
                if ttl and created_at:
                    creation_time = datetime.fromisoformat(created_at)
                    if datetime.now() > creation_time + timedelta(seconds=ttl):
                        # Expired, clean up
                        cursor.execute(
                            "DELETE FROM cache_entries WHERE key = ?", (key,)
                        )
                        conn.commit()
                        Path(file_path).unlink(missing_ok=True)
                        conn.close()
                        return None

                # Read file
                file_path_obj = Path(file_path)
                if not file_path_obj.exists():
                    # File missing, clean up index
                    cursor.execute(
                        "DELETE FROM cache_entries WHERE key = ?", (key,)
                    )
                    conn.commit()
                    conn.close()
                    return None

                with open(file_path_obj, "rb") as f:
                    data = f.read()

                # Update access time
                cursor.execute(
                    """
                    UPDATE cache_entries 
                    SET last_accessed = ?, access_count = access_count + 1 
                    WHERE key = ?
                """,
                    (datetime.now().isoformat(), key),
                )

                conn.commit()
                conn.close()

                # Deserialize
                if compressed:
                    data = gzip.decompress(data)

                return pickle.loads(data)

            return await asyncio.get_event_loop().run_in_executor(
                None, get_from_disk
            )

        except Exception as e:
            logger.error(f"L3 cache get error: {e}")
            return None

    async def _set_l3(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        tags: List[str] = None,
    ) -> bool:
        """Set in L3 disk cache"""
        try:
            # Generate file path
            key_hash = hashlib.md5(key.encode()).hexdigest()
            file_path = self.disk_cache_dir / f"{key_hash}.cache"

            # Serialize
            serialized = pickle.dumps(value)
            entry_size = len(serialized)

            # Compress if beneficial
            is_compressed = False
            if entry_size > self.compression_threshold:
                try:
                    compressed = gzip.compress(serialized)
                    if len(compressed) < entry_size * 0.8:
                        serialized = compressed
                        is_compressed = True
                except:
                    pass

            def write_to_disk():
                # Write file
                with open(file_path, "wb") as f:
                    f.write(serialized)

                # Update index
                db_path = self.disk_cache_dir / "cache_index.db"
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO cache_entries 
                    (key, file_path, size, created_at, last_accessed, access_count, ttl, tags, compressed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        key,
                        str(file_path),
                        len(serialized),
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        1,
                        ttl,
                        json.dumps(tags or []),
                        is_compressed,
                    ),
                )

                conn.commit()
                conn.close()

            await asyncio.get_event_loop().run_in_executor(None, write_to_disk)
            return True

        except Exception as e:
            logger.error(f"L3 cache set error: {e}")
            return False

    async def _delete_l3(self, key: str) -> bool:
        """Delete from L3 disk cache"""
        try:
            db_path = self.disk_cache_dir / "cache_index.db"

            def delete_from_disk():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()

                # Get file path
                cursor.execute(
                    "SELECT file_path FROM cache_entries WHERE key = ?", (key,)
                )
                result = cursor.fetchone()

                if result:
                    file_path = Path(result[0])
                    file_path.unlink(missing_ok=True)

                    # Delete from index
                    cursor.execute(
                        "DELETE FROM cache_entries WHERE key = ?", (key,)
                    )
                    conn.commit()
                    conn.close()
                    return True

                conn.close()
                return False

            return await asyncio.get_event_loop().run_in_executor(
                None, delete_from_disk
            )

        except Exception as e:
            logger.error(f"L3 cache delete error: {e}")
            return False

    async def _select_optimal_level(
        self, key: str, value: Any, ttl: int
    ) -> CacheLevel:
        """Select optimal cache level based on value characteristics"""
        try:
            # Calculate value size
            value_size = len(pickle.dumps(value))

            # Get access pattern if available
            pattern = self.access_patterns.get(key)

            # Decision logic
            if value_size < 1024 and ttl < 300:  # Small, short-lived
                return CacheLevel.L1_MEMORY
            elif (
                value_size < 10 * 1024 * 1024 and ttl < 3600
            ):  # Medium, medium-lived
                return (
                    CacheLevel.L2_REDIS
                    if self.redis_client
                    else CacheLevel.L1_MEMORY
                )
            else:  # Large or long-lived
                return CacheLevel.L3_DISK

        except:
            return CacheLevel.L1_MEMORY

    def _record_hit(self, level: CacheLevel, access_time: float):
        """Record cache hit"""
        metric = self.metrics[level]
        metric.hits += 1
        metric.avg_access_time = (metric.avg_access_time * 0.9) + (
            access_time * 0.1
        )
        self._update_hit_rate(level)

    def _record_miss_all_levels(self, access_time: float):
        """Record cache miss for all levels"""
        for level in CacheLevel:
            metric = self.metrics[level]
            metric.misses += 1
            self._update_hit_rate(level)

    def _update_hit_rate(self, level: CacheLevel):
        """Update hit rate for cache level"""
        metric = self.metrics[level]
        total_requests = metric.hits + metric.misses
        if total_requests > 0:
            metric.hit_rate = (metric.hits / total_requests) * 100

    def _update_access_pattern(self, key: str, size: int):
        """Update access pattern for key"""
        now = datetime.now()

        if key not in self.access_patterns:
            self.access_patterns[key] = CachePattern(
                key_pattern=key,
                access_frequency=1.0,
                avg_size=size,
                optimal_ttl=self.default_ttl,
                access_times=[now],
                prediction_score=0.0,
            )
        else:
            pattern = self.access_patterns[key]
            pattern.access_times.append(now)

            # Keep only recent accesses (last hour)
            cutoff_time = now - timedelta(hours=1)
            pattern.access_times = [
                t for t in pattern.access_times if t > cutoff_time
            ]

            # Update frequency (accesses per hour)
            pattern.access_frequency = len(pattern.access_times)

            # Update average size
            pattern.avg_size = (pattern.avg_size * 0.9) + (size * 0.1)

            # Calculate optimal TTL based on access frequency
            if pattern.access_frequency > 10:  # High frequency
                pattern.optimal_ttl = 3600  # 1 hour
            elif pattern.access_frequency > 1:  # Medium frequency
                pattern.optimal_ttl = 1800  # 30 minutes
            else:  # Low frequency
                pattern.optimal_ttl = 300  # 5 minutes

    async def _pattern_analysis_task(self):
        """Background task for pattern analysis"""
        while True:
            try:
                await asyncio.sleep(self.pattern_analysis_interval)
                await self._analyze_patterns()
            except Exception as e:
                logger.error(f"Pattern analysis error: {e}")

    async def _analyze_patterns(self):
        """Analyze cache access patterns"""
        now = datetime.now()
        cutoff_time = now - timedelta(hours=24)

        # Clean up old patterns
        keys_to_remove = []
        for key, pattern in self.access_patterns.items():
            if (
                not pattern.access_times
                or max(pattern.access_times) < cutoff_time
            ):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.access_patterns[key]

        # Identify hot keys for preloading
        hot_patterns = sorted(
            self.access_patterns.values(),
            key=lambda p: p.access_frequency,
            reverse=True,
        )[:10]

        # Update prediction scores
        for pattern in hot_patterns:
            if len(pattern.access_times) >= 3:
                # Simple prediction based on access interval consistency
                intervals = []
                for i in range(1, len(pattern.access_times)):
                    interval = (
                        pattern.access_times[i] - pattern.access_times[i - 1]
                    ).total_seconds()
                    intervals.append(interval)

                if intervals:
                    avg_interval = statistics.mean(intervals)
                    std_dev = (
                        statistics.stdev(intervals)
                        if len(intervals) > 1
                        else 0
                    )

                    # Lower deviation = higher predictability
                    pattern.prediction_score = (
                        max(0, 1.0 - (std_dev / avg_interval))
                        if avg_interval > 0
                        else 0
                    )

        logger.debug(
            f"Pattern analysis completed. Active patterns: {len(self.access_patterns)}"
        )

    async def _cache_maintenance_task(self):
        """Background task for cache maintenance"""
        while True:
            try:
                await asyncio.sleep(300)  # 5 minutes
                await self._perform_maintenance()
            except Exception as e:
                logger.error(f"Cache maintenance error: {e}")

    async def _perform_maintenance(self):
        """Perform cache maintenance"""
        # L1 memory maintenance
        with self.l1_lock:
            current_memory = self._get_l1_memory_usage()
            self.metrics[CacheLevel.L1_MEMORY].memory_usage = current_memory

        # L3 disk maintenance - clean expired entries
        try:
            db_path = self.disk_cache_dir / "cache_index.db"

            def cleanup_disk():
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()

                # Find expired entries
                now = datetime.now()
                cursor.execute(
                    """
                    SELECT key, file_path, ttl, created_at 
                    FROM cache_entries 
                    WHERE ttl IS NOT NULL
                """
                )

                expired_count = 0
                for key, file_path, ttl, created_at in cursor.fetchall():
                    creation_time = datetime.fromisoformat(created_at)
                    if now > creation_time + timedelta(seconds=ttl):
                        # Delete file
                        Path(file_path).unlink(missing_ok=True)

                        # Delete from index
                        cursor.execute(
                            "DELETE FROM cache_entries WHERE key = ?", (key,)
                        )
                        expired_count += 1

                conn.commit()
                conn.close()
                return expired_count

            expired_count = await asyncio.get_event_loop().run_in_executor(
                None, cleanup_disk
            )
            if expired_count > 0:
                logger.debug(
                    f"Cleaned up {expired_count} expired disk cache entries"
                )

        except Exception as e:
            logger.error(f"Disk cache cleanup error: {e}")

    async def _predictive_caching_task(self):
        """Background task for predictive caching"""
        while True:
            try:
                await asyncio.sleep(600)  # 10 minutes
                await self._perform_predictive_caching()
            except Exception as e:
                logger.error(f"Predictive caching error: {e}")

    async def _perform_predictive_caching(self):
        """Perform predictive cache preloading"""
        # Find highly predictable patterns
        predictable_patterns = [
            pattern
            for pattern in self.access_patterns.values()
            if pattern.prediction_score > 0.7 and pattern.access_frequency > 5
        ]

        for pattern in predictable_patterns[:5]:  # Top 5 predictions
            key = pattern.key_pattern

            # Check if key is likely to be accessed soon
            if pattern.access_times:
                last_access = max(pattern.access_times)
                time_since_access = (
                    datetime.now() - last_access
                ).total_seconds()

                # Predict next access based on frequency
                predicted_interval = 3600 / pattern.access_frequency  # seconds

                if time_since_access >= predicted_interval * 0.8:
                    # Queue for preloading
                    self.preload_queue.append((key, datetime.now()))

        logger.debug(
            f"Predictive caching queued {len(self.preload_queue)} items"
        )

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "levels": {},
            "patterns": {
                "total_patterns": len(self.access_patterns),
                "hot_keys": sorted(
                    [
                        (k, p.access_frequency)
                        for k, p in self.access_patterns.items()
                    ],
                    key=lambda x: x[1],
                    reverse=True,
                )[:10],
            },
            "memory_usage": {
                "l1_memory_mb": self._get_l1_memory_usage() / (1024 * 1024),
                "system_memory_percent": psutil.virtual_memory().percent,
            },
        }

        # Level statistics
        for level, metric in self.metrics.items():
            stats["levels"][level.value] = {
                "hits": metric.hits,
                "misses": metric.misses,
                "hit_rate": metric.hit_rate,
                "evictions": metric.evictions,
                "avg_access_time_ms": metric.avg_access_time * 1000,
                "memory_usage_mb": metric.memory_usage / (1024 * 1024),
            }

        # Disk cache statistics
        if (self.disk_cache_dir / "cache_index.db").exists():
            db_path = self.disk_cache_dir / "cache_index.db"

            def get_disk_stats():
                try:
                    conn = sqlite3.connect(str(db_path))
                    cursor = conn.cursor()

                    cursor.execute(
                        "SELECT COUNT(*), SUM(size) FROM cache_entries"
                    )
                    count, total_size = cursor.fetchone()

                    conn.close()
                    return {
                        "entry_count": count or 0,
                        "total_size_mb": (total_size or 0) / (1024 * 1024),
                    }
                except:
                    return {"entry_count": 0, "total_size_mb": 0}

            disk_stats = await asyncio.get_event_loop().run_in_executor(
                None, get_disk_stats
            )
            stats["levels"]["l3_disk"].update(disk_stats)

        return stats

    async def optimize_cache_configuration(self) -> Dict[str, Any]:
        """Optimize cache configuration based on usage patterns"""
        stats = await self.get_cache_statistics()
        recommendations = []

        # L1 memory analysis
        l1_stats = stats["levels"]["l1_memory"]
        l1_hit_rate = l1_stats["hit_rate"]
        memory_usage_mb = stats["memory_usage"]["l1_memory_mb"]

        if (
            l1_hit_rate < 80
            and memory_usage_mb < self.l1_max_size / (1024 * 1024) * 0.8
        ):
            recommendations.append(
                {
                    "type": "increase_l1_size",
                    "current_size_mb": self.l1_max_size / (1024 * 1024),
                    "recommended_size_mb": self.l1_max_size
                    / (1024 * 1024)
                    * 1.5,
                    "reason": f"L1 hit rate is low ({l1_hit_rate:.1f}%) and memory is underutilized",
                }
            )
        elif (
            l1_hit_rate > 95
            and memory_usage_mb > self.l1_max_size / (1024 * 1024) * 0.9
        ):
            recommendations.append(
                {
                    "type": "optimize_l1_efficiency",
                    "reason": "L1 cache is highly effective but nearly full",
                }
            )

        # Pattern-based recommendations
        hot_keys = stats["patterns"]["hot_keys"]
        if len(hot_keys) > 0:
            top_frequency = hot_keys[0][1]
            if top_frequency > 50:  # Very hot key
                recommendations.append(
                    {
                        "type": "pin_hot_keys",
                        "keys": [key for key, freq in hot_keys[:5]],
                        "reason": "Identify very frequently accessed keys for permanent L1 residence",
                    }
                )

        # Memory pressure analysis
        system_memory_percent = stats["memory_usage"]["system_memory_percent"]
        if system_memory_percent > 90:
            recommendations.append(
                {
                    "type": "reduce_memory_usage",
                    "reason": f"System memory usage is high ({system_memory_percent:.1f}%)",
                    "actions": [
                        "Increase compression threshold",
                        "Reduce L1 cache size",
                        "More aggressive eviction",
                    ],
                }
            )

        return {
            "timestamp": datetime.now().isoformat(),
            "current_config": {
                "l1_max_size_mb": self.l1_max_size / (1024 * 1024),
                "l1_max_entries": self.l1_max_entries,
                "compression_threshold": self.compression_threshold,
                "default_ttl": self.default_ttl,
            },
            "performance_summary": {
                "overall_hit_rate": sum(
                    s["hits"] for s in stats["levels"].values()
                )
                / max(
                    1,
                    sum(
                        s["hits"] + s["misses"]
                        for s in stats["levels"].values()
                    ),
                )
                * 100,
                "avg_access_time_ms": statistics.mean(
                    [s["avg_access_time_ms"] for s in stats["levels"].values()]
                ),
                "memory_efficiency": memory_usage_mb
                / (self.l1_max_size / (1024 * 1024))
                * 100,
            },
            "recommendations": recommendations,
        }


class CacheManager:
    """High-level cache manager"""

    def __init__(self, config_path: str = "config/cache-config.yaml"):
        self.config = self._load_config(config_path)
        self.cache = IntelligentCache(self.config)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load cache configuration"""
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            return self._default_config()

    def _default_config(self) -> Dict[str, Any]:
        """Default cache configuration"""
        return {
            "l1_max_size": 100 * 1024 * 1024,  # 100MB
            "l1_max_entries": 10000,
            "compression_threshold": 1024,
            "default_ttl": 3600,
            "pattern_analysis_interval": 300,
            "disk_cache_dir": "cache/disk",
            "redis": {
                "enabled": True,
                "host": "localhost",
                "port": 6379,
                "db": 2,
            },
        }

    async def initialize(self):
        """Initialize cache manager"""
        await self.cache.initialize()
        logger.info("Cache manager initialized")

    async def cached_function(
        self,
        func: Callable,
        *args,
        ttl: Optional[int] = None,
        tags: List[str] = None,
        **kwargs,
    ) -> Any:
        """Decorator-like function for caching function results"""
        # Generate cache key
        key_data = {"function": func.__name__, "args": args, "kwargs": kwargs}
        cache_key = f"func:{hashlib.md5(json.dumps(key_data, sort_keys=True, default=str).encode()).hexdigest()}"

        # Try to get from cache
        cached_result = await self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        # Execute function and cache result
        result = (
            await func(*args, **kwargs)
            if asyncio.iscoroutinefunction(func)
            else func(*args, **kwargs)
        )
        await self.cache.set(cache_key, result, ttl=ttl, tags=tags)

        return result

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return await self.cache.get_cache_statistics()

    async def optimize(self) -> Dict[str, Any]:
        """Optimize cache configuration"""
        return await self.cache.optimize_cache_configuration()


# Example usage and testing
async def example_usage():
    """Example of intelligent caching usage"""
    cache_manager = CacheManager()
    await cache_manager.initialize()

    # Basic caching
    await cache_manager.cache.set(
        "user:123", {"name": "John", "email": "john@example.com"}
    )
    user = await cache_manager.cache.get("user:123")
    print(f"Cached user: {user}")

    # Function caching
    async def expensive_computation(x: int, y: int) -> int:
        await asyncio.sleep(1)  # Simulate expensive operation
        return x * y + x**2

    # First call - will execute function
    start_time = time.time()
    result1 = await cache_manager.cached_function(expensive_computation, 5, 10)
    time1 = time.time() - start_time

    # Second call - will use cache
    start_time = time.time()
    result2 = await cache_manager.cached_function(expensive_computation, 5, 10)
    time2 = time.time() - start_time

    print(f"First call: {result1} in {time1:.3f}s")
    print(f"Second call: {result2} in {time2:.3f}s")

    # Cache statistics
    stats = await cache_manager.get_stats()
    print(f"Cache statistics: {json.dumps(stats, indent=2, default=str)}")

    # Cache optimization
    optimization = await cache_manager.optimize()
    print(
        f"Optimization recommendations: {json.dumps(optimization, indent=2, default=str)}"
    )


async def main():
    """Main function"""
    await example_usage()


if __name__ == "__main__":
    asyncio.run(main())
