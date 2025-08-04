"""
用戶行為追蹤 API 端點

提供用戶行為追蹤、分析、模式檢測和洞察生成的 RESTful API。
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from pydantic import BaseModel, Field

from ..auth.permissions import require_permission
from ..models.admin_user import AdminUser
from ..behavior import (
    behavior_collector, behavior_tracker, behavior_analyzer,
    pattern_detector, insight_generator, init_behavior_system
)
from ..behavior.models import ActionType, UserSegment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/behavior", tags=["behavior"])

# 確保行為追蹤系統已初始化
init_behavior_system()


# Pydantic 模型
class TrackActionRequest(BaseModel):
    user_id: str
    action_type: str
    page_url: Optional[str] = None
    element_id: Optional[str] = None
    element_text: Optional[str] = None
    coordinates: Optional[Dict[str, int]] = None
    duration_ms: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None


class PageViewRequest(BaseModel):
    user_id: str
    page_url: str
    page_title: Optional[str] = None
    referrer: Optional[str] = None
    load_time_ms: Optional[int] = None


class ConversionRequest(BaseModel):
    user_id: str
    conversion_type: str
    conversion_value: Optional[float] = None
    page_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    user_id: str
    query: str
    results_count: Optional[int] = None
    page_url: Optional[str] = None


class ABTestRequest(BaseModel):
    test_id: str
    test_name: str
    variants: List[str]
    traffic_allocation: Dict[str, float]
    success_metrics: List[str]
    description: Optional[str] = None


class CohortRequest(BaseModel):
    cohort_name: str
    user_ids: List[str]


# 數據收集 API
@router.post("/track/action")
async def track_action(
    request: TrackActionRequest,
    http_request: Request,
    current_user: AdminUser = Depends(require_permission("behavior:write"))
):
    """追蹤用戶動作"""
    try:
        # 提取請求信息
        request_info = {
            "ip_address": http_request.client.host,
            "user_agent": http_request.headers.get("user-agent"),
            "referrer": http_request.headers.get("referer")
        }
        
        action = await behavior_tracker.track_action(
            user_id=request.user_id,
            action_type=request.action_type,
            page_url=request.page_url,
            element_id=request.element_id,
            element_text=request.element_text,
            coordinates=request.coordinates,
            duration_ms=request.duration_ms,
            metadata=request.metadata,
            context=request.context,
            request_info=request_info
        )
        
        if action:
            return {"status": "success", "action_id": action.action_id}
        else:
            raise HTTPException(status_code=400, detail="無法追蹤動作")
            
    except Exception as e:
        logger.error(f"追蹤用戶動作失敗: {e}")
        raise HTTPException(status_code=500, detail=f"追蹤失敗: {str(e)}")


@router.post("/track/page-view")
async def track_page_view(
    request: PageViewRequest,
    http_request: Request,
    current_user: AdminUser = Depends(require_permission("behavior:write"))
):
    """追蹤頁面瀏覽"""
    try:
        request_info = {
            "ip_address": http_request.client.host,
            "user_agent": http_request.headers.get("user-agent"),
            "referrer": http_request.headers.get("referer")
        }
        
        action = await behavior_tracker.track_page_view(
            user_id=request.user_id,
            page_url=request.page_url,
            page_title=request.page_title,
            referrer=request.referrer,
            load_time_ms=request.load_time_ms,
            request_info=request_info
        )
        
        return {"status": "success", "action_id": action.action_id if action else None}
        
    except Exception as e:
        logger.error(f"追蹤頁面瀏覽失敗: {e}")
        raise HTTPException(status_code=500, detail=f"追蹤失敗: {str(e)}")


@router.post("/track/conversion")
async def track_conversion(
    request: ConversionRequest,
    http_request: Request,
    current_user: AdminUser = Depends(require_permission("behavior:write"))
):
    """追蹤轉換事件"""
    try:
        request_info = {
            "ip_address": http_request.client.host,
            "user_agent": http_request.headers.get("user-agent")
        }
        
        action = await behavior_tracker.track_conversion(
            user_id=request.user_id,
            conversion_type=request.conversion_type,
            conversion_value=request.conversion_value,
            page_url=request.page_url,
            metadata=request.metadata,
            request_info=request_info
        )
        
        return {"status": "success", "action_id": action.action_id if action else None}
        
    except Exception as e:
        logger.error(f"追蹤轉換失敗: {e}")
        raise HTTPException(status_code=500, detail=f"追蹤失敗: {str(e)}")


@router.post("/track/search")
async def track_search(
    request: SearchRequest,
    http_request: Request,
    current_user: AdminUser = Depends(require_permission("behavior:write"))
):
    """追蹤搜索事件"""
    try:
        request_info = {
            "ip_address": http_request.client.host,
            "user_agent": http_request.headers.get("user-agent")
        }
        
        action = await behavior_tracker.track_search(
            user_id=request.user_id,
            query=request.query,
            results_count=request.results_count,
            page_url=request.page_url,
            request_info=request_info
        )
        
        return {"status": "success", "action_id": action.action_id if action else None}
        
    except Exception as e:
        logger.error(f"追蹤搜索失敗: {e}")
        raise HTTPException(status_code=500, detail=f"追蹤失敗: {str(e)}")


# 數據查詢 API
@router.get("/users/{user_id}/sessions")
@require_permission("behavior:read")
async def get_user_sessions(
    user_id: str,
    limit: int = Query(10, ge=1, le=100),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: AdminUser = Depends(require_permission("behavior:read"))
):
    """獲取用戶會話"""
    try:
        sessions = await behavior_collector.get_user_sessions(
            user_id=user_id,
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "status": "success",
            "sessions": [session.to_dict() for session in sessions],
            "count": len(sessions)
        }
        
    except Exception as e:
        logger.error(f"獲取用戶會話失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取失敗: {str(e)}")


@router.get("/users/{user_id}/actions")
@require_permission("behavior:read")
async def get_user_actions(
    user_id: str,
    action_types: Optional[List[str]] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: AdminUser = Depends(require_permission("behavior:read"))
):
    """獲取用戶動作"""
    try:
        actions = await behavior_collector.get_user_actions(
            user_id=user_id,
            action_types=action_types,
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "status": "success",
            "actions": [action.to_dict() for action in actions],
            "count": len(actions)
        }
        
    except Exception as e:
        logger.error(f"獲取用戶動作失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取失敗: {str(e)}")


@router.get("/users/{user_id}/journey")
@require_permission("behavior:read")
async def get_user_journey(
    user_id: str,
    days: int = Query(7, ge=1, le=30),
    current_user: AdminUser = Depends(require_permission("behavior:read"))
):
    """獲取用戶行為路徑"""
    try:
        journey = await behavior_tracker.get_user_journey(user_id, days)
        
        return {
            "status": "success",
            "journey": journey
        }
        
    except Exception as e:
        logger.error(f"獲取用戶路徑失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取失敗: {str(e)}")


# 分析 API
@router.get("/users/{user_id}/analysis")
@require_permission("behavior:analyze")
async def analyze_user_behavior(
    user_id: str,
    days: int = Query(30, ge=1, le=90),
    current_user: AdminUser = Depends(require_permission("behavior:analyze"))
):
    """分析用戶行為"""
    try:
        analysis = await behavior_analyzer.analyze_user_behavior(user_id, days)
        
        return {
            "status": "success",
            "analysis": {
                "analysis_type": analysis.analysis_type,
                "timestamp": analysis.timestamp.isoformat(),
                "summary": analysis.summary,
                "details": analysis.details,
                "insights": analysis.insights,
                "recommendations": analysis.recommendations,
                "confidence_score": analysis.confidence_score,
                "data_points": analysis.data_points
            }
        }
        
    except Exception as e:
        logger.error(f"用戶行為分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"分析失敗: {str(e)}")


@router.post("/analyze/funnel")
@require_permission("behavior:analyze")
async def analyze_funnel(
    funnel_steps: List[Dict[str, Any]] = Body(...),
    time_window_hours: int = Body(24, ge=1, le=168),
    current_user: AdminUser = Depends(require_permission("behavior:analyze"))
):
    """分析轉換漏斗"""
    try:
        analysis = await behavior_analyzer.analyze_funnel_performance(
            funnel_steps=funnel_steps,
            time_window_hours=time_window_hours
        )
        
        return {
            "status": "success",
            "funnel_analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"漏斗分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"分析失敗: {str(e)}")


@router.get("/analyze/pages")
@require_permission("behavior:analyze")
async def analyze_page_performance(
    page_url: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),
    current_user: AdminUser = Depends(require_permission("behavior:analyze"))
):
    """分析頁面性能"""
    try:
        analysis = await behavior_analyzer.analyze_page_performance(
            page_url=page_url,
            hours=hours
        )
        
        return {
            "status": "success",
            "page_analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"頁面分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"分析失敗: {str(e)}")


@router.get("/analyze/anomalies")
@require_permission("behavior:analyze")
async def detect_anomalies(
    hours: int = Query(24, ge=1, le=168),
    current_user: AdminUser = Depends(require_permission("behavior:analyze"))
):
    """檢測行為異常"""
    try:
        anomalies = await behavior_analyzer.detect_anomalies(hours)
        
        return {
            "status": "success",
            "anomalies": anomalies,
            "count": len(anomalies)
        }
        
    except Exception as e:
        logger.error(f"異常檢測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"檢測失敗: {str(e)}")


# 模式檢測 API
@router.post("/patterns/detect/sequential")
@require_permission("behavior:analyze")
async def detect_sequential_patterns(
    min_support: int = Body(3, ge=2),
    max_length: int = Body(5, ge=2, le=10),
    time_window_hours: int = Body(24, ge=1, le=168),
    current_user: AdminUser = Depends(require_permission("behavior:analyze"))
):
    """檢測序列模式"""
    try:
        patterns = await pattern_detector.detect_sequential_patterns(
            min_support=min_support,
            max_length=max_length,
            time_window_hours=time_window_hours
        )
        
        return {
            "status": "success",
            "patterns": [pattern.to_dict() for pattern in patterns],
            "count": len(patterns)
        }
        
    except Exception as e:
        logger.error(f"序列模式檢測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"檢測失敗: {str(e)}")


@router.post("/patterns/detect/temporal")
@require_permission("behavior:analyze")
async def detect_temporal_patterns(
    days: int = Body(7, ge=1, le=30),
    current_user: AdminUser = Depends(require_permission("behavior:analyze"))
):
    """檢測時間模式"""
    try:
        patterns = await pattern_detector.detect_temporal_patterns(days)
        
        return {
            "status": "success",
            "patterns": [pattern.to_dict() for pattern in patterns],
            "count": len(patterns)
        }
        
    except Exception as e:
        logger.error(f"時間模式檢測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"檢測失敗: {str(e)}")


@router.post("/patterns/detect/journey")
@require_permission("behavior:analyze")
async def detect_journey_patterns(
    days: int = Body(7, ge=1, le=30),
    current_user: AdminUser = Depends(require_permission("behavior:analyze"))
):
    """檢測用戶旅程模式"""
    try:
        patterns = await pattern_detector.detect_user_journey_patterns(days)
        
        return {
            "status": "success",
            "patterns": [pattern.to_dict() for pattern in patterns],
            "count": len(patterns)
        }
        
    except Exception as e:
        logger.error(f"旅程模式檢測失敗: {e}")
        raise HTTPException(status_code=500, detail=f"檢測失敗: {str(e)}")


@router.get("/patterns")
@require_permission("behavior:read")
async def get_patterns(
    pattern_type: Optional[str] = Query(None),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    current_user: AdminUser = Depends(require_permission("behavior:read"))
):
    """獲取檢測到的模式"""
    try:
        patterns = await pattern_detector.get_all_patterns(
            pattern_type=pattern_type,
            min_confidence=min_confidence
        )
        
        return {
            "status": "success",
            "patterns": [pattern.to_dict() for pattern in patterns],
            "count": len(patterns)
        }
        
    except Exception as e:
        logger.error(f"獲取模式失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取失敗: {str(e)}")


# 洞察生成 API
@router.post("/insights/generate")
@require_permission("behavior:analyze")
async def generate_insights(
    days: int = Body(7, ge=1, le=30),
    current_user: AdminUser = Depends(require_permission("behavior:analyze"))
):
    """生成行為洞察"""
    try:
        insights = await insight_generator.generate_insights(days)
        
        return {
            "status": "success",
            "insights": [insight.to_dict() for insight in insights],
            "count": len(insights)
        }
        
    except Exception as e:
        logger.error(f"生成洞察失敗: {e}")
        raise HTTPException(status_code=500, detail=f"生成失敗: {str(e)}")


@router.get("/insights")
@require_permission("behavior:read")
async def get_insights(
    insight_type: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    current_user: AdminUser = Depends(require_permission("behavior:read"))
):
    """獲取行為洞察"""
    try:
        insights = await insight_generator.get_insights(
            insight_type=insight_type,
            priority=priority,
            limit=limit
        )
        
        return {
            "status": "success",
            "insights": [insight.to_dict() for insight in insights],
            "count": len(insights)
        }
        
    except Exception as e:
        logger.error(f"獲取洞察失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取失敗: {str(e)}")


@router.get("/insights/summary")
@require_permission("behavior:read")
async def get_insight_summary(
    current_user: AdminUser = Depends(require_permission("behavior:read"))
):
    """獲取洞察摘要"""
    try:
        summary = await insight_generator.get_insight_summary()
        
        return {
            "status": "success",
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"獲取洞察摘要失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取失敗: {str(e)}")


@router.post("/insights/{insight_id}/implement")
@require_permission("behavior:manage")
async def implement_insight(
    insight_id: str,
    current_user: AdminUser = Depends(require_permission("behavior:manage"))
):
    """標記洞察為已實施"""
    try:
        insight_generator.mark_insight_as_implemented(insight_id)
        
        return {"status": "success", "message": "洞察已標記為已實施"}
        
    except Exception as e:
        logger.error(f"標記洞察失敗: {e}")
        raise HTTPException(status_code=500, detail=f"操作失敗: {str(e)}")


@router.post("/insights/{insight_id}/dismiss")
@require_permission("behavior:manage")
async def dismiss_insight(
    insight_id: str,
    current_user: AdminUser = Depends(require_permission("behavior:manage"))
):
    """忽略洞察"""
    try:
        insight_generator.dismiss_insight(insight_id)
        
        return {"status": "success", "message": "洞察已忽略"}
        
    except Exception as e:
        logger.error(f"忽略洞察失敗: {e}")
        raise HTTPException(status_code=500, detail=f"操作失敗: {str(e)}")


# A/B 測試 API
@router.post("/ab-tests")
@require_permission("behavior:manage")
async def create_ab_test(
    request: ABTestRequest,
    current_user: AdminUser = Depends(require_permission("behavior:manage"))
):
    """創建 A/B 測試"""
    try:
        behavior_tracker.create_ab_test(
            test_id=request.test_id,
            test_name=request.test_name,
            variants=request.variants,
            traffic_allocation=request.traffic_allocation,
            success_metrics=request.success_metrics,
            description=request.description
        )
        
        return {"status": "success", "message": "A/B 測試已創建"}
        
    except Exception as e:
        logger.error(f"創建 A/B 測試失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建失敗: {str(e)}")


@router.get("/ab-tests/{test_id}/assign/{user_id}")
@require_permission("behavior:read")
async def assign_user_to_variant(
    test_id: str,
    user_id: str,
    current_user: AdminUser = Depends(require_permission("behavior:read"))
):
    """分配用戶到 A/B 測試變體"""
    try:
        variant = behavior_tracker.assign_user_to_variant(test_id, user_id)
        
        return {
            "status": "success",
            "test_id": test_id,
            "user_id": user_id,
            "variant": variant
        }
        
    except Exception as e:
        logger.error(f"分配 A/B 測試失敗: {e}")
        raise HTTPException(status_code=500, detail=f"分配失敗: {str(e)}")


@router.get("/ab-tests/{test_id}/results")
@require_permission("behavior:read")
async def get_ab_test_results(
    test_id: str,
    current_user: AdminUser = Depends(require_permission("behavior:read"))
):
    """獲取 A/B 測試結果"""
    try:
        results = await behavior_tracker.get_ab_test_results(test_id)
        
        return {
            "status": "success",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"獲取 A/B 測試結果失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取失敗: {str(e)}")


# 用戶分群 API
@router.post("/cohorts")
@require_permission("behavior:manage")
async def create_cohort(
    request: CohortRequest,
    current_user: AdminUser = Depends(require_permission("behavior:manage"))
):
    """創建用戶分群"""
    try:
        behavior_tracker.create_user_cohort(
            cohort_name=request.cohort_name,
            user_ids=request.user_ids
        )
        
        return {"status": "success", "message": "用戶分群已創建"}
        
    except Exception as e:
        logger.error(f"創建用戶分群失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建失敗: {str(e)}")


@router.get("/cohorts/{cohort_name}/analysis")
@require_permission("behavior:read")
async def get_cohort_analysis(
    cohort_name: str,
    days: int = Query(30, ge=1, le=90),
    current_user: AdminUser = Depends(require_permission("behavior:read"))
):
    """獲取分群分析"""
    try:
        analysis = await behavior_tracker.get_cohort_analysis(cohort_name, days)
        
        return {
            "status": "success",
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"獲取分群分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取失敗: {str(e)}")


# 實時統計 API
@router.get("/stats/real-time")
@require_permission("behavior:read")
async def get_real_time_stats(
    current_user: AdminUser = Depends(require_permission("behavior:read"))
):
    """獲取實時統計"""
    try:
        stats = await behavior_tracker.get_real_time_stats()
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"獲取實時統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取失敗: {str(e)}")


@router.get("/stats/active-users")
@require_permission("behavior:read")
async def get_active_users(
    minutes: int = Query(30, ge=1, le=1440),
    current_user: AdminUser = Depends(require_permission("behavior:read"))
):
    """獲取活躍用戶數"""
    try:
        count = await behavior_collector.get_active_users_count(minutes)
        
        return {
            "status": "success",
            "active_users": count,
            "time_window_minutes": minutes
        }
        
    except Exception as e:
        logger.error(f"獲取活躍用戶數失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取失敗: {str(e)}")


# 熱圖數據 API
@router.get("/heatmap/{page_url:path}")
@require_permission("behavior:read")
async def get_heatmap_data(
    page_url: str,
    hours: int = Query(24, ge=1, le=168),
    current_user: AdminUser = Depends(require_permission("behavior:read"))
):
    """獲取頁面熱圖數據"""
    try:
        heatmap_data = await behavior_tracker.get_heatmap_data(page_url, hours)
        
        return {
            "status": "success",
            "page_url": page_url,
            "heatmap_data": heatmap_data,
            "time_window_hours": hours
        }
        
    except Exception as e:
        logger.error(f"獲取熱圖數據失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取失敗: {str(e)}")


# 數據導出 API
@router.post("/export")
@require_permission("behavior:export")
async def export_behavior_data(
    user_id: Optional[str] = Body(None),
    start_date: Optional[datetime] = Body(None),
    end_date: Optional[datetime] = Body(None),
    format: str = Body("json", regex="^(json|csv)$"),
    current_user: AdminUser = Depends(require_permission("behavior:export"))
):
    """導出行為數據"""
    try:
        data = await behavior_collector.export_data(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            format=format
        )
        
        return {
            "status": "success",
            "data": data,
            "format": format
        }
        
    except Exception as e:
        logger.error(f"導出數據失敗: {e}")
        raise HTTPException(status_code=500, detail=f"導出失敗: {str(e)}")


# 系統管理 API
@router.get("/stats")
@require_permission("behavior:read")
async def get_behavior_stats(
    current_user: AdminUser = Depends(require_permission("behavior:read"))
):
    """獲取行為追蹤系統統計"""
    try:
        collector_stats = behavior_collector.get_stats()
        analyzer_stats = behavior_analyzer.get_analysis_stats()
        pattern_stats = pattern_detector.get_pattern_stats()
        insight_stats = insight_generator.get_insight_stats()
        
        return {
            "status": "success",
            "stats": {
                "collector": collector_stats,
                "analyzer": analyzer_stats,
                "patterns": pattern_stats,
                "insights": insight_stats
            }
        }
        
    except Exception as e:
        logger.error(f"獲取系統統計失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取失敗: {str(e)}")


@router.post("/cache/clear")
@require_permission("system:admin")
async def clear_cache(
    current_user: AdminUser = Depends(require_permission("system:admin"))
):
    """清空分析緩存"""
    try:
        behavior_analyzer.clear_cache()
        
        return {"status": "success", "message": "分析緩存已清空"}
        
    except Exception as e:
        logger.error(f"清空緩存失敗: {e}")
        raise HTTPException(status_code=500, detail=f"清空失敗: {str(e)}")


@router.get("/health")
async def health_check():
    """健康檢查"""
    try:
        # 檢查各組件狀態
        collector_stats = behavior_collector.get_stats()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "behavior_collector": {
                    "status": "healthy",
                    "total_actions": collector_stats.get("total_actions", 0),
                    "total_sessions": collector_stats.get("total_sessions", 0),
                    "total_users": collector_stats.get("total_users", 0)
                },
                "behavior_tracker": {"status": "healthy"},
                "behavior_analyzer": {"status": "healthy"},
                "pattern_detector": {"status": "healthy"},
                "insight_generator": {"status": "healthy"}
            }
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"行為追蹤健康檢查失敗: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }