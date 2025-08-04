import logging
import json
import traceback
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from functools import wraps
import inspect
import uuid
from sqlalchemy.orm import Session
from fastapi import Request

from .models import SystemLog, LogLevel
from .database import SessionLocal
from .schemas import SystemLogCreate

# 配置標準 logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/data/data/com.termux/files/home/myProject/logs/admin_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class StructuredLogger:
    """結構化日誌記錄器"""
    
    def __init__(self):
        self.batch_logs = []
        self.batch_size = 10
        self.batch_timeout = 30  # 秒
        self._last_batch_time = datetime.utcnow()
    
    async def log(self, 
                  action: str,
                  resource_type: str,
                  level: LogLevel = LogLevel.INFO,
                  message: str = "",
                  resource_id: Optional[str] = None,
                  user_id: Optional[int] = None,
                  username: Optional[str] = None,
                  details: Optional[Dict[str, Any]] = None,
                  ip_address: Optional[str] = None,
                  user_agent: Optional[str] = None,
                  request_id: Optional[str] = None,
                  session_id: Optional[str] = None,
                  duration_ms: Optional[int] = None,
                  status_code: Optional[int] = None,
                  error_code: Optional[str] = None,
                  stack_trace: Optional[str] = None) -> bool:
        """記錄結構化日誌"""
        
        try:
            log_entry = SystemLogCreate(
                user_id=user_id,
                username=username,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                level=level,
                message=message,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                session_id=session_id,
                duration_ms=duration_ms,
                status_code=status_code,
                error_code=error_code,
                stack_trace=stack_trace
            )
            
            # 立即記錄重要日誌
            if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                await self._write_log_to_db(log_entry)
            else:
                # 批量處理其他日誌
                self.batch_logs.append(log_entry)
                
                # 檢查是否需要批量寫入
                if (len(self.batch_logs) >= self.batch_size or 
                    (datetime.utcnow() - self._last_batch_time).seconds >= self.batch_timeout):
                    await self._flush_batch_logs()
            
            # 同時寫入標準日誌
            getattr(logging.getLogger(resource_type), level.value)(
                f"{action}: {message} | Resource: {resource_type}:{resource_id} | User: {username}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"記錄日誌失敗: {e}")
            return False
    
    async def _write_log_to_db(self, log_entry: SystemLogCreate):
        """寫入日誌到資料庫"""
        db = SessionLocal()
        try:
            log_obj = SystemLog(**log_entry.dict())
            db.add(log_obj)
            db.commit()
        except Exception as e:
            logger.error(f"寫入日誌到資料庫失敗: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def _flush_batch_logs(self):
        """批量寫入日誌"""
        if not self.batch_logs:
            return
        
        db = SessionLocal()
        try:
            for log_entry in self.batch_logs:
                log_obj = SystemLog(**log_entry.dict())
                db.add(log_obj)
            
            db.commit()
            logger.info(f"批量寫入 {len(self.batch_logs)} 條日誌")
            
            self.batch_logs.clear()
            self._last_batch_time = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"批量寫入日誌失敗: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def flush(self):
        """強制刷新所有待處理日誌"""
        await self._flush_batch_logs()


# 全域日誌記錄器實例
structured_logger = StructuredLogger()


class AuditLogger:
    """審計日誌記錄器"""
    
    @staticmethod
    async def log_user_action(user_id: int, username: str, action: str, 
                             resource_type: str, resource_id: str = None,
                             details: Dict[str, Any] = None,
                             request: Request = None):
        """記錄用戶操作"""
        
        # 從請求中提取信息
        ip_address = None
        user_agent = None
        request_id = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            request_id = getattr(request.state, "request_id", None)
        
        await structured_logger.log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            username=username,
            message=f"用戶 {username} 執行了 {action} 操作",
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            level=LogLevel.INFO
        )
    
    @staticmethod
    async def log_security_event(event_type: str, severity: LogLevel,
                                message: str, details: Dict[str, Any] = None,
                                user_id: int = None, username: str = None,
                                ip_address: str = None):
        """記錄安全事件"""
        
        await structured_logger.log(
            action=f"security_{event_type}",
            resource_type="security",
            level=severity,
            message=message,
            user_id=user_id,
            username=username,
            details=details,
            ip_address=ip_address,
            error_code=event_type.upper()
        )
    
    @staticmethod
    async def log_system_event(event_type: str, message: str,
                              details: Dict[str, Any] = None,
                              level: LogLevel = LogLevel.INFO):
        """記錄系統事件"""
        
        await structured_logger.log(
            action=f"system_{event_type}",
            resource_type="system",
            level=level,
            message=message,
            details=details
        )
    
    @staticmethod
    async def log_api_request(request: Request, response_status: int,
                             duration_ms: int, user_id: int = None,
                             username: str = None):
        """記錄 API 請求"""
        
        method = request.method
        path = str(request.url.path)
        query_params = dict(request.query_params) if request.query_params else None
        
        await structured_logger.log(
            action="api_request",
            resource_type="api",
            message=f"{method} {path}",
            user_id=user_id,
            username=username,
            details={
                "method": method,
                "path": path,
                "query_params": query_params,
                "headers": dict(request.headers)
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_id=getattr(request.state, "request_id", None),
            duration_ms=duration_ms,
            status_code=response_status,
            level=LogLevel.INFO if response_status < 400 else LogLevel.WARNING
        )
    
    @staticmethod
    async def log_error(error: Exception, context: str = "",
                       user_id: int = None, username: str = None,
                       request: Request = None):
        """記錄錯誤"""
        
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context
        }
        
        # 獲取調用堆疊
        stack_trace = traceback.format_exc()
        
        await structured_logger.log(
            action="error",
            resource_type="system",
            level=LogLevel.ERROR,
            message=f"系統錯誤: {str(error)}",
            user_id=user_id,
            username=username,
            details=error_details,
            ip_address=request.client.host if request and request.client else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_id=getattr(request.state, "request_id", None) if request else None,
            stack_trace=stack_trace,
            error_code=type(error).__name__
        )


class PerformanceLogger:
    """性能日誌記錄器"""
    
    def __init__(self):
        self.request_times = []
    
    async def log_performance_metric(self, metric_name: str, value: float,
                                   unit: str = "ms", details: Dict[str, Any] = None):
        """記錄性能指標"""
        
        await structured_logger.log(
            action="performance_metric",
            resource_type="performance",
            message=f"{metric_name}: {value}{unit}",
            details={
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                **(details or {})
            },
            level=LogLevel.INFO
        )
    
    async def log_slow_query(self, query: str, duration_ms: int,
                           table_name: str = None):
        """記錄慢查詢"""
        
        if duration_ms > 1000:  # 超過1秒的查詢
            await structured_logger.log(
                action="slow_query",
                resource_type="database",
                level=LogLevel.WARNING,
                message=f"慢查詢檢測: {duration_ms}ms",
                details={
                    "query": query[:500],  # 限制查詢長度
                    "duration_ms": duration_ms,
                    "table_name": table_name
                },
                duration_ms=duration_ms
            )
    
    @contextmanager
    def time_operation(self, operation_name: str):
        """操作計時上下文管理器"""
        start_time = datetime.utcnow()
        try:
            yield
        finally:
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # 異步記錄性能日誌
            asyncio.create_task(
                self.log_performance_metric(operation_name, duration_ms)
            )


# 全域性能日誌記錄器
performance_logger = PerformanceLogger()


def log_function_call(action: str = None, resource_type: str = "function"):
    """函數調用日誌裝飾器"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            function_name = action or func.__name__
            start_time = datetime.utcnow()
            
            try:
                result = await func(*args, **kwargs)
                
                end_time = datetime.utcnow()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                await structured_logger.log(
                    action=f"function_call_{function_name}",
                    resource_type=resource_type,
                    message=f"函數 {function_name} 調用成功",
                    duration_ms=duration_ms,
                    level=LogLevel.DEBUG
                )
                
                return result
                
            except Exception as e:
                end_time = datetime.utcnow()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                await AuditLogger.log_error(
                    error=e,
                    context=f"函數調用: {function_name}"
                )
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            function_name = action or func.__name__
            start_time = datetime.utcnow()
            
            try:
                result = func(*args, **kwargs)
                
                end_time = datetime.utcnow()
                duration_ms = int((end_time - start_time).total_seconds() * 1000)
                
                # 同步函數中異步記錄日誌
                asyncio.create_task(
                    structured_logger.log(
                        action=f"function_call_{function_name}",
                        resource_type=resource_type,
                        message=f"函數 {function_name} 調用成功",
                        duration_ms=duration_ms,
                        level=LogLevel.DEBUG
                    )
                )
                
                return result
                
            except Exception as e:
                asyncio.create_task(
                    AuditLogger.log_error(
                        error=e,
                        context=f"函數調用: {function_name}"
                    )
                )
                
                raise
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class LogAnalyzer:
    """日誌分析器"""
    
    def __init__(self):
        pass
    
    async def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """獲取錯誤統計"""
        db = SessionLocal()
        
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 錯誤總數
            total_errors = db.query(SystemLog).filter(
                SystemLog.level.in_([LogLevel.ERROR, LogLevel.CRITICAL]),
                SystemLog.created_at >= start_time
            ).count()
            
            # 按錯誤類型分組
            error_types = db.query(
                SystemLog.error_code,
                db.func.count(SystemLog.id).label('count')
            ).filter(
                SystemLog.level.in_([LogLevel.ERROR, LogLevel.CRITICAL]),
                SystemLog.created_at >= start_time,
                SystemLog.error_code.isnot(None)
            ).group_by(SystemLog.error_code).all()
            
            # 按資源類型分組
            resource_errors = db.query(
                SystemLog.resource_type,
                db.func.count(SystemLog.id).label('count')
            ).filter(
                SystemLog.level.in_([LogLevel.ERROR, LogLevel.CRITICAL]),
                SystemLog.created_at >= start_time
            ).group_by(SystemLog.resource_type).all()
            
            return {
                "total_errors": total_errors,
                "timeframe_hours": hours,
                "error_types": [{"type": et.error_code, "count": et.count} for et in error_types],
                "resource_errors": [{"resource": re.resource_type, "count": re.count} for re in resource_errors]
            }
        
        finally:
            db.close()
    
    async def get_performance_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """獲取性能指標"""
        db = SessionLocal()
        
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 平均響應時間
            avg_response_time = db.query(
                db.func.avg(SystemLog.duration_ms)
            ).filter(
                SystemLog.action == "api_request",
                SystemLog.created_at >= start_time,
                SystemLog.duration_ms.isnot(None)
            ).scalar()
            
            # 慢請求數量
            slow_requests = db.query(SystemLog).filter(
                SystemLog.action == "api_request",
                SystemLog.duration_ms > 5000,  # 超過5秒
                SystemLog.created_at >= start_time
            ).count()
            
            # 請求量統計
            request_count = db.query(SystemLog).filter(
                SystemLog.action == "api_request",
                SystemLog.created_at >= start_time
            ).count()
            
            return {
                "avg_response_time_ms": float(avg_response_time) if avg_response_time else 0,
                "slow_requests": slow_requests,
                "total_requests": request_count,
                "timeframe_hours": hours
            }
        
        finally:
            db.close()


# 全域日誌分析器
log_analyzer = LogAnalyzer()


# 日誌清理任務
async def cleanup_old_logs(days: int = 30):
    """清理舊日誌"""
    db = SessionLocal()
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        deleted_count = db.query(SystemLog).filter(
            SystemLog.created_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"清理了 {deleted_count} 條超過 {days} 天的舊日誌")
        
        await structured_logger.log(
            action="log_cleanup",
            resource_type="system",
            message=f"清理了 {deleted_count} 條舊日誌",
            details={"days": days, "deleted_count": deleted_count},
            level=LogLevel.INFO
        )
        
    except Exception as e:
        logger.error(f"清理舊日誌失敗: {e}")
        await AuditLogger.log_error(e, "日誌清理任務")
    
    finally:
        db.close()


# 導出日誌
async def export_logs(start_date: datetime, end_date: datetime,
                     level: LogLevel = None, format: str = "json") -> str:
    """導出日誌"""
    db = SessionLocal()
    
    try:
        query = db.query(SystemLog).filter(
            SystemLog.created_at >= start_date,
            SystemLog.created_at <= end_date
        )
        
        if level:
            query = query.filter(SystemLog.level == level)
        
        logs = query.order_by(SystemLog.created_at.desc()).all()
        
        if format.lower() == "json":
            log_data = []
            for log in logs:
                log_dict = {
                    "id": log.id,
                    "created_at": log.created_at.isoformat(),
                    "level": log.level.value,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "user_id": log.user_id,
                    "username": log.username,
                    "message": log.message,
                    "details": log.details,
                    "ip_address": log.ip_address,
                    "status_code": log.status_code,
                    "duration_ms": log.duration_ms
                }
                log_data.append(log_dict)
            
            return json.dumps(log_data, indent=2, ensure_ascii=False)
        
        # 其他格式可以在這裡實現
        return json.dumps({"error": "不支援的導出格式"})
        
    finally:
        db.close()