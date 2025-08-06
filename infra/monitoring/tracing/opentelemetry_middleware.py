"""
OpenTelemetry 分散式追蹤中介軟體
為 FastAPI 應用程式提供完整的請求追蹤功能
"""

import logging
import os
import time
from typing import Any, Callable, Dict

from fastapi import FastAPI, Request, Response
from opentelemetry import baggage, trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.propagate import extract, inject
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.semconv.trace import SpanAttributes

logger = logging.getLogger(__name__)


class OpenTelemetryMiddleware:
    """OpenTelemetry 分散式追蹤中介軟體"""

    def __init__(
        self,
        service_name: str,
        service_version: str = "1.0.0",
        jaeger_endpoint: str = None,
        otlp_endpoint: str = None,
        environment: str = "production",
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment

        # 設定資源屬性
        resource = Resource.create(
            {
                ResourceAttributes.SERVICE_NAME: service_name,
                ResourceAttributes.SERVICE_VERSION: service_version,
                ResourceAttributes.DEPLOYMENT_ENVIRONMENT: environment,
                ResourceAttributes.SERVICE_INSTANCE_ID: os.getenv("HOSTNAME", "unknown"),
            }
        )

        # 設定追蹤器提供者
        trace.set_tracer_provider(TracerProvider(resource=resource))
        self.tracer = trace.get_tracer(__name__)

        # 設定導出器
        self._setup_exporters(jaeger_endpoint, otlp_endpoint)

        # 自動儀器化常用套件
        self._setup_auto_instrumentation()

    def _setup_exporters(self, jaeger_endpoint: str, otlp_endpoint: str):
        """設定追蹤導出器"""
        tracer_provider = trace.get_tracer_provider()

        # Jaeger 導出器
        if jaeger_endpoint:
            jaeger_exporter = JaegerExporter(
                agent_host_name=jaeger_endpoint.split("://")[1].split(":")[0],
                agent_port=int(jaeger_endpoint.split(":")[-1]),
            )
            tracer_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

        # OTLP 導出器 (優先使用)
        otlp_endpoint = otlp_endpoint or os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317"
        )
        if otlp_endpoint:
            try:
                otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
                tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
                logger.info(f"OTLP exporter configured: {otlp_endpoint}")
            except Exception as e:
                logger.warning(f"Failed to setup OTLP exporter: {e}")

    def _setup_auto_instrumentation(self):
        """設定自動儀器化"""
        try:
            # HTTP 客戶端
            HTTPXClientInstrumentor().instrument()

            # PostgreSQL
            Psycopg2Instrumentor().instrument()

            # Redis
            RedisInstrumentor().instrument()

            # Celery
            CeleryInstrumentor().instrument()

            logger.info("Auto-instrumentation setup completed")
        except Exception as e:
            logger.warning(f"Auto-instrumentation setup failed: {e}")

    def instrument_app(self, app: FastAPI):
        """為 FastAPI 應用程式添加儀器化"""
        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=trace.get_tracer_provider(),
            excluded_urls="/metrics,/health,/docs,/redoc,/openapi.json",
        )

        # 添加自訂中介軟體
        app.middleware("http")(self._custom_middleware)

    async def _custom_middleware(self, request: Request, call_next: Callable) -> Response:
        """自訂追蹤中介軟體"""
        # 提取上游追蹤上下文
        headers = dict(request.headers)
        context = extract(headers)

        # 創建新的 span
        with self.tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            context=context,
            kind=trace.SpanKind.SERVER,
        ) as span:
            # 設定基本屬性
            span.set_attributes(
                {
                    SpanAttributes.HTTP_METHOD: request.method,
                    SpanAttributes.HTTP_URL: str(request.url),
                    SpanAttributes.HTTP_SCHEME: request.url.scheme,
                    SpanAttributes.HTTP_HOST: request.url.hostname,
                    SpanAttributes.HTTP_TARGET: request.url.path,
                    SpanAttributes.USER_AGENT_ORIGINAL: request.headers.get("user-agent", ""),
                }
            )

            # 添加用戶識別資訊
            user_id = self._extract_user_id(request)
            if user_id:
                span.set_attribute("user.id", user_id)
                baggage.set_baggage("user.id", user_id)

            # 添加請求 ID 和關聯 ID
            request_id = request.headers.get("x-request-id") or self._generate_request_id()
            correlation_id = (
                request.headers.get("x-correlation-id") or self._generate_correlation_id()
            )

            span.set_attribute("request.id", request_id)
            span.set_attribute("correlation.id", correlation_id)
            baggage.set_baggage("request.id", request_id)
            baggage.set_baggage("correlation.id", correlation_id)

            start_time = time.time()

            try:
                # 注入追蹤上下文到回應標頭
                headers_to_inject = {}
                inject(headers_to_inject)

                # 執行請求
                response = await call_next(request)

                # 設定回應屬性
                span.set_attributes(
                    {
                        SpanAttributes.HTTP_STATUS_CODE: response.status_code,
                        "http.response.duration_ms": (time.time() - start_time) * 1000,
                    }
                )

                # 添加追蹤標頭到回應
                for key, value in headers_to_inject.items():
                    response.headers[key] = value

                response.headers["x-trace-id"] = format(span.get_span_context().trace_id, "032x")
                response.headers["x-span-id"] = format(span.get_span_context().span_id, "016x")
                response.headers["x-request-id"] = request_id
                response.headers["x-correlation-id"] = correlation_id

                return response

            except Exception as e:
                # 記錄錯誤
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.set_attributes(
                    {
                        SpanAttributes.HTTP_STATUS_CODE: 500,
                        "error.type": type(e).__name__,
                        "error.message": str(e),
                    }
                )
                raise

    def _extract_user_id(self, request: Request) -> str:
        """從請求中提取用戶 ID"""
        # 從 JWT token 中提取用戶 ID
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                import jwt

                token = auth_header[7:]
                payload = jwt.decode(token, options={"verify_signature": False})
                return payload.get("sub") or payload.get("user_id")
            except Exception:
                pass

        # 從查詢參數中提取
        return request.query_params.get("user_id")

    def _generate_request_id(self) -> str:
        """生成請求 ID"""
        import uuid

        return str(uuid.uuid4())

    def _generate_correlation_id(self) -> str:
        """生成關聯 ID"""
        import uuid

        return str(uuid.uuid4())

    def create_span(self, name: str, attributes: Dict[str, Any] = None) -> trace.Span:
        """創建新的 span"""
        span = self.tracer.start_span(name)
        if attributes:
            span.set_attributes(attributes)
        return span

    def add_span_event(self, span: trace.Span, name: str, attributes: Dict[str, Any] = None):
        """添加 span 事件"""
        span.add_event(name, attributes or {})

    def record_exception(self, span: trace.Span, exception: Exception):
        """記錄異常到 span"""
        span.record_exception(exception)
        span.set_status(trace.Status(trace.StatusCode.ERROR, str(exception)))


