"""
用戶行為追蹤相關的 Celery 任務

提供異步的行為分析、模式檢測和洞察生成任務。
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ..celery_app import celery_app
from ..behavior import (
    behavior_collector, behavior_analyzer, pattern_detector, 
    insight_generator, init_behavior_system
)
from ..tracing.tracer import trace_celery_task

logger = logging.getLogger(__name__)

# 確保行為追蹤系統已初始化
init_behavior_system()


@celery_app.task(bind=True)
@trace_celery_task("behavior.analyze_user")
def analyze_user_behavior_task(self, user_id: str, days: int = 30):
    """
    分析用戶行為任務
    
    Args:
        user_id: 用戶ID
        days: 分析天數
    """
    try:
        logger.info(f"開始分析用戶行為: {user_id}, 天數: {days}")
        
        # 執行用戶行為分析
        analysis = asyncio.run(
            behavior_analyzer.analyze_user_behavior(user_id, days)
        )
        
        logger.info(f"用戶行為分析完成: {user_id}")
        
        return {
            "status": "success",
            "user_id": user_id,
            "analysis": {
                "analysis_type": analysis.analysis_type,
                "timestamp": analysis.timestamp.isoformat(),
                "summary": analysis.summary,
                "confidence_score": analysis.confidence_score,
                "data_points": analysis.data_points
            },
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"用戶行為分析失敗: {user_id}, 錯誤: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("behavior.batch_analyze_users")
def batch_analyze_users_task(self, user_ids: List[str], days: int = 30):
    """
    批量分析用戶行為任務
    
    Args:
        user_ids: 用戶ID列表
        days: 分析天數
    """
    try:
        logger.info(f"開始批量分析用戶行為: {len(user_ids)} 個用戶")
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for user_id in user_ids:
            try:
                analysis = asyncio.run(
                    behavior_analyzer.analyze_user_behavior(user_id, days)
                )
                
                results.append({
                    "user_id": user_id,
                    "status": "success",
                    "summary": analysis.summary,
                    "confidence_score": analysis.confidence_score
                })
                
                successful_count += 1
                
            except Exception as e:
                logger.warning(f"用戶行為分析失敗: {user_id}, 錯誤: {e}")
                results.append({
                    "user_id": user_id,
                    "status": "failed",
                    "error": str(e)
                })
                failed_count += 1
        
        logger.info(f"批量分析完成: 成功 {successful_count}, 失敗 {failed_count}")
        
        return {
            "status": "success",
            "total_users": len(user_ids),
            "successful_count": successful_count,
            "failed_count": failed_count,
            "results": results,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"批量用戶行為分析失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("behavior.detect_patterns")
def detect_behavior_patterns_task(self, pattern_type: str = "all", days: int = 7):
    """
    檢測行為模式任務
    
    Args:
        pattern_type: 模式類型 ("sequential", "temporal", "journey", "cohort", "all")
        days: 檢測天數
    """
    try:
        logger.info(f"開始檢測行為模式: 類型={pattern_type}, 天數={days}")
        
        patterns = []
        
        if pattern_type in ["sequential", "all"]:
            sequential_patterns = asyncio.run(
                pattern_detector.detect_sequential_patterns(time_window_hours=days*24)
            )
            patterns.extend(sequential_patterns)
        
        if pattern_type in ["temporal", "all"]:
            temporal_patterns = asyncio.run(
                pattern_detector.detect_temporal_patterns(days=days)
            )
            patterns.extend(temporal_patterns)
        
        if pattern_type in ["journey", "all"]:
            journey_patterns = asyncio.run(
                pattern_detector.detect_user_journey_patterns(days=days)
            )
            patterns.extend(journey_patterns)
        
        if pattern_type in ["cohort", "all"]:
            cohort_patterns = asyncio.run(
                pattern_detector.detect_cohort_patterns(days=days)
            )
            patterns.extend(cohort_patterns)
        
        logger.info(f"模式檢測完成: 發現 {len(patterns)} 個模式")
        
        return {
            "status": "success",
            "pattern_type": pattern_type,
            "patterns_count": len(patterns),
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_name": p.pattern_name,
                    "pattern_type": p.pattern_type,
                    "confidence_score": p.confidence_score,
                    "frequency": p.frequency
                }
                for p in patterns
            ],
            "detected_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"模式檢測失敗: {e}")
        raise


@celery_app.task(bind=True)  
@trace_celery_task("behavior.generate_insights")
def generate_behavior_insights_task(self, days: int = 7):
    """
    生成行為洞察任務
    
    Args:
        days: 分析天數
    """
    try:
        logger.info(f"開始生成行為洞察: {days} 天")
        
        # 生成洞察
        insights = asyncio.run(
            insight_generator.generate_insights(days)
        )
        
        # 按優先級分類
        priority_counts = {"high": 0, "medium": 0, "low": 0}
        type_counts = {}
        
        for insight in insights:
            priority_counts[insight.priority] += 1
            type_counts[insight.insight_type] = type_counts.get(insight.insight_type, 0) + 1
        
        logger.info(f"洞察生成完成: 生成 {len(insights)} 個洞察")
        
        return {
            "status": "success",
            "insights_count": len(insights),
            "priority_distribution": priority_counts,
            "type_distribution": type_counts,
            "high_priority_insights": [
                {
                    "insight_id": i.insight_id,
                    "title": i.title,
                    "description": i.description,
                    "affected_users": i.affected_users,
                    "potential_impact": i.potential_impact
                }
                for i in insights if i.priority == "high"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"生成行為洞察失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("behavior.analyze_funnel")
def analyze_funnel_task(self, funnel_steps: List[Dict[str, Any]], time_window_hours: int = 24):
    """
    分析轉換漏斗任務
    
    Args:
        funnel_steps: 漏斗步驟定義
        time_window_hours: 時間窗口（小時）
    """
    try:
        logger.info(f"開始漏斗分析: {len(funnel_steps)} 個步驟")
        
        # 執行漏斗分析
        analysis = asyncio.run(
            behavior_analyzer.analyze_funnel_performance(
                funnel_steps=funnel_steps,
                time_window_hours=time_window_hours
            )
        )
        
        logger.info("漏斗分析完成")
        
        return {
            "status": "success",
            "funnel_analysis": analysis,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"漏斗分析失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("behavior.analyze_pages")
def analyze_page_performance_task(self, page_url: str = None, hours: int = 24):
    """
    分析頁面性能任務
    
    Args:
        page_url: 頁面URL（可選，為空則分析所有頁面）
        hours: 分析時間範圍（小時）
    """
    try:
        logger.info(f"開始頁面性能分析: URL={page_url or 'all'}, hours={hours}")
        
        # 執行頁面分析
        analysis = asyncio.run(
            behavior_analyzer.analyze_page_performance(
                page_url=page_url,
                hours=hours
            )
        )
        
        logger.info("頁面性能分析完成")
        
        return {
            "status": "success",
            "page_analysis": analysis,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"頁面性能分析失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("behavior.detect_anomalies")
def detect_behavior_anomalies_task(self, hours: int = 24):
    """
    檢測行為異常任務
    
    Args:
        hours: 檢測時間範圍（小時）
    """
    try:
        logger.info(f"開始行為異常檢測: {hours} 小時")
        
        # 執行異常檢測
        anomalies = asyncio.run(
            behavior_analyzer.detect_anomalies(hours)
        )
        
        # 統計異常
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for anomaly in anomalies:
            severity = anomaly.get("severity", "low")
            severity_counts[severity] += 1
        
        logger.info(f"行為異常檢測完成: 發現 {len(anomalies)} 個異常")
        
        return {
            "status": "success",
            "anomalies_count": len(anomalies),
            "severity_distribution": severity_counts,
            "critical_anomalies": [
                a for a in anomalies 
                if a.get("severity") in ["high", "critical"]
            ],
            "detected_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"行為異常檢測失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("behavior.export_data")
def export_behavior_data_task(self, 
                             user_id: str = None,
                             start_date: str = None,
                             end_date: str = None,
                             format: str = "json"):
    """
    導出行為數據任務
    
    Args:
        user_id: 用戶ID（可選）
        start_date: 開始日期
        end_date: 結束日期  
        format: 導出格式
    """
    try:
        logger.info(f"開始導出行為數據: user_id={user_id}, format={format}")
        
        # 轉換日期
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # 執行數據導出
        data = asyncio.run(
            behavior_collector.export_data(
                user_id=user_id,
                start_date=start_dt,
                end_date=end_dt,
                format=format
            )
        )
        
        logger.info("行為數據導出完成")
        
        return {
            "status": "success",
            "export_summary": {
                "sessions_count": len(data.get("sessions", [])),
                "actions_count": len(data.get("actions", [])),
                "user_profiles_count": len(data.get("user_profiles", []))
            },
            "exported_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"導出行為數據失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("behavior.cleanup_old_data")
def cleanup_old_behavior_data_task(self, days: int = 30):
    """
    清理舊行為數據任務
    
    Args:
        days: 保留天數
    """
    try:
        logger.info(f"開始清理舊行為數據: 保留 {days} 天")
        
        # 清理舊模式
        pattern_detector.clear_patterns(older_than_days=days)
        
        # 清理分析緩存
        behavior_analyzer.clear_cache()
        
        # 獲取清理後的統計
        stats = behavior_collector.get_stats()
        
        logger.info(f"舊行為數據清理完成")
        
        return {
            "status": "success",
            "cleanup_days": days,
            "remaining_stats": stats,
            "cleaned_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"清理舊行為數據失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("behavior.health_check")
def behavior_health_check_task(self):
    """
    行為追蹤系統健康檢查任務
    """
    try:
        logger.info("開始行為追蹤系統健康檢查")
        
        # 獲取各組件統計
        collector_stats = behavior_collector.get_stats()
        analyzer_stats = behavior_analyzer.get_analysis_stats()
        pattern_stats = pattern_detector.get_pattern_stats()
        insight_stats = insight_generator.get_insight_stats()
        
        # 檢查組件健康狀態
        health_issues = []
        
        # 檢查數據收集
        if collector_stats.get("total_actions", 0) == 0:
            health_issues.append("沒有收集到用戶動作數據")
        
        # 檢查分析緩存
        if analyzer_stats.get("cache_size", 0) > 1000:
            health_issues.append("分析緩存過大，可能需要清理")
        
        # 檢查模式檢測
        if pattern_stats.get("total_patterns", 0) == 0:
            health_issues.append("沒有檢測到行為模式")
        
        overall_status = "healthy" if not health_issues else "warning"
        
        health_report = {
            "overall_status": overall_status,
            "health_issues": health_issues,
            "components": {
                "behavior_collector": {
                    "status": "healthy",
                    "stats": collector_stats
                },
                "behavior_analyzer": {
                    "status": "healthy",
                    "stats": analyzer_stats
                },
                "pattern_detector": {
                    "status": "healthy",
                    "stats": pattern_stats
                },
                "insight_generator": {
                    "status": "healthy",
                    "stats": insight_stats
                }
            },
            "checked_at": datetime.utcnow().isoformat()
        }
        
        logger.info("行為追蹤系統健康檢查完成")
        
        return {
            "status": "success",
            "health_report": health_report
        }
        
    except Exception as e:
        logger.error(f"行為追蹤系統健康檢查失敗: {e}")
        
        return {
            "status": "error",
            "error": str(e),
            "checked_at": datetime.utcnow().isoformat()
        }


@celery_app.task(bind=True)
@trace_celery_task("behavior.daily_analysis")
def daily_behavior_analysis_task(self):
    """
    每日行為分析任務
    
    執行全面的每日行為分析，包括模式檢測和洞察生成
    """
    try:
        logger.info("開始每日行為分析")
        
        results = {}
        
        # 1. 檢測行為模式
        try:
            patterns_result = asyncio.run(
                pattern_detector.detect_sequential_patterns(time_window_hours=24)
            )
            results["patterns"] = {
                "sequential_patterns": len(patterns_result),
                "status": "success"
            }
        except Exception as e:
            logger.warning(f"模式檢測失敗: {e}")
            results["patterns"] = {"status": "failed", "error": str(e)}
        
        # 2. 生成洞察
        try:
            insights_result = asyncio.run(
                insight_generator.generate_insights(days=1)
            )
            results["insights"] = {
                "insights_generated": len(insights_result),
                "high_priority": len([i for i in insights_result if i.priority == "high"]),
                "status": "success"
            }
        except Exception as e:
            logger.warning(f"洞察生成失敗: {e}")
            results["insights"] = {"status": "failed", "error": str(e)}
        
        # 3. 異常檢測
        try:
            anomalies_result = asyncio.run(
                behavior_analyzer.detect_anomalies(hours=24)
            )
            results["anomalies"] = {
                "anomalies_detected": len(anomalies_result),
                "critical_anomalies": len([a for a in anomalies_result if a.get("severity") == "critical"]),
                "status": "success"
            }
        except Exception as e:
            logger.warning(f"異常檢測失敗: {e}")
            results["anomalies"] = {"status": "failed", "error": str(e)}
        
        logger.info("每日行為分析完成")
        
        return {
            "status": "success",
            "analysis_results": results,
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"每日行為分析失敗: {e}")
        raise


@celery_app.task(bind=True)
@trace_celery_task("behavior.weekly_report")
def weekly_behavior_report_task(self):
    """
    每週行為報告任務
    
    生成詳細的每週行為分析報告
    """
    try:
        logger.info("開始生成每週行為報告")
        
        # 獲取統計數據
        collector_stats = behavior_collector.get_stats()
        pattern_stats = pattern_detector.get_pattern_stats()
        insight_stats = insight_generator.get_insight_stats()
        
        # 生成報告
        report = {
            "report_period": "weekly",
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_actions": collector_stats.get("total_actions", 0),
                "total_sessions": collector_stats.get("total_sessions", 0),
                "total_users": collector_stats.get("total_users", 0),
                "active_sessions": collector_stats.get("active_sessions", 0)
            },
            "patterns": {
                "total_patterns": pattern_stats.get("total_patterns", 0),
                "pattern_types": pattern_stats.get("pattern_types", {}),
                "avg_confidence": pattern_stats.get("avg_confidence", 0)
            },
            "insights": {
                "total_insights": insight_stats.get("total_insights", 0),
                "active_insights": insight_stats.get("active_insights", 0),
                "implemented_insights": insight_stats.get("implemented_insights", 0)
            }
        }
        
        logger.info("每週行為報告生成完成")
        
        return {
            "status": "success",
            "report": report
        }
        
    except Exception as e:
        logger.error(f"生成每週行為報告失敗: {e}")
        raise