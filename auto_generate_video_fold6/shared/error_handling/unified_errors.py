#!/usr/bin/env python3
"""
統一錯誤處理系統
提供一致的錯誤格式和處理機制
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import traceback
import json
import logging
from fastapi import HTTPException, status
from pydantic import BaseModel


class ErrorCode(Enum):
    """標準錯誤代碼"""
    
    # 通用錯誤 (1000-1999)
    UNKNOWN_ERROR = "ERR_1000"
    VALIDATION_ERROR = "ERR_1001"
    AUTHENTICATION_ERROR = "ERR_1002"
    AUTHORIZATION_ERROR = "ERR_1003"
    NOT_FOUND = "ERR_1004"
    CONFLICT = "ERR_1005"
    RATE_LIMIT_EXCEEDED = "ERR_1006"
    SERVICE_UNAVAILABLE = "ERR_1007"
    
    # 用戶相關錯誤 (2000-2999)
    USER_NOT_FOUND = "ERR_2001"
    USER_ALREADY_EXISTS = "ERR_2002"
    INVALID_CREDENTIALS = "ERR_2003"
    EMAIL_NOT_VERIFIED = "ERR_2004"
    PASSWORD_TOO_WEAK = "ERR_2005"
    
    # 影片處理錯誤 (3000-3999)
    VIDEO_PROCESSING_FAILED = "ERR_3001"
    INVALID_VIDEO_FORMAT = "ERR_3002"
    VIDEO_TOO_LARGE = "ERR_3003"
    INSUFFICIENT_STORAGE = "ERR_3004"
    RENDERING_TIMEOUT = "ERR_3005"
    
    # AI 服務錯誤 (4000-4999)
    AI_SERVICE_ERROR = "ERR_4001"
    MODEL_NOT_AVAILABLE = "ERR_4002"
    GENERATION_FAILED = "ERR_4003"
    QUOTA_EXCEEDED = "ERR_4004"
    INVALID_PROMPT = "ERR_4005"
    
    # 社群媒體錯誤 (5000-5999)
    PLATFORM_API_ERROR = "ERR_5001"
    INVALID_API_KEY = "ERR_5002"
    UPLOAD_FAILED = "ERR_5003"
    PLATFORM_RATE_LIMIT = "ERR_5004"
    CONTENT_POLICY_VIOLATION = "ERR_5005"
    
    # 資料庫錯誤 (6000-6999)
    DATABASE_CONNECTION_ERROR = "ERR_6001"
    DATABASE_TRANSACTION_ERROR = "ERR_6002"
    DATA_INTEGRITY_ERROR = "ERR_6003"
    MIGRATION_ERROR = "ERR_6004"
    
    # 外部服務錯誤 (7000-7999)
    EXTERNAL_API_ERROR = "ERR_7001"
    NETWORK_TIMEOUT = "ERR_7002"
    SERVICE_TIMEOUT = "ERR_7003"
    INVALID_RESPONSE = "ERR_7004"


class ErrorSeverity(Enum):
    """錯誤嚴重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """錯誤分類"""
    USER_ERROR = "user_error"
    SYSTEM_ERROR = "system_error"
    EXTERNAL_ERROR = "external_error"
    BUSINESS_ERROR = "business_error"


class ErrorDetail(BaseModel):
    """錯誤詳情"""
    field: Optional[str] = None
    message: str
    code: Optional[str] = None


