"""
Voice Enhancement Service 中介軟體
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import structlog
from prometheus_client import Counter, Histogram

logger = structlog.get_logger()

# Prometheus 指標
REQUEST_COUNT = Counter(
    "voice_enhancement_requests_total",
    "總 Voice Enhancement 請求數",
    ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "voice_enhancement_request_duration_seconds",
    "Voice Enhancement 請求處理時間",
    ["method", "endpoint"]
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
            method=method,
            endpoint=path,
            status_code=response.status_code
        ).inc()
        
        # 結構化日誌
        logger.info(
            "Voice Enhancement 請求完成",
            method=method,
            path=path,
            status_code=response.status_code,
            duration=duration,
            user_agent=request.headers.get("user-agent"),
            ip=request.client.host
        )
        
        return response