"""
Auto Video System API 回應時間優化
包含各種效能優化技術和中介軟體
"""

import time
import gzip
import asyncio
import functools
from typing import Any, Callable, Optional, Dict, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.responses import JSONResponse
import json
import logging
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """效能監控中介軟體"""

    def __init__(self, app, enable_detailed_logging: bool = False):
        super().__init__(app)
        self.enable_detailed_logging = enable_detailed_logging
        self.request_times = []

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid.uuid4())[:8]

        # 添加請求 ID 到標頭
        request.state.request_id = request_id

        # 記錄請求開始
        if self.enable_detailed_logging:
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} started"
            )

        try:
            response = await call_next(request)

            # 計算處理時間
            process_time = time.time() - start_time

            # 添加效能標頭
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id

            # 記錄請求完成
            if self.enable_detailed_logging:
                logger.info(
                    f"[{request_id}] {request.method} {request.url.path} "
                    f"completed in {process_time:.3f}s - Status: {response.status_code}"
                )

            # 收集效能數據
            self._collect_metrics(request, response, process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} "
                f"failed in {process_time:.3f}s - Error: {str(e)}"
            )
            raise

    def _collect_metrics(
        self, request: Request, response: Response, process_time: float
    ):
        """收集效能指標"""
        metric = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": process_time,
            "timestamp": datetime.now().isoformat(),
        }

        # 保持最近 1000 個請求的記錄
        self.request_times.append(metric)
        if len(self.request_times) > 1000:
            self.request_times.pop(0)


class CompressionMiddleware(BaseHTTPMiddleware):
    """智慧壓縮中介軟體"""

    def __init__(
        self, app, minimum_size: int = 1024, compression_level: int = 6
    ):
        super().__init__(app)
        self.minimum_size = minimum_size
        self.compression_level = compression_level

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 檢查是否需要壓縮
        if not self._should_compress(request, response):
            return response

        # 執行壓縮
        return await self._compress_response(response)

    def _should_compress(self, request: Request, response: Response) -> bool:
        """判斷是否需要壓縮"""
        # 檢查 Accept-Encoding 標頭
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding:
            return False

        # 檢查 Content-Type
        content_type = response.headers.get("content-type", "")
        compressible_types = [
            "application/json",
            "text/plain",
            "text/html",
            "text/css",
            "application/javascript",
            "text/javascript",
        ]

        return any(ct in content_type for ct in compressible_types)

    async def _compress_response(self, response: Response) -> Response:
        """壓縮回應"""
        # 取得回應內容
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # 檢查內容大小
        if len(body) < self.minimum_size:
            return response

        # 執行 gzip 壓縮
        compressed_body = gzip.compress(
            body, compresslevel=self.compression_level
        )

        # 更新標頭
        response.headers["content-encoding"] = "gzip"
        response.headers["content-length"] = str(len(compressed_body))

        # 創建新的回應
        return Response(
            content=compressed_body,
            status_code=response.status_code,
            headers=response.headers,
            media_type=response.media_type,
        )


