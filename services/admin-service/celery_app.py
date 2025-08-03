from celery import Celery
from celery.schedules import crontab
import os
import logging
from datetime import datetime, timedelta

# Celery 配置
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")

# 創建 Celery 應用
celery_app = Celery(
    "admin_system",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "services.admin-service.tasks.crawler_tasks",
        "services.admin-service.tasks.trends_tasks",
        "services.admin-service.tasks.maintenance_tasks",
        "services.admin-service.tasks.notification_tasks"
    ]
)

# Celery 配置
celery_app.conf.update(
    # 任務序列化
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 時區設置
    timezone="UTC",
    enable_utc=True,
    
    # 任務路由
    task_routes={
        "crawler.*": {"queue": "crawler"},
        "trends.*": {"queue": "trends"}, 
        "maintenance.*": {"queue": "maintenance"},
        "notifications.*": {"queue": "notifications"},
    },
    
    # 任務過期設置
    task_time_limit=3600,  # 1小時超時
    task_soft_time_limit=3000,  # 50分鐘軟超時
    
    # 工作器設置
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    
    # 結果設置
    result_expires=3600,  # 結果保存1小時
    
    # 監控設置
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # 定時任務配置
    beat_schedule={
        # 爬蟲任務 - 每分鐘檢查一次
        "check-crawler-schedules": {
            "task": "crawler.check_scheduled_crawlers",
            "schedule": crontab(minute="*"),  # 每分鐘
            "options": {"queue": "crawler"}
        },
        
        # 社交媒體趨勢收集 - 每小時一次
        "collect-social-trends": {
            "task": "trends.collect_all_trends",
            "schedule": crontab(minute=0),  # 每小時整點
            "options": {"queue": "trends"}
        },
        
        # YouTube 趨勢收集 - 每2小時一次
        "collect-youtube-trends": {
            "task": "trends.collect_youtube_trends",
            "schedule": crontab(minute=0, hour="*/2"),  # 每2小時
            "options": {"queue": "trends"}
        },
        
        # Twitter 趨勢收集 - 每30分鐘一次
        "collect-twitter-trends": {
            "task": "trends.collect_twitter_trends", 
            "schedule": crontab(minute="*/30"),  # 每30分鐘
            "options": {"queue": "trends"}
        },
        
        # 日誌清理 - 每天凌晨2點
        "cleanup-old-logs": {
            "task": "maintenance.cleanup_old_logs",
            "schedule": crontab(hour=2, minute=0),  # 每天2:00
            "options": {"queue": "maintenance"}
        },
        
        # 系統健康檢查 - 每5分鐘
        "system-health-check": {
            "task": "maintenance.system_health_check",
            "schedule": crontab(minute="*/5"),  # 每5分鐘
            "options": {"queue": "maintenance"}
        },
        
        # 數據備份 - 每天凌晨3點
        "backup-database": {
            "task": "maintenance.backup_database",
            "schedule": crontab(hour=3, minute=0),  # 每天3:00
            "options": {"queue": "maintenance"}
        },
        
        # 性能監控報告 - 每小時
        "performance-monitoring": {
            "task": "maintenance.performance_monitoring",
            "schedule": crontab(minute=15),  # 每小時15分
            "options": {"queue": "maintenance"}
        },
        
        # 錯誤報告 - 每天早上8點
        "daily-error-report": {
            "task": "notifications.daily_error_report",
            "schedule": crontab(hour=8, minute=0),  # 每天8:00
            "options": {"queue": "notifications"}
        },
        
        # 系統統計報告 - 每週一早上9點
        "weekly-stats-report": {
            "task": "notifications.weekly_stats_report",
            "schedule": crontab(hour=9, minute=0, day_of_week=1),  # 每週一9:00
            "options": {"queue": "notifications"}
        }
    }
)

# 日誌配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class CeleryConfig:
    """Celery 配置類"""
    
    @staticmethod
    def configure_queues():
        """配置隊列"""
        return {
            "crawler": {
                "exchange": "crawler",
                "exchange_type": "direct",
                "routing_key": "crawler"
            },
            "trends": {
                "exchange": "trends", 
                "exchange_type": "direct",
                "routing_key": "trends"
            },
            "maintenance": {
                "exchange": "maintenance",
                "exchange_type": "direct", 
                "routing_key": "maintenance"
            },
            "notifications": {
                "exchange": "notifications",
                "exchange_type": "direct",
                "routing_key": "notifications"
            }
        }
    
    @staticmethod
    def get_worker_config():
        """獲取工作器配置"""
        return {
            "crawler": {
                "concurrency": 2,
                "max_memory_per_child": 200000,  # 200MB
                "queues": ["crawler"]
            },
            "trends": {
                "concurrency": 4,
                "max_memory_per_child": 300000,  # 300MB
                "queues": ["trends"]
            },
            "maintenance": {
                "concurrency": 1,
                "max_memory_per_child": 100000,  # 100MB
                "queues": ["maintenance"]
            },
            "notifications": {
                "concurrency": 2,
                "max_memory_per_child": 100000,  # 100MB
                "queues": ["notifications"]
            }
        }


