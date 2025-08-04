"""
認證中間件

提供 FastAPI 的認證和授權中間件。
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from .jwt_handler import jwt_handler
from .session_manager import session_manager
from .permission_manager import permission_manager
from .auth_manager import auth_manager

logger = logging.getLogger(__name__)


# HTTP Bearer 認證方案
security = HTTPBearer()


class AuthMiddleware(BaseHTTPMiddleware):
    """認證中間件"""
    
    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        
        # 排除認證的路徑
        self.excluded_paths = self.config.get("excluded_paths", [
            "/docs", "/redoc", "/openapi.json", "/health",
            "/auth/login", "/auth/register", "/auth/reset-password"
        ])
        
        # 排除認證的路徑前綴
        self.excluded_prefixes = self.config.get("excluded_prefixes", [
            "/static", "/assets"
        ])
        
        logger.info("認證中間件初始化完成")
    
    async def dispatch(self, request: Request, call_next):
        """處理請求"""
        # 檢查是否需要認證
        if self._should_skip_auth(request):
            return await call_next(request)
        
        try:
            # 提取並驗證令牌
            token = self._extract_token(request)
            if not token:
                return self._create_auth_error_response("缺少認證令牌")
            
            # 驗證 JWT 令牌
            payload = jwt_handler.verify_token(token, "access")
            if not payload:
                return self._create_auth_error_response("無效的認證令牌")
            
            # 檢查會話是否有效
            user_id = payload["sub"]
            username = payload["username"]
            
            # 將用戶信息附加到請求
            request.state.user_id = user_id
            request.state.username = username
            request.state.user_role = payload.get("role")
            request.state.user_permissions = set(payload.get("permissions", []))
            request.state.token_payload = payload
            
            # 記錄訪問日誌
            self._log_access(request, user_id, username)
            
            # 繼續處理請求
            response = await call_next(request)
            
            return response
            
        except Exception as e:
            logger.error(f"認證中間件錯誤: {e}")
            return self._create_auth_error_response("認證處理錯誤")
    
    def _should_skip_auth(self, request: Request) -> bool:
        """檢查是否應該跳過認證"""
        path = request.url.path
        
        # 檢查排除路徑
        if path in self.excluded_paths:
            return True
        
        # 檢查排除前綴
        for prefix in self.excluded_prefixes:
            if path.startswith(prefix):
                return True
        
        return False
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """從請求中提取令牌"""
        # 從 Authorization 頭部提取
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:]  # 移除 "Bearer " 前綴
        
        # 從查詢參數提取（不推薦，但支持）
        token = request.query_params.get("token")
        if token:
            return token
        
        return None
    
    def _create_auth_error_response(self, message: str) -> JSONResponse:
        """創建認證錯誤響應"""
        return JSONResponse(
            status_code=401,
            content={
                "error": "authentication_required",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _log_access(self, request: Request, user_id: str, username: str):
        """記錄訪問日誌"""
        logger.info(f"用戶 {username} ({user_id}) 訪問 {request.method} {request.url.path}")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    獲取當前用戶信息的依賴函數
    
    Args:
        credentials: HTTP Bearer 認證憑據
        
    Returns:
        當前用戶信息
        
    Raises:
        HTTPException: 認證失敗時
    """
    try:
        # 驗證令牌
        payload = jwt_handler.verify_token(credentials.credentials, "access")
        if not payload:
            raise HTTPException(
                status_code=401,
                detail="無效的認證令牌",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return {
            "id": payload["sub"],
            "username": payload["username"],
            "role": payload.get("role"),
            "permissions": set(payload.get("permissions", [])),
            "payload": payload
        }
        
    except Exception as e:
        logger.error(f"獲取當前用戶失敗: {e}")
        raise HTTPException(
            status_code=401,
            detail="認證失敗",
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_optional_user(request: Request) -> Optional[Dict[str, Any]]:
    """
    獲取可選的當前用戶信息（用於不強制認證的端點）
    
    Args:
        request: FastAPI 請求對象
        
    Returns:
        當前用戶信息（如果已認證）
    """
    try:
        # 嘗試從請求狀態獲取用戶信息
        if hasattr(request.state, "user_id"):
            return {
                "id": request.state.user_id,
                "username": request.state.username,
                "role": request.state.user_role,
                "permissions": request.state.user_permissions
            }
        
        # 嘗試從 Authorization 頭部獲取
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header[7:]
        payload = jwt_handler.verify_token(token, "access")
        if not payload:
            return None
        
        return {
            "id": payload["sub"],
            "username": payload["username"],
            "role": payload.get("role"),
            "permissions": set(payload.get("permissions", [])),
            "payload": payload
        }
        
    except Exception as e:
        logger.warning(f"獲取可選用戶信息失敗: {e}")
        return None


def require_permission(permission: str, resource_id_param: Optional[str] = None):
    """
    權限檢查依賴函數
    
    Args:
        permission: 需要的權限
        resource_id_param: 資源ID參數名
        
    Returns:
        依賴函數
    """
    def permission_checker(
        current_user: Dict[str, Any] = Depends(get_current_user),
        request: Request = None
    ):
        user_id = current_user["id"]
        
        # 獲取資源ID
        resource_id = None
        if resource_id_param and request:
            resource_id = request.path_params.get(resource_id_param)
        
        # 檢查權限
        if not permission_manager.check_permission(user_id, permission, resource_id):
            raise HTTPException(
                status_code=403,
                detail=f"用戶沒有權限: {permission}"
            )
        
        return current_user
    
    return permission_checker


def require_any_permission(*permissions: str):
    """
    要求任一權限的依賴函數
    
    Args:
        permissions: 權限列表
        
    Returns:
        依賴函數
    """
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_id = current_user["id"]
        
        if not permission_manager.check_any_permission(user_id, list(permissions)):
            raise HTTPException(
                status_code=403,
                detail=f"用戶沒有以下任一權限: {', '.join(permissions)}"
            )
        
        return current_user
    
    return permission_checker


def require_all_permissions(*permissions: str):
    """
    要求所有權限的依賴函數
    
    Args:
        permissions: 權限列表
        
    Returns:
        依賴函數
    """
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_id = current_user["id"]
        
        if not permission_manager.check_all_permissions(user_id, list(permissions)):
            raise HTTPException(
                status_code=403,
                detail=f"用戶缺少以下權限: {', '.join(permissions)}"
            )
        
        return current_user
    
    return permission_checker


def require_role(role: str):
    """
    角色檢查依賴函數
    
    Args:
        role: 需要的角色
        
    Returns:
        依賴函數
    """
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        from .role_manager import role_manager
        
        user_id = current_user["id"]
        
        if not role_manager.user_has_role(user_id, role):
            raise HTTPException(
                status_code=403,
                detail=f"用戶沒有角色: {role}"
            )
        
        return current_user
    
    return role_checker


def require_superuser():
    """
    超級用戶檢查依賴函數
    
    Returns:
        依賴函數
    """
    def superuser_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        from .role_manager import role_manager
        
        user_id = current_user["id"]
        
        if not role_manager.user_has_role(user_id, "super_admin"):
            raise HTTPException(
                status_code=403,
                detail="需要超級管理員權限"
            )
        
        return current_user
    
    return superuser_checker


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中間件"""
    
    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        
        # 速率限制配置
        self.requests_per_minute = self.config.get("requests_per_minute", 60)
        self.requests_per_hour = self.config.get("requests_per_hour", 1000)
        
        # 請求計數器
        self.request_counters: Dict[str, Dict[str, Any]] = {}
        
        logger.info("速率限制中間件初始化完成")
    
    async def dispatch(self, request: Request, call_next):
        """處理請求"""
        client_ip = request.client.host
        
        # 檢查速率限制
        if self._is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "請求過於頻繁，請稍後重試",
                    "retry_after": 60
                }
            )
        
        # 記錄請求
        self._record_request(client_ip)
        
        return await call_next(request)
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """檢查是否達到速率限制"""
        now = datetime.utcnow()
        
        if client_ip not in self.request_counters:
            return False
        
        counter = self.request_counters[client_ip]
        
        # 檢查分鐘限制
        minute_requests = counter.get("minute_requests", 0)
        minute_reset_time = counter.get("minute_reset_time", now)
        
        if now >= minute_reset_time:
            counter["minute_requests"] = 0
            counter["minute_reset_time"] = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        elif minute_requests >= self.requests_per_minute:
            return True
        
        # 檢查小時限制
        hour_requests = counter.get("hour_requests", 0)
        hour_reset_time = counter.get("hour_reset_time", now)
        
        if now >= hour_reset_time:
            counter["hour_requests"] = 0
            counter["hour_reset_time"] = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif hour_requests >= self.requests_per_hour:
            return True
        
        return False
    
    def _record_request(self, client_ip: str):
        """記錄請求"""
        now = datetime.utcnow()
        
        if client_ip not in self.request_counters:
            self.request_counters[client_ip] = {
                "minute_requests": 0,
                "hour_requests": 0,
                "minute_reset_time": now.replace(second=0, microsecond=0) + timedelta(minutes=1),
                "hour_reset_time": now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            }
        
        counter = self.request_counters[client_ip]
        counter["minute_requests"] += 1
        counter["hour_requests"] += 1


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全頭部中間件"""
    
    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        
        # 安全頭部配置
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
        }
        
        # 自定義頭部
        custom_headers = self.config.get("security_headers", {})
        self.security_headers.update(custom_headers)
        
        logger.info("安全頭部中間件初始化完成")
    
    async def dispatch(self, request: Request, call_next):
        """處理請求"""
        response = await call_next(request)
        
        # 添加安全頭部
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        return response