"""
監控相關的 Celery 任務
"""

from celery import current_task
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any

from ..celery_app import celery_app, TaskRetryMixin
from ..monitoring.health_monitor import health_monitor

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=celery_app.Task)
class MonitoringTask(TaskRetryMixin):
    """監控任務基類"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任務失敗處理"""
        logger.error(f"監控任務 {task_id} 失敗: {exc}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """任務成功處理"""
        logger.info(f"監控任務 {task_id} 成功完成")


@celery_app.task(bind=True, base=MonitoringTask, name="monitoring.health_monitoring_task")
def health_monitoring_task(self):
    """健康監控任務"""
    try:
        logger.info("開始執行健康監控檢查")
        
        # 創建事件循環來運行異步函數
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 執行健康檢查
            loop.run_until_complete(health_monitor.run_health_checks())
            
            # 獲取當前狀態
            current_status = health_monitor.get_health_status()
            active_alerts = health_monitor.get_active_alerts()
            
            result = {
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": current_status.get("overall_status", "unknown"),
                "components_checked": len(current_status.get("components", {})),
                "active_alerts_count": len(active_alerts),
                "execution_time": datetime.utcnow().isoformat()
            }
            
            logger.info(f"健康監控完成: {result['overall_status']}, {result['active_alerts_count']} 個活躍告警")
            
            return result
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"健康監控任務執行失敗: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=MonitoringTask)
def alert_notification_task(self, alert_data: Dict[str, Any]):
    """告警通知任務"""
    try:
        logger.info(f"處理告警通知: {alert_data.get('title', '未知告警')}")
        
        # 這裡可以實現具體的通知邏輯
        # 例如發送郵件、Slack 通知、Webhook 等
        
        # 示例：記錄告警到日誌
        alert_level = alert_data.get('level', 'unknown')
        alert_title = alert_data.get('title', '未知告警')
        alert_message = alert_data.get('message', '')
        
        if alert_level in ['critical', 'error']:
            logger.error(f"嚴重告警: {alert_title} - {alert_message}")
        elif alert_level == 'warning':
            logger.warning(f"警告告警: {alert_title} - {alert_message}")
        else:
            logger.info(f"資訊告警: {alert_title} - {alert_message}")
        
        return {
            "success": True,
            "alert_processed": alert_title,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"告警通知任務失敗: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=MonitoringTask)
def metrics_aggregation_task(self, hours: int = 1):
    """指標聚合任務"""
    try:
        logger.info(f"開始聚合過去 {hours} 小時的指標數據")
        
        # 創建事件循環
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 獲取歷史數據
            from datetime import timedelta
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # 過濾歷史數據
            filtered_history = [
                record for record in health_monitor.health_history
                if datetime.fromisoformat(record["timestamp"]) > cutoff_time
            ]
            
            if not filtered_history:
                return {
                    "success": True,
                    "message": "沒有數據需要聚合",
                    "records_processed": 0,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # 計算聚合指標
            total_records = len(filtered_history)
            healthy_count = sum(1 for record in filtered_history 
                              if record.get("overall_status") == "healthy")
            warning_count = sum(1 for record in filtered_history 
                              if record.get("overall_status") == "warning")
            critical_count = sum(1 for record in filtered_history 
                               if record.get("overall_status") == "critical")
            
            # 計算平均響應時間
            total_execution_time = 0
            execution_count = 0
            
            for record in filtered_history:
                components = record.get("components", {})
                for component_data in components.values():
                    if "execution_time_ms" in component_data:
                        total_execution_time += component_data["execution_time_ms"]
                        execution_count += 1
            
            avg_execution_time = total_execution_time / execution_count if execution_count > 0 else 0
            
            aggregated_data = {
                "period_hours": hours,
                "total_records": total_records,
                "health_distribution": {
                    "healthy": healthy_count,
                    "warning": warning_count,
                    "critical": critical_count
                },
                "availability_percentage": (healthy_count / total_records * 100) if total_records > 0 else 0,
                "average_execution_time_ms": round(avg_execution_time, 2),
                "aggregation_timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"指標聚合完成: 處理 {total_records} 條記錄, 可用性 {aggregated_data['availability_percentage']:.2f}%")
            
            return {
                "success": True,
                "aggregated_data": aggregated_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"指標聚合任務失敗: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True, base=MonitoringTask)
def monitoring_cleanup_task(self, days: int = 7):
    """監控數據清理任務"""
    try:
        logger.info(f"開始清理超過 {days} 天的監控數據")
        
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # 清理歷史記錄
        initial_count = len(health_monitor.health_history)
        health_monitor.health_history = [
            record for record in health_monitor.health_history
            if datetime.fromisoformat(record["timestamp"]) > cutoff_time
        ]
        final_count = len(health_monitor.health_history)
        
        cleaned_count = initial_count - final_count
        
        logger.info(f"監控數據清理完成: 清理了 {cleaned_count} 條記錄")
        
        return {
            "success": True,
            "records_cleaned": cleaned_count,
            "records_remaining": final_count,
            "retention_days": days,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"監控數據清理任務失敗: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# 工具函數：排程監控任務
def schedule_monitoring_task(task_name: str, delay_seconds: int = 0, **kwargs):
    """排程監控任務"""
    task_map = {
        "health_check": health_monitoring_task,
        "alert_notification": alert_notification_task,
        "metrics_aggregation": metrics_aggregation_task,
        "monitoring_cleanup": monitoring_cleanup_task
    }
    
    task = task_map.get(task_name)
    if not task:
        raise ValueError(f"未知的監控任務: {task_name}")
    
    if delay_seconds > 0:
        return task.apply_async(
            kwargs=kwargs,
            countdown=delay_seconds,
            queue="maintenance"
        )
    else:
        return task.delay(**kwargs)