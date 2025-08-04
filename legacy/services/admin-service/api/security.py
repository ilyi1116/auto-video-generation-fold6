"""
API 安全管理端點
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

from ..security.rate_limiter import rate_limiter, LimitType, RateLimit, WindowType
from ..security import require_permission, audit_log
from ..models import AdminUser
from ..schemas import APIResponse
from ..database import get_db

router = APIRouter(prefix="/security", tags=["security"])


class RateLimitConfig(BaseModel):
    """限流配置模型"""
    limit: int
    window_seconds: int
    window_type: str = "sliding"
    description: str = ""


class IPListRequest(BaseModel):
    """IP 列表請求模型"""
    ip_address: str
    duration_hours: Optional[int] = 24


class SecurityStatsResponse(BaseModel):
    """安全統計響應模型"""
    total_requests: int
    blocked_requests: int
    rate_limited_requests: int
    unique_ips: int
    threat_level: str


@router.get("/rate-limits/stats")
@require_permission("system:dashboard")
async def get_rate_limit_stats(
    current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """獲取限流統計"""
    try:
        stats = rate_limiter.get_stats()
        return APIResponse(data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rate-limits/config")
@require_permission("system:settings")
async def get_rate_limit_config(
    current_user: AdminUser = Depends(require_permission("system:settings"))
):
    """獲取限流配置"""
    try:
        config = {
            "default_limits": {
                limit_type.value: {
                    "limit": limit_config.limit,
                    "window_seconds": limit_config.window_seconds,
                    "window_type": limit_config.window_type.value,
                    "description": limit_config.description
                }
                for limit_type, limit_config in rate_limiter.default_limits.items()
            },
            "endpoint_limits": {
                endpoint: {
                    "limit": limit_config.limit,
                    "window_seconds": limit_config.window_seconds,
                    "window_type": limit_config.window_type.value,
                    "description": limit_config.description
                }
                for endpoint, limit_config in rate_limiter.endpoint_limits.items()
            }
        }
        return APIResponse(data=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rate-limits/default/{limit_type}")
@require_permission("system:settings")
@audit_log("update_rate_limit", "security")
async def update_default_rate_limit(
    limit_type: str,
    config: RateLimitConfig,
    current_user: AdminUser = Depends(require_permission("system:settings"))
):
    """更新默認限流配置"""
    try:
        # 驗證限流類型
        try:
            limit_type_enum = LimitType(limit_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"無效的限流類型: {limit_type}")
        
        # 驗證窗口類型
        try:
            window_type_enum = WindowType(config.window_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"無效的窗口類型: {config.window_type}")
        
        # 創建新的限流配置
        new_limit = RateLimit(
            limit=config.limit,
            window_seconds=config.window_seconds,
            window_type=window_type_enum,
            description=config.description
        )
        
        # 更新配置
        rate_limiter.update_limit(limit_type_enum, new_limit)
        
        return APIResponse(
            message=f"已更新 {limit_type} 限流配置",
            data={
                "limit_type": limit_type,
                "new_config": {
                    "limit": config.limit,
                    "window_seconds": config.window_seconds,
                    "window_type": config.window_type,
                    "description": config.description
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rate-limits/endpoint")
@require_permission("system:settings")
@audit_log("update_endpoint_rate_limit", "security")
async def update_endpoint_rate_limit(
    endpoint: str,
    config: RateLimitConfig,
    current_user: AdminUser = Depends(require_permission("system:settings"))
):
    """更新端點限流配置"""
    try:
        # 驗證窗口類型
        try:
            window_type_enum = WindowType(config.window_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"無效的窗口類型: {config.window_type}")
        
        # 創建新的限流配置
        new_limit = RateLimit(
            limit=config.limit,
            window_seconds=config.window_seconds,
            window_type=window_type_enum,
            description=config.description
        )
        
        # 更新配置
        rate_limiter.update_endpoint_limit(endpoint, new_limit)
        
        return APIResponse(
            message=f"已更新端點 {endpoint} 限流配置",
            data={
                "endpoint": endpoint,
                "new_config": {
                    "limit": config.limit,
                    "window_seconds": config.window_seconds,
                    "window_type": config.window_type,
                    "description": config.description
                }
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blacklist")
@require_permission("system:dashboard")
async def get_blacklist(
    current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """獲取黑名單 IP"""
    try:
        blacklist = list(rate_limiter.blacklist_ips)
        return APIResponse(data={"blacklist": blacklist, "count": len(blacklist)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/blacklist")
@require_permission("system:settings")
@audit_log("add_ip_blacklist", "security")
async def add_to_blacklist(
    request_data: IPListRequest,
    current_user: AdminUser = Depends(require_permission("system:settings"))
):
    """添加 IP 到黑名單"""
    try:
        rate_limiter.add_to_blacklist(
            request_data.ip_address, 
            request_data.duration_hours or 24
        )
        
        return APIResponse(
            message=f"已將 IP {request_data.ip_address} 添加到黑名單",
            data={
                "ip_address": request_data.ip_address,
                "duration_hours": request_data.duration_hours or 24
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/blacklist/{ip_address}")
@require_permission("system:settings")
@audit_log("remove_ip_blacklist", "security")
async def remove_from_blacklist(
    ip_address: str,
    current_user: AdminUser = Depends(require_permission("system:settings"))
):
    """從黑名單移除 IP"""
    try:
        rate_limiter.remove_from_blacklist(ip_address)
        
        return APIResponse(
            message=f"已將 IP {ip_address} 從黑名單移除",
            data={"ip_address": ip_address}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/whitelist")
@require_permission("system:dashboard")
async def get_whitelist(
    current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """獲取白名單 IP"""
    try:
        whitelist = list(rate_limiter.whitelist_ips)
        return APIResponse(data={"whitelist": whitelist, "count": len(whitelist)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/whitelist")
@require_permission("system:settings")
@audit_log("add_ip_whitelist", "security")
async def add_to_whitelist(
    request_data: IPListRequest,
    current_user: AdminUser = Depends(require_permission("system:settings"))
):
    """添加 IP 到白名單"""
    try:
        rate_limiter.add_to_whitelist(request_data.ip_address)
        
        return APIResponse(
            message=f"已將 IP {request_data.ip_address} 添加到白名單",
            data={"ip_address": request_data.ip_address}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/whitelist/{ip_address}")
@require_permission("system:settings")
@audit_log("remove_ip_whitelist", "security")
async def remove_from_whitelist(
    ip_address: str,
    current_user: AdminUser = Depends(require_permission("system:settings"))
):
    """從白名單移除 IP"""
    try:
        rate_limiter.remove_from_whitelist(ip_address)
        
        return APIResponse(
            message=f"已將 IP {ip_address} 從白名單移除",
            data={"ip_address": ip_address}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/threats/analysis")
@require_permission("system:dashboard")
async def get_threat_analysis(
    hours: int = 24,
    current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """獲取威脅分析"""
    try:
        from ..database import SessionLocal
        from ..models import SystemLog
        from sqlalchemy import func, and_
        from datetime import datetime, timedelta
        
        db = SessionLocal()
        
        try:
            # 計算時間範圍
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 查詢安全相關日誌
            security_logs = db.query(SystemLog).filter(
                and_(
                    SystemLog.created_at >= cutoff_time,
                    SystemLog.action.in_([
                        "rate_limit_exceeded",
                        "invalid_token",
                        "user_not_found",
                        "login_failed"
                    ])
                )
            ).all()
            
            # 統計分析
            threat_stats = {
                "total_threats": len(security_logs),
                "rate_limit_violations": len([log for log in security_logs if log.action == "rate_limit_exceeded"]),
                "invalid_tokens": len([log for log in security_logs if log.action == "invalid_token"]),
                "failed_logins": len([log for log in security_logs if log.action == "login_failed"]),
                "unique_ips": len(set(log.ip_address for log in security_logs if log.ip_address)),
                "time_range_hours": hours
            }
            
            # 計算威脅等級
            if threat_stats["total_threats"] > 100:
                threat_level = "high"
            elif threat_stats["total_threats"] > 50:
                threat_level = "medium"
            elif threat_stats["total_threats"] > 10:
                threat_level = "low"
            else:
                threat_level = "minimal"
            
            threat_stats["threat_level"] = threat_level
            
            # 獲取最活躍的 IP
            ip_counts = {}
            for log in security_logs:
                if log.ip_address:
                    ip_counts[log.ip_address] = ip_counts.get(log.ip_address, 0) + 1
            
            top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            threat_stats["top_threat_ips"] = [
                {"ip": ip, "count": count} for ip, count in top_ips
            ]
            
            return APIResponse(data=threat_stats)
            
        finally:
            db.close()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-rate-limit")
@require_permission("system:dashboard")
async def test_rate_limit(
    request: Request,
    current_user: AdminUser = Depends(require_permission("system:dashboard"))
):
    """測試限流功能"""
    try:
        # 檢查當前請求的限流狀態
        limit_result = await rate_limiter.check_rate_limit(request)
        
        if limit_result and not limit_result.allowed:
            return APIResponse(
                success=False,
                message="請求被限流",
                data={
                    "allowed": False,
                    "limit": limit_result.limit,
                    "remaining": limit_result.remaining,
                    "reset_time": limit_result.reset_time.isoformat(),
                    "retry_after": limit_result.retry_after
                }
            )
        else:
            return APIResponse(
                message="請求通過限流檢查",
                data={
                    "allowed": True,
                    "message": "當前請求未觸發任何限流規則"
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))