# Celery 事件處理
@celery_app.task(bind=True)
def debug_task(self):
    """調試任務"""
    print(f"Request: {self.request!r}")


# 任務失敗處理
@celery_app.task(bind=True)
def task_failure_handler(self, task_id, error, traceback):
    """任務失敗處理器"""
    logger.error(f"任務 {task_id} 失敗: {error}")
    logger.error(f"堆疊追蹤: {traceback}")
    
    # 這裡可以發送通知或記錄到數據庫
    # send_failure_notification(task_id, error)


# 任務成功處理
@celery_app.task(bind=True)
def task_success_handler(self, retval, task_id, args, kwargs):
    """任務成功處理器"""
    logger.info(f"任務 {task_id} 成功完成")


# 應用啟動時的鉤子
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """設置週期性任務"""
    logger.info("正在設置週期性任務...")
    
    # 動態添加任務
    sender.add_periodic_task(
        60.0,  # 60秒
        debug_task.s(),
        name="每分鐘調試任務"
    )


# 工作器準備就緒時的鉤子
@celery_app.on_after_finalize.connect
def setup_routing(sender, **kwargs):
    """設置路由"""
    logger.info("正在設置任務路由...")


# 任務預運行鉤子
@celery_app.task(bind=True, base=celery_app.Task)
def base_task(self, *args, **kwargs):
    """基礎任務類"""
    logger.info(f"任務 {self.name} 開始執行")
    
    try:
        result = super().run(*args, **kwargs)
        logger.info(f"任務 {self.name} 執行成功")
        return result
    except Exception as exc:
        logger.error(f"任務 {self.name} 執行失敗: {exc}")
        raise


# 監控工具
class CeleryMonitor:
    """Celery 監控器"""
    
    def __init__(self):
        self.app = celery_app
    
    def get_active_tasks(self):
        """獲取活躍任務"""
        inspect = self.app.control.inspect()
        return inspect.active()
    
    def get_scheduled_tasks(self):
        """獲取計劃任務"""
        inspect = self.app.control.inspect()
        return inspect.scheduled()
    
    def get_worker_stats(self):
        """獲取工作器統計"""
        inspect = self.app.control.inspect()
        return inspect.stats()
    
    def get_registered_tasks(self):
        """獲取註冊任務"""
        inspect = self.app.control.inspect()
        return inspect.registered()
    
    def cancel_task(self, task_id):
        """取消任務"""
        self.app.control.revoke(task_id, terminate=True)
    
    def purge_queue(self, queue_name):
        """清空隊列"""
        self.app.control.purge()
    
    def get_queue_length(self, queue_name):
        """獲取隊列長度"""
        # 這需要根據具體的訊息代理實現
        return 0


# 任務重試配置
class TaskRetryMixin:
    """任務重試混合類"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 60}
    retry_backoff = True
    retry_backoff_max = 700
    retry_jitter = False


# 全域監控器實例
celery_monitor = CeleryMonitor()


# 工具函數
def get_task_status(task_id):
    """獲取任務狀態"""
    result = celery_app.AsyncResult(task_id)
    return {
        "id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
        "traceback": result.traceback if result.failed() else None
    }


def schedule_task(task_name, args=None, kwargs=None, eta=None, countdown=None, queue=None):
    """排程任務"""
    return celery_app.send_task(
        task_name,
        args=args or [],
        kwargs=kwargs or {},
        eta=eta,
        countdown=countdown,
        queue=queue
    )


def schedule_periodic_task(task_name, schedule, args=None, kwargs=None):
    """排程週期性任務"""
    # 這需要動態添加到 beat_schedule
    pass


# 健康檢查
def celery_health_check():
    """Celery 健康檢查"""
    try:
        # 檢查工作器是否響應
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if not stats:
            return False, "沒有活躍的工作器"
        
        # 檢查隊列是否正常
        active = inspect.active()
        if active is None:
            return False, "無法獲取活躍任務信息"
        
        return True, "Celery 運行正常"
        
    except Exception as e:
        return False, f"Celery 健康檢查失敗: {str(e)}"


if __name__ == "__main__":
    # 啟動 Celery 工作器
    celery_app.start()