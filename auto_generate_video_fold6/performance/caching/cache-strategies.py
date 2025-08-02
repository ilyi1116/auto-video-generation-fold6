"""
Auto Video System 快取策略實現
包含各種快取模式和最佳化策略
"""

import asyncio
import functools
import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """快取配置"""

    default_ttl: int = 3600  # 1小時
    max_retries: int = 3
    circuit_breaker_threshold: int = 5
    compression_threshold: int = 1024  # 1KB 以上壓縮


class CacheManager:
    """統一快取管理器"""

    def __init__(self, redis_client: redis.Redis, config: CacheConfig = None):
        self.redis = redis_client
        self.config = config or CacheConfig()
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = None

    async def get(self, key: str, default: Any = None) -> Any:
        """獲取快取值"""
        try:
            if self._is_circuit_breaker_open():
                logger.warning(
                    f"Circuit breaker open, skipping cache get for {key}"
                )
                return default

            value = await self.redis.get(key)
            if value is None:
                return default

            # 解壓縮和反序列化
            return self._deserialize(value)

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self._handle_failure()
            return default

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """設置快取值"""
        try:
            if self._is_circuit_breaker_open():
                return False

            ttl = ttl or self.config.default_ttl
            serialized_value = self._serialize(value)

            await self.redis.setex(key, ttl, serialized_value)
            self._reset_circuit_breaker()
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self._handle_failure()
            return False

    async def delete(self, key: str) -> bool:
        """刪除快取"""
        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """批量獲取快取"""
        try:
            if self._is_circuit_breaker_open():
                return {}

            values = await self.redis.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = self._deserialize(value)

            return result

        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            self._handle_failure()
            return {}

    async def set_many(self, mapping: Dict[str, Any], ttl: int = None) -> bool:
        """批量設置快取"""
        try:
            if self._is_circuit_breaker_open():
                return False

            ttl = ttl or self.config.default_ttl
            pipe = self.redis.pipeline()

            for key, value in mapping.items():
                serialized_value = self._serialize(value)
                pipe.setex(key, ttl, serialized_value)

            await pipe.execute()
            self._reset_circuit_breaker()
            return True

        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            self._handle_failure()
            return False

    def _serialize(self, value: Any) -> bytes:
        """序列化值"""
        json_str = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        data = json_str.encode("utf-8")

        # 大於閾值時壓縮
        if len(data) > self.config.compression_threshold:
            import gzip

            data = gzip.compress(data)
            # 添加壓縮標記
            data = b"GZIP:" + data

        return data

    def _deserialize(self, data: bytes) -> Any:
        """反序列化值"""
        # 檢查是否壓縮
        if data.startswith(b"GZIP:"):
            import gzip

            data = gzip.decompress(data[5:])

        json_str = data.decode("utf-8")
        return json.loads(json_str)

    def _is_circuit_breaker_open(self) -> bool:
        """檢查斷路器狀態"""
        if (
            self.circuit_breaker_failures
            < self.config.circuit_breaker_threshold
        ):
            return False

        if self.circuit_breaker_last_failure is None:
            return False

        # 30秒後重試
        return (
            datetime.now() - self.circuit_breaker_last_failure
        ).seconds < 30

    def _handle_failure(self):
        """處理失敗"""
        self.circuit_breaker_failures += 1
        self.circuit_breaker_last_failure = datetime.now()

    def _reset_circuit_breaker(self):
        """重置斷路器"""
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = None


class CacheKeyGenerator:
    """快取鍵生成器"""

    @staticmethod
    def user_session(user_id: int) -> str:
        return f"session:user:{user_id}"

    @staticmethod
    def user_profile(user_id: int) -> str:
        return f"profile:user:{user_id}"

    @staticmethod
    def audio_file_metadata(file_id: int) -> str:
        return f"audio:metadata:{file_id}"

    @staticmethod
    def training_job_status(job_id: int) -> str:
        return f"training:status:{job_id}"

    @staticmethod
    def inference_result(model_id: int, input_hash: str) -> str:
        return f"inference:result:{model_id}:{input_hash}"

    @staticmethod
    def video_project_data(project_id: int) -> str:
        return f"video:project:{project_id}"

    @staticmethod
    def social_media_token(user_id: int, platform: str) -> str:
        return f"social:token:{user_id}:{platform}"

    @staticmethod
    def trend_data(platform: str, category: str = None) -> str:
        category_part = f":{category}" if category else ""
        return f"trends:{platform}{category_part}"

    @staticmethod
    def api_rate_limit(user_id: int, endpoint: str) -> str:
        return f"ratelimit:{user_id}:{endpoint}"

    @staticmethod
    def generate_hash(*args) -> str:
        """生成快取鍵雜湊"""
        content = ":".join(str(arg) for arg in args)
        return hashlib.sha256(content.encode()).hexdigest()


def cache_result(ttl: int = 3600, key_prefix: str = None):
    """快取裝飾器"""

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成快取鍵
            cache_key = _generate_cache_key(func, key_prefix, args, kwargs)

            # 從 kwargs 中獲取 cache_manager
            cache_manager = kwargs.pop("cache_manager", None)
            if not cache_manager:
                # 如果沒有快取管理器，直接執行函數
                return await func(*args, **kwargs)

            # 嘗試從快取獲取
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            # 執行函數
            result = await func(*args, **kwargs)

            # 存入快取
            if result is not None:
                await cache_manager.set(cache_key, result, ttl)
                logger.debug(f"Cache set for {cache_key}")

            return result

        return wrapper

    return decorator


