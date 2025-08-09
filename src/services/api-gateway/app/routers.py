"""
API Gateway 路由模組
處理所有進入的 HTTP 請求並將其轉發到適當的微服務
"""

import structlog
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from .auth import get_current_user
from .proxy import proxy
from .rate_limiter import limiter

logger = structlog.get_logger()

# Create routers
auth_router = APIRouter(prefix="/auth", tags=["authentication"])
data_router = APIRouter(prefix="/data", tags=["data"])
inference_router = APIRouter(prefix="/inference", tags=["inference"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


# Authentication routes
@auth_router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request):
    """Register new user"""
    body = await request.json()
    result = await proxy.forward_request(
        service="auth",
        path="/api/v1/register",
        method="POST",
        headers=dict(request.headers),
        json_data=body,
    )

    if result["status_code"] == 201:
        return JSONResponse(
            status_code=result["status_code"], content=result["data"]
        )
    else:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["data"].get("detail", "Registration failed"),
        )


@auth_router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request):
    """Login user"""
    body = await request.json()
    result = await proxy.forward_request(
        service="auth",
        path="/api/v1/login",
        method="POST",
        headers=dict(request.headers),
        json_data=body,
    )

    if result["status_code"] == 200:
        return JSONResponse(
            status_code=result["status_code"], content=result["data"]
        )
    else:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["data"].get("detail", "Login failed"),
        )


@auth_router.get("/me")
@limiter.limit("30/minute")
async def get_profile(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Get current user profile"""
    result = await proxy.forward_request(
        service="auth",
        path="/api/v1/me",
        method="GET",
        headers=dict(request.headers),
    )

    return JSONResponse(
        status_code=result["status_code"], content=result["data"]
    )


@auth_router.put("/me")
@limiter.limit("10/minute")
async def update_profile(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    body = await request.json()
    result = await proxy.forward_request(
        service="auth",
        path="/api/v1/me",
        method="PUT",
        headers=dict(request.headers),
        json_data=body,
    )

    return JSONResponse(
        status_code=result["status_code"], content=result["data"]
    )


# Data processing routes
@data_router.post("/upload")
@limiter.limit("20/minute")
async def upload_data(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Upload data for processing"""
    # Handle file upload
    form = await request.form()
    result = await proxy.forward_request(
        service="data",
        path="/api/v1/upload",
        method="POST",
        headers=dict(request.headers),
        form_data=form,
    )

    return JSONResponse(
        status_code=result["status_code"], content=result["data"]
    )


@data_router.get("/status/{task_id}")
@limiter.limit("60/minute")
async def get_processing_status(
    task_id: str, request: Request, current_user: dict = Depends(get_current_user)
):
    """Get processing status"""
    result = await proxy.forward_request(
        service="data",
        path=f"/api/v1/status/{task_id}",
        method="GET",
        headers=dict(request.headers),
    )

    return JSONResponse(
        status_code=result["status_code"], content=result["data"]
    )


# Inference routes
@inference_router.post("/generate")
@limiter.limit("10/minute")
async def generate_content(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Generate content using AI models"""
    body = await request.json()
    result = await proxy.forward_request(
        service="inference",
        path="/api/v1/generate",
        method="POST",
        headers=dict(request.headers),
        json_data=body,
    )

    return JSONResponse(
        status_code=result["status_code"], content=result["data"]
    )


@inference_router.get("/models")
@limiter.limit("30/minute")
async def list_models(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """List available AI models"""
    result = await proxy.forward_request(
        service="inference",
        path="/api/v1/models",
        method="GET",
        headers=dict(request.headers),
    )

    return JSONResponse(
        status_code=result["status_code"], content=result["data"]
    )


# Admin routes
@admin_router.get("/health")
@limiter.limit("60/minute")
async def admin_health_check(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Admin health check for all services"""
    # Check all services health
    services = ["auth", "data", "inference"]
    health_status = {}
    
    for service in services:
        try:
            result = await proxy.forward_request(
                service=service,
                path="/health",
                method="GET",
                headers=dict(request.headers),
                timeout=5
            )
            health_status[service] = {
                "status": "healthy" if result["status_code"] == 200 else "unhealthy",
                "response_time": result.get("response_time", 0)
            }
        except Exception as e:
            health_status[service] = {
                "status": "unreachable",
                "error": str(e)
            }
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "services": health_status,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    )


@admin_router.get("/stats")
@limiter.limit("30/minute")
async def admin_stats(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Get system statistics"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "stats": {
                "total_requests": 0,
                "active_users": 0,
                "system_load": "low"
            }
        }
    )