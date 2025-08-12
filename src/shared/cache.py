"""
Enterprise Cache Management System
企業級緩存管理系統 - 多層次緩存策略與優化
"""

import asyncio
import json
import pickle
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import aioredis
import structlog
from pydantic import BaseModel

logger = structlog.get_logger()


class CacheConfig(BaseModel):
    """Cache configuration"""
    
    redis_url: str = "redis://localhost:6379/0"
    default_ttl: int = 3600  # 1 hour
    key_prefix: str = "av_cache:"
    compression_enabled: bool = True
    serialization_format: str = "json"  # json, pickle
    max_memory_policy: str = "allkeys-lru"
    
    # Cache warming settings
    warming_enabled: bool = True
    warming_batch_size: int = 100
    
    # Performance settings
    connection_pool_size: int = 10
    retry_attempts: int = 3
    timeout_seconds: int = 5


class CacheStats(BaseModel):
    """Cache statistics"""
    
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
        
    @property
    def total_operations(self) -> int:
        """Total cache operations"""
        return self.hits + self.misses + self.sets + self.deletes


class CacheKey:
    """Cache key builder with namespacing"""
    
    def __init__(self, prefix: str = "av_cache:"):
        self.prefix = prefix
        
    def build(self, namespace: str, key: str, *args) -> str:
        """Build cache key with namespace"""
        key_parts = [self.prefix, namespace, key]
        if args:
            key_parts.extend(str(arg) for arg in args)
        return ":".join(key_parts)
        
    def user_key(self, user_id: int, key: str) -> str:
        """Build user-specific cache key"""
        return self.build("user", str(user_id), key)
        
    def video_key(self, video_id: str, key: str) -> str:
        """Build video-specific cache key"""
        return self.build("video", video_id, key)
        
    def ai_key(self, service: str, prompt_hash: str) -> str:
        """Build AI service cache key"""
        return self.build("ai", service, prompt_hash)
        
    def trending_key(self, platform: str, timeframe: str) -> str:
        """Build trending data cache key"""
        return self.build("trending", platform, timeframe)


class CacheSerializer:
    """Handle cache serialization/deserialization"""
    
    @staticmethod
    def serialize(data: Any, format: str = "json") -> bytes:
        """Serialize data for caching"""
        if format == "json":
            return json.dumps(data, default=str).encode('utf-8')
        elif format == "pickle":
            return pickle.dumps(data)
        else:
            raise ValueError(f"Unsupported serialization format: {format}")
            
    @staticmethod
    def deserialize(data: bytes, format: str = "json") -> Any:
        """Deserialize cached data"""
        if format == "json":
            return json.loads(data.decode('utf-8'))
        elif format == "pickle":
            return pickle.loads(data)
        else:
            raise ValueError(f"Unsupported serialization format: {format}")


