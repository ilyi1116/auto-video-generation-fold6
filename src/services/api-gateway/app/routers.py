from datetime import datetime

import structlog
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import JSONResponse

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
        return JSONResponse(status_code=result["status_code"], content=result["data"])
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
        return JSONResponse(status_code=result["status_code"], content=result["data"])
    else:
        raise HTTPException(
            status_code=result["status_code"],
            detail=result["data"].get("detail", "Login failed"),
        )


@auth_router.get("/me")
@limiter.limit("30/minute")
async def get_profile(request: Request, current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    result = await proxy.forward_request(
        service="auth",
        path="/api/v1/me",
        method="GET",
        headers=dict(request.headers),
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@auth_router.put("/me")
@limiter.limit("10/minute")
async def update_profile(request: Request, current_user: dict = Depends(get_current_user)):
    """Update user profile"""
    body = await request.json()
    result = await proxy.forward_request(
        service="auth",
        path="/api/v1/me",
        method="PUT",
        headers=dict(request.headers),
        json_data=body,
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@auth_router.post("/change-password")
@limiter.limit("5/minute")
async def change_password(request: Request, current_user: dict = Depends(get_current_user)):
    """Change user password"""
    body = await request.json()
    result = await proxy.forward_request(
        service="auth",
        path="/api/v1/change-password",
        method="POST",
        headers=dict(request.headers),
        json_data=body,
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


# Data ingestion routes
@data_router.post("/upload")
@limiter.limit("10/minute")
async def upload_audio(
    request: Request,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Upload audio file for training"""
    # Forward to data service
    result = await proxy.forward_file_request(
        service="data",
        path="/api/v1/upload",
        method="POST",
        headers=dict(request.headers),
        file=file,
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@data_router.get("/files")
@limiter.limit("30/minute")
async def get_user_files(request: Request, current_user: dict = Depends(get_current_user)):
    """Get user's uploaded files"""
    result = await proxy.forward_request(
        service="data",
        path="/api/v1/files",
        method="GET",
        headers=dict(request.headers),
        params=dict(request.query_params),
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@data_router.delete("/files/{file_id}")
@limiter.limit("10/minute")
async def delete_file(
    file_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Delete uploaded file"""
    result = await proxy.forward_request(
        service="data",
        path=f"/api/v1/files/{file_id}",
        method="DELETE",
        headers=dict(request.headers),
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@data_router.post("/process/{file_id}")
@limiter.limit("20/minute")
async def start_processing(
    file_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Start processing job for uploaded file"""
    body = await request.json()
    result = await proxy.forward_request(
        service="data",
        path=f"/api/v1/process/{file_id}",
        method="POST",
        headers=dict(request.headers),
        json_data=body,
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@data_router.get("/jobs")
@limiter.limit("30/minute")
async def get_processing_jobs(request: Request, current_user: dict = Depends(get_current_user)):
    """Get user's processing jobs"""
    result = await proxy.forward_request(
        service="data",
        path="/api/v1/jobs",
        method="GET",
        headers=dict(request.headers),
        params=dict(request.query_params),
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@data_router.get("/jobs/{job_id}")
@limiter.limit("30/minute")
async def get_job_status(
    job_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get processing job status"""
    result = await proxy.forward_request(
        service="data",
        path=f"/api/v1/jobs/{job_id}",
        method="GET",
        headers=dict(request.headers),
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@data_router.delete("/jobs/{job_id}")
@limiter.limit("10/minute")
async def cancel_job(
    job_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Cancel processing job"""
    result = await proxy.forward_request(
        service="data",
        path=f"/api/v1/jobs/{job_id}",
        method="DELETE",
        headers=dict(request.headers),
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


# Inference routes
@inference_router.post("/synthesize")
@limiter.limit("20/minute")
async def synthesize_voice(request: Request, current_user: dict = Depends(get_current_user)):
    """Synthesize voice from text"""
    body = await request.json()
    result = await proxy.forward_request(
        service="inference",
        path="/api/v1/synthesize",
        method="POST",
        headers=dict(request.headers),
        json_data=body,
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@inference_router.post("/synthesize/batch")
@limiter.limit("10/minute")
async def batch_synthesize_voice(request: Request, current_user: dict = Depends(get_current_user)):
    """Batch synthesize multiple texts"""
    body = await request.json()
    result = await proxy.forward_request(
        service="inference",
        path="/api/v1/synthesize/batch",
        method="POST",
        headers=dict(request.headers),
        json_data=body,
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@inference_router.get("/synthesize/audio/{job_id}")
@limiter.limit("30/minute")
async def get_synthesis_audio(
    job_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get synthesized audio file"""
    result = await proxy.forward_request(
        service="inference",
        path=f"/api/v1/synthesize/audio/{job_id}",
        method="GET",
        headers=dict(request.headers),
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@inference_router.get("/jobs")
@limiter.limit("30/minute")
async def get_synthesis_jobs(request: Request, current_user: dict = Depends(get_current_user)):
    """Get user's synthesis jobs"""
    result = await proxy.forward_request(
        service="inference",
        path="/api/v1/jobs",
        method="GET",
        headers=dict(request.headers),
        params=dict(request.query_params),
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@inference_router.get("/jobs/{job_id}")
@limiter.limit("30/minute")
async def get_synthesis_job(
    job_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get synthesis job details"""
    result = await proxy.forward_request(
        service="inference",
        path=f"/api/v1/jobs/{job_id}",
        method="GET",
        headers=dict(request.headers),
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@inference_router.get("/models")
@limiter.limit("30/minute")
async def get_available_models(request: Request, current_user: dict = Depends(get_current_user)):
    """Get available voice models for user"""
    result = await proxy.forward_request(
        service="inference",
        path="/api/v1/models",
        method="GET",
        headers=dict(request.headers),
        params=dict(request.query_params),
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@inference_router.get("/models/ready")
@limiter.limit("30/minute")
async def get_ready_models(request: Request, current_user: dict = Depends(get_current_user)):
    """Get ready-to-use voice models"""
    result = await proxy.forward_request(
        service="inference",
        path="/api/v1/models/ready",
        method="GET",
        headers=dict(request.headers),
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@inference_router.get("/models/{model_id}")
@limiter.limit("30/minute")
async def get_model_details(
    model_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Get voice model details"""
    result = await proxy.forward_request(
        service="inference",
        path=f"/api/v1/models/{model_id}",
        method="GET",
        headers=dict(request.headers),
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


@inference_router.post("/models/{model_id}/preload")
@limiter.limit("10/minute")
async def preload_model(
    model_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Preload model into cache"""
    result = await proxy.forward_request(
        service="inference",
        path=f"/api/v1/models/{model_id}/preload",
        method="POST",
        headers=dict(request.headers),
    )

    return JSONResponse(status_code=result["status_code"], content=result["data"])


# Admin routes
@admin_router.get("/health")
async def admin_health_check(request: Request):
    """Check health of all services"""
    health_status = {}

    for service in ["auth", "data", "inference"]:
        health_status[service] = await proxy.health_check_service(service)

    overall_healthy = all(health_status.values())
    status_code = 200 if overall_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if overall_healthy else "unhealthy",
            "services": health_status,
            "gateway": "healthy",
        },
    )


@admin_router.get("/metrics")
@limiter.limit("10/minute")
async def get_metrics(request: Request):
    """Get basic metrics"""
    try:
        # Collect basic metrics
        metrics = {
            "uptime": get_uptime(),
            "requests_total": get_total_requests(),
            "active_users": get_active_users(),
            "services_health": await get_services_health(),
            "system_resources": get_system_resources(),
            "timestamp": datetime.utcnow().isoformat(),
        }

        return JSONResponse(status_code=200, content=metrics)
    except Exception as e:
        logger.error(f"Failed to collect metrics: {e}")
        return JSONResponse(status_code=500, content={"error": "Failed to collect metrics"})


def get_uptime() -> str:
    """Get system uptime"""
    import time

    import psutil

    try:
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        return format_uptime(uptime_seconds)
    except:
        return "unknown"


def get_total_requests() -> int:
    """Get total requests count"""
    # This would typically come from a metrics collector
    # For now, return a placeholder
    return 0


def get_active_users() -> int:
    """Get active users count"""
    # This would typically come from session management
    # For now, return a placeholder
    return 0


async def get_services_health() -> dict:
    """Get health status of all services"""
    services = [
        "auth",
        "data",
        "inference",
        "video",
        "ai",
        "social",
        "trend",
        "scheduler",
    ]
    health_status = {}

    for service in services:
        try:
            health_status[service] = await proxy.health_check_service(service)
        except Exception:
            health_status[service] = False

    return health_status


def get_system_resources() -> dict:
    """Get system resource usage"""
    import psutil

    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        }
    except:
        return {"cpu_percent": 0, "memory_percent": 0, "disk_percent": 0}


def format_uptime(seconds: float) -> str:
    """Format uptime in human readable format"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)

    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"
