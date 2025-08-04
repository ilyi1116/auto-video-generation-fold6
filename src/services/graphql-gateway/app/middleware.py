"""
GraphQL Gateway 中介軟體
"""

import time

import structlog
from fastapi import Request, Response
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

# Prometheus 指標
REQUEST_COUNT = Counter(
    "graphql_gateway_requests_total",
    "總 GraphQL Gateway 請求數",
    ["method", "endpoint", "status_code"],
)

REQUEST_DURATION = Histogram(
    "graphql_gateway_request_duration_seconds",
    "GraphQL Gateway 請求處理時間",
    ["method", "endpoint"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Prometheus 監控中介軟體"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        path = request.url.path

        response = await call_next(request)

        # 記錄指標
        duration = time.time() - start_time
        REQUEST_DURATION.labels(method=method, endpoint=path).observe(duration)
        REQUEST_COUNT.labels(
            method=method, endpoint=path, status_code=response.status_code
        ).inc()

        # 結構化日誌
        logger.info(
            "GraphQL Gateway 請求完成",
            method=method,
            path=path,
            status_code=response.status_code,
            duration=duration,
            user_agent=request.headers.get("user-agent"),
            ip=request.client.host,
        )

        return response


class CacheMiddleware(BaseHTTPMiddleware):
    """快取中介軟體"""

    def __init__(self, app, cache_client=None):
        super().__init__(app)
        self.cache_client = cache_client

    async def dispatch(self, request: Request, call_next):
        # 只對 GET 請求進行快取
        if request.method != "GET" or not self.cache_client:
            return await call_next(request)

        # 生成快取鍵
        cache_key = (
            f"graphql_gateway:{request.url.path}:{str(request.query_params)}"
        )

        # 檢查快取
        try:
            cached_response = await self.cache_client.get(cache_key)
            if cached_response:
                logger.info("使用快取回應", cache_key=cache_key)
                return Response(
                    content=cached_response, media_type="application/json"
                )
        except Exception as e:
            logger.warning("快取讀取失敗", error=str(e))

        # 處理請求
        response = await call_next(request)

        # 快取成功回應
        if response.status_code == 200:
            try:
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                await self.cache_client.setex(
                    cache_key,
                    300,
                    response_body.decode(),  # 5 分鐘 TTL
                )

                # 重建回應
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )
            except Exception as e:
                logger.warning("快取寫入失敗", error=str(e))

        return response