class CacheBackend(ABC):
    """Abstract cache backend"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
        
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        pass
        
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass
        
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
        
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        pass


class RedisBackend(CacheBackend):
    """Redis cache backend with advanced features"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis: Optional[aioredis.Redis] = None
        self.stats = CacheStats()
        self.serializer = CacheSerializer()
        self.key_builder = CacheKey(config.key_prefix)
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await aioredis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We handle serialization manually
                max_connections=self.config.connection_pool_size,
                retry_on_timeout=True,
                socket_connect_timeout=self.config.timeout_seconds,
            )
            
            # Test connection
            await self.redis.ping()
            logger.info("Redis cache backend connected", url=self.config.redis_url)
            
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
            
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis cache backend disconnected")
            
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis with error handling"""
        if not self.redis:
            await self.connect()
            
        try:
            data = await self.redis.get(key)
            if data is None:
                self.stats.misses += 1
                return None
                
            # Deserialize data
            result = self.serializer.deserialize(data, self.config.serialization_format)
            self.stats.hits += 1
            
            logger.debug("Cache hit", key=key, size=len(data))
            return result
            
        except Exception as e:
            self.stats.errors += 1
            logger.warning("Cache get error", key=key, error=str(e))
            return None
            
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis with compression and TTL"""
        if not self.redis:
            await self.connect()
            
        try:
            # Serialize data
            data = self.serializer.serialize(value, self.config.serialization_format)
            
            # Set with TTL
            ttl = ttl or self.config.default_ttl
            await self.redis.setex(key, ttl, data)
            
            self.stats.sets += 1
            logger.debug("Cache set", key=key, ttl=ttl, size=len(data))
            return True
            
        except Exception as e:
            self.stats.errors += 1
            logger.error("Cache set error", key=key, error=str(e))
            return False
            
    async def delete(self, key: str) -> bool:
        """Delete value from Redis"""
        if not self.redis:
            await self.connect()
            
        try:
            result = await self.redis.delete(key)
            self.stats.deletes += 1
            logger.debug("Cache delete", key=key, existed=bool(result))
            return bool(result)
            
        except Exception as e:
            self.stats.errors += 1
            logger.error("Cache delete error", key=key, error=str(e))
            return False
            
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        if not self.redis:
            await self.connect()
            
        try:
            result = await self.redis.exists(key)
            return bool(result)
        except Exception as e:
            logger.error("Cache exists error", key=key, error=str(e))
            return False
            
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        if not self.redis:
            await self.connect()
            
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                deleted = await self.redis.delete(*keys)
                logger.info("Cache pattern cleared", pattern=pattern, count=deleted)
                return deleted
            return 0
            
        except Exception as e:
            logger.error("Cache pattern clear error", pattern=pattern, error=str(e))
            return 0
            
    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis and cache statistics"""
        if not self.redis:
            return {}
            
        try:
            redis_info = await self.redis.info()
            return {
                "cache_stats": self.stats.dict(),
                "redis_info": {
                    "used_memory": redis_info.get("used_memory_human"),
                    "connected_clients": redis_info.get("connected_clients"),
                    "total_commands_processed": redis_info.get("total_commands_processed"),
                    "keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "keyspace_misses": redis_info.get("keyspace_misses", 0),
                }
            }
        except Exception as e:
            logger.error("Failed to get Redis stats", error=str(e))
            return {"cache_stats": self.stats.dict()}


class CacheManager:
    """High-level cache manager with smart caching strategies"""
    
    def __init__(self, backend: CacheBackend):
        self.backend = backend
        self.key_builder = CacheKey()
        self._warming_tasks: Dict[str, asyncio.Task] = {}
        
    async def get_or_set(
        self,
        key: str,
        factory_func,
        ttl: Optional[int] = None,
        skip_cache: bool = False
    ) -> Any:
        """Get from cache or execute factory function and cache result"""
        if skip_cache:
            return await self._execute_factory(factory_func)
            
        # Try to get from cache first
        cached_value = await self.backend.get(key)
        if cached_value is not None:
            return cached_value
            
        # Execute factory function and cache result
        value = await self._execute_factory(factory_func)
        if value is not None:
            await self.backend.set(key, value, ttl)
            
        return value
        
    async def _execute_factory(self, factory_func) -> Any:
        """Execute factory function (sync or async)"""
        if asyncio.iscoroutinefunction(factory_func):
            return await factory_func()
        else:
            return factory_func()
            
    async def cache_user_data(self, user_id: int, data_type: str, data: Any, ttl: int = 3600):
        """Cache user-specific data"""
        key = self.key_builder.user_key(user_id, data_type)
        await self.backend.set(key, data, ttl)
        
    async def get_user_data(self, user_id: int, data_type: str) -> Optional[Any]:
        """Get user-specific cached data"""
        key = self.key_builder.user_key(user_id, data_type)
        return await self.backend.get(key)
        
    async def cache_ai_response(
        self,
        service: str,
        prompt: str,
        response: Any,
        ttl: int = 7200  # 2 hours for AI responses
    ):
        """Cache AI service response with prompt hash"""
        import hashlib
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        key = self.key_builder.ai_key(service, prompt_hash)
        
        cache_data = {
            "response": response,
            "cached_at": datetime.utcnow().isoformat(),
            "prompt_hash": prompt_hash,
        }
        
        await self.backend.set(key, cache_data, ttl)
        
    async def get_ai_response(self, service: str, prompt: str) -> Optional[Any]:
        """Get cached AI service response"""
        import hashlib
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        key = self.key_builder.ai_key(service, prompt_hash)
        
        cached_data = await self.backend.get(key)
        if cached_data:
            return cached_data.get("response")
        return None
        
    async def cache_trending_data(
        self,
        platform: str,
        timeframe: str,
        data: List[Dict],
        ttl: int = 1800  # 30 minutes for trending data
    ):
        """Cache trending keywords/topics data"""
        key = self.key_builder.trending_key(platform, timeframe)
        
        cache_data = {
            "data": data,
            "cached_at": datetime.utcnow().isoformat(),
            "platform": platform,
            "timeframe": timeframe,
        }
        
        await self.backend.set(key, cache_data, ttl)
        
    async def get_trending_data(self, platform: str, timeframe: str) -> Optional[List[Dict]]:
        """Get cached trending data"""
        key = self.key_builder.trending_key(platform, timeframe)
        
        cached_data = await self.backend.get(key)
        if cached_data:
            return cached_data.get("data")
        return None
        
    async def invalidate_user_cache(self, user_id: int):
        """Invalidate all cache for a specific user"""
        pattern = self.key_builder.build("user", str(user_id), "*")
        deleted = await self.backend.clear_pattern(pattern)
        logger.info("User cache invalidated", user_id=user_id, deleted_keys=deleted)
        
    async def warm_cache_async(self, warming_tasks: List[Dict[str, Any]]):
        """Warm cache with batch operations"""
        logger.info("Starting cache warming", tasks_count=len(warming_tasks))
        
        for task in warming_tasks:
            try:
                key = task["key"]
                factory = task["factory"]
                ttl = task.get("ttl")
                
                # Check if already cached
                if await self.backend.exists(key):
                    continue
                    
                # Execute factory and cache
                value = await self._execute_factory(factory)
                await self.backend.set(key, value, ttl)
                
            except Exception as e:
                logger.error("Cache warming task failed", task=task, error=str(e))
                
        logger.info("Cache warming completed")
        
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        if hasattr(self.backend, 'get_stats'):
            return await self.backend.get_stats()
        return {}


# Cache decorators for easy use
def cached(
    key_pattern: str,
    ttl: int = 3600,
    cache_manager: Optional[CacheManager] = None
):
    """Decorator for caching function results"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            if cache_manager is None:
                return await func(*args, **kwargs)
                
            # Build cache key from pattern and arguments
            import hashlib
            key_data = f"{key_pattern}:{str(args)}:{str(kwargs)}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            return await cache_manager.get_or_set(
                cache_key,
                lambda: func(*args, **kwargs),
                ttl
            )
            
        return wrapper
    return decorator


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


async def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    
    if _cache_manager is None:
        config = CacheConfig()
        backend = RedisBackend(config)
        await backend.connect()
        _cache_manager = CacheManager(backend)
        
    return _cache_manager


async def close_cache_manager():
    """Close global cache manager"""
    global _cache_manager
    
    if _cache_manager and hasattr(_cache_manager.backend, 'disconnect'):
        await _cache_manager.backend.disconnect()
        _cache_manager = None