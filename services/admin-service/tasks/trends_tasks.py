from celery import current_task
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ..celery_app import celery_app, TaskRetryMixin
from ..database import SessionLocal
from ..models import SocialTrendConfig, KeywordTrend, SocialPlatform, TrendTimeframe
from ..social_trends import SocialTrendsManager
from ..logging_system import AuditLogger, structured_logger

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, base=celery_app.Task)
class TrendsTask(TaskRetryMixin):
    """趨勢任務基類"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """任務失敗處理"""
        logger.error(f"趨勢任務 {task_id} 失敗: {exc}")
        
        # 記錄失敗日誌
        asyncio.create_task(
            AuditLogger.log_error(
                error=exc,
                context=f"Celery趨勢任務失敗: {task_id}"
            )
        )
    
    def on_success(self, retval, task_id, args, kwargs):
        """任務成功處理"""
        logger.info(f"趨勢任務 {task_id} 成功完成")


@celery_app.task(bind=True, base=TrendsTask)
def collect_all_trends(self):
    """收集所有平台的趨勢數據"""
    try:
        logger.info("開始收集所有平台的趨勢數據")
        
        # 在新的事件循環中運行異步任務
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_collection():
            manager = SocialTrendsManager()
            return await manager.collect_all_trends()
        
        result = loop.run_until_complete(run_collection())
        loop.close()
        
        # 更新任務進度
        if hasattr(self, 'update_state'):
            self.update_state(
                state='SUCCESS',
                meta={
                    'status': '收集完成',
                    'total_configs': result.get('total_configs', 0),
                    'results': result.get('results', {})
                }
            )
        
        # 記錄成功日誌
        asyncio.create_task(
            structured_logger.log(
                action="trends_collected",
                resource_type="social_trends",
                message="全平台趨勢收集完成",
                details=result
            )
        )
        
        return result
        
    except Exception as e:
        logger.error(f"收集所有趨勢失敗: {e}")
        raise


@celery_app.task(bind=True, base=TrendsTask)
def collect_platform_trends(self, platform: str, region: str = "global"):
    """收集指定平台的趨勢數據"""
    try:
        logger.info(f"開始收集 {platform} {region} 的趨勢數據")
        
        # 在新的事件循環中運行異步任務
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_collection():
            manager = SocialTrendsManager()
            platform_enum = SocialPlatform(platform.lower())
            return await manager.collect_platform_trends(platform_enum, region)
        
        result = loop.run_until_complete(run_collection())
        loop.close()
        
        # 更新任務進度
        if hasattr(self, 'update_state'):
            self.update_state(
                state='SUCCESS',
                meta={
                    'platform': platform,
                    'region': region,
                    'status': '收集完成',
                    'total_keywords': result.get('total_keywords', 0)
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(f"收集 {platform} {region} 趨勢失敗: {e}")
        raise


@celery_app.task(bind=True, base=TrendsTask)
def collect_twitter_trends(self):
    """收集 Twitter 趨勢"""
    return collect_platform_trends.delay("twitter", "global")


@celery_app.task(bind=True, base=TrendsTask)
def collect_youtube_trends(self):
    """收集 YouTube 趨勢"""
    return collect_platform_trends.delay("youtube", "global")


@celery_app.task(bind=True, base=TrendsTask)
def collect_tiktok_trends(self):
    """收集 TikTok 趨勢"""
    return collect_platform_trends.delay("tiktok", "global")


@celery_app.task(bind=True, base=TrendsTask)
def collect_instagram_trends(self):
    """收集 Instagram 趨勢"""
    return collect_platform_trends.delay("instagram", "global")


@celery_app.task(bind=True, base=TrendsTask)
def collect_facebook_trends(self):
    """收集 Facebook 趨勢"""
    return collect_platform_trends.delay("facebook", "global")


@celery_app.task(bind=True, base=TrendsTask)
def collect_keyword_trends_new(self, platforms: List[str] = None, period: str = "day"):
    """收集關鍵字趨勢數據 (新版本 API)"""
    try:
        logger.info(f"開始收集關鍵字趨勢數據 - 平台: {platforms}, 週期: {period}")
        
        # 在新的事件循環中運行異步任務
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_collection():
            from ..social_trends import collect_and_save_trends
            return await collect_and_save_trends(platforms=platforms, period=period)
        
        result = loop.run_until_complete(run_collection())
        loop.close()
        
        # 更新任務進度
        if hasattr(self, 'update_state'):
            self.update_state(
                state='SUCCESS',
                meta={
                    'status': '收集完成',
                    'platforms': platforms,
                    'period': period,
                    'total_records_saved': result.get('total_records_saved', 0)
                }
            )
        
        # 記錄成功日誌
        asyncio.create_task(
            structured_logger.log(
                action="keyword_trends_collected",
                resource_type="keyword_trends",
                message=f"關鍵字趨勢收集完成 - {period}",
                details=result
            )
        )
        
        return result
        
    except Exception as e:
        logger.error(f"收集關鍵字趨勢失敗: {e}")
        raise


@celery_app.task(bind=True, base=TrendsTask)
def cleanup_old_trends(self, days: int = 90):
    """清理舊的趨勢數據"""
    from ..models import TrendingKeyword
    
    db = SessionLocal()
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 清理舊的 trending_keywords 數據
        deleted_old_count = db.query(TrendingKeyword).filter(
            TrendingKeyword.trend_date < cutoff_date
        ).delete()
        
        # 清理舊的 keyword_trends 數據
        deleted_new_count = db.query(KeywordTrend).filter(
            KeywordTrend.collected_at < cutoff_date
        ).delete()
        
        db.commit()
        
        total_deleted = deleted_old_count + deleted_new_count
        logger.info(f"清理了 {total_deleted} 條超過 {days} 天的趨勢數據 (舊格式: {deleted_old_count}, 新格式: {deleted_new_count})")
        
        return {
            "success": True,
            "deleted_count": total_deleted,
            "deleted_old_format": deleted_old_count,
            "deleted_new_format": deleted_new_count,
            "cutoff_date": cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"清理趨勢數據失敗: {e}")
        db.rollback()
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True, base=TrendsTask)
def analyze_trend_patterns(self):
    """分析趨勢模式"""
    from ..models import TrendingKeyword
    from sqlalchemy import func, desc
    
    db = SessionLocal()
    
    try:
        # 過去7天的數據
        last_week = datetime.utcnow() - timedelta(days=7)
        
        # 熱門關鍵字分析
        top_keywords = db.query(
            TrendingKeyword.keyword,
            func.count(TrendingKeyword.id).label('frequency'),
            func.avg(TrendingKeyword.rank).label('avg_rank'),
            func.min(TrendingKeyword.rank).label('best_rank')
        ).filter(
            TrendingKeyword.trend_date >= last_week
        ).group_by(
            TrendingKeyword.keyword
        ).order_by(
            desc('frequency')
        ).limit(50).all()
        
        # 平台活躍度分析
        platform_activity = db.query(
            TrendingKeyword.platform,
            func.count(TrendingKeyword.id).label('total_trends'),
            func.count(func.distinct(TrendingKeyword.keyword)).label('unique_keywords')
        ).filter(
            TrendingKeyword.trend_date >= last_week
        ).group_by(
            TrendingKeyword.platform
        ).all()
        
        # 趨勢上升關鍵字
        # 計算關鍵字在不同時間段的平均排名變化
        trending_up = db.query(
            TrendingKeyword.keyword,
            func.avg(
                func.case(
                    [(TrendingKeyword.trend_date >= datetime.utcnow() - timedelta(days=1), TrendingKeyword.rank)],
                    else_=None
                )
            ).label('recent_avg_rank'),
            func.avg(
                func.case(
                    [(TrendingKeyword.trend_date < datetime.utcnow() - timedelta(days=1), TrendingKeyword.rank)],
                    else_=None
                )
            ).label('older_avg_rank')
        ).filter(
            TrendingKeyword.trend_date >= last_week
        ).group_by(
            TrendingKeyword.keyword
        ).having(
            func.count(TrendingKeyword.id) >= 5  # 至少出現5次
        ).all()
        
        # 計算上升趨勢
        trending_keywords = []
        for trend in trending_up:
            if trend.recent_avg_rank and trend.older_avg_rank:
                # 排名越小越好，所以如果recent_avg_rank < older_avg_rank表示上升
                improvement = trend.older_avg_rank - trend.recent_avg_rank
                if improvement > 0:
                    trending_keywords.append({
                        "keyword": trend.keyword,
                        "improvement": round(improvement, 2),
                        "recent_avg_rank": round(trend.recent_avg_rank, 2),
                        "older_avg_rank": round(trend.older_avg_rank, 2)
                    })
        
        # 按改進程度排序
        trending_keywords.sort(key=lambda x: x["improvement"], reverse=True)
        
        return {
            "success": True,
            "analysis_period": "last_7_days",
            "top_keywords": [
                {
                    "keyword": kw.keyword,
                    "frequency": kw.frequency,
                    "avg_rank": round(kw.avg_rank, 2),
                    "best_rank": kw.best_rank
                }
                for kw in top_keywords
            ],
            "platform_activity": [
                {
                    "platform": pa.platform,
                    "total_trends": pa.total_trends,
                    "unique_keywords": pa.unique_keywords
                }
                for pa in platform_activity
            ],
            "trending_up": trending_keywords[:20]  # 前20個上升趨勢
        }
        
    except Exception as e:
        logger.error(f"分析趨勢模式失敗: {e}")
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True, base=TrendsTask)
def generate_trends_report(self):
    """生成趨勢報告"""
    from ..models import TrendingKeyword, SocialTrendConfig
    from sqlalchemy import func, desc
    
    db = SessionLocal()
    
    try:
        # 今日統計
        today = datetime.utcnow().date()
        today_trends = db.query(TrendingKeyword).filter(
            func.date(TrendingKeyword.trend_date) == today
        ).count()
        
        # 過去24小時統計
        last_24h = datetime.utcnow() - timedelta(hours=24)
        last_24h_trends = db.query(TrendingKeyword).filter(
            TrendingKeyword.trend_date >= last_24h
        ).count()
        
        # 活躍配置統計
        active_configs = db.query(SocialTrendConfig).filter(
            SocialTrendConfig.is_active == True
        ).count()
        
        # 各平台今日趨勢統計
        platform_today_stats = db.query(
            TrendingKeyword.platform,
            func.count(TrendingKeyword.id).label('count')
        ).filter(
            func.date(TrendingKeyword.trend_date) == today
        ).group_by(TrendingKeyword.platform).all()
        
        # 今日熱門關鍵字 (各平台前5)
        today_top_keywords = {}
        for platform in SocialPlatform:
            top_keywords = db.query(TrendingKeyword).filter(
                TrendingKeyword.platform == platform,
                func.date(TrendingKeyword.trend_date) == today
            ).order_by(TrendingKeyword.rank.asc()).limit(5).all()
            
            today_top_keywords[platform.value] = [
                {
                    "keyword": kw.keyword,
                    "rank": kw.rank,
                    "score": kw.score
                }
                for kw in top_keywords
            ]
        
        return {
            "success": True,
            "report_date": today.isoformat(),
            "summary": {
                "today_trends": today_trends,
                "last_24h_trends": last_24h_trends,
                "active_configs": active_configs
            },
            "platform_stats": [
                {
                    "platform": stat.platform,
                    "today_count": stat.count
                }
                for stat in platform_today_stats
            ],
            "today_top_keywords": today_top_keywords
        }
        
    except Exception as e:
        logger.error(f"生成趨勢報告失敗: {e}")
        raise
        
    finally:
        db.close()


@celery_app.task(bind=True, base=TrendsTask)
def validate_trend_configs(self):
    """驗證趨勢配置的有效性"""
    db = SessionLocal()
    validation_results = []
    
    try:
        configs = db.query(SocialTrendConfig).filter(
            SocialTrendConfig.is_active == True
        ).all()
        
        for config in configs:
            try:
                # 驗證 API 配置
                is_valid = True
                errors = []
                
                # 檢查必要字段
                if not config.timeframes:
                    errors.append("時間範圍配置為空")
                    is_valid = False
                
                if not config.schedule_config:
                    errors.append("排程配置為空")
                    is_valid = False
                
                # 檢查 API Key (如果需要)
                if config.platform in [SocialPlatform.TWITTER, SocialPlatform.YOUTUBE]:
                    if not config.api_key:
                        errors.append("缺少 API Key")
                        is_valid = False
                
                # 檢查地區代碼
                valid_regions = ["global", "US", "UK", "TW", "JP", "KR", "CN"]
                if config.region not in valid_regions:
                    errors.append(f"無效的地區代碼: {config.region}")
                    is_valid = False
                
                validation_results.append({
                    "config_id": config.id,
                    "platform": config.platform,
                    "region": config.region,
                    "is_valid": is_valid,
                    "errors": errors
                })
                
            except Exception as e:
                logger.error(f"驗證趨勢配置 {config.id} 失敗: {e}")
                validation_results.append({
                    "config_id": config.id,
                    "platform": config.platform,
                    "region": config.region,
                    "is_valid": False,
                    "errors": [str(e)]
                })
        
        return {
            "success": True,
            "total_configs": len(configs),
            "validation_results": validation_results
        }
        
    except Exception as e:
        logger.error(f"驗證趨勢配置失敗: {e}")
        raise
        
    finally:
        db.close()


# 手動觸發任務的工具函數
def schedule_trends_collection(platform: str = None, region: str = "global", delay_seconds: int = 0):
    """排程趨勢收集"""
    if platform:
        task = collect_platform_trends
        args = [platform, region]
    else:
        task = collect_all_trends
        args = []
    
    if delay_seconds > 0:
        return task.apply_async(
            args=args,
            countdown=delay_seconds,
            queue="trends"
        )
    else:
        return task.delay(*args)


def get_trends_task_status(task_id: str):
    """獲取趨勢任務狀態"""
    from ..celery_app import get_task_status
    return get_task_status(task_id)


# 新版本 API 的便利函數
def schedule_keyword_trends_collection(platforms: List[str] = None, period: str = "day", delay_seconds: int = 0):
    """排程關鍵字趨勢收集 (新版本)"""
    if delay_seconds > 0:
        return collect_keyword_trends_new.apply_async(
            args=[platforms, period],
            countdown=delay_seconds,
            queue="trends"
        )
    else:
        return collect_keyword_trends_new.delay(platforms, period)


def trigger_daily_trends_collection():
    """觸發每日趨勢收集"""
    platforms = ["TikTok", "YouTube", "Instagram", "Facebook", "Twitter"]
    return schedule_keyword_trends_collection(platforms=platforms, period="day")


def trigger_weekly_trends_collection():
    """觸發每週趨勢收集"""
    platforms = ["TikTok", "YouTube", "Instagram", "Facebook", "Twitter"]
    return schedule_keyword_trends_collection(platforms=platforms, period="week")