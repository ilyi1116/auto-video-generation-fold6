#!/usr/bin/env python3
"""
標準 API 回應格式
確保所有服務的 API 回應格式統一
"""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from fastapi import status
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseStatus(Enum):
    """回應狀態"""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class PaginationInfo(BaseModel):
    """分頁信息"""

    page: int = Field(ge=1, description="當前頁碼")
    size: int = Field(ge=1, le=100, description="每頁大小")
    total: int = Field(ge=0, description="總記錄數")
    pages: int = Field(ge=0, description="總頁數")
    has_next: bool = Field(description="是否有下一頁")
    has_prev: bool = Field(description="是否有上一頁")

    @classmethod
    def create(cls, page: int, size: int, total: int) -> "PaginationInfo":
        """創建分頁信息"""
        pages = (total + size - 1) // size  # 向上取整
        return cls(
            page=page,
            size=size,
            total=total,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1,
        )


class APIMetadata(BaseModel):
    """API 元數據"""

    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    request_id: Optional[str] = None
    version: str = "v1"
    service: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    execution_time_ms: Optional[float] = None
    user_id: Optional[str] = None


class StandardResponse(BaseModel, Generic[T]):
    """標準 API 回應格式"""

    status: ResponseStatus = Field(description="回應狀態")
    message: str = Field(description="回應消息")
    data: Optional[T] = Field(default=None, description="回應數據")
    errors: Optional[List[Dict[str, Any]]] = Field(default=None, description="錯誤詳情")
    warnings: Optional[List[str]] = Field(default=None, description="警告信息")
    pagination: Optional[PaginationInfo] = Field(default=None, description="分頁信息")
    metadata: APIMetadata = Field(default_factory=APIMetadata, description="元數據")

    class Config:
        use_enum_values = True

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return self.dict(exclude_none=True)

    def to_json(self) -> str:
        """轉換為 JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class PaginatedResponse(StandardResponse[List[T]]):
    """分頁回應格式"""

    pagination: PaginationInfo = Field(description="分頁信息")


class ResponseBuilder:
    """回應建構器"""

    def __init__(self):
        self.response_data: Dict[str, Any] = {"metadata": APIMetadata()}

    def status(self, status: ResponseStatus) -> "ResponseBuilder":
        """設置狀態"""
        self.response_data["status"] = status
        return self

    def message(self, message: str) -> "ResponseBuilder":
        """設置消息"""
        self.response_data["message"] = message
        return self

    def data(self, data: Any) -> "ResponseBuilder":
        """設置數據"""
        self.response_data["data"] = data
        return self

    def errors(self, errors: List[Dict[str, Any]]) -> "ResponseBuilder":
        """設置錯誤"""
        self.response_data["errors"] = errors
        return self

    def add_error(self, code: str, message: str, field: Optional[str] = None) -> "ResponseBuilder":
        """添加錯誤"""
        if "errors" not in self.response_data:
            self.response_data["errors"] = []

        error = {"code": code, "message": message}
        if field:
            error["field"] = field

        self.response_data["errors"].append(error)
        return self

    def warnings(self, warnings: List[str]) -> "ResponseBuilder":
        """設置警告"""
        self.response_data["warnings"] = warnings
        return self

    def add_warning(self, warning: str) -> "ResponseBuilder":
        """添加警告"""
        if "warnings" not in self.response_data:
            self.response_data["warnings"] = []
        self.response_data["warnings"].append(warning)
        return self

    def pagination(self, pagination: PaginationInfo) -> "ResponseBuilder":
        """設置分頁"""
        self.response_data["pagination"] = pagination
        return self

    def request_id(self, request_id: str) -> "ResponseBuilder":
        """設置請求 ID"""
        self.response_data["metadata"].request_id = request_id
        return self

    def service(self, service: str) -> "ResponseBuilder":
        """設置服務名稱"""
        self.response_data["metadata"].service = service
        return self

    def method(self, method: str) -> "ResponseBuilder":
        """設置方法"""
        self.response_data["metadata"].method = method
        return self

    def path(self, path: str) -> "ResponseBuilder":
        """設置路徑"""
        self.response_data["metadata"].path = path
        return self

    def execution_time(self, time_ms: float) -> "ResponseBuilder":
        """設置執行時間"""
        self.response_data["metadata"].execution_time_ms = time_ms
        return self

    def user_id(self, user_id: str) -> "ResponseBuilder":
        """設置用戶 ID"""
        self.response_data["metadata"].user_id = user_id
        return self

    def build(self) -> StandardResponse:
        """建構回應"""
        return StandardResponse(**self.response_data)


# 快捷回應函數
def success_response(
    message: str = "操作成功", data: Any = None, request_id: str = None
) -> StandardResponse:
    """成功回應"""
    builder = ResponseBuilder().status(ResponseStatus.SUCCESS).message(message)

    if data is not None:
        builder.data(data)

    if request_id:
        builder.request_id(request_id)

    return builder.build()


def error_response(
    message: str,
    errors: List[Dict[str, Any]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    request_id: str = None,
) -> StandardResponse:
    """錯誤回應"""
    builder = ResponseBuilder().status(ResponseStatus.ERROR).message(message)

    if errors:
        builder.errors(errors)

    if request_id:
        builder.request_id(request_id)

    return builder.build()


def validation_error_response(
    field_errors: Dict[str, str],
    message: str = "輸入驗證失敗",
    request_id: str = None,
) -> StandardResponse:
    """驗證錯誤回應"""
    errors = [
        {"code": "VALIDATION_ERROR", "field": field, "message": msg}
        for field, msg in field_errors.items()
    ]

    return error_response(message, errors, status.HTTP_422_UNPROCESSABLE_ENTITY, request_id)


def not_found_response(resource: str = "資源", request_id: str = None) -> StandardResponse:
    """未找到回應"""
    return error_response(
        f"{resource}未找到",
        [{"code": "NOT_FOUND", "message": f"請求的{resource}不存在"}],
        status.HTTP_404_NOT_FOUND,
        request_id,
    )


def unauthorized_response(message: str = "未授權訪問", request_id: str = None) -> StandardResponse:
    """未授權回應"""
    return error_response(
        message,
        [{"code": "UNAUTHORIZED", "message": message}],
        status.HTTP_401_UNAUTHORIZED,
        request_id,
    )


def forbidden_response(message: str = "權限不足", request_id: str = None) -> StandardResponse:
    """禁止訪問回應"""
    return error_response(
        message,
        [{"code": "FORBIDDEN", "message": message}],
        status.HTTP_403_FORBIDDEN,
        request_id,
    )


def paginated_response(
    data: List[Any],
    pagination: PaginationInfo,
    message: str = "查詢成功",
    request_id: str = None,
) -> PaginatedResponse:
    """分頁回應"""
    builder = (
        ResponseBuilder()
        .status(ResponseStatus.SUCCESS)
        .message(message)
        .data(data)
        .pagination(pagination)
    )

    if request_id:
        builder.request_id(request_id)

    response_data = builder.build().dict()
    return PaginatedResponse(**response_data)


def internal_error_response(
    message: str = "內部服務錯誤", request_id: str = None
) -> StandardResponse:
    """內部錯誤回應"""
    return error_response(
        message,
        [{"code": "INTERNAL_ERROR", "message": "服務暫時不可用，請稍後重試"}],
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id,
    )


def rate_limit_response(
    message: str = "請求頻率超出限制",
    retry_after: int = 60,
    request_id: str = None,
) -> StandardResponse:
    """限流回應"""
    return error_response(
        message,
        [
            {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"請在 {retry_after} 秒後重試",
            }
        ],
        status.HTTP_429_TOO_MANY_REQUESTS,
        request_id,
    )


# 資料模型標準化
class StandardListQuery(BaseModel):
    """標準列表查詢參數"""

    page: int = Field(1, ge=1, description="頁碼")
    size: int = Field(20, ge=1, le=100, description="每頁大小")
    sort: Optional[str] = Field(None, description="排序字段")
    order: Optional[str] = Field("asc", regex="^(asc|desc)$", description="排序方向")
    search: Optional[str] = Field(None, min_length=1, max_length=100, description="搜索關鍵字")
    filters: Optional[Dict[str, Any]] = Field(None, description="篩選條件")


class StandardCreateResponse(BaseModel):
    """標準創建回應"""

    id: Union[str, int] = Field(description="創建的資源 ID")
    created_at: datetime = Field(description="創建時間")
    message: str = Field(default="創建成功", description="操作消息")


class StandardUpdateResponse(BaseModel):
    """標準更新回應"""

    id: Union[str, int] = Field(description="更新的資源 ID")
    updated_at: datetime = Field(description="更新時間")
    message: str = Field(default="更新成功", description="操作消息")


class StandardDeleteResponse(BaseModel):
    """標準刪除回應"""

    id: Union[str, int] = Field(description="刪除的資源 ID")
    deleted_at: datetime = Field(description="刪除時間")
    message: str = Field(default="刪除成功", description="操作消息")


# API 文檔標準
@dataclass
class APIEndpointDoc:
    """API 端點文檔"""

    path: str
    method: str
    summary: str
    description: str
    tags: List[str]
    request_model: Optional[BaseModel] = None
    response_model: Optional[BaseModel] = None
    status_codes: Dict[int, str] = None
    examples: Dict[str, Any] = None

    def __post_init__(self):
        if self.status_codes is None:
            self.status_codes = {
                200: "操作成功",
                400: "請求參數錯誤",
                401: "未授權訪問",
                403: "權限不足",
                404: "資源未找到",
                500: "內部服務錯誤",
            }


class APIDocumentationGenerator:
    """API 文檔生成器"""

    def __init__(self, service_name: str, version: str = "v1"):
        self.service_name = service_name
        self.version = version
        self.endpoints: List[APIEndpointDoc] = []

    def add_endpoint(self, endpoint: APIEndpointDoc):
        """添加端點"""
        self.endpoints.append(endpoint)

    def generate_openapi_spec(self) -> Dict[str, Any]:
        """生成 OpenAPI 規範"""
        spec: Dict[str, Any] = {
            "openapi": "3.0.0",
            "info": {
                "title": f"{self.service_name} API",
                "version": self.version,
                "description": f"{self.service_name} 微服務 API 文檔",
            },
            "servers": [
                {
                    "url": f"http://localhost:8000/api/{self.version}",
                    "description": "開發環境",
                },
                {
                    "url": f"https://api.autovideo.com/{self.version}",
                    "description": "生產環境",
                },
            ],
            "paths": {},
            "components": {
                "schemas": {
                    "StandardResponse": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": [
                                    "success",
                                    "error",
                                    "warning",
                                    "info",
                                ],
                            },
                            "message": {"type": "string"},
                            "data": {"type": "object"},
                            "errors": {
                                "type": "array",
                                "items": {"type": "object"},
                            },
                            "metadata": {"type": "object"},
                        },
                    }
                }
            },
        }

        # 添加端點文檔
        for endpoint in self.endpoints:
            if endpoint.path not in spec["paths"]:
                spec["paths"][endpoint.path] = {}

            spec["paths"][endpoint.path][endpoint.method.lower()] = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "tags": endpoint.tags,
                "responses": {
                    str(code): {"description": desc} for code, desc in endpoint.status_codes.items()
                },
            }

        return spec

    def save_documentation(self, output_file: str = None) -> str:
        """保存文檔"""
        if output_file is None:
            output_file = f"{self.service_name.lower()}_api_docs.json"

        spec = self.generate_openapi_spec()

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(spec, f, indent=2, ensure_ascii=False)

        return output_file


# 響應時間監控裝飾器
def monitor_response_time(func):
    """響應時間監控裝飾器"""
    import time
    from functools import wraps

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000

            # 如果結果是 StandardResponse，更新執行時間
            if isinstance(result, StandardResponse):
                result.metadata.execution_time_ms = execution_time

            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            # 記錄錯誤和執行時間
            raise e

    return wrapper


if __name__ == "__main__":
    # 測試標準回應格式
    print("=== 標準 API 回應格式測試 ===")

    # 成功回應
    success = success_response("用戶查詢成功", {"id": 1, "name": "測試用戶"})
    print("成功回應:")
    print(success.to_json())

    # 錯誤回應
    error = validation_error_response({"username": "用戶名不能為空", "email": "郵箱格式錯誤"})
    print("\n驗證錯誤回應:")
    print(error.to_json())

    # 分頁回應
    pagination = PaginationInfo.create(page=1, size=10, total=100)
    paginated = paginated_response(
        [{"id": i, "name": f"用戶{i}"} for i in range(1, 11)], pagination
    )
    print("\n分頁回應:")
    print(paginated.to_json())

    # API 文檔生成
    doc_gen = APIDocumentationGenerator("Auth Service")
    endpoint = APIEndpointDoc(
        path="/api/v1/users",
        method="GET",
        summary="獲取用戶列表",
        description="獲取系統中的用戶列表，支持分頁和搜索",
        tags=["用戶管理"],
    )
    doc_gen.add_endpoint(endpoint)

    docs_file = doc_gen.save_documentation()
    print(f"\nAPI 文檔已生成: {docs_file}")
