"""
分散式追蹤中間件
提供 FastAPI 請求追蹤和上下文傳播
"""

import time
import uuid
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from .tracer import tracer, TraceContext

logger = logging.getLogger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """分散式追蹤中間件"""
    
    def __init__(self, app, service_name: str = "admin-service", 
                 exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.service_name = service_name
        self.exclude_paths = exclude_paths or [
            "/health", "/metrics", "/favicon.ico", "/docs", "/redoc", "/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """處理請求追蹤"""
        start_time = time.time()
        
        # 檢查是否需要跳過追蹤
        if self._should_skip_tracing(request):
            return await call_next(request)
        
        # 提取或創建追蹤上下文
        trace_context = self._extract_trace_context(request)
        
        # 開始新的 Span
        span_context = tracer.start_span(
            name=f"{request.method} {request.url.path}",
            parent_context=trace_context,
            attributes=self._get_request_attributes(request)
        )
        
        # 設置當前上下文
        tracer.set_current_context(span_context)
        
        # 在請求狀態中保存追蹤上下文
        request.state.trace_context = span_context
        
        try:
            # 處理請求
            response = await call_next(request)
            
            # 記錄成功回應
            self._record_response(span_context, response, start_time)
            tracer.finish_span(span_context, "success")
            
            # 添加追蹤標頭到回應
            self._add_trace_headers(response, span_context)
            
            return response
            
        except Exception as e:
            # 記錄錯誤
            self._record_error(span_context, e, start_time)
            tracer.finish_span(span_context, "error", e)
            raise
    
    def _should_skip_tracing(self, request: Request) -> bool:
        """判斷是否應該跳過追蹤"""
        path = request.url.path
        return any(path.startswith(exclude_path) for exclude_path in self.exclude_paths)
    
    def _extract_trace_context(self, request: Request) -> Optional[TraceContext]:
        """從請求標頭提取追蹤上下文"""
        # 提取標準追蹤標頭
        trace_id = request.headers.get("x-trace-id")
        span_id = request.headers.get("x-span-id") 
        parent_span_id = request.headers.get("x-parent-span-id")
        
        # 提取 OpenTelemetry 標頭
        if not trace_id:
            # 解析 traceparent 標頭 (W3C Trace Context)
            traceparent = request.headers.get("traceparent")
            if traceparent:
                try:
                    parts = traceparent.split("-")
                    if len(parts) >= 4:
                        trace_id = parts[1]
                        parent_span_id = parts[2]
                except Exception as e:
                    logger.warning(f"解析 traceparent 失敗: {e}")
        
        if trace_id:
            return TraceContext(
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                service_name=self.service_name
            )
        
        return None
    
    def _get_request_attributes(self, request: Request) -> Dict[str, Any]:
        """獲取請求屬性"""
        attributes = {
            "http.method": request.method,
            "http.url": str(request.url),
            "http.scheme": request.url.scheme,
            "http.host": request.url.hostname,
            "http.target": request.url.path,
            "http.user_agent": request.headers.get("user-agent", ""),
            "http.client_ip": self._get_client_ip(request),
            "service.name": self.service_name
        }
        
        # 添加查詢參數
        if request.query_params:
            attributes["http.query_string"] = str(request.query_params)
        
        # 添加內容類型
        content_type = request.headers.get("content-type")
        if content_type:
            attributes["http.request.content_type"] = content_type
        
        # 添加自定義標頭
        for header_name in ["x-request-id", "x-correlation-id", "x-session-id"]:
            header_value = request.headers.get(header_name)
            if header_value:
                attributes[f"http.request.header.{header_name}"] = header_value
        
        return attributes
    
    def _get_client_ip(self, request: Request) -> str:
        """獲取客戶端 IP 地址"""
        # 嘗試從不同的標頭獲取真實 IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _record_response(self, context: TraceContext, response: Response, start_time: float):
        """記錄回應資訊"""
        end_time = time.time()
        duration = end_time - start_time
        
        context.add_attribute("http.status_code", response.status_code)
        context.add_attribute("http.response.duration_ms", round(duration * 1000, 2))
        
        # 添加回應標頭
        content_type = response.headers.get("content-type")
        if content_type:
            attributes["http.response.content_type"] = content_type
        
        content_length = response.headers.get("content-length")
        if content_length:
            context.add_attribute("http.response.content_length", int(content_length))
        
        # 判斷狀態
        if response.status_code >= 400:
            context.add_attribute("error", True)
            context.add_attribute("error.type", "http_error")
    
    def _record_error(self, context: TraceContext, error: Exception, start_time: float):
        """記錄錯誤資訊"""
        end_time = time.time()
        duration = end_time - start_time
        
        context.add_attribute("http.response.duration_ms", round(duration * 1000, 2))
        context.add_attribute("error", True)
        context.add_attribute("error.type", type(error).__name__)
        context.add_attribute("error.message", str(error))
    
    def _add_trace_headers(self, response: Response, context: TraceContext):
        """添加追蹤標頭到回應"""
        response.headers["x-trace-id"] = context.trace_id
        response.headers["x-span-id"] = context.span_id
        
        if context.parent_span_id:
            response.headers["x-parent-span-id"] = context.parent_span_id


class DatabaseTracingMiddleware:
    """資料庫追蹤中間件"""
    
    def __init__(self):
        self.active_queries = {}
    
    async def before_query(self, query: str, parameters: Dict[str, Any] = None):
        """查詢前的追蹤"""
        query_id = str(uuid.uuid4())
        
        parent_context = tracer.get_current_context()
        context = tracer.start_span(
            name="db.query",
            parent_context=parent_context,
            attributes={
                "db.statement": query[:1000],  # 限制長度
                "db.type": "postgresql",
                "db.operation": self._extract_operation(query)
            }
        )
        
        if parameters:
            context.add_attribute("db.parameters", str(parameters)[:500])
        
        self.active_queries[query_id] = {
            "context": context,
            "start_time": time.time()
        }
        
        return query_id
    
    async def after_query(self, query_id: str, result_count: int = None, 
                         error: Exception = None):
        """查詢後的追蹤"""
        if query_id not in self.active_queries:
            return
        
        query_info = self.active_queries[query_id]
        context = query_info["context"]
        duration = time.time() - query_info["start_time"]
        
        context.add_attribute("db.duration_ms", round(duration * 1000, 2))
        
        if result_count is not None:
            context.add_attribute("db.result_count", result_count)
        
        if error:
            tracer.finish_span(context, "error", error)
        else:
            tracer.finish_span(context, "success")
        
        del self.active_queries[query_id]
    
    def _extract_operation(self, query: str) -> str:
        """提取 SQL 操作類型"""
        query = query.strip().upper()
        if query.startswith("SELECT"):
            return "SELECT"
        elif query.startswith("INSERT"):
            return "INSERT"
        elif query.startswith("UPDATE"):
            return "UPDATE"
        elif query.startswith("DELETE"):
            return "DELETE"
        elif query.startswith("CREATE"):
            return "CREATE"
        elif query.startswith("DROP"):
            return "DROP"
        else:
            return "OTHER"


class CeleryTracingMiddleware:
    """Celery 任務追蹤中間件"""
    
    @staticmethod
    def before_task_publish(sender=None, headers=None, body=None, 
                           properties=None, **kwargs):
        """任務發布前的追蹤"""
        current_context = tracer.get_current_context()
        if current_context:
            # 將追蹤上下文添加到任務標頭
            if headers is None:
                headers = {}
            
            headers.update({
                "trace_id": current_context.trace_id,
                "parent_span_id": current_context.span_id,
                "service_name": current_context.service_name
            })
    
    @staticmethod
    def task_prerun(sender=None, task_id=None, task=None, args=None, 
                   kwargs=None, **kwds):
        """任務執行前的追蹤"""
        # 從任務標頭提取追蹤上下文
        headers = getattr(task.request, 'headers', {})
        
        parent_context = None
        if headers.get("trace_id"):
            parent_context = TraceContext(
                trace_id=headers.get("trace_id"),
                parent_span_id=headers.get("parent_span_id"),
                service_name=headers.get("service_name", "celery-worker")
            )
        
        # 開始新的 Span
        context = tracer.start_span(
            name=f"celery.{task.name}",
            parent_context=parent_context,
            attributes={
                "celery.task_id": task_id,
                "celery.task_name": task.name,
                "celery.args": str(args),
                "celery.kwargs": str(kwargs)
            }
        )
        
        tracer.set_current_context(context)
        
        # 在任務上下文中保存追蹤資訊
        task.request.trace_context = context
    
    @staticmethod
    def task_postrun(sender=None, task_id=None, task=None, args=None, 
                    kwargs=None, retval=None, state=None, **kwds):
        """任務執行後的追蹤"""
        context = getattr(task.request, 'trace_context', None)
        if context:
            context.add_attribute("celery.result", str(retval)[:500])
            context.add_attribute("celery.state", state)
            tracer.finish_span(context, "success" if state == "SUCCESS" else "error")
    
    @staticmethod
    def task_failure(sender=None, task_id=None, exception=None, 
                    traceback=None, einfo=None, **kwds):
        """任務失敗時的追蹤"""
        context = getattr(sender.request, 'trace_context', None)
        if context:
            tracer.finish_span(context, "error", exception)


# 全域中間件實例
db_tracing = DatabaseTracingMiddleware()
celery_tracing = CeleryTracingMiddleware()