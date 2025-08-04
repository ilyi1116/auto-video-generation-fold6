"""
監控相關 API 端點
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List
import asyncio
from datetime import datetime, timedelta

from ..monitoring.health_monitor import health_monitor
from ..security import require_permission
from ..logging_system import AuditLogger

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
async def get_health_status():
    """獲取系統健康狀態"""
    try:
        status = health_monitor.get_health_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/components")
async def get_component_health():
    """獲取各組件健康狀態"""
    try:
        status = health_monitor.get_health_status()
        if "components" not in status:
            return {
                "success": True,
                "data": {}
            }
        
        return {
            "success": True,
            "data": status["components"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
@require_permission("system:dashboard")
async def get_active_alerts():
    """獲取活躍告警"""
    try:
        alerts = health_monitor.get_active_alerts()
        return {
            "success": True,
            "data": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/history")
@require_permission("system:dashboard")
async def get_metrics_history(hours: int = 24):
    """獲取指標歷史數據"""
    try:
        if hours > 168:  # 限制最多7天
            hours = 168
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # 過濾歷史數據
        filtered_history = [
            record for record in health_monitor.health_history
            if datetime.fromisoformat(record["timestamp"]) > cutoff_time
        ]
        
        return {
            "success": True,
            "data": {
                "history": filtered_history,
                "timeframe_hours": hours,
                "record_count": len(filtered_history)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/health/check")
@require_permission("system:dashboard")
async def trigger_health_check():
    """手動觸發健康檢查"""
    try:
        await health_monitor.run_health_checks()
        
        await AuditLogger.log_system_event(
            action="manual_health_check",
            message="手動觸發系統健康檢查",
            level="info"
        )
        
        return {
            "success": True,
            "message": "健康檢查已完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/summary")
async def get_metrics_summary():
    """獲取指標摘要"""
    try:
        status = health_monitor.get_health_status()
        alerts = health_monitor.get_active_alerts()
        
        if "components" not in status:
            return {
                "success": True,
                "data": {
                    "overall_status": "unknown",
                    "total_components": 0,
                    "healthy_components": 0,
                    "warning_components": 0,
                    "critical_components": 0,
                    "active_alerts": 0,
                    "last_check": None
                }
            }
        
        components = status["components"]
        healthy_count = sum(1 for comp in components.values() if comp["status"] == "healthy")
        warning_count = sum(1 for comp in components.values() if comp["status"] == "warning")
        critical_count = sum(1 for comp in components.values() if comp["status"] == "critical")
        
        return {
            "success": True,
            "data": {
                "overall_status": status.get("overall_status", "unknown"),
                "total_components": len(components),
                "healthy_components": healthy_count,
                "warning_components": warning_count,
                "critical_components": critical_count,
                "active_alerts": len(alerts),
                "last_check": status.get("timestamp")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config/thresholds")
@require_permission("system:settings")
async def update_thresholds(thresholds: Dict):
    """更新監控閾值"""
    try:
        # 驗證閾值格式
        valid_metrics = ["cpu_usage", "memory_usage", "disk_usage", "response_time", "error_rate", "queue_size"]
        
        for metric, values in thresholds.items():
            if metric not in valid_metrics:
                raise HTTPException(status_code=400, detail=f"無效的指標: {metric}")
            
            if not isinstance(values, dict) or "warning" not in values or "critical" not in values:
                raise HTTPException(status_code=400, detail=f"指標 {metric} 格式錯誤")
            
            if values["warning"] >= values["critical"]:
                raise HTTPException(status_code=400, detail=f"指標 {metric} 的警告閾值必須小於嚴重閾值")
        
        # 更新閾值
        health_monitor.thresholds.update(thresholds)
        
        await AuditLogger.log_system_event(
            action="update_monitoring_thresholds",
            message="更新監控閾值配置",
            details={"new_thresholds": thresholds},
            level="info"
        )
        
        return {
            "success": True,
            "message": "閾值更新成功",
            "data": health_monitor.thresholds
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/thresholds")
@require_permission("system:dashboard")
async def get_thresholds():
    """獲取當前監控閾值"""
    try:
        return {
            "success": True,
            "data": health_monitor.thresholds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/start")
@require_permission("system:settings")
async def start_monitoring():
    """啟動監控"""
    try:
        if health_monitor.running:
            return {
                "success": False,
                "message": "監控已在運行中"
            }
        
        # 在背景啟動監控
        asyncio.create_task(health_monitor.start_monitoring())
        
        await AuditLogger.log_system_event(
            action="start_monitoring",
            message="啟動健康監控系統",
            level="info"
        )
        
        return {
            "success": True,
            "message": "監控已啟動"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitoring/stop")
@require_permission("system:settings")
async def stop_monitoring():
    """停止監控"""
    try:
        health_monitor.stop_monitoring()
        
        await AuditLogger.log_system_event(
            action="stop_monitoring",
            message="停止健康監控系統",
            level="info"
        )
        
        return {
            "success": True,
            "message": "監控已停止"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))