class UnifiedError(BaseModel):
    """統一錯誤格式"""
    
    code: str
    message: str
    details: Optional[List[ErrorDetail]] = None
    severity: str = ErrorSeverity.MEDIUM.value
    category: str = ErrorCategory.SYSTEM_ERROR.value
    timestamp: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    service: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return self.dict(exclude_none=True)
    
    def to_json(self) -> str:
        """轉換為 JSON 格式"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class ErrorBuilder:
    """錯誤建構器"""
    
    def __init__(self):
        self.error_data = {
            "timestamp": datetime.now().isoformat(),
            "severity": ErrorSeverity.MEDIUM.value,
            "category": ErrorCategory.SYSTEM_ERROR.value
        }
    
    def code(self, error_code: Union[ErrorCode, str]) -> 'ErrorBuilder':
        """設置錯誤代碼"""
        if isinstance(error_code, ErrorCode):
            self.error_data["code"] = error_code.value
        else:
            self.error_data["code"] = error_code
        return self
    
    def message(self, message: str) -> 'ErrorBuilder':
        """設置錯誤消息"""
        self.error_data["message"] = message
        return self
    
    def details(self, details: List[ErrorDetail]) -> 'ErrorBuilder':
        """設置錯誤詳情"""
        self.error_data["details"] = details
        return self
    
    def add_detail(self, field: str = None, message: str = "", code: str = None) -> 'ErrorBuilder':
        """添加錯誤詳情"""
        if "details" not in self.error_data:
            self.error_data["details"] = []
        
        detail = ErrorDetail(field=field, message=message, code=code)
        self.error_data["details"].append(detail)
        return self
    
    def severity(self, severity: ErrorSeverity) -> 'ErrorBuilder':
        """設置嚴重程度"""
        self.error_data["severity"] = severity.value
        return self
    
    def category(self, category: ErrorCategory) -> 'ErrorBuilder':
        """設置錯誤分類"""
        self.error_data["category"] = category.value
        return self
    
    def request_id(self, request_id: str) -> 'ErrorBuilder':
        """設置請求 ID"""
        self.error_data["request_id"] = request_id
        return self
    
    def user_id(self, user_id: str) -> 'ErrorBuilder':
        """設置用戶 ID"""
        self.error_data["user_id"] = user_id
        return self
    
    def service(self, service: str) -> 'ErrorBuilder':
        """設置服務名稱"""
        self.error_data["service"] = service
        return self
    
    def method(self, method: str) -> 'ErrorBuilder':
        """設置方法名稱"""
        self.error_data["method"] = method
        return self
    
    def path(self, path: str) -> 'ErrorBuilder':
        """設置請求路徑"""
        self.error_data["path"] = path
        return self
    
    def context(self, context: Dict[str, Any]) -> 'ErrorBuilder':
        """設置上下文信息"""
        self.error_data["context"] = context
        return self
    
    def add_context(self, key: str, value: Any) -> 'ErrorBuilder':
        """添加上下文信息"""
        if "context" not in self.error_data:
            self.error_data["context"] = {}
        self.error_data["context"][key] = value
        return self
    
    def with_stack_trace(self) -> 'ErrorBuilder':
        """添加堆疊追蹤"""
        self.error_data["stack_trace"] = traceback.format_exc()
        return self
    
    def build(self) -> UnifiedError:
        """建構錯誤對象"""
        return UnifiedError(**self.error_data)


class ErrorHandler:
    """錯誤處理器"""
    
    def __init__(self, service_name: str, logger: logging.Logger = None):
        self.service_name = service_name
        self.logger = logger or logging.getLogger(__name__)
    
    def handle_error(self, error: Exception, request_id: str = None, 
                    user_id: str = None, context: Dict[str, Any] = None) -> UnifiedError:
        """處理異常並轉換為統一錯誤格式"""
        
        builder = ErrorBuilder().service(self.service_name)
        
        if request_id:
            builder.request_id(request_id)
        
        if user_id:
            builder.user_id(user_id)
        
        if context:
            builder.context(context)
        
        # 根據異常類型設置錯誤信息
        if isinstance(error, ValueError):
            builder.code(ErrorCode.VALIDATION_ERROR).message(str(error)).category(ErrorCategory.USER_ERROR)
        elif isinstance(error, FileNotFoundError):
            builder.code(ErrorCode.NOT_FOUND).message("資源未找到").category(ErrorCategory.USER_ERROR)
        elif isinstance(error, PermissionError):
            builder.code(ErrorCode.AUTHORIZATION_ERROR).message("權限不足").category(ErrorCategory.USER_ERROR)
        elif isinstance(error, ConnectionError):
            builder.code(ErrorCode.EXTERNAL_API_ERROR).message("外部服務連接失敗").category(ErrorCategory.EXTERNAL_ERROR).severity(ErrorSeverity.HIGH)
        elif isinstance(error, TimeoutError):
            builder.code(ErrorCode.SERVICE_TIMEOUT).message("服務超時").category(ErrorCategory.SYSTEM_ERROR).severity(ErrorSeverity.HIGH)
        else:
            builder.code(ErrorCode.UNKNOWN_ERROR).message(f"未知錯誤: {str(error)}").severity(ErrorSeverity.HIGH)
        
        # 在開發模式下添加堆疊追蹤
        import os
        if os.getenv("DEBUG", "false").lower() == "true":
            builder.with_stack_trace()
        
        unified_error = builder.build()
        
        # 記錄錯誤
        self._log_error(unified_error)
        
        return unified_error
    
    def _log_error(self, error: UnifiedError):
        """記錄錯誤"""
        log_level = self._get_log_level(error.severity)
        
        log_message = f"[{error.code}] {error.message}"
        
        extra_data = {
            "error_code": error.code,
            "severity": error.severity,
            "category": error.category,
            "service": error.service,
            "request_id": error.request_id,
            "user_id": error.user_id
        }
        
        self.logger.log(log_level, log_message, extra=extra_data)
    
    def _get_log_level(self, severity: str) -> int:
        """根據嚴重程度獲取日誌級別"""
        mapping = {
            ErrorSeverity.LOW.value: logging.INFO,
            ErrorSeverity.MEDIUM.value: logging.WARNING,
            ErrorSeverity.HIGH.value: logging.ERROR,
            ErrorSeverity.CRITICAL.value: logging.CRITICAL
        }
        return mapping.get(severity, logging.ERROR)
    
    def to_http_exception(self, error: UnifiedError) -> HTTPException:
        """轉換為 FastAPI HTTP 異常"""
        status_code_mapping = {
            ErrorCode.VALIDATION_ERROR.value: status.HTTP_400_BAD_REQUEST,
            ErrorCode.AUTHENTICATION_ERROR.value: status.HTTP_401_UNAUTHORIZED,
            ErrorCode.AUTHORIZATION_ERROR.value: status.HTTP_403_FORBIDDEN,
            ErrorCode.NOT_FOUND.value: status.HTTP_404_NOT_FOUND,
            ErrorCode.CONFLICT.value: status.HTTP_409_CONFLICT,
            ErrorCode.RATE_LIMIT_EXCEEDED.value: status.HTTP_429_TOO_MANY_REQUESTS,
            ErrorCode.SERVICE_UNAVAILABLE.value: status.HTTP_503_SERVICE_UNAVAILABLE,
        }
        
        status_code = status_code_mapping.get(error.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return HTTPException(
            status_code=status_code,
            detail=error.to_dict()
        )


# 全域錯誤處理器實例
_global_handlers: Dict[str, ErrorHandler] = {}


def get_error_handler(service_name: str) -> ErrorHandler:
    """獲取錯誤處理器"""
    if service_name not in _global_handlers:
        _global_handlers[service_name] = ErrorHandler(service_name)
    return _global_handlers[service_name]


def create_error(error_code: ErrorCode, message: str = None) -> ErrorBuilder:
    """快速創建錯誤"""
    builder = ErrorBuilder().code(error_code)
    if message:
        builder.message(message)
    return builder


# 常用錯誤快捷函數
def validation_error(message: str, field: str = None) -> UnifiedError:
    """創建驗證錯誤"""
    builder = create_error(ErrorCode.VALIDATION_ERROR, message).category(ErrorCategory.USER_ERROR)
    if field:
        builder.add_detail(field=field, message=message)
    return builder.build()


def not_found_error(resource: str) -> UnifiedError:
    """創建資源未找到錯誤"""
    return create_error(
        ErrorCode.NOT_FOUND, 
        f"{resource} 未找到"
    ).category(ErrorCategory.USER_ERROR).build()


def unauthorized_error(message: str = "未授權訪問") -> UnifiedError:
    """創建未授權錯誤"""
    return create_error(
        ErrorCode.AUTHORIZATION_ERROR, 
        message
    ).category(ErrorCategory.USER_ERROR).build()


def internal_error(message: str = "內部服務錯誤") -> UnifiedError:
    """創建內部錯誤"""
    return create_error(
        ErrorCode.UNKNOWN_ERROR, 
        message
    ).severity(ErrorSeverity.HIGH).build()


def external_service_error(service: str, message: str = None) -> UnifiedError:
    """創建外部服務錯誤"""
    if message is None:
        message = f"{service} 服務暫時不可用"
    
    return create_error(
        ErrorCode.EXTERNAL_API_ERROR, 
        message
    ).category(ErrorCategory.EXTERNAL_ERROR).severity(ErrorSeverity.HIGH).add_context("external_service", service).build()


# 錯誤統計和監控
class ErrorMetrics:
    """錯誤指標收集"""
    
    def __init__(self):
        self.error_counts = {}
        self.error_history = []
    
    def record_error(self, error: UnifiedError):
        """記錄錯誤"""
        # 統計錯誤計數
        key = f"{error.service}:{error.code}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1
        
        # 保存錯誤歷史 (最近1000條)
        self.error_history.append({
            "timestamp": error.timestamp,
            "service": error.service,
            "code": error.code,
            "severity": error.severity,
            "category": error.category
        })
        
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """獲取錯誤統計"""
        return {
            "total_errors": len(self.error_history),
            "error_counts": self.error_counts,
            "recent_errors": self.error_history[-10:]  # 最近10條
        }


# 全域錯誤指標
error_metrics = ErrorMetrics()


if __name__ == "__main__":
    # 測試錯誤處理系統
    print("=== 統一錯誤處理系統測試 ===")
    
    # 測試錯誤建構器
    error = create_error(ErrorCode.VALIDATION_ERROR, "用戶名不能為空").add_detail(
        field="username", message="用戶名是必填欄位"
    ).severity(ErrorSeverity.MEDIUM).category(ErrorCategory.USER_ERROR).build()
    
    print("建構的錯誤:")
    print(error.to_json())
    
    # 測試錯誤處理器
    handler = ErrorHandler("test-service")
    
    try:
        raise ValueError("測試錯誤")
    except Exception as e:
        handled_error = handler.handle_error(e, request_id="req-123", user_id="user-456")
        print("\n處理後的錯誤:")
        print(handled_error.to_json())
    
    # 測試快捷函數
    validation_err = validation_error("密碼太短", "password")
    print("\n驗證錯誤:")
    print(validation_err.to_json())
    
    not_found_err = not_found_error("用戶")
    print("\n未找到錯誤:")
    print(not_found_err.to_json())