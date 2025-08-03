from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import traceback
from datetime import datetime, timedelta
import uuid

from .database import get_db, init_db
from .models import AdminUser
from .schemas import (
    AIProviderCreate, AIProviderUpdate, AIProviderResponse,
    CrawlerConfigCreate, CrawlerConfigUpdate, CrawlerConfigResponse,
    CrawlerTaskCreate, CrawlerTaskUpdate, CrawlerTaskResponse,
    SocialTrendConfigCreate, SocialTrendConfigUpdate, SocialTrendConfigResponse,
    TrendingKeywordResponse, SystemLogResponse, AdminUserCreate, AdminUserResponse,
    LogQueryParams, TrendQueryParams, PaginationParams, DashboardStats,
    APIResponse, ErrorResponse, PaginatedResponse
)
from .crud import (
    crud_ai_provider, crud_crawler_config, crud_crawler_task, crud_social_trend_config,
    crud_trending_keyword, crud_keyword_trend, crud_system_log, crud_admin_user
)
from .security import (
    verify_token, create_access_token, PermissionChecker, require_permission,
    audit_log, hash_password
)

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建 FastAPI 應用
app = FastAPI(
    title="後台管理系統 API",
    description="AI Provider、爬蟲管理、社交媒體趨勢追蹤和操作日誌系統",
    version="1.0.0"
)

# CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境應該限制具體域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# HTTP Bearer 認證
security = HTTPBearer()

# 初始化資料庫
@app.on_event("startup")
async def startup_event():
    init_db()
    logger.info("後台管理系統 API 啟動完成")


