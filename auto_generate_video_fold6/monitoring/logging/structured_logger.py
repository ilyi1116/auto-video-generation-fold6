"""
結構化日誌記錄模組
為 Auto Video 系統提供統一的日誌記錄功能
"""

import os
import json
import time
import logging
import traceback
from typing import Dict, Any, Optional, Union
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, asdict
from contextvars import ContextVar
import structlog
from pythonjsonlogger import jsonlogger

# 上下文變數，用於追蹤請求
request_id_context: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_context: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
trace_id_context: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)


class LogLevel(Enum):
    """日誌級別枚舉"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    """事件類型枚舉"""
    REQUEST = "request"
    RESPONSE = "response"
    ERROR = "error"
    SECURITY = "security"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    SYSTEM = "system"
    AUDIT = "audit"


@dataclass
class LogEvent:
    """結構化日誌事件"""
    timestamp: str
    level: str
    service: str
    event_type: str
    message: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    error_type: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    business_metrics: Optional[Dict[str, Any]] = None
    extra: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {k: v for k, v in asdict(self).items() if v is not None}


class StructuredLogger:
    """結構化日誌記錄器"""
    
    def __init__(
        self,
        service_name: str,
        version: str = "1.0.0",
        environment: str = "production",
        log_level: str = "INFO",
        output_file: Optional[str] = None,
        enable_console: bool = True,
        enable_json: bool = True
    ):
        self.service_name = service_name
        self.version = version
        self.environment = environment
        
        # 設定基本日誌記錄器
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # 清除現有處理器
        self.logger.handlers.clear()
        
        # 設定格式器
        if enable_json:
            formatter = jsonlogger.JsonFormatter(
                fmt='%(timestamp)s %(level)s %(service)s %(event_type)s %(message)s',
                datefmt='%Y-%m-%dT%H:%M:%S.%fZ'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        # 控制台處理器
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 檔案處理器
        if output_file:
            file_handler = logging.FileHandler(output_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # 設定 structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                self._add_context_processor,
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        self.struct_logger = structlog.get_logger()
    
    def _add_context_processor(self, logger, method_name, event_dict):
        """添加上下文資訊處理器"""
        event_dict['service'] = self.service_name
        event_dict['version'] = self.version
        event_dict['environment'] = self.environment
        event_dict['timestamp'] = datetime.now(timezone.utc).isoformat()
        
        # 添加上下文變數
        if request_id_context.get():
            event_dict['request_id'] = request_id_context.get()
        if user_id_context.get():
            event_dict['user_id'] = user_id_context.get()
        if trace_id_context.get():
            event_dict['trace_id'] = trace_id_context.get()
        
        return event_dict
    
    def _create_log_event(
        self,
        level: LogLevel,
        event_type: EventType,
        message: str,
        **kwargs
    ) -> LogEvent:
        """創建日誌事件"""
        return LogEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=level.value,
            service=self.service_name,
            event_type=event_type.value,
            message=message,
            request_id=request_id_context.get(),
            user_id=user_id_context.get(),
            trace_id=trace_id_context.get(),
            **kwargs
        )
    
    def debug(self, message: str, event_type: EventType = EventType.SYSTEM, **kwargs):
        """記錄 DEBUG 級別日誌"""
        event = self._create_log_event(LogLevel.DEBUG, event_type, message, **kwargs)
        self.struct_logger.debug(message, **event.to_dict())
    
    def info(self, message: str, event_type: EventType = EventType.SYSTEM, **kwargs):
        """記錄 INFO 級別日誌"""
        event = self._create_log_event(LogLevel.INFO, event_type, message, **kwargs)
        self.struct_logger.info(message, **event.to_dict())
    
    def warning(self, message: str, event_type: EventType = EventType.SYSTEM, **kwargs):
        """記錄 WARNING 級別日誌"""
        event = self._create_log_event(LogLevel.WARNING, event_type, message, **kwargs)
        self.struct_logger.warning(message, **event.to_dict())
    
    def error(self, message: str, event_type: EventType = EventType.ERROR, **kwargs):
        """記錄 ERROR 級別日誌"""
        event = self._create_log_event(LogLevel.ERROR, event_type, message, **kwargs)
        self.struct_logger.error(message, **event.to_dict())
    
    def critical(self, message: str, event_type: EventType = EventType.ERROR, **kwargs):
        """記錄 CRITICAL 級別日誌"""
        event = self._create_log_event(LogLevel.CRITICAL, event_type, message, **kwargs)
        self.struct_logger.critical(message, **event.to_dict())
    
    def log_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        ip_address: str = None,
        user_agent: str = None,
        **kwargs
    ):
        """記錄 HTTP 請求"""
        self.info(
            f"{method} {endpoint} - {status_code}",
            event_type=EventType.REQUEST,
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=duration_ms,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs
        )
    
    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any] = None,
        **kwargs
    ):
        """記錄錯誤"""
        error_details = {
            'type': type(error).__name__,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        self.error(
            f"Error occurred: {type(error).__name__}: {str(error)}",
            event_type=EventType.ERROR,
            error_type=type(error).__name__,
            error_details=error_details,
            **kwargs
        )
    
    def log_security_event(
        self,
        event_description: str,
        severity: str = "medium",
        source_ip: str = None,
        user_id: str = None,
        action: str = None,
        resource: str = None,
        **kwargs
    ):
        """記錄安全事件"""
        security_data = {
            'severity': severity,
            'source_ip': source_ip,
            'action': action,
            'resource': resource
        }
        
        level = LogLevel.WARNING if severity in ['low', 'medium'] else LogLevel.ERROR
        
        if level == LogLevel.ERROR:
            self.error(
                event_description,
                event_type=EventType.SECURITY,
                extra=security_data,
                **kwargs
            )
        else:
            self.warning(
                event_description,
                event_type=EventType.SECURITY,
                extra=security_data,
                **kwargs
            )
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        metrics: Dict[str, Any] = None,
        **kwargs
    ):
        """記錄效能指標"""
        perf_data = {
            'operation': operation,
            'duration_ms': duration_ms,
            'success': success,
            'metrics': metrics or {}
        }
        
        level = LogLevel.INFO if success else LogLevel.WARNING
        message = f"Performance: {operation} took {duration_ms:.2f}ms"
        
        if level == LogLevel.WARNING:
            self.warning(
                message,
                event_type=EventType.PERFORMANCE,
                extra=perf_data,
                **kwargs
            )
        else:
            self.info(
                message,
                event_type=EventType.PERFORMANCE,
                extra=perf_data,
                **kwargs
            )
    
    def log_business_event(
        self,
        event_name: str,
        metrics: Dict[str, Any],
        **kwargs
    ):
        """記錄業務事件"""
        self.info(
            f"Business event: {event_name}",
            event_type=EventType.BUSINESS,
            business_metrics=metrics,
            **kwargs
        )
    
    def log_audit(
        self,
        action: str,
        resource: str,
        user_id: str = None,
        details: Dict[str, Any] = None,
        **kwargs
    ):
        """記錄審計事件"""
        audit_data = {
            'action': action,
            'resource': resource,
            'details': details or {}
        }
        
        self.info(
            f"Audit: {action} on {resource}",
            event_type=EventType.AUDIT,
            extra=audit_data,
            **kwargs
        )


# 全域日誌記錄器實例
_global_loggers: Dict[str, StructuredLogger] = {}


def get_logger(
    service_name: str,
    version: str = "1.0.0",
    environment: str = None,
    **kwargs
) -> StructuredLogger:
    """獲取或創建日誌記錄器"""
    environment = environment or os.getenv("ENVIRONMENT", "production")
    
    logger_key = f"{service_name}:{environment}"
    
    if logger_key not in _global_loggers:
        _global_loggers[logger_key] = StructuredLogger(
            service_name=service_name,
            version=version,
            environment=environment,
            **kwargs
        )
    
    return _global_loggers[logger_key]


# 上下文管理器
class LogContext:
    """日誌上下文管理器"""
    
    def __init__(
        self,
        request_id: str = None,
        user_id: str = None,
        trace_id: str = None
    ):
        self.request_id = request_id
        self.user_id = user_id
        self.trace_id = trace_id
        self.tokens = []
    
    def __enter__(self):
        if self.request_id:
            self.tokens.append(request_id_context.set(self.request_id))
        if self.user_id:
            self.tokens.append(user_id_context.set(self.user_id))
        if self.trace_id:
            self.tokens.append(trace_id_context.set(self.trace_id))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        for token in reversed(self.tokens):
            token.var.reset(token)


# 裝飾器
def log_function_call(
    logger: StructuredLogger = None,
    include_args: bool = False,
    include_result: bool = False
):
    """函數調用日誌裝飾器"""
    def decorator(func):
        from functools import wraps
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            nonlocal logger
            if not logger:
                logger = get_logger(func.__module__)
            
            func_name = f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            log_data = {'function': func_name}
            if include_args:
                log_data['args'] = str(args)
                log_data['kwargs'] = str(kwargs)
            
            logger.debug(f"Function called: {func_name}", extra=log_data)
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                log_data['duration_ms'] = duration_ms
                if include_result:
                    log_data['result'] = str(result)
                
                logger.debug(f"Function completed: {func_name}", extra=log_data)
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Function failed: {func_name}",
                    error_type=type(e).__name__,
                    extra={'duration_ms': duration_ms}
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            nonlocal logger
            if not logger:
                logger = get_logger(func.__module__)
            
            func_name = f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            
            log_data = {'function': func_name}
            if include_args:
                log_data['args'] = str(args)
                log_data['kwargs'] = str(kwargs)
            
            logger.debug(f"Function called: {func_name}", extra=log_data)
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                log_data['duration_ms'] = duration_ms
                if include_result:
                    log_data['result'] = str(result)
                
                logger.debug(f"Function completed: {func_name}", extra=log_data)
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Function failed: {func_name}",
                    error_type=type(e).__name__,
                    extra={'duration_ms': duration_ms}
                )
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator