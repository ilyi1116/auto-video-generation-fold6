"""
分散式追蹤相關的 Celery 任務
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict

from ..celery_app import celery_app
from ..tracing import trace_analyzer, trace_collector
from ..tracing.tracer import trace_celery_task

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
@trace_celery_task("tracing.collect_span_data")
def collect_span_data_task(self, span_data: Dict[str, Any]):
    """
    收集 Span 資料任務

    Args:
        span_data: Span 資料
    """
    try:
        logger.info(f"開始收集 Span 資料: {span_data.get('span_id', 'unknown')}")

        # 異步收集追蹤資料
        asyncio.run(trace_collector.collect_trace(span_data))

        logger.info(f"Span 資料收集完成: {span_data.get('span_id', 'unknown')}")

        return {
            "status": "success",
            "span_id": span_data.get("span_id"),
            "trace_id": span_data.get("trace_id"),
            "collected_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"收集 Span 資料失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("tracing.analyze_traces")
def analyze_traces_task(self, analysis_params: Dict[str, Any]):
    """
    分析追蹤資料任務

    Args:
        analysis_params: 分析參數
    """
    try:
        service_name = analysis_params.get("service_name")
        hours = analysis_params.get("hours", 24)
        analysis_type = analysis_params.get("type", "performance")

        logger.info(
            f"開始分析追蹤資料: {analysis_type}, 服務: {service_name}, 時間範圍: {hours}小時"
        )

        # 執行不同類型的分析
        if analysis_type == "performance":
            result = asyncio.run(
                trace_analyzer.analyze_performance(service_name=service_name, hours=hours)
            )
        elif analysis_type == "errors":
            result = asyncio.run(trace_analyzer.analyze_errors(hours=hours))
        elif analysis_type == "services":
            result = asyncio.run(trace_analyzer.analyze_services(hours=hours))
        elif analysis_type == "trends":
            interval_minutes = analysis_params.get("interval_minutes", 60)
            result = asyncio.run(
                trace_analyzer.analyze_trends(hours=hours, interval_minutes=interval_minutes)
            )
        else:
            raise ValueError(f"不支持的分析類型: {analysis_type}")

        logger.info(f"追蹤資料分析完成: {analysis_type}")

        return {
            "status": "success",
            "analysis_type": analysis_type,
            "analysis_params": analysis_params,
            "result": result,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"分析追蹤資料失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("tracing.health_check")
def health_check_task(self, service_name: str = None):
    """
    追蹤系統健康檢查任務

    Args:
        service_name: 服務名稱（可選）
    """
    try:
        logger.info(f"開始追蹤系統健康檢查: {service_name or '所有服務'}")

        # 計算健康評分
        health_score = asyncio.run(
            trace_analyzer.get_health_score(service_name=service_name, hours=1)
        )

        # 獲取收集器統計
        collector_stats = trace_collector.get_stats()

        # 獲取慢操作
        slow_operations = asyncio.run(trace_analyzer.get_slow_operations(limit=5, hours=24))

        result = {
            "health_score": health_score,
            "collector_stats": collector_stats,
            "slow_operations": slow_operations,
            "service_name": service_name,
            "checked_at": datetime.utcnow().isoformat(),
        }

        # 如果健康評分太低，記錄警告
        if health_score.get("health_score", 0) < 70:
            logger.warning(
                f"服務健康評分偏低: {service_name or '整體'} - "
                f"評分: {health_score.get('health_score', 0)}"
            )

        logger.info(f"追蹤系統健康檢查完成: {service_name or '所有服務'}")

        return result

    except Exception as e:
        logger.error(f"追蹤系統健康檢查失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("tracing.cleanup_old_traces")
def cleanup_old_traces_task(self, days: int = 7):
    """
    清理舊追蹤資料任務

    Args:
        days: 保留天數
    """
    try:
        logger.info(f"開始清理 {days} 天前的追蹤資料")

        # 清理追蹤檔案
        asyncio.run(trace_collector._cleanup_old_traces())

        # 清理內存快取
        from ..tracing.tracer import tracer

        tracer.clear_cache(max_age=days * 24 * 3600)

        # 獲取清理後的統計
        final_stats = trace_collector.get_stats()

        logger.info(f"追蹤資料清理完成，保留 {days} 天")

        return {
            "status": "success",
            "cleanup_days": days,
            "final_stats": final_stats,
            "cleaned_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"清理追蹤資料失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("tracing.export_traces")
def export_traces_task(self, export_params: Dict[str, Any]):
    """
    導出追蹤資料任務

    Args:
        export_params: 導出參數
    """
    try:
        start_date = export_params.get("start_date")
        end_date = export_params.get("end_date")
        output_path = export_params.get("output_path")

        logger.info(f"開始導出追蹤資料: {start_date} 到 {end_date}")

        if not output_path:
            # 生成默認輸出路徑
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = f"/tmp/traces_export_{timestamp}.jsonl"

        # 執行導出
        exported_count = asyncio.run(
            trace_collector.export_traces(
                output_path=output_path, start_date=start_date, end_date=end_date
            )
        )

        logger.info(f"追蹤資料導出完成: {exported_count} 條記錄")

        return {
            "status": "success",
            "exported_count": exported_count,
            "output_path": output_path,
            "export_params": export_params,
            "exported_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"導出追蹤資料失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("tracing.generate_report")
def generate_report_task(self, report_params: Dict[str, Any]):
    """
    生成追蹤分析報告任務

    Args:
        report_params: 報告參數
    """
    try:
        hours = report_params.get("hours", 24)
        service_name = report_params.get("service_name")

        logger.info(f"開始生成追蹤分析報告: 服務={service_name}, 時間範圍={hours}小時")

        # 收集各種分析結果
        performance_analysis = asyncio.run(
            trace_analyzer.analyze_performance(service_name=service_name, hours=hours)
        )

        error_analysis = asyncio.run(trace_analyzer.analyze_errors(hours=hours))

        services_analysis = asyncio.run(trace_analyzer.analyze_services(hours=hours))

        trends_analysis = asyncio.run(
            trace_analyzer.analyze_trends(hours=hours, interval_minutes=60)
        )

        slow_operations = asyncio.run(trace_analyzer.get_slow_operations(limit=10, hours=hours))

        health_score = asyncio.run(
            trace_analyzer.get_health_score(service_name=service_name, hours=1)
        )

        # 組合報告
        report = {
            "report_metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "service_name": service_name,
                "time_range_hours": hours,
                "report_type": "comprehensive_trace_analysis",
            },
            "executive_summary": {
                "health_score": health_score.get("health_score", 0),
                "total_requests": performance_analysis.get("total_requests", 0),
                "error_rate": performance_analysis.get("error_rate", 0),
                "avg_response_time": performance_analysis.get("performance_metrics", {}).get(
                    "avg_duration_ms", 0
                ),
            },
            "performance_analysis": performance_analysis,
            "error_analysis": error_analysis,
            "services_analysis": services_analysis,
            "trends_analysis": trends_analysis,
            "slow_operations": slow_operations,
            "health_score": health_score,
        }

        logger.info(f"追蹤分析報告生成完成")

        return {"status": "success", "report": report, "report_params": report_params}

    except Exception as e:
        logger.error(f"生成追蹤分析報告失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("tracing.batch_process_spans")
def batch_process_spans_task(self, spans_data: list):
    """
    批量處理 Span 資料任務

    Args:
        spans_data: Span 資料列表
    """
    try:
        logger.info(f"開始批量處理 {len(spans_data)} 個 Span")

        processed_count = 0
        failed_count = 0

        for span_data in spans_data:
            try:
                asyncio.run(trace_collector.collect_trace(span_data))
                processed_count += 1
            except Exception as e:
                logger.warning(f"處理 Span 失敗: {span_data.get('span_id', 'unknown')}, 錯誤: {e}")
                failed_count += 1

        logger.info(f"批量處理完成: 成功 {processed_count}, 失敗 {failed_count}")

        return {
            "status": "success",
            "total_spans": len(spans_data),
            "processed_count": processed_count,
            "failed_count": failed_count,
            "processed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"批量處理 Span 失敗: {e}")
        raise
