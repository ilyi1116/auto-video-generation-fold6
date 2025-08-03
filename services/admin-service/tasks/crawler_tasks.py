from celery import current_task
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ..celery_app import celery_app, TaskRetryMixin
from ..database import SessionLocal
from ..models import CrawlerConfig, CrawlerStatus
from ..crawler_engine import WebCrawler
from ..logging_system import AuditLogger, structured_logger
from ..schemas import SystemLogCreate

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=celery_app.Task)
class CrawlerTask(TaskRetryMixin):
    """爬蟲任務基類"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任務失敗處理"""
        logger.error(f"爬蟲任務 {task_id} 失敗: {exc}")
        
        # 記錄失敗日誌
        asyncio.create_task(
            AuditLogger.log_error(
                error=exc,
                context=f"Celery爬蟲任務失敗: {task_id}"
            )
        )
    
    def on_success(self, retval, task_id, args, kwargs):
        """任務成功處理"""
        logger.info(f"爬蟲任務 {task_id} 成功完成")


@celery_app.task(bind=True, base=CrawlerTask)
def check_scheduled_crawlers(self):
    """檢查並執行計劃的爬蟲任務"""
    db = SessionLocal()
    executed_count = 0
    
    try:
        # 獲取需要執行的爬蟲配置
        current_time = datetime.utcnow()
        due_configs = db.query(CrawlerConfig).filter(
            CrawlerConfig.status == CrawlerStatus.ACTIVE,
            CrawlerConfig.next_run_at <= current_time
        ).all()
        
        logger.info(f"發現 {len(due_configs)} 個需要執行的爬蟲配置")
        
        for config in due_configs:
            try:
                # 異步執行爬蟲任務
                task = run_crawler_config.delay(config.id)
                logger.info(f"已排程爬蟲配置 {config.name} (任務ID: {task.id})")
                executed_count += 1
                
            except Exception as e:
                logger.error(f"排程爬蟲配置 {config.name} 失敗: {e}")
        
        return {
            "success": True,
            "executed_count": executed_count,
            "total_due": len(due_configs),
            "check_time": current_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"檢查計劃爬蟲任務失敗: {e}")
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True, base=CrawlerTask)
def run_crawler_config(self, config_id: int):
    """執行指定的爬蟲配置"""
    db = SessionLocal()
    
    try:
        # 獲取爬蟲配置
        config = db.query(CrawlerConfig).filter(CrawlerConfig.id == config_id).first()
        if not config:
            raise ValueError(f"爬蟲配置 {config_id} 不存在")
        
        if config.status != CrawlerStatus.ACTIVE:
            raise ValueError(f"爬蟲配置 {config.name} 未啟用")
        
        logger.info(f"開始執行爬蟲配置: {config.name}")
        
        # 使用同步方式運行爬蟲
        import asyncio
        
        async def run_crawler():
            async with WebCrawler() as crawler:
                return await crawler.crawl_config(config)
        
        # 在新的事件循環中運行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_crawler())
        loop.close()
        
        # 更新任務進度
        if hasattr(self, 'update_state'):
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': result.get('pages_crawled', 0),
                    'total': config.max_pages,
                    'status': '爬取完成'
                }
            )
        
        # 記錄成功日誌
        asyncio.create_task(
            structured_logger.log(
                action="crawler_executed",
                resource_type="crawler_config",
                resource_id=str(config_id),
                message=f"爬蟲配置 {config.name} 執行完成",
                details=result
            )
        )
        
        return {
            "success": result["success"],
            "config_id": config_id,
            "config_name": config.name,
            "pages_crawled": result.get("pages_crawled", 0),
            "duration_seconds": result.get("duration_seconds", 0),
            "error": result.get("error") if not result["success"] else None
        }
        
    except Exception as e:
        logger.error(f"執行爬蟲配置 {config_id} 失敗: {e}")
        
        # 記錄錯誤日誌
        asyncio.create_task(
            AuditLogger.log_error(
                error=e,
                context=f"Celery爬蟲任務執行失敗: config_id={config_id}"
            )
        )
        
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True, base=CrawlerTask)
def batch_run_crawlers(self, config_ids: List[int]):
    """批量執行爬蟲配置"""
    results = []
    
    for config_id in config_ids:
        try:
            # 執行單個爬蟲配置
            result = run_crawler_config.delay(config_id)
            results.append({
                "config_id": config_id,
                "task_id": result.id,
                "status": "scheduled"
            })
            
        except Exception as e:
            logger.error(f"批量執行爬蟲配置 {config_id} 失敗: {e}")
            results.append({
                "config_id": config_id,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "success": True,
        "total_configs": len(config_ids),
        "results": results
    }


@celery_app.task(bind=True, base=CrawlerTask) 
def cleanup_crawler_results(self, days: int = 30):
    """清理舊的爬蟲結果"""
    from ..models import CrawlerResult
    
    db = SessionLocal()
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 刪除舊結果
        deleted_count = db.query(CrawlerResult).filter(
            CrawlerResult.scraped_at < cutoff_date
        ).delete()
        
        db.commit()
        
        logger.info(f"清理了 {deleted_count} 條超過 {days} 天的爬蟲結果")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"清理爬蟲結果失敗: {e}")
        db.rollback()
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True, base=CrawlerTask)
def validate_crawler_configs(self):
    """驗證所有爬蟲配置的有效性"""
    db = SessionLocal()
    validation_results = []
    
    try:
        configs = db.query(CrawlerConfig).filter(
            CrawlerConfig.status == CrawlerStatus.ACTIVE
        ).all()
        
        for config in configs:
            try:
                # 驗證配置
                from ..crawler_engine import validate_crawler_config
                
                config_data = {
                    "target_url": config.target_url,
                    "keywords": config.keywords,
                    "max_pages": config.max_pages,
                    "delay_seconds": config.delay_seconds,
                    "css_selectors": config.css_selectors
                }
                
                is_valid, errors = validate_crawler_config(config_data)
                
                validation_results.append({
                    "config_id": config.id,
                    "config_name": config.name,
                    "is_valid": is_valid,
                    "errors": errors
                })
                
                # 如果配置無效，設置為錯誤狀態
                if not is_valid:
                    config.status = CrawlerStatus.ERROR
                    db.commit()
                    
            except Exception as e:
                logger.error(f"驗證爬蟲配置 {config.id} 失敗: {e}")
                validation_results.append({
                    "config_id": config.id,
                    "config_name": config.name,
                    "is_valid": False,
                    "errors": [str(e)]
                })
        
        return {
            "success": True,
            "total_configs": len(configs),
            "validation_results": validation_results
        }
        
    except Exception as e:
        logger.error(f"驗證爬蟲配置失敗: {e}")
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True, base=CrawlerTask)
def crawler_performance_report(self):
    """生成爬蟲性能報告"""
    from ..models import CrawlerResult
    from sqlalchemy import func
    
    db = SessionLocal()
    
    try:
        # 過去24小時的統計
        last_24h = datetime.utcnow() - timedelta(hours=24)
        
        # 成功率統計
        total_runs = db.query(CrawlerResult).filter(
            CrawlerResult.scraped_at >= last_24h
        ).count()
        
        successful_runs = db.query(CrawlerResult).filter(
            CrawlerResult.scraped_at >= last_24h,
            CrawlerResult.success == True
        ).count()
        
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
        
        # 每個配置的統計
        config_stats = db.query(
            CrawlerResult.config_id,
            func.count(CrawlerResult.id).label('total_runs'),
            func.sum(func.cast(CrawlerResult.success, db.Integer)).label('successful_runs')
        ).filter(
            CrawlerResult.scraped_at >= last_24h
        ).group_by(CrawlerResult.config_id).all()
        
        # 錯誤統計
        error_stats = db.query(
            CrawlerResult.error_message,
            func.count(CrawlerResult.id).label('count')
        ).filter(
            CrawlerResult.scraped_at >= last_24h,
            CrawlerResult.success == False,
            CrawlerResult.error_message.isnot(None)
        ).group_by(CrawlerResult.error_message).all()
        
        return {
            "success": True,
            "period": "last_24_hours",
            "overall_stats": {
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "success_rate": round(success_rate, 2)
            },
            "config_stats": [
                {
                    "config_id": stat.config_id,
                    "total_runs": stat.total_runs,
                    "successful_runs": stat.successful_runs or 0,
                    "success_rate": round((stat.successful_runs or 0) / stat.total_runs * 100, 2)
                }
                for stat in config_stats
            ],
            "error_stats": [
                {
                    "error_message": stat.error_message[:100],  # 限制長度
                    "count": stat.count
                }
                for stat in error_stats
            ]
        }
        
    except Exception as e:
        logger.error(f"生成爬蟲性能報告失敗: {e}")
        raise
        
    finally:
        db.close()


# 手動觸發任務的工具函數
def schedule_crawler_run(config_id: int, delay_seconds: int = 0):
    """排程爬蟲運行"""
    if delay_seconds > 0:
        return run_crawler_config.apply_async(
            args=[config_id],
            countdown=delay_seconds,
            queue="crawler"
        )
    else:
        return run_crawler_config.delay(config_id)


def schedule_batch_crawler_run(config_ids: List[int], delay_seconds: int = 0):
    """排程批量爬蟲運行"""
    if delay_seconds > 0:
        return batch_run_crawlers.apply_async(
            args=[config_ids],
            countdown=delay_seconds,
            queue="crawler"
        )
    else:
        return batch_run_crawlers.delay(config_ids)


def get_crawler_task_status(task_id: str):
    """獲取爬蟲任務狀態"""
    from ..celery_app import get_task_status
    return get_task_status(task_id)