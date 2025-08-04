"""
智能日誌分析 API 端點

提供日誌分析、異常檢測、預測分析和告警管理的 RESTful API。
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

from ..auth.permissions import require_permission
from ..models.admin_user import AdminUser
from ..logs import (
    log_collector, log_analyzer, anomaly_detector, 
    log_predictor, log_aggregator, log_alerting
)
from ..logs.analyzer import AnalysisType
from ..logs.detector import AnomalyType, Severity
from ..logs.predictor import PredictionType, TimeHorizon
from ..logs.aggregator import AggregationType, TimeGranularity, AggregationQuery
from ..logs.alerting import AlertType, AlertSeverity, AlertRule

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/logs", tags=["logs"])


# Pydantic 模型
class LogEntryModel(BaseModel):
    timestamp: datetime
    level: str
    message: str
    service: str
    source: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    duration_ms: Optional[float] = None
    error_code: Optional[str] = None
    error_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AnalysisRequest(BaseModel):
    analysis_type: str
    service: Optional[str] = None
    hours: int = Field(default=24, ge=1, le=168)  # 1小時到1週


class AnomalyDetectionRequest(BaseModel):
    hours: int = Field(default=1, ge=1, le=24)
    service: Optional[str] = None


class PredictionRequest(BaseModel):
    time_horizon: str = Field(default="short_term")
    service: Optional[str] = None


class AggregationRequest(BaseModel):
    metric_name: str
    aggregation_type: str
    time_granularity: str
    start_time: datetime
    end_time: datetime
    group_by: Optional[List[str]] = None
    filter_conditions: Optional[Dict[str, Any]] = None
    percentile: Optional[int] = Field(default=None, ge=1, le=99)


class AlertRuleModel(BaseModel):
    rule_id: str
    name: str
    description: str
    alert_type: str
    severity: str
    conditions: Dict[str, Any]
    thresholds: Dict[str, float]
    enabled: bool = True
    cooldown_minutes: int = Field(default=15, ge=1, le=1440)
    auto_resolve: bool = True
    notification_channels: List[str] = []


class AlertActionRequest(BaseModel):
    comment: Optional[str] = ""


# 日誌收集 API
@router.post("/collect")
@require_permission("logs:write")
async def collect_log(
    log_entry: LogEntryModel,
    current_user: AdminUser = Depends(require_permission("logs:write"))
):
    """收集日誌條目"""
    try:
        await log_collector.collect_log(log_entry.dict())
        return {"status": "success", "message": "日誌已收集"}
    except Exception as e:
        logger.error(f"收集日誌失敗: {e}")
        raise HTTPException(status_code=500, detail=f"收集日誌失敗: {str(e)}")


@router.post("/collect/batch")
@require_permission("logs:write")
async def collect_logs_batch(
    log_entries: List[LogEntryModel],
    current_user: AdminUser = Depends(require_permission("logs:write"))
):
    """批量收集日誌條目"""
    try:
        for log_entry in log_entries:
            await log_collector.collect_log(log_entry.dict())
        
        return {
            "status": "success", 
            "message": f"已收集 {len(log_entries)} 條日誌",
            "count": len(log_entries)
        }
    except Exception as e:
        logger.error(f"批量收集日誌失敗: {e}")
        raise HTTPException(status_code=500, detail=f"批量收集日誌失敗: {str(e)}")


# 日誌查詢 API
@router.get("/search")
@require_permission("logs:read")
async def search_logs(
    service: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    error_only: bool = Query(False),
    current_user: AdminUser = Depends(require_permission("logs:read"))
):
    """搜索日誌"""
    try:
        logs = await log_collector.get_logs(
            service=service,
            level=level,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            error_only=error_only
        )
        
        return {
            "logs": [log.to_dict() for log in logs],
            "count": len(logs),
            "search_params": {
                "service": service,
                "level": level,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "limit": limit,
                "error_only": error_only
            }
        }
    except Exception as e:
        logger.error(f"搜索日誌失敗: {e}")
        raise HTTPException(status_code=500, detail=f"搜索日誌失敗: {str(e)}")


@router.get("/stats")
@require_permission("logs:read")
async def get_log_stats(
    current_user: AdminUser = Depends(require_permission("logs:read"))
):
    """獲取日誌統計"""
    try:
        stats = log_collector.get_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"獲取日誌統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取統計失敗: {str(e)}")


# 日誌分析 API
@router.post("/analyze")
@require_permission("logs:analyze")
async def analyze_logs(
    request: AnalysisRequest,
    current_user: AdminUser = Depends(require_permission("logs:analyze"))
):
    """執行日誌分析"""
    try:
        # 驗證分析類型
        try:
            analysis_type = AnalysisType(request.analysis_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的分析類型: {request.analysis_type}")
        
        result = await log_analyzer.analyze_logs(
            analysis_type=analysis_type,
            service=request.service,
            hours=request.hours
        )
        
        return {
            "status": "success",
            "analysis": {
                "type": result.analysis_type.value,
                "timestamp": result.timestamp.isoformat(),
                "service": result.service,
                "summary": result.summary,
                "details": result.details,
                "severity": result.severity,
                "recommendations": result.recommendations,
                "affected_users": result.affected_users,
                "affected_requests": result.affected_requests
            }
        }
    except Exception as e:
        logger.error(f"日誌分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"分析失敗: {str(e)}")


@router.get("/analyze/patterns")
@require_permission("logs:analyze")
async def detect_patterns(
    hours: int = Query(24, ge=1, le=168),
    current_user: AdminUser = Depends(require_permission("logs:analyze"))
):
    """檢測日誌模式"""
    try:
        patterns = await log_analyzer.detect_patterns(hours=hours)
        
        return {
            "status": "success",
            "patterns": [
                {
                    "pattern_type": p.pattern_type.value,
                    "timestamp": p.timestamp.isoformat(),
                    "description": p.description,
                    "confidence": p.confidence,
                    "evidence": p.evidence,
                    "impact_score": p.impact_score
                }
                for p in patterns
            ],
            "count": len(patterns)
        }
    except Exception as e:
        logger.error(f"模式檢測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"模式檢測失敗: {str(e)}")


# 異常檢測 API
@router.post("/anomalies/detect")
@require_permission("logs:analyze")
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    current_user: AdminUser = Depends(require_permission("logs:analyze"))
):
    """檢測異常"""
    try:
        anomalies = await anomaly_detector.detect_anomalies(
            hours=request.hours,
            service=request.service
        )
        
        return {
            "status": "success",
            "anomalies": [
                {
                    "anomaly_id": a.anomaly_id,
                    "anomaly_type": a.anomaly_type.value,
                    "severity": a.severity.value,
                    "timestamp": a.timestamp.isoformat(),
                    "description": a.description,
                    "confidence_score": a.confidence_score,
                    "baseline_value": a.baseline_value,
                    "actual_value": a.actual_value,
                    "threshold_value": a.threshold_value,
                    "affected_service": a.affected_service,
                    "metadata": a.metadata
                }
                for a in anomalies
            ],
            "count": len(anomalies)
        }
    except Exception as e:
        logger.error(f"異常檢測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"異常檢測失敗: {str(e)}")


@router.get("/anomalies/stats")
@require_permission("logs:read")
async def get_anomaly_stats(
    current_user: AdminUser = Depends(require_permission("logs:read"))
):
    """獲取異常統計"""
    try:
        stats = anomaly_detector.get_anomaly_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"獲取異常統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取統計失敗: {str(e)}")


# 預測分析 API
@router.post("/predict")
@require_permission("logs:analyze")
async def generate_predictions(
    request: PredictionRequest,
    current_user: AdminUser = Depends(require_permission("logs:analyze"))
):
    """生成預測"""
    try:
        # 驗證時間範圍
        try:
            time_horizon = TimeHorizon(request.time_horizon)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"不支持的時間範圍: {request.time_horizon}")
        
        predictions = await log_predictor.generate_predictions(
            time_horizon=time_horizon,
            service=request.service
        )
        
        return {
            "status": "success",
            "predictions": [
                {
                    "prediction_id": p.prediction_id,
                    "prediction_type": p.prediction_type.value,
                    "time_horizon": p.time_horizon.value,
                    "created_at": p.created_at.isoformat(),
                    "forecast_time": p.forecast_time.isoformat(),
                    "predicted_value": p.predicted_value,
                    "confidence_interval": p.confidence_interval,
                    "confidence_score": p.confidence_score,
                    "description": p.description,
                    "baseline_value": p.baseline_value,
                    "trend_direction": p.trend_direction,
                    "risk_level": p.risk_level,
                    "affected_service": p.affected_service,
                    "recommendations": p.recommendations
                }
                for p in predictions
            ],
            "count": len(predictions)
        }
    except Exception as e:
        logger.error(f"預測分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"預測分析失敗: {str(e)}")


@router.get("/predict/stats")
@require_permission("logs:read")
async def get_prediction_stats(
    current_user: AdminUser = Depends(require_permission("logs:read"))
):
    """獲取預測統計"""
    try:
        stats = log_predictor.get_prediction_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"獲取預測統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取統計失敗: {str(e)}")


# 聚合分析 API
@router.post("/aggregate")
@require_permission("logs:analyze")
async def aggregate_logs(
    request: AggregationRequest,
    current_user: AdminUser = Depends(require_permission("logs:analyze"))
):
    """執行日誌聚合"""
    try:
        # 構建聚合查詢
        query = AggregationQuery(
            metric_name=request.metric_name,
            aggregation_type=AggregationType(request.aggregation_type),
            time_granularity=TimeGranularity(request.time_granularity),
            start_time=request.start_time,
            end_time=request.end_time,
            group_by=request.group_by,
            filter_conditions=request.filter_conditions,
            percentile=request.percentile
        )
        
        result = await log_aggregator.aggregate(query)
        
        return {
            "status": "success",
            "aggregation": {
                "data_points": result.data_points,
                "summary": result.summary,
                "created_at": result.created_at.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"無效的聚合參數: {str(e)}")
    except Exception as e:
        logger.error(f"日誌聚合失敗: {e}")
        raise HTTPException(status_code=500, detail=f"聚合失敗: {str(e)}")


@router.get("/aggregate/predefined/{query_name}")
@require_permission("logs:read")
async def get_predefined_aggregation(
    query_name: str,
    current_user: AdminUser = Depends(require_permission("logs:read"))
):
    """獲取預定義聚合結果"""
    try:
        result = await log_aggregator.get_predefined_aggregation(query_name)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"未找到預定義查詢: {query_name}")
        
        return {
            "status": "success",
            "aggregation": {
                "data_points": result.data_points,
                "summary": result.summary,
                "created_at": result.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取預定義聚合失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取聚合失敗: {str(e)}")


@router.get("/dashboard")
@require_permission("logs:read")
async def get_dashboard_data(
    time_range_hours: int = Query(24, ge=1, le=168),
    current_user: AdminUser = Depends(require_permission("logs:read"))
):
    """獲取儀表板數據"""
    try:
        dashboard_data = await log_aggregator.create_dashboard_data(
            time_range_hours=time_range_hours
        )
        
        return {
            "status": "success",
            "dashboard": dashboard_data
        }
    except Exception as e:
        logger.error(f"獲取儀表板數據失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取儀表板數據失敗: {str(e)}")


@router.get("/reports/{report_type}")
@require_permission("logs:read")
async def generate_report(
    report_type: str,
    service: Optional[str] = Query(None),
    current_user: AdminUser = Depends(require_permission("logs:read"))
):
    """生成聚合報告"""
    try:
        if report_type not in ["daily", "weekly", "monthly"]:
            raise HTTPException(status_code=400, detail=f"不支持的報告類型: {report_type}")
        
        report = await log_aggregator.generate_report(
            report_type=report_type,
            service=service
        )
        
        return {
            "status": "success",
            "report": report
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成報告失敗: {e}")
        raise HTTPException(status_code=500, detail=f"生成報告失敗: {str(e)}")


# 告警管理 API
@router.get("/alerts")
@require_permission("logs:read")
async def get_active_alerts(
    severity: Optional[str] = Query(None),
    current_user: AdminUser = Depends(require_permission("logs:read"))
):
    """獲取活躍告警"""
    try:
        severity_enum = None
        if severity:
            try:
                severity_enum = AlertSeverity(severity)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"無效的嚴重程度: {severity}")
        
        alerts = log_alerting.get_active_alerts(severity=severity_enum)
        
        return {
            "status": "success",
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "rule_id": a.rule_id,
                    "title": a.title,
                    "description": a.description,
                    "alert_type": a.alert_type.value,
                    "severity": a.severity.value,
                    "status": a.status.value,
                    "created_at": a.created_at.isoformat(),
                    "affected_service": a.affected_service,
                    "affected_users": a.affected_users,
                    "evidence": a.evidence,
                    "recommendations": a.recommendations,
                    "acknowledged_at": a.acknowledged_at.isoformat() if a.acknowledged_at else None,
                    "acknowledged_by": a.acknowledged_by
                }
                for a in alerts
            ],
            "count": len(alerts)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取告警失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取告警失敗: {str(e)}")


@router.post("/alerts/{alert_id}/acknowledge")
@require_permission("logs:manage")
async def acknowledge_alert(
    alert_id: str,
    request: AlertActionRequest,
    current_user: AdminUser = Depends(require_permission("logs:manage"))
):
    """確認告警"""
    try:
        success = await log_alerting.acknowledge_alert(
            alert_id=alert_id,
            acknowledged_by=current_user.username,
            comment=request.comment
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        return {"status": "success", "message": "告警已確認"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"確認告警失敗: {e}")
        raise HTTPException(status_code=500, detail=f"確認告警失敗: {str(e)}")


@router.post("/alerts/{alert_id}/resolve")
@require_permission("logs:manage")
async def resolve_alert(
    alert_id: str,
    request: AlertActionRequest,
    current_user: AdminUser = Depends(require_permission("logs:manage"))
):
    """解決告警"""
    try:
        success = await log_alerting.resolve_alert(
            alert_id=alert_id,
            resolved_by=current_user.username,
            comment=request.comment
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        return {"status": "success", "message": "告警已解決"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解決告警失敗: {e}")
        raise HTTPException(status_code=500, detail=f"解決告警失敗: {str(e)}")


@router.get("/alerts/stats")
@require_permission("logs:read")
async def get_alert_statistics(
    current_user: AdminUser = Depends(require_permission("logs:read"))
):
    """獲取告警統計"""
    try:
        stats = log_alerting.get_alert_statistics()
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"獲取告警統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取統計失敗: {str(e)}")


# 告警規則管理 API
@router.get("/alert-rules")
@require_permission("logs:read")
async def get_alert_rules(
    current_user: AdminUser = Depends(require_permission("logs:read"))
):
    """獲取告警規則"""
    try:
        rules = list(log_alerting.alert_rules.values())
        
        return {
            "status": "success",
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "name": r.name,
                    "description": r.description,
                    "alert_type": r.alert_type.value,
                    "severity": r.severity.value,
                    "conditions": r.conditions,
                    "thresholds": r.thresholds,
                    "enabled": r.enabled,
                    "cooldown_minutes": r.cooldown_minutes,
                    "auto_resolve": r.auto_resolve,
                    "notification_channels": r.notification_channels
                }
                for r in rules
            ],
            "count": len(rules)
        }
    except Exception as e:
        logger.error(f"獲取告警規則失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取規則失敗: {str(e)}")


@router.post("/alert-rules")
@require_permission("logs:manage")
async def create_alert_rule(
    rule_model: AlertRuleModel,
    current_user: AdminUser = Depends(require_permission("logs:manage"))
):
    """創建告警規則"""
    try:
        rule = AlertRule(
            rule_id=rule_model.rule_id,
            name=rule_model.name,
            description=rule_model.description,
            alert_type=AlertType(rule_model.alert_type),
            severity=AlertSeverity(rule_model.severity),
            conditions=rule_model.conditions,
            thresholds=rule_model.thresholds,
            enabled=rule_model.enabled,
            cooldown_minutes=rule_model.cooldown_minutes,
            auto_resolve=rule_model.auto_resolve,
            notification_channels=rule_model.notification_channels
        )
        
        log_alerting.add_alert_rule(rule)
        
        return {"status": "success", "message": "告警規則已創建"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"無效的規則參數: {str(e)}")
    except Exception as e:
        logger.error(f"創建告警規則失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建規則失敗: {str(e)}")


@router.put("/alert-rules/{rule_id}/enable")
@require_permission("logs:manage")
async def enable_alert_rule(
    rule_id: str,
    current_user: AdminUser = Depends(require_permission("logs:manage"))
):
    """啟用告警規則"""
    try:
        success = log_alerting.enable_rule(rule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="告警規則不存在")
        
        return {"status": "success", "message": "告警規則已啟用"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"啟用告警規則失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟用規則失敗: {str(e)}")


@router.put("/alert-rules/{rule_id}/disable")
@require_permission("logs:manage")
async def disable_alert_rule(
    rule_id: str,
    current_user: AdminUser = Depends(require_permission("logs:manage"))
):
    """禁用告警規則"""
    try:
        success = log_alerting.disable_rule(rule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="告警規則不存在")
        
        return {"status": "success", "message": "告警規則已禁用"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"禁用告警規則失敗: {e}")
        raise HTTPException(status_code=500, detail=f"禁用規則失敗: {str(e)}")


@router.delete("/alert-rules/{rule_id}")
@require_permission("logs:manage")
async def delete_alert_rule(
    rule_id: str,
    current_user: AdminUser = Depends(require_permission("logs:manage"))
):
    """刪除告警規則"""
    try:
        success = log_alerting.remove_alert_rule(rule_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="告警規則不存在")
        
        return {"status": "success", "message": "告警規則已刪除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除告警規則失敗: {e}")
        raise HTTPException(status_code=500, detail=f"刪除規則失敗: {str(e)}")


# 數據導出 API
@router.post("/export")
@require_permission("logs:export")
async def export_logs(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    output_format: str = Query("jsonl", regex="^(jsonl|csv)$"),
    current_user: AdminUser = Depends(require_permission("logs:export"))
):
    """導出日誌"""
    try:
        # 生成導出文件路徑
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = f"/tmp/logs_export_{timestamp}.{output_format}"
        
        # 執行導出
        exported_count = await log_collector.export_logs(
            output_path=output_path,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "status": "success",
            "message": f"已導出 {exported_count} 條日誌",
            "exported_count": exported_count,
            "output_path": output_path,
            "output_format": output_format
        }
    except Exception as e:
        logger.error(f"導出日誌失敗: {e}")
        raise HTTPException(status_code=500, detail=f"導出失敗: {str(e)}")


# 系統管理 API
@router.post("/cache/clear")
@require_permission("system:admin")
async def clear_cache(
    current_user: AdminUser = Depends(require_permission("system:admin"))
):
    """清空緩存"""
    try:
        log_aggregator.clear_cache()
        return {"status": "success", "message": "緩存已清空"}
    except Exception as e:
        logger.error(f"清空緩存失敗: {e}")
        raise HTTPException(status_code=500, detail=f"清空緩存失敗: {str(e)}")


@router.get("/health")
async def health_check():
    """健康檢查"""
    try:
        # 檢查各個組件的狀態
        collector_stats = log_collector.get_stats()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "log_collector": {
                    "status": "healthy",
                    "total_logs": collector_stats.get("total_logs", 0),
                    "memory_logs": collector_stats.get("memory_logs_count", 0)
                },
                "log_analyzer": {"status": "healthy"},
                "anomaly_detector": {"status": "healthy"},
                "log_predictor": {"status": "healthy"},
                "log_aggregator": {"status": "healthy"},
                "log_alerting": {"status": "healthy"}
            }
        }
        
        return health_status
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }