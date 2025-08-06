"""
智能日誌分析相關的 Celery 任務
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from ..celery_app import celery_app
from ..logs import (
    anomaly_detector,
    init_anomaly_detector,
    init_log_aggregator,
    init_log_alerting,
    init_log_analyzer,
    init_log_predictor,
    log_aggregator,
    log_alerting,
    log_analyzer,
    log_collector,
    log_predictor,
)
from ..logs.analyzer import AnalysisType
from ..logs.predictor import TimeHorizon
from ..tracing.tracer import trace_celery_task

logger = logging.getLogger(__name__)


# 確保初始化所有組件
def ensure_initialization():
    """確保所有日誌分析組件已初始化"""
    try:
        if not hasattr(log_analyzer, "__name__") or log_analyzer is None:
            init_log_analyzer(log_collector)

        if not hasattr(anomaly_detector, "__name__") or anomaly_detector is None:
            init_anomaly_detector(log_collector)

        if not hasattr(log_predictor, "__name__") or log_predictor is None:
            init_log_predictor(log_collector)

        if not hasattr(log_aggregator, "__name__") or log_aggregator is None:
            init_log_aggregator(log_collector)

        if not hasattr(log_alerting, "__name__") or log_alerting is None:
            init_log_alerting(log_collector, log_analyzer, anomaly_detector, log_predictor)
    except Exception as e:
        logger.error(f"初始化日誌分析組件失敗: {e}")


@celery_app.task(bind=True)
@trace_celery_task("logs.collect_log_data")
def collect_log_data_task(self, log_data: Dict[str, Any]):
    """
    收集日誌數據任務

    Args:
        log_data: 日誌數據
    """
    try:
        logger.info(f"開始收集日誌數據: {log_data.get('service', 'unknown')}")

        # 異步收集日誌
        asyncio.run(log_collector.collect_log(log_data))

        logger.info(f"日誌數據收集完成: {log_data.get('service', 'unknown')}")

        return {
            "status": "success",
            "service": log_data.get("service"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"收集日誌數據失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("logs.batch_collect")
def batch_collect_logs_task(self, logs_data: List[Dict[str, Any]]):
    """
    批量收集日誌數據任務

    Args:
        logs_data: 日誌數據列表
    """
    try:
        logger.info(f"開始批量收集 {len(logs_data)} 條日誌")

        collected_count = 0
        failed_count = 0

        for log_data in logs_data:
            try:
                asyncio.run(log_collector.collect_log(log_data))
                collected_count += 1
            except Exception as e:
                logger.warning(f"收集日誌失敗: {log_data.get('service', 'unknown')}, 錯誤: {e}")
                failed_count += 1

        logger.info(f"批量收集完成: 成功 {collected_count}, 失敗 {failed_count}")

        return {
            "status": "success",
            "total_logs": len(logs_data),
            "collected_count": collected_count,
            "failed_count": failed_count,
            "processed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"批量收集日誌失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("logs.analyze_performance")
def analyze_performance_task(self, analysis_params: Dict[str, Any]):
    """
    性能分析任務

    Args:
        analysis_params: 分析參數
    """
    try:
        ensure_initialization()

        service = analysis_params.get("service")
        hours = analysis_params.get("hours", 24)

        logger.info(f"開始性能分析: 服務={service}, 時間範圍={hours}小時")

        # 執行性能分析
        result = asyncio.run(
            log_analyzer.analyze_logs(
                analysis_type=AnalysisType.PERFORMANCE, service=service, hours=hours
            )
        )

        logger.info(f"性能分析完成: {result.summary}")

        return {
            "status": "success",
            "analysis_type": "performance",
            "service": service,
            "summary": result.summary,
            "severity": result.severity,
            "recommendations": result.recommendations,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"性能分析失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("logs.detect_anomalies")
def detect_anomalies_task(self, detection_params: Dict[str, Any]):
    """
    異常檢測任務

    Args:
        detection_params: 檢測參數
    """
    try:
        ensure_initialization()

        hours = detection_params.get("hours", 1)
        service = detection_params.get("service")

        logger.info(f"開始異常檢測: 服務={service}, 時間範圍={hours}小時")

        # 執行異常檢測
        anomalies = asyncio.run(anomaly_detector.detect_anomalies(hours=hours, service=service))

        logger.info(f"異常檢測完成: 發現 {len(anomalies)} 個異常")

        # 轉換異常對象為字典
        anomalies_data = []
        for anomaly in anomalies:
            anomalies_data.append(
                {
                    "anomaly_id": anomaly.anomaly_id,
                    "anomaly_type": anomaly.anomaly_type.value,
                    "severity": anomaly.severity.value,
                    "description": anomaly.description,
                    "confidence_score": anomaly.confidence_score,
                    "timestamp": anomaly.timestamp.isoformat(),
                }
            )

        return {
            "status": "success",
            "anomalies_count": len(anomalies),
            "anomalies": anomalies_data,
            "detection_params": detection_params,
            "detected_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"異常檢測失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("logs.generate_predictions")
def generate_predictions_task(self, prediction_params: Dict[str, Any]):
    """
    生成預測任務

    Args:
        prediction_params: 預測參數
    """
    try:
        ensure_initialization()

        time_horizon_str = prediction_params.get("time_horizon", "short_term")
        service = prediction_params.get("service")

        time_horizon = TimeHorizon(time_horizon_str)

        logger.info(f"開始預測分析: 服務={service}, 時間範圍={time_horizon.value}")

        # 生成預測
        predictions = asyncio.run(
            log_predictor.generate_predictions(time_horizon=time_horizon, service=service)
        )

        logger.info(f"預測分析完成: 生成 {len(predictions)} 個預測")

        # 轉換預測對象為字典
        predictions_data = []
        for prediction in predictions:
            predictions_data.append(
                {
                    "prediction_id": prediction.prediction_id,
                    "prediction_type": prediction.prediction_type.value,
                    "description": prediction.description,
                    "predicted_value": prediction.predicted_value,
                    "confidence_score": prediction.confidence_score,
                    "risk_level": prediction.risk_level,
                    "forecast_time": prediction.forecast_time.isoformat(),
                }
            )

        return {
            "status": "success",
            "predictions_count": len(predictions),
            "predictions": predictions_data,
            "prediction_params": prediction_params,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"預測分析失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("logs.generate_dashboard")
def generate_dashboard_task(self, dashboard_params: Dict[str, Any]):
    """
    生成儀表板數據任務

    Args:
        dashboard_params: 儀表板參數
    """
    try:
        ensure_initialization()

        time_range_hours = dashboard_params.get("time_range_hours", 24)

        logger.info(f"開始生成儀表板數據: 時間範圍={time_range_hours}小時")

        # 生成儀表板數據
        dashboard_data = asyncio.run(
            log_aggregator.create_dashboard_data(time_range_hours=time_range_hours)
        )

        logger.info(f"儀表板數據生成完成")

        return {
            "status": "success",
            "dashboard_data": dashboard_data,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"生成儀表板數據失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("logs.generate_report")
def generate_report_task(self, report_params: Dict[str, Any]):
    """
    生成報告任務

    Args:
        report_params: 報告參數
    """
    try:
        ensure_initialization()

        report_type = report_params.get("report_type", "daily")
        service = report_params.get("service")

        logger.info(f"開始生成 {report_type} 報告: 服務={service}")

        # 生成報告
        report = asyncio.run(
            log_aggregator.generate_report(report_type=report_type, service=service)
        )

        logger.info(f"{report_type} 報告生成完成")

        return {"status": "success", "report": report, "report_params": report_params}

    except Exception as e:
        logger.error(f"生成報告失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("logs.export_logs")
def export_logs_task(self, export_params: Dict[str, Any]):
    """
    導出日誌任務

    Args:
        export_params: 導出參數
    """
    try:
        output_path = export_params.get("output_path")
        start_date = export_params.get("start_date")
        end_date = export_params.get("end_date")

        logger.info(f"開始導出日誌: {start_date} 到 {end_date}")

        if not output_path:
            # 生成默認輸出路徑
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = f"/tmp/logs_export_{timestamp}.jsonl"

        # 執行導出
        exported_count = asyncio.run(
            log_collector.export_logs(
                output_path=output_path, start_date=start_date, end_date=end_date
            )
        )

        logger.info(f"日誌導出完成: {exported_count} 條記錄")

        return {
            "status": "success",
            "exported_count": exported_count,
            "output_path": output_path,
            "export_params": export_params,
            "exported_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"導出日誌失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("logs.cleanup_old_logs")
def cleanup_old_logs_task(self, cleanup_params: Dict[str, Any]):
    """
    清理舊日誌任務

    Args:
        cleanup_params: 清理參數
    """
    try:
        days = cleanup_params.get("days", 30)

        logger.info(f"開始清理 {days} 天前的日誌")

        # 執行清理
        asyncio.run(log_collector._cleanup_old_logs(days=days))

        # 獲取清理後的統計
        final_stats = log_collector.get_stats()

        logger.info(f"日誌清理完成，保留 {days} 天")

        return {
            "status": "success",
            "cleanup_days": days,
            "final_stats": final_stats,
            "cleaned_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"清理日誌失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("logs.health_check")
def log_health_check_task(self):
    """
    日誌系統健康檢查任務
    """
    try:
        logger.info("開始日誌系統健康檢查")

        # 獲取各組件統計
        collector_stats = log_collector.get_stats()

        # 檢查是否有組件初始化
        ensure_initialization()

        if anomaly_detector:
            anomaly_stats = anomaly_detector.get_anomaly_stats()
        else:
            anomaly_stats = {"error": "anomaly_detector not initialized"}

        if log_predictor:
            prediction_stats = log_predictor.get_prediction_stats()
        else:
            prediction_stats = {"error": "log_predictor not initialized"}

        if log_aggregator:
            aggregator_stats = log_aggregator.get_cache_stats()
        else:
            aggregator_stats = {"error": "log_aggregator not initialized"}

        if log_alerting:
            alerting_stats = log_alerting.get_alert_statistics()
        else:
            alerting_stats = {"error": "log_alerting not initialized"}

        health_report = {
            "overall_status": "healthy",
            "components": {
                "log_collector": {"status": "healthy", "stats": collector_stats},
                "anomaly_detector": {
                    "status": "healthy" if "error" not in anomaly_stats else "error",
                    "stats": anomaly_stats,
                },
                "log_predictor": {
                    "status": "healthy" if "error" not in prediction_stats else "error",
                    "stats": prediction_stats,
                },
                "log_aggregator": {
                    "status": "healthy" if "error" not in aggregator_stats else "error",
                    "stats": aggregator_stats,
                },
                "log_alerting": {
                    "status": "healthy" if "error" not in alerting_stats else "error",
                    "stats": alerting_stats,
                },
            },
            "checked_at": datetime.utcnow().isoformat(),
        }

        logger.info("日誌系統健康檢查完成")

        return {"status": "success", "health_report": health_report}

    except Exception as e:
        logger.error(f"日誌系統健康檢查失敗: {e}")

        return {"status": "error", "error": str(e), "checked_at": datetime.utcnow().isoformat()}


@celery_app.task(bind=True)
@trace_celery_task("logs.automated_analysis")
def automated_analysis_task(self):
    """
    自動化日誌分析任務

    定期執行各種日誌分析以發現潛在問題
    """
    try:
        ensure_initialization()

        logger.info("開始自動化日誌分析")

        results = {}

        # 1. 性能分析
        try:
            performance_result = asyncio.run(
                log_analyzer.analyze_logs(analysis_type=AnalysisType.PERFORMANCE, hours=1)
            )
            results["performance"] = {
                "summary": performance_result.summary,
                "severity": performance_result.severity,
            }
        except Exception as e:
            logger.warning(f"性能分析失敗: {e}")
            results["performance"] = {"error": str(e)}

        # 2. 錯誤分析
        try:
            error_result = asyncio.run(
                log_analyzer.analyze_logs(analysis_type=AnalysisType.ERROR, hours=1)
            )
            results["error"] = {"summary": error_result.summary, "severity": error_result.severity}
        except Exception as e:
            logger.warning(f"錯誤分析失敗: {e}")
            results["error"] = {"error": str(e)}

        # 3. 安全分析
        try:
            security_result = asyncio.run(
                log_analyzer.analyze_logs(analysis_type=AnalysisType.SECURITY, hours=1)
            )
            results["security"] = {
                "summary": security_result.summary,
                "severity": security_result.severity,
            }
        except Exception as e:
            logger.warning(f"安全分析失敗: {e}")
            results["security"] = {"error": str(e)}

        # 4. 異常檢測
        try:
            anomalies = asyncio.run(anomaly_detector.detect_anomalies(hours=1))
            results["anomalies"] = {
                "count": len(anomalies),
                "high_severity_count": len(
                    [a for a in anomalies if a.severity.value in ["high", "critical"]]
                ),
            }
        except Exception as e:
            logger.warning(f"異常檢測失敗: {e}")
            results["anomalies"] = {"error": str(e)}

        logger.info("自動化日誌分析完成")

        return {
            "status": "success",
            "analysis_results": results,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"自動化日誌分析失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("logs.alert_monitoring")
def alert_monitoring_task(self):
    """
    告警監控任務

    檢查系統狀態並觸發相應告警
    """
    try:
        ensure_initialization()

        logger.info("開始告警監控")

        # 執行告警檢查
        # 這個功能已經在 log_alerting 的後台任務中實現
        # 這裡主要是提供一個手動觸發的入口

        if log_alerting:
            active_alerts = log_alerting.get_active_alerts()
            alert_stats = log_alerting.get_alert_statistics()

            logger.info(f"當前活躍告警: {len(active_alerts)} 個")

            return {
                "status": "success",
                "active_alerts_count": len(active_alerts),
                "alert_statistics": alert_stats,
                "monitored_at": datetime.utcnow().isoformat(),
            }
        else:
            logger.warning("告警系統未初始化")
            return {
                "status": "warning",
                "message": "告警系統未初始化",
                "monitored_at": datetime.utcnow().isoformat(),
            }

    except Exception as e:
        logger.error(f"告警監控失敗: {e}")
        raise
