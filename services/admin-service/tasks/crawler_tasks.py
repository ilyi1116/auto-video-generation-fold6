import logging
from datetime import datetime, timedelta
from typing import List


from ..celery_app import TaskRetryMixin, celery_app
from ..crawler_engine import WebCrawler
from ..database import SessionLocal
from ..logging_system import AuditLogger, structured_logger
from ..models import CrawlerConfig, CrawlerStatus, CrawlerTask

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=celery_app.Task)
class CrawlerTask(TaskRetryMixin):
    """爬蟲任務基類"""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任務失敗處理"""
        logger.error(f"爬蟲任務 {task_id} 失敗: {exc}")

        # 記錄失敗日誌
        asyncio.create_task(
            AuditLogger.log_error(error=exc, context=f"Celery爬蟲任務失敗: {task_id}")
        )

    def on_success(self, retval, task_id, args, kwargs):
        """任務成功處理"""
        logger.info(f"爬蟲任務 {task_id} 成功完成")


@celery_app.task(bind=True, base=CrawlerTask)
def check_scheduled_crawler_tasks(self):
    """檢查並執行計劃的爬蟲任務"""
    db = SessionLocal()
    executed_count = 0

    try:
        # 獲取需要執行的爬蟲配置
        current_time = datetime.utcnow()
        due_configs = (
            db.query(CrawlerConfig)
            .filter(
                CrawlerConfig.status == CrawlerStatus.ACTIVE,
                CrawlerConfig.next_run_at <= current_time,
            )
            .all()
        )

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
            "check_time": current_time.isoformat(),
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
        if hasattr(self, "update_state"):
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": result.get("pages_crawled", 0),
                    "total": config.max_pages,
                    "status": "爬取完成",
                },
            )

        # 記錄成功日誌
        asyncio.create_task(
            structured_logger.log(
                action="crawler_executed",
                resource_type="crawler_config",
                resource_id=str(config_id),
                message=f"爬蟲配置 {config.name} 執行完成",
                details=result,
            )
        )

        return {
            "success": result["success"],
            "config_id": config_id,
            "config_name": config.name,
            "pages_crawled": result.get("pages_crawled", 0),
            "duration_seconds": result.get("duration_seconds", 0),
            "error": result.get("error") if not result["success"] else None,
        }

    except Exception as e:
        logger.error(f"執行爬蟲配置 {config_id} 失敗: {e}")

        # 記錄錯誤日誌
        asyncio.create_task(
            AuditLogger.log_error(error=e, context=f"Celery爬蟲任務執行失敗: config_id={config_id}")
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
            results.append({"config_id": config_id, "task_id": result.id, "status": "scheduled"})

        except Exception as e:
            logger.error(f"批量執行爬蟲配置 {config_id} 失敗: {e}")
            results.append({"config_id": config_id, "status": "failed", "error": str(e)})

    return {"success": True, "total_configs": len(config_ids), "results": results}


@celery_app.task(bind=True, base=CrawlerTask)
def cleanup_crawler_results(self, days: int = 30):
    """清理舊的爬蟲結果"""
    from ..models import CrawlerResult

    db = SessionLocal()

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # 刪除舊結果
        deleted_count = (
            db.query(CrawlerResult).filter(CrawlerResult.scraped_at < cutoff_date).delete()
        )

        db.commit()

        logger.info(f"清理了 {deleted_count} 條超過 {days} 天的爬蟲結果")

        return {
            "success": True,
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
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
        configs = db.query(CrawlerConfig).filter(CrawlerConfig.status == CrawlerStatus.ACTIVE).all()

        for config in configs:
            try:
                # 驗證配置
                from ..crawler_engine import validate_crawler_config

                config_data = {
                    "target_url": config.target_url,
                    "keywords": config.keywords,
                    "max_pages": config.max_pages,
                    "delay_seconds": config.delay_seconds,
                    "css_selectors": config.css_selectors,
                }

                is_valid, errors = validate_crawler_config(config_data)

                validation_results.append(
                    {
                        "config_id": config.id,
                        "config_name": config.name,
                        "is_valid": is_valid,
                        "errors": errors,
                    }
                )

                # 如果配置無效，設置為錯誤狀態
                if not is_valid:
                    config.status = CrawlerStatus.ERROR
                    db.commit()

            except Exception as e:
                logger.error(f"驗證爬蟲配置 {config.id} 失敗: {e}")
                validation_results.append(
                    {
                        "config_id": config.id,
                        "config_name": config.name,
                        "is_valid": False,
                        "errors": [str(e)],
                    }
                )

        return {
            "success": True,
            "total_configs": len(configs),
            "validation_results": validation_results,
        }

    except Exception as e:
        logger.error(f"驗證爬蟲配置失敗: {e}")
        raise

    finally:
        db.close()


@celery_app.task(bind=True, base=CrawlerTask)
def crawler_performance_report(self):
    """生成爬蟲性能報告"""
    from sqlalchemy import func

    from ..models import CrawlerResult

    db = SessionLocal()

    try:
        # 過去24小時的統計
        last_24h = datetime.utcnow() - timedelta(hours=24)

        # 成功率統計
        total_runs = db.query(CrawlerResult).filter(CrawlerResult.scraped_at >= last_24h).count()

        successful_runs = (
            db.query(CrawlerResult)
            .filter(CrawlerResult.scraped_at >= last_24h, CrawlerResult.success == True)
            .count()
        )

        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0

        # 每個配置的統計
        config_stats = (
            db.query(
                CrawlerResult.config_id,
                func.count(CrawlerResult.id).label("total_runs"),
                func.sum(func.cast(CrawlerResult.success, db.Integer)).label("successful_runs"),
            )
            .filter(CrawlerResult.scraped_at >= last_24h)
            .group_by(CrawlerResult.config_id)
            .all()
        )

        # 錯誤統計
        error_stats = (
            db.query(CrawlerResult.error_message, func.count(CrawlerResult.id).label("count"))
            .filter(
                CrawlerResult.scraped_at >= last_24h,
                CrawlerResult.success == False,
                CrawlerResult.error_message.isnot(None),
            )
            .group_by(CrawlerResult.error_message)
            .all()
        )

        return {
            "success": True,
            "period": "last_24_hours",
            "overall_stats": {
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "success_rate": round(success_rate, 2),
            },
            "config_stats": [
                {
                    "config_id": stat.config_id,
                    "total_runs": stat.total_runs,
                    "successful_runs": stat.successful_runs or 0,
                    "success_rate": round((stat.successful_runs or 0) / stat.total_runs * 100, 2),
                }
                for stat in config_stats
            ],
            "error_stats": [
                {"error_message": stat.error_message[:100], "count": stat.count}  # 限制長度
                for stat in error_stats
            ],
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
            args=[config_id], countdown=delay_seconds, queue="crawler"
        )
    else:
        return run_crawler_config.delay(config_id)


def schedule_batch_crawler_run(config_ids: List[int], delay_seconds: int = 0):
    """排程批量爬蟲運行"""
    if delay_seconds > 0:
        return batch_run_crawlers.apply_async(
            args=[config_ids], countdown=delay_seconds, queue="crawler"
        )
    else:
        return batch_run_crawlers.delay(config_ids)


def get_crawler_task_status(task_id: str):
    """獲取爬蟲任務狀態"""
    from ..celery_app import get_task_status

    return get_task_status(task_id)


# ==================== CrawlerTask 新增任務處理 ====================


def should_run_task(task: CrawlerTask, current_time: datetime) -> bool:
    """判斷任務是否應該運行"""
    if not task.is_active:
        return False

    # 如果從未執行過，應該運行
    if not task.last_run_at:
        return True

    # 根據排程類型判斷
    if task.schedule_type == "hourly":
        # 每小時執行一次
        return (current_time - task.last_run_at).total_seconds() >= 3600

    elif task.schedule_type == "daily":
        # 每日執行一次
        return (current_time - task.last_run_at).total_seconds() >= 86400

    elif task.schedule_type == "weekly":
        # 每週執行一次
        return (current_time - task.last_run_at).total_seconds() >= 604800

    elif task.schedule_type == "cron":
        # Cron 表達式需要更複雜的邏輯
        return should_run_cron_task(task, current_time)

    return False


def should_run_cron_task(task: CrawlerTask, current_time: datetime) -> bool:
    """檢查 Cron 任務是否應該運行"""
    # 簡化實現，實際應該使用 croniter 庫
    # 這裡先返回基本檢查
    if not task.schedule_time:
        return False

    # 如果超過1小時沒執行，先執行一次
    if not task.last_run_at:
        return True

    return (current_time - task.last_run_at).total_seconds() >= 3600


@celery_app.task(bind=True, base=CrawlerTask)
def run_crawler_task(self, task_id: int):
    """執行指定的 CrawlerTask 任務"""
    db = SessionLocal()

    try:
        # 獲取爬蟲任務
        task = db.query(CrawlerTask).filter(CrawlerTask.id == task_id).first()
        if not task:
            raise ValueError(f"爬蟲任務 {task_id} 不存在")

        if not task.is_active:
            raise ValueError(f"爬蟲任務 {task.task_name} 未啟用")

        logger.info(f"開始執行爬蟲任務: {task.task_name}")

        # 解析關鍵字（從 JSON 字符串轉換為列表）
        import json

        try:
            keywords = (
                json.loads(task.keywords) if isinstance(task.keywords, str) else task.keywords
            )
        except (json.JSONDecodeError, TypeError):
            keywords = []

        # 使用同步方式運行爬蟲
        import asyncio

        async def run_task_crawler():
            async with WebCrawler() as crawler:
                # 構建爬蟲配置
                crawler_config = {
                    "task_id": task.id,  # 添加任務ID以便保存結果
                    "task_name": task.task_name,
                    "keywords": keywords,
                    "target_url": task.target_url,
                    "max_pages": 10,  # 默認值
                    "delay_seconds": 1,  # 默認值
                }
                return await crawler.crawl_task(crawler_config)

        # 在新的事件循環中運行
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(run_task_crawler())
        loop.close()

        # 更新任務進度
        if hasattr(self, "update_state"):
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": result.get("pages_crawled", 0),
                    "total": result.get("total_pages", 10),
                    "status": "爬取完成",
                },
            )

        # 記錄成功日誌
        asyncio.create_task(
            structured_logger.log(
                action="crawler_task_executed",
                resource_type="crawler_task",
                resource_id=str(task_id),
                message=f"爬蟲任務 {task.task_name} 執行完成",
                details=result,
            )
        )

        return {
            "success": result["success"],
            "task_id": task_id,
            "task_name": task.task_name,
            "pages_crawled": result.get("pages_crawled", 0),
            "duration_seconds": result.get("duration_seconds", 0),
            "error": result.get("error") if not result["success"] else None,
        }

    except Exception as e:
        logger.error(f"執行爬蟲任務 {task_id} 失敗: {e}")

        # 記錄錯誤日誌
        asyncio.create_task(
            AuditLogger.log_error(error=e, context=f"Celery爬蟲任務執行失敗: task_id={task_id}")
        )

        raise

    finally:
        db.close()


@celery_app.task(bind=True, base=CrawlerTask)
def batch_run_crawler_tasks(self, task_ids: List[int]):
    """批量執行 CrawlerTask 任務"""
    results = []

    for task_id in task_ids:
        try:
            # 執行單個爬蟲任務
            result = run_crawler_task.delay(task_id)
            results.append({"task_id": task_id, "celery_task_id": result.id, "status": "scheduled"})

        except Exception as e:
            logger.error(f"批量執行爬蟲任務 {task_id} 失敗: {e}")
            results.append({"task_id": task_id, "status": "failed", "error": str(e)})

    return {"success": True, "total_tasks": len(task_ids), "results": results}


# 手動觸發 CrawlerTask 任務的工具函數
def schedule_crawler_task_run(task_id: int, delay_seconds: int = 0):
    """排程 CrawlerTask 運行"""
    if delay_seconds > 0:
        return run_crawler_task.apply_async(
            args=[task_id], countdown=delay_seconds, queue="crawler"
        )
    else:
        return run_crawler_task.delay(task_id)


def schedule_batch_crawler_task_run(task_ids: List[int], delay_seconds: int = 0):
    """排程批量 CrawlerTask 運行"""
    if delay_seconds > 0:
        return batch_run_crawler_tasks.apply_async(
            args=[task_ids], countdown=delay_seconds, queue="crawler"
        )
    else:
        return batch_run_crawler_tasks.delay(task_ids)