# 使用範例和工具函數
def setup_tracing(
    app: FastAPI,
    service_name: str,
    service_version: str = "1.0.0",
    jaeger_endpoint: str = None,
    otlp_endpoint: str = None,
    environment: str = None,
) -> OpenTelemetryMiddleware:
    """設定應用程式追蹤"""
    environment = environment or os.getenv("ENVIRONMENT", "production")

    middleware = OpenTelemetryMiddleware(
        service_name=service_name,
        service_version=service_version,
        jaeger_endpoint=jaeger_endpoint,
        otlp_endpoint=otlp_endpoint,
        environment=environment,
    )

    middleware.instrument_app(app)
    return middleware


def trace_function(operation_name: str = None):
    """函數追蹤裝飾器"""

    def decorator(func):
        from functools import wraps

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(name) as span:
                span.set_attributes(
                    {
                        "function.name": func.__name__,
                        "function.module": func.__module__,
                    }
                )

                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("function.result", "success")
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            name = operation_name or f"{func.__module__}.{func.__name__}"

            with tracer.start_as_current_span(name) as span:
                span.set_attributes(
                    {
                        "function.name": func.__name__,
                        "function.module": func.__module__,
                    }
                )

                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("function.result", "success")
                    return result
                except Exception as e:
                    span.record_exception(e)
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# 資料庫追蹤工具
class DatabaseTracing:
    """資料庫操作追蹤工具"""

    @staticmethod
    def trace_query(operation: str, table: str = None):
        """追蹤資料庫查詢"""

        def decorator(func):
            from functools import wraps

            @wraps(func)
            async def wrapper(*args, **kwargs):
                tracer = trace.get_tracer(__name__)

                with tracer.start_as_current_span(f"db.{operation}") as span:
                    span.set_attributes(
                        {
                            "db.operation": operation,
                            "db.system": "postgresql",
                        }
                    )

                    if table:
                        span.set_attribute("db.collection.name", table)

                    try:
                        result = await func(*args, **kwargs)

                        # 記錄結果統計
                        if hasattr(result, "rowcount"):
                            span.set_attribute("db.rows_affected", result.rowcount)

                        return result
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        raise

            return wrapper

        return decorator


# HTTP 客戶端追蹤工具
class HTTPClientTracing:
    """HTTP 客戶端追蹤工具"""

    @staticmethod
    def trace_request(service_name: str = None):
        """追蹤 HTTP 請求"""

        def decorator(func):
            from functools import wraps

            @wraps(func)
            async def wrapper(*args, **kwargs):
                tracer = trace.get_tracer(__name__)

                # 提取 URL 資訊
                url = kwargs.get("url") or (args[0] if args else "unknown")
                method = kwargs.get("method", "GET")

                with tracer.start_as_current_span(f"http.{method}") as span:
                    span.set_attributes(
                        {
                            SpanAttributes.HTTP_METHOD: method,
                            SpanAttributes.HTTP_URL: str(url),
                            "http.client.service": service_name or "external",
                        }
                    )

                    try:
                        response = await func(*args, **kwargs)

                        if hasattr(response, "status_code"):
                            span.set_attribute(
                                SpanAttributes.HTTP_STATUS_CODE,
                                response.status_code,
                            )

                        return response
                    except Exception as e:
                        span.record_exception(e)
                        span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        raise

            return wrapper

        return decorator
