"""
API Gateway 模組
提供統一的API入口點，實現路由、認證、限流等功能
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .service_discovery import (
    ServiceClient,
    ServiceRegistry,
)

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """限流中間件"""

    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.call_history: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # 清理過期的請求記錄
        if client_ip in self.call_history:
            self.call_history[client_ip] = [
                t for t in self.call_history[client_ip] if current_time - t < 60
            ]
        else:
            self.call_history[client_ip] = []

        # 檢查是否超過限制
        if len(self.call_history[client_ip]) >= self.calls_per_minute:
            return JSONResponse(
                status_code=429, content={"error": "Rate limit exceeded", "retry_after": 60}
            )

        # 記錄當前請求
        self.call_history[client_ip].append(current_time)

        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


class LoadBalancerMiddleware(BaseHTTPMiddleware):
    """負載均衡中間件"""

    def __init__(self, app, service_client: ServiceClient):
        super().__init__(app)
        self.service_client = service_client

    async def dispatch(self, request: Request, call_next):
        # 檢查是否為需要代理的服務請求
        path = request.url.path

        if path.startswith("/api/v1/"):
            service_name = self._extract_service_name(path)
            if service_name:
                return await self._proxy_request(request, service_name)

        # 非代理請求，正常處理
        response = await call_next(request)
        return response

    def _extract_service_name(self, path: str) -> Optional[str]:
        """從路徑中提取服務名稱"""
        path_parts = path.strip("/").split("/")
        if len(path_parts) >= 3 and path_parts[0] == "api" and path_parts[1] == "v1":
            service_map = {
                "auth": "auth-service",
                "users": "user-service",
                "video": "video-service",
                "ai": "ai-service",
                "upload": "upload-service",
                "analytics": "analytics-service",
                "social": "social-service",
                "notifications": "notification-service",
                "storage": "storage-service",
                "payments": "payment-service",
                "search": "search-service",
                "recommendations": "recommendation-service",
                "cache": "cache-service",
            }
            return service_map.get(path_parts[2])
        return None

    async def _proxy_request(self, request: Request, service_name: str) -> Response:
        """代理請求到目標服務"""
        try:
            method = request.method
            path = request.url.path
            query_params = dict(request.query_params)
            headers = dict(request.headers)

            # 移除可能造成問題的頭部
            headers.pop("host", None)
            headers.pop("content-length", None)

            # 讀取請求體
            body = await request.body()
            data = None
            json_data = None

            if body:
                content_type = headers.get("content-type", "")
                if "application/json" in content_type:
                    try:
                        json_data = json.loads(body.decode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        data = body
                else:
                    data = body

            # 調用服務
            result = await self.service_client.call_service(
                service_name=service_name,
                method=method,
                path=path
                + (
                    "?" + "&".join(f"{k}={v}" for k, v in query_params.items())
                    if query_params
                    else ""
                ),
                data=data,
                json_data=json_data,
                headers=headers,
            )

            return JSONResponse(content=result)

        except Exception as e:
            logger.error(f"Proxy request failed: {str(e)}")
            return JSONResponse(
                status_code=503, content={"error": "Service unavailable", "detail": str(e)}
            )


class APIGateway:
    """API Gateway 主類"""

    def __init__(self, registry: ServiceRegistry):
        self.app = FastAPI(title="API Gateway", description="統一API入口點", version="1.0.0")
        self.registry = registry
        self.service_client = ServiceClient(registry)

        self._setup_middleware()
        self._setup_routes()

    def _setup_middleware(self):
        """設置中間件"""
        # CORS中間件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 生產環境中應該限制域名
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 限流中間件
        self.app.add_middleware(RateLimitMiddleware, calls_per_minute=100)

        # 負載均衡中間件
        self.app.add_middleware(LoadBalancerMiddleware, service_client=self.service_client)

    def _setup_routes(self):
        """設置路由"""

        @self.app.get("/health")
        async def health_check():
            """Gateway健康檢查"""
            service_health = {}

            for service_name, instances in self.registry._services.items():
                healthy_count = len([i for i in instances if i.is_healthy()])
                total_count = len(instances)
                service_health[service_name] = {
                    "healthy_instances": healthy_count,
                    "total_instances": total_count,
                    "status": "healthy" if healthy_count > 0 else "unhealthy",
                }

            return {
                "status": "healthy",
                "service": "api-gateway",
                "timestamp": time.time(),
                "services": service_health,
            }

        @self.app.get("/services")
        async def list_services():
            """列出所有註冊的服務"""
            services = {}

            for service_name, instances in self.registry._services.items():
                services[service_name] = [
                    {
                        "host": instance.host,
                        "port": instance.port,
                        "status": instance.status.value,
                        "response_time": instance.response_time,
                        "active_connections": instance.active_connections,
                        "last_health_check": instance.last_health_check,
                    }
                    for instance in instances
                ]

            return {"services": services}

        @self.app.post("/services/{service_name}/health-check")
        async def trigger_health_check(service_name: str):
            """觸發特定服務的健康檢查"""
            instances = self.registry.get_service_instances(service_name)
            if not instances:
                raise HTTPException(status_code=404, detail="Service not found")

            # 這裡可以觸發即時健康檢查
            results = []
            async with self.service_client:
                for instance in instances:
                    try:
                        result = await self.service_client.get(service_name, "/health")
                        results.append(
                            {
                                "instance": f"{instance.host}:{instance.port}",
                                "status": "healthy",
                                "response": result,
                            }
                        )
                    except Exception as e:
                        results.append(
                            {
                                "instance": f"{instance.host}:{instance.port}",
                                "status": "unhealthy",
                                "error": str(e),
                            }
                        )

            return {"service": service_name, "health_checks": results}

        @self.app.get("/metrics")
        async def get_metrics():
            """獲取Gateway指標"""
            total_instances = 0
            healthy_instances = 0

            for instances in self.registry._services.values():
                total_instances += len(instances)
                healthy_instances += len([i for i in instances if i.is_healthy()])

            return {
                "total_services": len(self.registry._services),
                "total_instances": total_instances,
                "healthy_instances": healthy_instances,
                "health_ratio": healthy_instances / total_instances if total_instances > 0 else 0,
            }


def create_api_gateway(registry: ServiceRegistry) -> APIGateway:
    """創建API Gateway實例"""
    return APIGateway(registry)


# 使用範例的輔助函數
async def start_gateway_with_health_checks(registry: ServiceRegistry) -> APIGateway:
    """啟動Gateway並開始健康檢查"""
    from .service_discovery import HealthChecker, register_default_services

    # 註冊預設服務
    await register_default_services()

    # 創建並啟動健康檢查器
    health_checker = HealthChecker(registry, check_interval=30)
    asyncio.create_task(health_checker.start_health_checks())

    # 創建Gateway
    gateway = create_api_gateway(registry)

    return gateway
