"""
分散式追蹤管理 API 端點
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..models import AdminUser
from ..schemas import APIResponse
from ..security import audit_log, require_permission
from ..tracing import trace_analyzer, trace_collector, tracer

router = APIRouter(prefix="/tracing", tags=["tracing"])


class TraceQuery(BaseModel):
    """追蹤查詢請求"""

    trace_id: Optional[str] = None
    service_name: Optional[str] = None
    operation_category: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100


class AnalysisRequest(BaseModel):
    """分析請求"""

    service_name: Optional[str] = None
    operation_category: Optional[str] = None
    hours: int = 24


@router.get("/")
@require_permission("system:monitoring")
async def get_traces(
    trace_id: Optional[str] = Query(None, description="追蹤ID"),
    service_name: Optional[str] = Query(None, description="服務名稱"),
    operation_category: Optional[str] = Query(None, description="操作類別"),
    hours: int = Query(24, description="時間範圍(小時)"),
    limit: int = Query(100, description="結果限制"),
    current_user: AdminUser = Depends(require_permission("system:monitoring")),
):
    """獲取追蹤資料"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        traces = await trace_collector.get_traces(
            trace_id=trace_id,
            service_name=service_name,
            operation_category=operation_category,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        return APIResponse(
            data={
                "traces": traces,
                "total": len(traces),
                "query_params": {
                    "trace_id": trace_id,
                    "service_name": service_name,
                    "operation_category": operation_category,
                    "hours": hours,
                    "limit": limit,
                },
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{trace_id}")
@require_permission("system:monitoring")
async def get_trace_details(
    trace_id: str, current_user: AdminUser = Depends(require_permission("system:monitoring"))
):
    """獲取特定追蹤的詳細資訊"""
    try:
        trace = await trace_collector.get_trace_by_id(trace_id)

        if not trace:
            raise HTTPException(status_code=404, detail=f"追蹤 {trace_id} 不存在")

        # 獲取相關的 Span 資訊
        span_info = tracer.get_span_info(trace.get("span_id", ""))

        return APIResponse(data={"trace": trace, "span_info": span_info})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/performance")
@require_permission("system:monitoring")
async def analyze_performance(
    service_name: Optional[str] = Query(None, description="服務名稱"),
    operation_category: Optional[str] = Query(None, description="操作類別"),
    hours: int = Query(24, description="分析時間範圍"),
    current_user: AdminUser = Depends(require_permission("system:monitoring")),
):
    """性能分析"""
    try:
        analysis = await trace_analyzer.analyze_performance(
            service_name=service_name, operation_category=operation_category, hours=hours
        )

        return APIResponse(data=analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/errors")
@require_permission("system:monitoring")
async def analyze_errors(
    hours: int = Query(24, description="分析時間範圍"),
    current_user: AdminUser = Depends(require_permission("system:monitoring")),
):
    """錯誤分析"""
    try:
        analysis = await trace_analyzer.analyze_errors(hours=hours)

        return APIResponse(data=analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/services")
@require_permission("system:monitoring")
async def analyze_services(
    hours: int = Query(24, description="分析時間範圍"),
    current_user: AdminUser = Depends(require_permission("system:monitoring")),
):
    """服務分析"""
    try:
        analysis = await trace_analyzer.analyze_services(hours=hours)

        return APIResponse(data=analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/trends")
@require_permission("system:monitoring")
async def analyze_trends(
    hours: int = Query(24, description="分析時間範圍"),
    interval_minutes: int = Query(60, description="時間間隔(分鐘)"),
    current_user: AdminUser = Depends(require_permission("system:monitoring")),
):
    """趨勢分析"""
    try:
        analysis = await trace_analyzer.analyze_trends(
            hours=hours, interval_minutes=interval_minutes
        )

        return APIResponse(data=analysis)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/slow-operations")
@require_permission("system:monitoring")
async def get_slow_operations(
    limit: int = Query(10, description="結果限制"),
    hours: int = Query(24, description="分析時間範圍"),
    current_user: AdminUser = Depends(require_permission("system:monitoring")),
):
    """獲取最慢的操作"""
    try:
        slow_ops = await trace_analyzer.get_slow_operations(limit=limit, hours=hours)

        return APIResponse(data={"slow_operations": slow_ops, "analysis_period": f"{hours} hours"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{service_name}")
@require_permission("system:monitoring")
async def get_service_health(
    service_name: str,
    hours: int = Query(1, description="健康檢查時間範圍"),
    current_user: AdminUser = Depends(require_permission("system:monitoring")),
):
    """獲取服務健康評分"""
    try:
        health = await trace_analyzer.get_health_score(service_name=service_name, hours=hours)

        return APIResponse(data=health)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
@require_permission("system:monitoring")
async def get_overall_health(
    hours: int = Query(1, description="健康檢查時間範圍"),
    current_user: AdminUser = Depends(require_permission("system:monitoring")),
):
    """獲取整體健康評分"""
    try:
        health = await trace_analyzer.get_health_score(hours=hours)

        return APIResponse(data=health)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/collector")
@require_permission("system:monitoring")
async def get_collector_stats(
    current_user: AdminUser = Depends(require_permission("system:monitoring")),
):
    """獲取收集器統計資訊"""
    try:
        stats = trace_collector.get_stats()

        return APIResponse(data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/tracer")
@require_permission("system:monitoring")
async def get_tracer_stats(
    current_user: AdminUser = Depends(require_permission("system:monitoring")),
):
    """獲取追蹤器統計資訊"""
    try:
        all_spans = tracer.get_all_spans()

        # 統計 Span 狀態
        status_counts = {}
        for span in all_spans:
            status = span.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        stats = {
            "total_spans": len(all_spans),
            "status_distribution": status_counts,
            "cache_size": len(tracer.spans_cache),
        }

        return APIResponse(data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
@require_permission("system:admin")
@audit_log("export_traces", "tracing")
async def export_traces(
    start_date: Optional[str] = Query(None, description="開始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="結束日期 (YYYY-MM-DD)"),
    current_user: AdminUser = Depends(require_permission("system:admin")),
):
    """導出追蹤資料"""
    try:
        import os
        import tempfile

        # 創建臨時檔案
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tmp_file:
            output_path = tmp_file.name

        # 導出資料
        exported_count = await trace_collector.export_traces(
            output_path=output_path, start_date=start_date, end_date=end_date
        )

        # 讀取檔案內容
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 清理臨時檔案
        os.unlink(output_path)

        return APIResponse(
            data={
                "exported_count": exported_count,
                "export_params": {"start_date": start_date, "end_date": end_date},
                "content": content[:10000] + "..." if len(content) > 10000 else content,
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
@require_permission("system:admin")
@audit_log("cleanup_traces", "tracing")
async def cleanup_old_traces(
    days: int = Query(7, description="保留天數"),
    current_user: AdminUser = Depends(require_permission("system:admin")),
):
    """清理舊的追蹤資料"""
    try:
        # 觸發收集器的清理流程
        await trace_collector._cleanup_old_traces()

        # 清理追蹤器快取
        tracer.clear_cache()

        return APIResponse(message=f"已清理超過 {days} 天的追蹤資料", data={"cleanup_days": days})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
@require_permission("system:monitoring")
async def search_traces(
    query: str = Query(..., description="搜索查詢"),
    service_name: Optional[str] = Query(None, description="服務名稱"),
    hours: int = Query(24, description="搜索時間範圍"),
    limit: int = Query(50, description="結果限制"),
    current_user: AdminUser = Depends(require_permission("system:monitoring")),
):
    """搜索追蹤資料"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)

        # 獲取所有追蹤
        all_traces = await trace_collector.get_traces(
            service_name=service_name,
            start_time=start_time,
            end_time=end_time,
            limit=1000,  # 搜索更多資料
        )

        # 執行文本搜索
        query_lower = query.lower()
        matching_traces = []

        for trace in all_traces:
            # 搜索各個欄位
            searchable_text = " ".join(
                [
                    str(trace.get("operation_name", "")),
                    str(trace.get("error", "")),
                    str(trace.get("attributes", {})),
                    str(trace.get("trace_id", "")),
                    str(trace.get("span_id", "")),
                ]
            ).lower()

            if query_lower in searchable_text:
                matching_traces.append(trace)

                if len(matching_traces) >= limit:
                    break

        return APIResponse(
            data={
                "traces": matching_traces,
                "total": len(matching_traces),
                "query": query,
                "search_params": {"service_name": service_name, "hours": hours, "limit": limit},
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