# 依賴項：獲取當前用戶
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    request: Request = None
) -> AdminUser:
    token = credentials.credentials
    username = verify_token(token)
    if username is None:
        # 記錄無效令牌嘗試
        from .logging_system import AuditLogger
        await AuditLogger.log_security_event(
            "invalid_token",
            "warning",
            "無效的認證令牌訪問嘗試",
            ip_address=request.client.host if request and request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的認證令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = crud_admin_user.get_by_username(db, username=username)
    if user is None:
        # 記錄不存在用戶嘗試
        from .logging_system import AuditLogger
        await AuditLogger.log_security_event(
            "user_not_found",
            "warning",
            f"嘗試使用不存在的用戶名: {username}",
            ip_address=request.client.host if request and request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶不存在"
        )
    
    if not user.is_active:
        # 記錄禁用用戶嘗試
        from .logging_system import AuditLogger
        await AuditLogger.log_security_event(
            "disabled_user_access",
            "warning",
            f"禁用用戶嘗試訪問: {username}",
            user_id=user.id,
            username=username,
            ip_address=request.client.host if request and request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用戶已被禁用"
        )
    
    return user


# 權限檢查依賴項
def require_permission(permission: str):
    """權限檢查裝飾器"""
    def permission_checker(
        current_user: AdminUser = Depends(get_current_user),
        request: Request = None
    ):
        from .security import PermissionChecker
        
        has_permission = PermissionChecker.check_permission(
            current_user.role,
            current_user.permissions,
            permission
        )
        
        if not has_permission:
            # 記錄權限不足嘗試
            import asyncio
            from .logging_system import AuditLogger
            asyncio.create_task(
                AuditLogger.log_security_event(
                    "permission_denied",
                    "warning",
                    f"用戶 {current_user.username} 嘗試訪問需要 {permission} 權限的資源",
                    user_id=current_user.id,
                    username=current_user.username,
                    ip_address=request.client.host if request and request.client else None,
                    details={"required_permission": permission, "user_role": current_user.role}
                )
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少必要權限: {permission}"
            )
        
        return current_user
    
    return permission_checker


# 更新現有的 require_permission 裝飾器
def require_permission_decorator(permission: str):
    """權限裝飾器（用於函數裝飾）"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 在實際使用中，這裡應該從請求上下文獲取用戶信息
            return func(*args, **kwargs)
        return wrapper
    return decorator


# IP 白名單檢查
def check_ip_whitelist(request: Request):
    """檢查 IP 白名單"""
    allowed_ips = os.getenv("ALLOWED_IPS", "").split(",")
    if not allowed_ips or allowed_ips == [""]:
        return True  # 如果沒有配置白名單，允許所有 IP
    
    client_ip = request.client.host if request.client else "unknown"
    
    # 檢查是否在白名單中
    for allowed_ip in allowed_ips:
        if client_ip == allowed_ip.strip():
            return True
    
    return False


# 速率限制檢查
class RateLimiter:
    """簡單的速率限制器"""
    
    def __init__(self):
        self.requests = {}
        self.window_size = 60  # 1分鐘窗口
        self.max_requests = 100  # 每分鐘最多100個請求
    
    def is_allowed(self, client_ip: str) -> bool:
        now = datetime.utcnow()
        
        # 清理過期記錄
        self.requests = {
            ip: timestamps for ip, timestamps in self.requests.items()
            if timestamps and (now - timestamps[-1]).seconds < self.window_size
        }
        
        # 獲取當前 IP 的請求記錄
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        # 過濾出窗口內的請求
        window_start = now - timedelta(seconds=self.window_size)
        self.requests[client_ip] = [
            timestamp for timestamp in self.requests[client_ip]
            if timestamp > window_start
        ]
        
        # 檢查是否超過限制
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        # 記錄新請求
        self.requests[client_ip].append(now)
        return True


# 全域速率限制器
rate_limiter = RateLimiter()


# 安全中間件
@app.middleware("http")
async def security_middleware(request: Request, call_next):
    start_time = datetime.utcnow()
    request_id = str(uuid.uuid4())
    
    # 添加請求 ID 到請求上下文
    request.state.request_id = request_id
    
    client_ip = request.client.host if request.client else "unknown"
    
    # IP 白名單檢查（僅對敏感端點）
    sensitive_paths = ["/admin/users", "/admin/logs/cleanup", "/admin/system"]
    if any(request.url.path.startswith(path) for path in sensitive_paths):
        if not check_ip_whitelist(request):
            # 記錄 IP 白名單違規
            from .logging_system import AuditLogger
            await AuditLogger.log_security_event(
                "ip_whitelist_violation",
                "warning",
                f"未授權 IP 嘗試訪問敏感端點: {request.url.path}",
                ip_address=client_ip,
                details={"path": str(request.url.path), "method": request.method}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="訪問被拒絕：IP 不在白名單中"
            )
    
    # 速率限制檢查
    if not rate_limiter.is_allowed(client_ip):
        # 記錄速率限制違規
        from .logging_system import AuditLogger
        await AuditLogger.log_security_event(
            "rate_limit_exceeded",
            "warning",
            f"IP {client_ip} 超過速率限制",
            ip_address=client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="請求過於頻繁，請稍後再試"
        )
    
    # 檢查可疑的 User-Agent
    user_agent = request.headers.get("user-agent", "")
    suspicious_agents = ["sqlmap", "nikto", "nmap", "masscan", "curl/7."]
    if any(agent in user_agent.lower() for agent in suspicious_agents):
        # 記錄可疑 User-Agent
        from .logging_system import AuditLogger
        await AuditLogger.log_security_event(
            "suspicious_user_agent",
            "warning",
            f"檢測到可疑 User-Agent: {user_agent}",
            ip_address=client_ip,
            details={"user_agent": user_agent, "path": str(request.url.path)}
        )
    
    response = await call_next(request)
    
    # 計算處理時間
    process_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    
    # 記錄 API 請求日誌
    from .logging_system import AuditLogger
    await AuditLogger.log_api_request(
        request=request,
        response_status=response.status_code,
        duration_ms=int(process_time)
    )
    
    # 添加安全響應頭
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response


# 全域異常處理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"全域異常: {exc}\n{traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            message="內部伺服器錯誤",
            errors=[str(exc)],
            error_code="INTERNAL_ERROR"
        ).dict()
    )


# ============= 認證相關 API =============

@app.post("/admin/auth/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):
    """管理員登錄"""
    user = crud_admin_user.authenticate(db, username=username, password=password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用戶名或密碼錯誤"
        )
    
    access_token = create_access_token(subject=user.username)
    
    return APIResponse(
        message="登錄成功",
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user": AdminUserResponse.from_orm(user)
        }
    )


@app.get("/admin/auth/me", response_model=APIResponse)
async def get_current_user_info(current_user: AdminUser = Depends(get_current_user)):
    """獲取當前用戶信息"""
    return APIResponse(
        data=AdminUserResponse.from_orm(current_user)
    )


# ============= AI Provider API =============

@app.get("/admin/ai-providers", response_model=APIResponse)
async def get_ai_providers(
    skip: int = 0,
    limit: int = 100,
    current_user: AdminUser = Depends(require_permission("ai_provider:read")),
    db: Session = Depends(get_db),
    request: Request = None
):
    """獲取 AI Provider 列表"""
    providers = crud_ai_provider.get_multi(db, skip=skip, limit=limit)
    
    # 記錄操作日誌
    from .logging_system import AuditLogger
    await AuditLogger.log_user_action(
        user_id=current_user.id,
        username=current_user.username,
        action="view_ai_providers",
        resource_type="ai_provider",
        details={"skip": skip, "limit": limit},
        request=request
    )
    
    return APIResponse(data=[AIProviderResponse.from_orm(p) for p in providers])


@app.post("/admin/ai-providers", response_model=APIResponse)
@require_permission("ai_provider:create")
@audit_log("create", "ai_provider")
async def create_ai_provider(
    provider_in: AIProviderCreate,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """創建 AI Provider"""
    try:
        provider = crud_ai_provider.create_ai_provider(db, provider_in=provider_in)
        return APIResponse(
            message="AI Provider 創建成功",
            data=AIProviderResponse.from_orm(provider)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/admin/ai-providers/{provider_id}", response_model=APIResponse)
@require_permission("ai_provider:read")
async def get_ai_provider(
    provider_id: int,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取指定 AI Provider"""
    provider = crud_ai_provider.get(db, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="AI Provider 不存在")
    
    return APIResponse(data=AIProviderResponse.from_orm(provider))


@app.put("/admin/ai-providers/{provider_id}", response_model=APIResponse)
@require_permission("ai_provider:update")
@audit_log("update", "ai_provider")
async def update_ai_provider(
    provider_id: int,
    provider_in: AIProviderUpdate,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新 AI Provider"""
    try:
        provider = crud_ai_provider.update_ai_provider(
            db, provider_id=provider_id, provider_in=provider_in
        )
        if not provider:
            raise HTTPException(status_code=404, detail="AI Provider 不存在")
        
        return APIResponse(
            message="AI Provider 更新成功",
            data=AIProviderResponse.from_orm(provider)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/admin/ai-providers/{provider_id}", response_model=APIResponse)
@require_permission("ai_provider:delete")
@audit_log("delete", "ai_provider")
async def delete_ai_provider(
    provider_id: int,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刪除 AI Provider"""
    provider = crud_ai_provider.remove(db, id=provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="AI Provider 不存在")
    
    return APIResponse(message="AI Provider 刪除成功")


@app.post("/admin/ai-providers/{provider_id}/test", response_model=APIResponse)
@require_permission("ai_provider:test")
async def test_ai_provider(
    provider_id: int,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """測試 AI Provider 連接"""
    success = crud_ai_provider.test_provider_connection(db, provider_id)
    
    return APIResponse(
        message="連接測試完成",
        data={"success": success, "provider_id": provider_id}
    )


# ============= 爬蟲配置 API =============

@app.get("/admin/crawler-configs", response_model=APIResponse)
@require_permission("crawler:read")
async def get_crawler_configs(
    skip: int = 0,
    limit: int = 100,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取爬蟲配置列表"""
    configs = crud_crawler_config.get_multi(db, skip=skip, limit=limit)
    return APIResponse(data=[CrawlerConfigResponse.from_orm(c) for c in configs])


@app.post("/admin/crawler-configs", response_model=APIResponse)
@require_permission("crawler:create")
@audit_log("create", "crawler_config")
async def create_crawler_config(
    config_in: CrawlerConfigCreate,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """創建爬蟲配置"""
    try:
        config = crud_crawler_config.create_crawler_config(db, config_in=config_in)
        return APIResponse(
            message="爬蟲配置創建成功",
            data=CrawlerConfigResponse.from_orm(config)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/admin/crawler-configs/{config_id}", response_model=APIResponse)
@require_permission("crawler:update")
@audit_log("update", "crawler_config")
async def update_crawler_config(
    config_id: int,
    config_in: CrawlerConfigUpdate,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新爬蟲配置"""
    try:
        config = crud_crawler_config.update_crawler_config(
            db, config_id=config_id, config_in=config_in
        )
        if not config:
            raise HTTPException(status_code=404, detail="爬蟲配置不存在")
        
        return APIResponse(
            message="爬蟲配置更新成功",
            data=CrawlerConfigResponse.from_orm(config)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/admin/crawler-configs/{config_id}", response_model=APIResponse)
@require_permission("crawler:delete")
@audit_log("delete", "crawler_config")
async def delete_crawler_config(
    config_id: int,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刪除爬蟲配置"""
    config = crud_crawler_config.remove(db, id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail="爬蟲配置不存在")
    
    return APIResponse(message="爬蟲配置刪除成功")


# ============= 爬蟲運行 API =============

@app.post("/admin/crawler-configs/{config_id}/run", response_model=APIResponse)
@require_permission("crawler:run")
@audit_log("run", "crawler_config")
async def run_crawler_manually(
    config_id: int,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手動運行爬蟲配置"""
    from .crawler_engine import run_crawler_config
    
    config = crud_crawler_config.get(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="爬蟲配置不存在")
    
    try:
        result = await run_crawler_config(config_id)
        return APIResponse(
            message="爬蟲運行完成",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"爬蟲運行失敗: {str(e)}")


@app.get("/admin/crawler-configs/{config_id}/results", response_model=APIResponse)
@require_permission("crawler:read")
async def get_crawler_results(
    config_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取爬蟲結果"""
    from .models import CrawlerResult
    
    config = crud_crawler_config.get(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="爬蟲配置不存在")
    
    results = db.query(CrawlerResult).filter(
        CrawlerResult.config_id == config_id
    ).order_by(CrawlerResult.scraped_at.desc()).offset(skip).limit(limit).all()
    
    total = db.query(CrawlerResult).filter(CrawlerResult.config_id == config_id).count()
    
    return APIResponse(
        data={
            "results": [
                {
                    "id": r.id,
                    "url": r.url,
                    "title": r.title,
                    "keywords_found": r.keywords_found,
                    "success": r.success,
                    "scraped_at": r.scraped_at,
                    "metadata": r.metadata
                }
                for r in results
            ],
            "total": total,
            "config_name": config.name
        }
    )


# ============= 爬蟲任務 API =============

@app.get("/admin/crawler-tasks", response_model=APIResponse)
@require_permission("crawler:read")
async def get_crawler_tasks(
    skip: int = 0,
    limit: int = 100,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取爬蟲任務列表"""
    tasks = crud_crawler_task.get_multi(db, skip=skip, limit=limit)
    
    # 轉換關鍵字 JSON 字符串為列表
    import json
    task_responses = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "task_name": task.task_name,
            "keywords": json.loads(task.keywords) if task.keywords else [],
            "target_url": task.target_url,
            "schedule_type": task.schedule_type,
            "schedule_time": task.schedule_time,
            "last_run_at": task.last_run_at,
            "is_active": task.is_active,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        task_responses.append(task_dict)
    
    return APIResponse(data=task_responses)


@app.post("/admin/crawler-tasks", response_model=APIResponse)
@require_permission("crawler:create")
@audit_log("create", "crawler_task")
async def create_crawler_task(
    task_in: CrawlerTaskCreate,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """創建爬蟲任務"""
    try:
        task = crud_crawler_task.create_crawler_task(db, task_in=task_in)
        
        # 轉換響應數據
        import json
        task_response = {
            "id": task.id,
            "task_name": task.task_name,
            "keywords": json.loads(task.keywords) if task.keywords else [],
            "target_url": task.target_url,
            "schedule_type": task.schedule_type,
            "schedule_time": task.schedule_time,
            "last_run_at": task.last_run_at,
            "is_active": task.is_active,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        
        return APIResponse(
            message="爬蟲任務創建成功",
            data=task_response
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/admin/crawler-tasks/{task_id}", response_model=APIResponse)
@require_permission("crawler:read")
async def get_crawler_task(
    task_id: int,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取指定爬蟲任務"""
    task = crud_crawler_task.get(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="爬蟲任務不存在")
    
    # 轉換響應數據
    import json
    task_response = {
        "id": task.id,
        "task_name": task.task_name,
        "keywords": json.loads(task.keywords) if task.keywords else [],
        "target_url": task.target_url,
        "schedule_type": task.schedule_type,
        "schedule_time": task.schedule_time,
        "last_run_at": task.last_run_at,
        "is_active": task.is_active,
        "created_at": task.created_at,
        "updated_at": task.updated_at
    }
    
    return APIResponse(data=task_response)


@app.put("/admin/crawler-tasks/{task_id}", response_model=APIResponse)
@require_permission("crawler:update")
@audit_log("update", "crawler_task")
async def update_crawler_task(
    task_id: int,
    task_in: CrawlerTaskUpdate,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新爬蟲任務"""
    try:
        task = crud_crawler_task.update_crawler_task(
            db, task_id=task_id, task_in=task_in
        )
        if not task:
            raise HTTPException(status_code=404, detail="爬蟲任務不存在")
        
        # 轉換響應數據
        import json
        task_response = {
            "id": task.id,
            "task_name": task.task_name,
            "keywords": json.loads(task.keywords) if task.keywords else [],
            "target_url": task.target_url,
            "schedule_type": task.schedule_type,
            "schedule_time": task.schedule_time,
            "last_run_at": task.last_run_at,
            "is_active": task.is_active,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        
        return APIResponse(
            message="爬蟲任務更新成功",
            data=task_response
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/admin/crawler-tasks/{task_id}", response_model=APIResponse)
@require_permission("crawler:delete")
@audit_log("delete", "crawler_task")
async def delete_crawler_task(
    task_id: int,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刪除爬蟲任務"""
    task = crud_crawler_task.remove(db, id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="爬蟲任務不存在")
    
    return APIResponse(message="爬蟲任務刪除成功")


@app.post("/admin/crawler-tasks/{task_id}/run", response_model=APIResponse)
@require_permission("crawler:run")
@audit_log("run", "crawler_task")
async def run_crawler_task_manually(
    task_id: int,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手動運行爬蟲任務"""
    task = crud_crawler_task.get(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="爬蟲任務不存在")
    
    if not task.is_active:
        raise HTTPException(status_code=400, detail="任務已停用，無法執行")
    
    try:
        # 使用 Celery 任務執行
        from .tasks.crawler_tasks import schedule_crawler_task_run
        
        celery_task = schedule_crawler_task_run(task_id)
        
        # 更新最後運行時間
        crud_crawler_task.update_last_run_time(db, task_id)
        
        result = {
            "task_id": task_id,
            "task_name": task.task_name,
            "celery_task_id": celery_task.id,
            "status": "scheduled",
            "message": "爬蟲任務已排程執行",
            "scheduled_at": datetime.utcnow().isoformat()
        }
        
        return APIResponse(
            message="爬蟲任務已排程執行",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"爬蟲任務運行失敗: {str(e)}")


@app.get("/admin/crawler-tasks/{task_id}/results", response_model=APIResponse)
@require_permission("crawler:read")
async def get_crawler_task_results(
    task_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取爬蟲任務執行結果"""
    from .models import CrawlerTaskResult
    import json
    
    # 檢查任務是否存在
    task = crud_crawler_task.get(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="爬蟲任務不存在")
    
    # 查詢結果
    results = db.query(CrawlerTaskResult).filter(
        CrawlerTaskResult.task_id == task_id
    ).order_by(
        CrawlerTaskResult.scraped_at.desc()
    ).offset(skip).limit(limit).all()
    
    # 格式化結果
    formatted_results = []
    for result in results:
        try:
            matched_keywords = json.loads(result.matched_keywords) if result.matched_keywords else []
        except (json.JSONDecodeError, TypeError):
            matched_keywords = []
        
        formatted_results.append({
            "id": result.id,
            "run_id": result.run_id,
            "url": result.url,
            "title": result.title,
            "description": result.description,
            "content": result.content,
            "matched_keywords": matched_keywords,
            "page_number": result.page_number,
            "success": result.success,
            "error_message": result.error_message,
            "scraped_at": result.scraped_at
        })
    
    # 獲取總數
    total = db.query(CrawlerTaskResult).filter(
        CrawlerTaskResult.task_id == task_id
    ).count()
    
    return APIResponse(
        message="獲取爬蟲任務結果成功",
        data={
            "task_id": task_id,
            "task_name": task.task_name,
            "results": formatted_results,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    )


@app.get("/admin/crawler-tasks/statistics", response_model=APIResponse)
@require_permission("crawler:read")
async def get_crawler_task_statistics(
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取爬蟲任務統計信息"""
    stats = crud_crawler_task.get_task_statistics(db)
    return APIResponse(data=stats)


@app.get("/admin/crawler-tasks/active", response_model=APIResponse)
@require_permission("crawler:read")
async def get_active_crawler_tasks(
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取所有活躍的爬蟲任務"""
    tasks = crud_crawler_task.get_active_tasks(db)
    
    # 轉換關鍵字 JSON 字符串為列表
    import json
    task_responses = []
    for task in tasks:
        task_dict = {
            "id": task.id,
            "task_name": task.task_name,
            "keywords": json.loads(task.keywords) if task.keywords else [],
            "target_url": task.target_url,
            "schedule_type": task.schedule_type,
            "schedule_time": task.schedule_time,
            "last_run_at": task.last_run_at,
            "is_active": task.is_active,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        }
        task_responses.append(task_dict)
    
    return APIResponse(data=task_responses)


# ============= 社交媒體趨勢配置 API =============

@app.get("/admin/social-trend-configs", response_model=APIResponse)
@require_permission("trends:read")
async def get_social_trend_configs(
    skip: int = 0,
    limit: int = 100,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取社交媒體趨勢配置列表"""
    configs = crud_social_trend_config.get_multi(db, skip=skip, limit=limit)
    return APIResponse(data=[SocialTrendConfigResponse.from_orm(c) for c in configs])


@app.post("/admin/social-trend-configs", response_model=APIResponse)
@require_permission("trends:create")
@audit_log("create", "social_trend_config")
async def create_social_trend_config(
    config_in: SocialTrendConfigCreate,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """創建社交媒體趨勢配置"""
    try:
        config = crud_social_trend_config.create_trend_config(db, config_in=config_in)
        return APIResponse(
            message="社交媒體趨勢配置創建成功",
            data=SocialTrendConfigResponse.from_orm(config)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/admin/social-trend-configs/{config_id}", response_model=APIResponse)
@require_permission("trends:update")
@audit_log("update", "social_trend_config")
async def update_social_trend_config(
    config_id: int,
    config_in: SocialTrendConfigUpdate,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新社交媒體趨勢配置"""
    config = crud_social_trend_config.get(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="趨勢配置不存在")
    
    update_data = config_in.dict(exclude_unset=True)
    updated_config = crud_social_trend_config.update(db, db_obj=config, obj_in=update_data)
    
    return APIResponse(
        message="社交媒體趨勢配置更新成功",
        data=SocialTrendConfigResponse.from_orm(updated_config)
    )


@app.delete("/admin/social-trend-configs/{config_id}", response_model=APIResponse)
@require_permission("trends:delete")
@audit_log("delete", "social_trend_config")
async def delete_social_trend_config(
    config_id: int,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刪除社交媒體趨勢配置"""
    config = crud_social_trend_config.remove(db, id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail="趨勢配置不存在")
    
    return APIResponse(message="社交媒體趨勢配置刪除成功")


@app.post("/admin/social-trends/collect", response_model=APIResponse)
@require_permission("trends:update")
@audit_log("collect", "social_trends")
async def collect_trends_manually(
    platform: Optional[str] = None,
    region: str = "global",
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手動收集社交媒體趨勢"""
    from .social_trends import SocialTrendsManager, SocialPlatform
    
    try:
        manager = SocialTrendsManager()
        
        if platform:
            # 收集指定平台的趨勢
            platform_enum = SocialPlatform(platform.lower())
            result = await manager.collect_platform_trends(platform_enum, region)
        else:
            # 收集所有平台的趨勢
            result = await manager.collect_all_trends()
        
        return APIResponse(
            message="趨勢收集完成",
            data=result
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"無效的平台: {platform}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"趨勢收集失敗: {str(e)}")


# ============= 熱門關鍵字 API =============

@app.get("/admin/trending-keywords", response_model=APIResponse)
@require_permission("trends:read")
async def get_trending_keywords(
    params: TrendQueryParams = Depends(),
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取熱門關鍵字"""
    keywords, total = crud_trending_keyword.get_trending_keywords(db, params=params)
    pages = (total + params.size - 1) // params.size
    
    return APIResponse(
        data=PaginatedResponse(
            items=[TrendingKeywordResponse.from_orm(k) for k in keywords],
            total=total,
            page=params.page,
            size=params.size,
            pages=pages
        )
    )


@app.get("/admin/trending-keywords/top", response_model=APIResponse)
@require_permission("trends:read")
async def get_top_trending_keywords(
    platform: str,
    timeframe: str = "1d",
    limit: int = 20,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取指定平台的熱門關鍵字"""
    from .models import SocialPlatform, TrendTimeframe
    
    try:
        platform_enum = SocialPlatform(platform.lower())
        timeframe_enum = TrendTimeframe(timeframe)
        
        keywords = crud_trending_keyword.get_top_keywords(
            db, platform_enum, timeframe_enum, limit
        )
        
        return APIResponse(
            data=[TrendingKeywordResponse.from_orm(k) for k in keywords]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"無效的參數: {str(e)}")


@app.get("/admin/trending-keywords/stats", response_model=APIResponse)
@require_permission("trends:read")
async def get_trending_keywords_stats(
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取熱門關鍵字統計數據"""
    from .models import TrendingKeyword, SocialPlatform
    from sqlalchemy import func
    
    # 按平台統計
    platform_stats = db.query(
        TrendingKeyword.platform,
        func.count(TrendingKeyword.id).label('count'),
        func.max(TrendingKeyword.trend_date).label('last_update')
    ).group_by(TrendingKeyword.platform).all()
    
    # 今日新增趨勢
    today = datetime.utcnow().date()
    today_count = db.query(TrendingKeyword).filter(
        func.date(TrendingKeyword.trend_date) == today
    ).count()
    
    return APIResponse(
        data={
            "platform_stats": [
                {
                    "platform": stat.platform,
                    "count": stat.count,
                    "last_update": stat.last_update
                }
                for stat in platform_stats
            ],
            "today_trends": today_count,
            "total_trends": db.query(TrendingKeyword).count()
        }
    )


# ============= 系統日誌 API =============

@app.get("/admin/logs", response_model=APIResponse)
@require_permission("logs:read")
async def get_system_logs(
    params: LogQueryParams = Depends(),
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取系統日誌"""
    logs, total = crud_system_log.get_logs(db, params=params)
    pages = (total + params.size - 1) // params.size
    
    return APIResponse(
        data=PaginatedResponse(
            items=[SystemLogResponse.from_orm(log) for log in logs],
            total=total,
            page=params.page,
            size=params.size,
            pages=pages
        )
    )


@app.get("/admin/logs/stats", response_model=APIResponse)
@require_permission("logs:read")
async def get_log_statistics(
    hours: int = 24,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取日誌統計數據"""
    from .logging_system import log_analyzer
    
    error_stats = await log_analyzer.get_error_statistics(hours)
    performance_stats = await log_analyzer.get_performance_metrics(hours)
    
    return APIResponse(
        data={
            "error_statistics": error_stats,
            "performance_metrics": performance_stats,
            "timeframe_hours": hours
        }
    )


@app.post("/admin/logs/export", response_model=APIResponse)
@require_permission("logs:export")
@audit_log("export", "system_logs")
async def export_system_logs(
    start_date: datetime,
    end_date: datetime,
    level: Optional[str] = None,
    format: str = "json",
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """導出系統日誌"""
    from .logging_system import export_logs
    from .models import LogLevel
    
    try:
        log_level = LogLevel(level) if level else None
        exported_data = await export_logs(start_date, end_date, log_level, format)
        
        return APIResponse(
            message="日誌導出成功",
            data={
                "exported_data": exported_data,
                "start_date": start_date,
                "end_date": end_date,
                "format": format
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"無效的參數: {str(e)}")


@app.delete("/admin/logs/cleanup", response_model=APIResponse)
@require_permission("system:settings")
@audit_log("cleanup", "system_logs")
async def cleanup_old_logs(
    days: int = 30,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """清理舊日誌"""
    from .logging_system import cleanup_old_logs
    
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="需要超級管理員權限")
    
    if days < 7:
        raise HTTPException(status_code=400, detail="保留天數不能少於7天")
    
    try:
        await cleanup_old_logs(days)
        return APIResponse(
            message=f"成功清理超過 {days} 天的舊日誌"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理日誌失敗: {str(e)}")


# ============= 儀表板 API =============

@app.get("/admin/dashboard", response_model=APIResponse)
@require_permission("system:dashboard")
async def get_dashboard_stats(
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取儀表板統計數據"""
    
    # 獲取各種統計數據
    stats = DashboardStats(
        total_ai_providers=db.query(crud_ai_provider.model).count(),
        active_ai_providers=len(crud_ai_provider.get_active_providers(db)),
        total_crawlers=db.query(crud_crawler_config.model).count(),
        active_crawlers=len(crud_crawler_config.get_active_configs(db)),
        total_trends_today=0,  # 今天的趨勢數據
        total_logs_today=0,    # 今天的日誌數量
        error_logs_today=0,    # 今天的錯誤日誌
        last_24h_activity={}   # 過去24小時活動
    )
    
    # 獲取日誌統計
    log_stats = crud_system_log.get_dashboard_stats(db)
    stats.total_logs_today = log_stats["total_logs_today"]
    stats.error_logs_today = log_stats["error_logs_today"]
    stats.last_24h_activity = log_stats["last_24h_activity"]
    
    return APIResponse(data=stats)


# ============= 用戶管理 API =============

@app.post("/admin/users", response_model=APIResponse)
@require_permission("users:create")
@audit_log("create", "admin_user")
async def create_admin_user(
    user_in: AdminUserCreate,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """創建管理員用戶"""
    try:
        user = crud_admin_user.create_admin_user(db, user_in=user_in)
        return APIResponse(
            message="管理員用戶創建成功",
            data=AdminUserResponse.from_orm(user)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============= 健康檢查和系統狀態 API =============

@app.get("/admin/health")
async def health_check():
    """系統健康檢查"""
    try:
        # 檢查資料庫連接
        db = SessionLocal()
        try:
            db.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"error: {str(e)}"
        finally:
            db.close()
        
        # 檢查 Celery 狀態
        from .celery_app import celery_health_check
        celery_healthy, celery_message = celery_health_check()
        
        # 系統基本信息
        import psutil
        system_info = {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
        }
        
        # 計算總體健康狀態
        is_healthy = (
            db_status == "healthy" and 
            celery_healthy and
            system_info["cpu_usage"] < 90 and
            system_info["memory_usage"] < 90 and
            system_info["disk_usage"] < 95
        )
        
        status_code = 200 if is_healthy else 503
        
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "healthy" if is_healthy else "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "database": db_status,
                    "celery": {
                        "status": "healthy" if celery_healthy else "error",
                        "message": celery_message
                    }
                },
                "system": system_info,
                "version": "1.0.0"
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


@app.get("/admin/system/info")
async def get_system_info(
    current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """獲取系統信息"""
    import platform
    import psutil
    
    return APIResponse(
        data={
            "system": {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version()
            },
            "resources": {
                "cpu_count": psutil.cpu_count(),
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory": {
                    "total": psutil.virtual_memory().total,
                    "available": psutil.virtual_memory().available,
                    "percent": psutil.virtual_memory().percent
                },
                "disk": {
                    "total": psutil.disk_usage('/').total,
                    "used": psutil.disk_usage('/').used,
                    "free": psutil.disk_usage('/').free,
                    "percent": (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
                }
            },
            "process_count": len(psutil.pids()),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
    )


# ============= 關鍵字趨勢 API (新版本) =============

@app.get("/admin/keyword-trends", response_model=APIResponse)
@require_permission("trends:read")
async def get_keyword_trends(
    platform: Optional[str] = None,
    period: str = "day", 
    limit: int = 50,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取關鍵字趨勢數據"""
    try:
        trends = crud_keyword_trend.get_latest_trends(
            db, platform=platform, period=period, limit=limit
        )
        
        return APIResponse(
            data={
                "trends": [
                    {
                        "id": trend.id,
                        "platform": trend.platform,
                        "keyword": trend.keyword,
                        "period": trend.period,
                        "rank": trend.rank,
                        "search_volume": trend.search_volume,
                        "change_percentage": trend.change_percentage,
                        "region": trend.region,
                        "category": trend.category,
                        "collected_at": trend.collected_at.isoformat(),
                        "metadata": trend.metadata
                    }
                    for trend in trends
                ],
                "total": len(trends),
                "platform": platform,
                "period": period
            }
        )
    except Exception as e:
        logger.error(f"獲取關鍵字趨勢失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取趨勢數據失敗")


@app.get("/admin/keyword-trends/platforms", response_model=APIResponse)
@require_permission("trends:read")
async def get_platforms_trends(
    period: str = "day",
    top_n: int = 10,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取各平台的熱門關鍵字排行榜"""
    try:
        platforms_data = crud_keyword_trend.get_top_keywords_by_period(
            db, period=period, top_n=top_n
        )
        
        return APIResponse(
            data={
                "platforms": platforms_data,
                "period": period,
                "top_n": top_n,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        logger.error(f"獲取平台趨勢失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取平台趨勢失敗")


@app.get("/admin/keyword-trends/statistics", response_model=APIResponse)
@require_permission("trends:read")
async def get_trends_statistics(
    days: int = 7,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """獲取趨勢統計數據"""
    try:
        stats = crud_keyword_trend.get_platform_statistics(db, days=days)
        
        return APIResponse(data=stats)
    except Exception as e:
        logger.error(f"獲取趨勢統計失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取統計數據失敗")


@app.get("/admin/keyword-trends/search", response_model=APIResponse)
@require_permission("trends:read")
async def search_keyword_trends(
    q: str,
    platforms: Optional[str] = None,
    limit: int = 100,
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜尋關鍵字趨勢"""
    try:
        platform_list = platforms.split(",") if platforms else None
        
        trends = crud_keyword_trend.search_keywords(
            db, search_term=q, platforms=platform_list, limit=limit
        )
        
        return APIResponse(
            data={
                "results": [
                    {
                        "id": trend.id,
                        "platform": trend.platform,
                        "keyword": trend.keyword,
                        "period": trend.period,
                        "rank": trend.rank,
                        "search_volume": trend.search_volume,
                        "collected_at": trend.collected_at.isoformat()
                    }
                    for trend in trends
                ],
                "query": q,
                "platforms": platform_list,
                "total": len(trends)
            }
        )
    except Exception as e:
        logger.error(f"搜尋關鍵字趨勢失敗: {e}")
        raise HTTPException(status_code=500, detail="搜尋失敗")


@app.post("/admin/keyword-trends/collect", response_model=APIResponse)
@require_permission("trends:write")
async def trigger_trends_collection(
    platforms: Optional[List[str]] = None,
    period: str = "day",
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手動觸發趨勢數據收集"""
    try:
        from .social_trends import collect_and_save_trends
        
        # 記錄操作日誌
        await audit_log(
            db, current_user.id, "trigger_trends_collection", "keyword_trends",
            f"手動觸發趨勢收集 - 平台: {platforms}, 週期: {period}"
        )
        
        # 執行收集任務
        result = await collect_and_save_trends(platforms=platforms, period=period)
        
        return APIResponse(
            data=result,
            message="趨勢數據收集任務已觸發"
        )
    except Exception as e:
        logger.error(f"觸發趨勢收集失敗: {e}")
        raise HTTPException(status_code=500, detail="觸發收集任務失敗")


@app.get("/admin/keyword-trends/date-range", response_model=APIResponse)
@require_permission("trends:read")
async def get_trends_by_date_range(
    start_date: datetime,
    end_date: datetime,
    platform: Optional[str] = None,
    period: str = "day",
    current_user: AdminUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """根據日期範圍獲取趨勢數據"""
    try:
        trends = crud_keyword_trend.get_trending_keywords_by_date_range(
            db, start_date=start_date, end_date=end_date, 
            platform=platform, period=period
        )
        
        # 按日期分組
        trends_by_date = {}
        for trend in trends:
            date_key = trend.collected_at.date().isoformat()
            if date_key not in trends_by_date:
                trends_by_date[date_key] = []
            
            trends_by_date[date_key].append({
                "id": trend.id,
                "platform": trend.platform,
                "keyword": trend.keyword,
                "rank": trend.rank,
                "search_volume": trend.search_volume,
                "change_percentage": trend.change_percentage
            })
        
        return APIResponse(
            data={
                "trends_by_date": trends_by_date,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "platform": platform,
                "period": period,
                "total_records": len(trends)
            }
        )
    except Exception as e:
        logger.error(f"獲取日期範圍趨勢失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取趨勢數據失敗")


@app.get("/admin/system/tasks")
async def get_system_tasks(
    current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """獲取系統任務狀態"""
    from .celery_app import celery_monitor
    
    try:
        active_tasks = celery_monitor.get_active_tasks()
        scheduled_tasks = celery_monitor.get_scheduled_tasks()
        worker_stats = celery_monitor.get_worker_stats()
        
        return APIResponse(
            data={
                "active_tasks": active_tasks,
                "scheduled_tasks": scheduled_tasks,
                "worker_stats": worker_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except Exception as e:
        return APIResponse(
            success=False,
            message="獲取任務狀態失敗",
            errors=[str(e)]
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)