class CacheMiddleware(BaseHTTPMiddleware):
    """HTTP 快取中介軟體"""

    def __init__(self, app, cache_manager=None, default_ttl: int = 300):
        super().__init__(app)
        self.cache_manager = cache_manager
        self.default_ttl = default_ttl

    async def dispatch(self, request: Request, call_next):
        # 只快取 GET 請求
        if request.method != "GET" or not self.cache_manager:
            return await call_next(request)

        # 生成快取鍵
        cache_key = self._generate_cache_key(request)

        # 嘗試從快取獲取
        cached_response = await self.cache_manager.get(cache_key)
        if cached_response:
            logger.debug(f"Cache hit for {request.url.path}")
            return JSONResponse(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers={
                    **cached_response["headers"],
                    "X-Cache": "HIT",
                    "X-Cache-Key": cache_key[:16],
                },
            )

        # 執行請求
        response = await call_next(request)

        # 檢查是否應該快取
        if self._should_cache(request, response):
            await self._cache_response(cache_key, response)
            response.headers["X-Cache"] = "MISS"
            response.headers["X-Cache-Key"] = cache_key[:16]

        return response

    def _generate_cache_key(self, request: Request) -> str:
        """生成快取鍵"""
        import hashlib

        key_parts = [
            request.method,
            str(request.url),
            request.headers.get("accept", ""),
            request.headers.get("accept-language", ""),
        ]

        key_string = ":".join(key_parts)
        return f"http_cache:{hashlib.sha256(key_string.encode()).hexdigest()}"

    def _should_cache(self, request: Request, response: Response) -> bool:
        """判斷是否應該快取"""
        # 只快取成功的回應
        if response.status_code != 200:
            return False

        # 檢查 Cache-Control 標頭
        cache_control = response.headers.get("cache-control", "")
        if "no-cache" in cache_control or "no-store" in cache_control:
            return False

        # 可快取的路徑
        cacheable_paths = [
            "/api/trends",
            "/api/user/profile",
            "/api/analytics",
            "/api/models/list",
        ]

        return any(path in request.url.path for path in cacheable_paths)

    async def _cache_response(self, cache_key: str, response: Response):
        """快取回應"""
        try:
            # 讀取回應內容
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # 解析 JSON 內容
            content = json.loads(body.decode())

            cache_data = {
                "content": content,
                "status_code": response.status_code,
                "headers": dict(response.headers),
            }

            await self.cache_manager.set(
                cache_key, cache_data, self.default_ttl
            )
            logger.debug(f"Cached response for key {cache_key[:16]}")

        except Exception as e:
            logger.error(f"Failed to cache response: {e}")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中介軟體"""

    def __init__(self, app, rate_limiter=None):
        super().__init__(app)
        self.rate_limiter = rate_limiter

    async def dispatch(self, request: Request, call_next):
        if not self.rate_limiter:
            return await call_next(request)

        # 從 Authorization 標頭獲取用戶 ID
        user_id = self._extract_user_id(request)
        if not user_id:
            return await call_next(request)

        # 檢查速率限制
        endpoint = request.url.path
        allowed, current_count = await self.rate_limiter.check_rate_limit(
            user_id, endpoint, limit=100, window=60
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": 60,
                    "current_count": current_count,
                },
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)

        # 添加速率限制標頭
        response.headers["X-RateLimit-Limit"] = "100"
        response.headers["X-RateLimit-Remaining"] = str(100 - current_count)
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))

        return response

    def _extract_user_id(self, request: Request) -> Optional[int]:
        """從請求中提取用戶 ID"""
        # 這裡應該根據實際的認證方式實現
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        # 簡化版本，實際需要解析 JWT
        try:
            # 假設 token 中包含用戶 ID
            # 實際實現需要解析 JWT token
            return 1  # 示例用戶 ID
        except:
            return None


def create_optimized_app(
    cache_manager=None,
    rate_limiter=None,
    enable_compression: bool = True,
    enable_performance_logging: bool = True,
) -> FastAPI:
    """創建優化的 FastAPI 應用"""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 啟動時的初始化
        logger.info("🚀 Starting optimized Auto Video API")
        yield
        # 關閉時的清理
        logger.info("🛑 Shutting down Auto Video API")

    app = FastAPI(
        title="Auto Video API",
        description="Optimized voice cloning and video generation API",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS 中介軟體
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生產環境應該限制
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 效能監控中介軟體
    if enable_performance_logging:
        app.add_middleware(
            PerformanceMiddleware,
            enable_detailed_logging=enable_performance_logging,
        )

    # 快取中介軟體
    if cache_manager:
        app.add_middleware(
            CacheMiddleware, cache_manager=cache_manager, default_ttl=300
        )

    # 速率限制中介軟體
    if rate_limiter:
        app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)

    # 壓縮中介軟體
    if enable_compression:
        app.add_middleware(
            CompressionMiddleware, minimum_size=1024, compression_level=6
        )

    return app


# 效能優化工具函數
def async_cache(ttl: int = 300):
    """非同步函數快取裝飾器"""

    def decorator(func: Callable):
        cache = {}
        cache_times = {}

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成快取鍵
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # 檢查快取
            now = time.time()
            if cache_key in cache:
                cached_time = cache_times.get(cache_key, 0)
                if now - cached_time < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cache[cache_key]

            # 執行函數
            result = await func(*args, **kwargs)

            # 存入快取
            cache[cache_key] = result
            cache_times[cache_key] = now

            # 清理過期快取
            if len(cache) > 1000:  # 限制快取大小
                expired_keys = [
                    k for k, t in cache_times.items() if now - t > ttl
                ]
                for k in expired_keys:
                    cache.pop(k, None)
                    cache_times.pop(k, None)

            logger.debug(f"Cache miss for {func.__name__}, result cached")
            return result

        return wrapper

    return decorator


def batch_processor(batch_size: int = 10, timeout: float = 1.0):
    """批次處理裝飾器"""

    def decorator(func: Callable):
        pending_requests = []

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 創建請求項目
            future = asyncio.Future()
            request_item = (args, kwargs, future)
            pending_requests.append(request_item)

            # 如果達到批次大小，立即處理
            if len(pending_requests) >= batch_size:
                await _process_batch(func, pending_requests.copy())
                pending_requests.clear()
            else:
                # 設置超時處理
                asyncio.create_task(
                    _timeout_handler(func, pending_requests, timeout)
                )

            return await future

        return wrapper

    async def _process_batch(func: Callable, batch: List):
        """處理批次請求"""
        try:
            # 準備批次數據
            batch_args = [item[0] for item in batch]
            batch_kwargs = [item[1] for item in batch]
            futures = [item[2] for item in batch]

            # 執行批次處理
            results = await func(batch_args, batch_kwargs)

            # 設置結果
            for future, result in zip(futures, results):
                if not future.done():
                    future.set_result(result)

        except Exception as e:
            # 設置異常
            for _, _, future in batch:
                if not future.done():
                    future.set_exception(e)

    async def _timeout_handler(func: Callable, pending: List, timeout: float):
        """超時處理器"""
        await asyncio.sleep(timeout)
        if pending:
            await _process_batch(func, pending.copy())
            pending.clear()

    return decorator


# 使用範例
if __name__ == "__main__":
    # 創建優化的應用
    app = create_optimized_app(
        enable_compression=True, enable_performance_logging=True
    )

    @app.get("/api/health")
    async def health_check():
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}

    @app.get("/api/test-cache")
    @async_cache(ttl=60)
    async def test_cache():
        # 模擬慢速操作
        await asyncio.sleep(1)
        return {
            "data": "cached_result",
            "timestamp": datetime.now().isoformat(),
        }

    logger.info("API optimization configured successfully")