def _generate_cache_key(
    func: Callable, prefix: str, args: tuple, kwargs: dict
) -> str:
    """生成快取鍵"""
    func_name = f"{func.__module__}.{func.__name__}"

    # 排除特殊參數
    filtered_kwargs = {
        k: v for k, v in kwargs.items() if k not in ["cache_manager", "db"]
    }

    # 生成參數雜湊
    args_str = ":".join(str(arg) for arg in args)
    kwargs_str = ":".join(
        f"{k}={v}" for k, v in sorted(filtered_kwargs.items())
    )

    content = f"{func_name}:{args_str}:{kwargs_str}"
    hash_key = hashlib.sha256(content.encode()).hexdigest()

    if prefix:
        return f"{prefix}:{hash_key}"
    return f"func:{hash_key}"


class SessionCache:
    """會話快取管理"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.session_ttl = 86400  # 24小時

    async def create_session(self, user_id: int, session_data: dict) -> str:
        """創建用戶會話"""
        session_id = CacheKeyGenerator.generate_hash(
            user_id, datetime.now().isoformat()
        )
        session_key = CacheKeyGenerator.user_session(user_id)

        session_info = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            **session_data,
        }

        await self.cache.set(session_key, session_info, self.session_ttl)
        return session_id

    async def get_session(self, user_id: int) -> Optional[dict]:
        """獲取用戶會話"""
        session_key = CacheKeyGenerator.user_session(user_id)
        return await self.cache.get(session_key)

    async def update_session(self, user_id: int, update_data: dict) -> bool:
        """更新會話數據"""
        session = await self.get_session(user_id)
        if not session:
            return False

        session.update(update_data)
        session["last_activity"] = datetime.now().isoformat()

        session_key = CacheKeyGenerator.user_session(user_id)
        return await self.cache.set(session_key, session, self.session_ttl)

    async def invalidate_session(self, user_id: int) -> bool:
        """使會話失效"""
        session_key = CacheKeyGenerator.user_session(user_id)
        return await self.cache.delete(session_key)


class RateLimitCache:
    """速率限制快取"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager

    async def check_rate_limit(
        self, user_id: int, endpoint: str, limit: int, window: int
    ) -> tuple[bool, int]:
        """檢查速率限制"""
        key = CacheKeyGenerator.api_rate_limit(user_id, endpoint)

        current_count = await self.cache.get(key, 0)

        if current_count >= limit:
            return False, current_count

        # 增加計數
        new_count = current_count + 1
        await self.cache.set(key, new_count, window)

        return True, new_count

    async def reset_rate_limit(self, user_id: int, endpoint: str) -> bool:
        """重置速率限制"""
        key = CacheKeyGenerator.api_rate_limit(user_id, endpoint)
        return await self.cache.delete(key)


class ModelCache:
    """AI 模型快取"""

    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.inference_ttl = 3600  # 1小時

    async def cache_inference_result(
        self, model_id: int, input_data: dict, result: Any
    ) -> bool:
        """快取推論結果"""
        input_hash = CacheKeyGenerator.generate_hash(str(input_data))
        key = CacheKeyGenerator.inference_result(model_id, input_hash)

        cache_data = {
            "result": result,
            "cached_at": datetime.now().isoformat(),
            "model_id": model_id,
            "input_hash": input_hash,
        }

        return await self.cache.set(key, cache_data, self.inference_ttl)

    async def get_cached_inference(
        self, model_id: int, input_data: dict
    ) -> Optional[Any]:
        """獲取快取的推論結果"""
        input_hash = CacheKeyGenerator.generate_hash(str(input_data))
        key = CacheKeyGenerator.inference_result(model_id, input_hash)

        cached_data = await self.cache.get(key)
        if cached_data:
            return cached_data["result"]
        return None


# 使用範例
async def example_usage():
    """使用範例"""

    # 初始化 Redis 連接
    redis_client = redis.from_url("redis://localhost:6379")

    # 創建快取管理器
    cache_config = CacheConfig(default_ttl=3600)
    cache_manager = CacheManager(redis_client, cache_config)

    # 使用快取裝飾器
    @cache_result(ttl=1800, key_prefix="user_data")
    async def get_user_data(user_id: int, cache_manager=None):
        # 模擬資料庫查詢
        await asyncio.sleep(0.1)
        return {"user_id": user_id, "name": f"User {user_id}"}

    # 調用函數（會自動快取）
    result = await get_user_data(123, cache_manager=cache_manager)
    print(f"結果: {result}")

    # 使用會話快取
    session_cache = SessionCache(cache_manager)
    session_id = await session_cache.create_session(123, {"role": "user"})
    print(f"會話 ID: {session_id}")

    # 使用速率限制
    rate_limit = RateLimitCache(cache_manager)
    allowed, count = await rate_limit.check_rate_limit(
        123, "api/upload", 10, 60
    )
    print(f"允許請求: {allowed}, 當前計數: {count}")


if __name__ == "__main__":
    asyncio.run(example_usage())
