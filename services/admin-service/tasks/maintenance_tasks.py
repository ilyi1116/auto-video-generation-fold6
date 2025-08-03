from celery import current_task
import logging
import os
import shutil
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ..celery_app import celery_app, TaskRetryMixin
from ..database import SessionLocal
from ..logging_system import cleanup_old_logs, log_analyzer, AuditLogger

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=celery_app.Task)
class MaintenanceTask(TaskRetryMixin):
    """維護任務基類"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任務失敗處理"""
        logger.error(f"維護任務 {task_id} 失敗: {exc}")
    
    def on_success(self, retval, task_id, args, kwargs):
        """任務成功處理"""
        logger.info(f"維護任務 {task_id} 成功完成")


@celery_app.task(bind=True, base=MaintenanceTask)
def cleanup_old_logs_task(self, days: int = 30):
    """清理舊日誌任務"""
    try:
        logger.info(f"開始清理超過 {days} 天的舊日誌")
        
        # 使用異步函數清理日誌
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(cleanup_old_logs(days))
        loop.close()
        
        return {
            "success": True,
            "days": days,
            "cleanup_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"清理舊日誌失敗: {e}")
        raise


@celery_app.task(bind=True, base=MaintenanceTask)
def system_health_check(self):
    """系統健康檢查"""
    try:
        health_data = {}
        
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        health_data["cpu_usage"] = cpu_percent
        
        # 記憶體使用情況
        memory = psutil.virtual_memory()
        health_data["memory"] = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
        
        # 磁碟使用情況
        disk = psutil.disk_usage('/')
        health_data["disk"] = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": (disk.used / disk.total) * 100
        }
        
        # 網路統計
        net_io = psutil.net_io_counters()
        health_data["network"] = {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
        
        # 進程數量
        health_data["process_count"] = len(psutil.pids())
        
        # 系統負載 (Unix 系統)
        try:
            load_avg = os.getloadavg()
            health_data["load_average"] = {
                "1min": load_avg[0],
                "5min": load_avg[1],
                "15min": load_avg[2]
            }
        except (OSError, AttributeError):
            # Windows 系統沒有 getloadavg
            health_data["load_average"] = None
        
        # 檢查資料庫連接
        try:
            db = SessionLocal()
            db.execute("SELECT 1")
            db.close()
            health_data["database_status"] = "healthy"
        except Exception as e:
            health_data["database_status"] = f"error: {str(e)}"
        
        # 檢查 Celery 狀態
        try:
            from ..celery_app import celery_health_check
            celery_healthy, celery_message = celery_health_check()
            health_data["celery_status"] = {
                "healthy": celery_healthy,
                "message": celery_message
            }
        except Exception as e:
            health_data["celery_status"] = {
                "healthy": False,
                "message": f"檢查失敗: {str(e)}"
            }
        
        # 計算健康分數
        health_score = 100
        
        if cpu_percent > 80:
            health_score -= 20
        elif cpu_percent > 60:
            health_score -= 10
        
        if memory.percent > 90:
            health_score -= 25
        elif memory.percent > 75:
            health_score -= 10
        
        if health_data["disk"]["percent"] > 90:
            health_score -= 25
        elif health_data["disk"]["percent"] > 80:
            health_score -= 10
        
        if health_data["database_status"] != "healthy":
            health_score -= 30
        
        if not health_data["celery_status"]["healthy"]:
            health_score -= 20
        
        health_data["health_score"] = max(0, health_score)
        health_data["status"] = "healthy" if health_score >= 70 else "warning" if health_score >= 40 else "critical"
        health_data["check_time"] = datetime.utcnow().isoformat()
        
        # 如果健康分數較低，記錄警告日誌
        if health_score < 70:
            import asyncio
            asyncio.create_task(
                AuditLogger.log_system_event(
                    "health_warning",
                    f"系統健康分數較低: {health_score}/100",
                    details=health_data,
                    level="warning" if health_score >= 40 else "error"
                )
            )
        
        return health_data
        
    except Exception as e:
        logger.error(f"系統健康檢查失敗: {e}")
        raise


@celery_app.task(bind=True, base=MaintenanceTask)
def backup_database(self):
    """資料庫備份"""
    try:
        backup_dir = "/data/data/com.termux/files/home/myProject/backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/admin_db_backup_{timestamp}.sql"
        
        # 這裡應該根據實際的資料庫類型執行備份
        # PostgreSQL 示例:
        # os.system(f"pg_dump admin_db > {backup_file}")
        
        # SQLite 示例:
        db_path = os.getenv("DATABASE_PATH", "/data/data/com.termux/files/home/myProject/data/admin.db")
        if os.path.exists(db_path):
            shutil.copy2(db_path, f"{backup_dir}/admin_db_backup_{timestamp}.db")
        
        # 清理舊備份 (保留最近7個)
        backup_files = sorted([
            f for f in os.listdir(backup_dir) 
            if f.startswith("admin_db_backup_") and (f.endswith(".sql") or f.endswith(".db"))
        ])
        
        if len(backup_files) > 7:
            for old_backup in backup_files[:-7]:
                os.remove(os.path.join(backup_dir, old_backup))
        
        backup_size = os.path.getsize(f"{backup_dir}/admin_db_backup_{timestamp}.db") if os.path.exists(f"{backup_dir}/admin_db_backup_{timestamp}.db") else 0
        
        return {
            "success": True,
            "backup_file": f"admin_db_backup_{timestamp}.db",
            "backup_size": backup_size,
            "backup_time": datetime.utcnow().isoformat(),
            "retained_backups": len(backup_files)
        }
        
    except Exception as e:
        logger.error(f"資料庫備份失敗: {e}")
        raise


@celery_app.task(bind=True, base=MaintenanceTask)
def performance_monitoring(self):
    """性能監控"""
    try:
        # 獲取過去1小時的性能指標
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def get_performance_data():
            return await log_analyzer.get_performance_metrics(hours=1)
        
        performance_data = loop.run_until_complete(get_performance_data())
        loop.close()
        
        # 添加系統性能數據
        performance_data["system_metrics"] = {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100
        }
        
        # 檢查性能警告
        warnings = []
        
        if performance_data["avg_response_time_ms"] > 5000:
            warnings.append("平均響應時間過長")
        
        if performance_data["slow_requests"] > 10:
            warnings.append("慢請求數量過多")
        
        if performance_data["system_metrics"]["cpu_usage"] > 80:
            warnings.append("CPU 使用率過高")
        
        if performance_data["system_metrics"]["memory_usage"] > 85:
            warnings.append("記憶體使用率過高")
        
        performance_data["warnings"] = warnings
        performance_data["monitor_time"] = datetime.utcnow().isoformat()
        
        return performance_data
        
    except Exception as e:
        logger.error(f"性能監控失敗: {e}")
        raise


@celery_app.task(bind=True, base=MaintenanceTask)
def cleanup_temp_files(self):
    """清理臨時文件"""
    try:
        temp_dirs = [
            "/tmp",
            "/data/data/com.termux/files/home/myProject/temp",
            "/data/data/com.termux/files/home/myProject/logs/temp"
        ]
        
        cleaned_files = 0
        freed_space = 0
        
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue
                
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # 檢查文件修改時間
                        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                        if mod_time < cutoff_time:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleaned_files += 1
                            freed_space += file_size
                    except (OSError, IOError):
                        # 忽略無法刪除的文件
                        pass
        
        return {
            "success": True,
            "cleaned_files": cleaned_files,
            "freed_space_bytes": freed_space,
            "freed_space_mb": round(freed_space / (1024 * 1024), 2),
            "cleanup_time": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"清理臨時文件失敗: {e}")
        raise


@celery_app.task(bind=True, base=MaintenanceTask)
def update_system_stats(self):
    """更新系統統計"""
    from ..models import SystemLog, AIProvider, CrawlerConfig, SocialTrendConfig, TrendingKeyword
    from sqlalchemy import func
    
    db = SessionLocal()
    
    try:
        # 收集系統統計數據
        stats = {}
        
        # 日誌統計
        today = datetime.utcnow().date()
        stats["logs"] = {
            "total": db.query(SystemLog).count(),
            "today": db.query(SystemLog).filter(
                func.date(SystemLog.created_at) == today
            ).count(),
            "errors_today": db.query(SystemLog).filter(
                func.date(SystemLog.created_at) == today,
                SystemLog.level.in_(["error", "critical"])
            ).count()
        }
        
        # AI Provider 統計
        stats["ai_providers"] = {
            "total": db.query(AIProvider).count(),
            "active": db.query(AIProvider).filter(AIProvider.is_active == True).count()
        }
        
        # 爬蟲統計
        stats["crawlers"] = {
            "total": db.query(CrawlerConfig).count(),
            "active": db.query(CrawlerConfig).filter(CrawlerConfig.status == "active").count()
        }
        
        # 趨勢配置統計
        stats["trend_configs"] = {
            "total": db.query(SocialTrendConfig).count(),
            "active": db.query(SocialTrendConfig).filter(SocialTrendConfig.is_active == True).count()
        }
        
        # 趨勢數據統計
        stats["trending_keywords"] = {
            "total": db.query(TrendingKeyword).count(),
            "today": db.query(TrendingKeyword).filter(
                func.date(TrendingKeyword.trend_date) == today
            ).count()
        }
        
        stats["update_time"] = datetime.utcnow().isoformat()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"更新系統統計失敗: {e}")
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True, base=MaintenanceTask)
def security_scan(self):
    """安全掃描"""
    try:
        security_issues = []
        
        # 檢查弱密碼 (這裡是示例，實際應該更複雜)
        from ..models import AdminUser
        db = SessionLocal()
        
        try:
            # 檢查是否有預設密碼的用戶
            users = db.query(AdminUser).all()
            for user in users:
                # 這裡應該檢查密碼強度
                if not user.is_active:
                    continue
                    
                # 檢查最後登錄時間
                if user.last_login_at:
                    days_since_login = (datetime.utcnow() - user.last_login_at).days
                    if days_since_login > 90:
                        security_issues.append({
                            "type": "inactive_user",
                            "severity": "medium",
                            "description": f"用戶 {user.username} 超過90天未登錄",
                            "user_id": user.id
                        })
        finally:
            db.close()
        
        # 檢查文件權限
        critical_files = [
            "/data/data/com.termux/files/home/myProject/services/admin-service/security.py",
            "/data/data/com.termux/files/home/myProject/services/admin-service/database.py"
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                file_stat = os.stat(file_path)
                # 檢查文件權限 (簡化版)
                if file_stat.st_mode & 0o077:  # 其他用戶有讀寫權限
                    security_issues.append({
                        "type": "file_permission",
                        "severity": "high",
                        "description": f"文件 {file_path} 權限過於寬鬆",
                        "file_path": file_path
                    })
        
        # 檢查異常登錄模式
        # 這裡可以添加更多安全檢查...
        
        return {
            "success": True,
            "scan_time": datetime.utcnow().isoformat(),
            "issues_found": len(security_issues),
            "security_issues": security_issues
        }
        
    except Exception as e:
        logger.error(f"安全掃描失敗: {e}")
        raise


# 手動觸發維護任務的工具函數
def schedule_maintenance_task(task_name: str, delay_seconds: int = 0, **kwargs):
    """排程維護任務"""
    task_map = {
        "cleanup_logs": cleanup_old_logs_task,
        "health_check": system_health_check,
        "backup_db": backup_database,
        "performance_monitor": performance_monitoring,
        "cleanup_temp": cleanup_temp_files,
        "update_stats": update_system_stats,
        "security_scan": security_scan
    }
    
    task = task_map.get(task_name)
    if not task:
        raise ValueError(f"未知的維護任務: {task_name}")
    
    if delay_seconds > 0:
        return task.apply_async(
            kwargs=kwargs,
            countdown=delay_seconds,
            queue="maintenance"
        )
    else:
        return task.delay(**kwargs)