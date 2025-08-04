"""
行為洞察生成器

基於用戶行為數據和模式生成可操作的商業洞察。
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import defaultdict, Counter
import statistics

from .collector import BehaviorCollector
from .analyzer import BehaviorAnalyzer
from .pattern import PatternDetector
from .models import (
    UserAction, BehaviorSession, UserProfile, ActionType, 
    UserSegment, BehaviorInsight, BehaviorPattern
)

logger = logging.getLogger(__name__)


class InsightGenerator:
    """行為洞察生成器"""
    
    def __init__(self, 
                 collector: BehaviorCollector,
                 analyzer: BehaviorAnalyzer,
                 pattern_detector: PatternDetector):
        """
        初始化洞察生成器
        
        Args:
            collector: 行為收集器
            analyzer: 行為分析器
            pattern_detector: 模式檢測器
        """
        self.collector = collector
        self.analyzer = analyzer
        self.pattern_detector = pattern_detector
        
        # 生成的洞察
        self.insights: Dict[str, BehaviorInsight] = {}
        
        # 洞察生成規則
        self.insight_rules = [
            self._generate_engagement_insights,
            self._generate_conversion_insights,
            self._generate_retention_insights,
            self._generate_feature_usage_insights,
            self._generate_user_segment_insights,
            self._generate_performance_insights,
            self._generate_trend_insights,
            self._generate_anomaly_insights
        ]
        
        # 配置
        self.config = {
            "insight_retention_days": 30,
            "min_impact_threshold": 0.1,
            "min_confidence_threshold": 0.6,
            "priority_thresholds": {
                "high": 0.8,
                "medium": 0.5,
                "low": 0.0
            }
        }
    
    async def generate_insights(self, days: int = 7) -> List[BehaviorInsight]:
        """生成所有類型的洞察"""
        logger.info(f"開始生成 {days} 天的行為洞察")
        
        new_insights = []
        
        # 運行所有洞察生成規則
        for rule in self.insight_rules:
            try:
                rule_insights = await rule(days)
                new_insights.extend(rule_insights)
            except Exception as e:
                logger.error(f"洞察生成規則執行失敗 ({rule.__name__}): {e}")
        
        # 存儲新洞察
        for insight in new_insights:
            self.insights[insight.insight_id] = insight
        
        # 清理舊洞察
        self._cleanup_old_insights()
        
        logger.info(f"生成了 {len(new_insights)} 個新洞察")
        return new_insights
    
    async def _generate_engagement_insights(self, days: int) -> List[BehaviorInsight]:
        """生成參與度洞察"""
        insights = []
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # 計算平均參與度
        recent_sessions = [
            s for s in self.collector.sessions.values()
            if s.start_time >= cutoff_time
        ]
        
        if not recent_sessions:
            return insights
        
        engagement_scores = [s.calculate_engagement_score() for s in recent_sessions]
        avg_engagement = statistics.mean(engagement_scores)
        
        # 低參與度警告
        if avg_engagement < 0.3:
            insights.append(BehaviorInsight(
                insight_id=f"low_engagement_{datetime.utcnow().date()}",
                title="用戶參與度偏低",
                description=f"最近{days}天的平均用戶參與度為{avg_engagement:.2f}，低於理想水平",
                insight_type="risk",
                priority="high",
                affected_users=len(set(s.user_id for s in recent_sessions)),
                potential_impact="可能導致用戶流失和產品使用率下降",
                recommendations=[
                    "優化用戶界面和體驗",
                    "增加互動功能和遊戲化元素",
                    "個性化內容推薦",
                    "簡化用戶操作流程"
                ],
                data_points={
                    "avg_engagement_score": avg_engagement,
                    "total_sessions": len(recent_sessions),
                    "low_engagement_sessions": sum(1 for s in engagement_scores if s < 0.3)
                },
                confidence_level=0.8
            ))
        
        # 高參與度用戶識別
        elif avg_engagement > 0.7:
            high_engagement_users = set()
            for session in recent_sessions:
                if session.calculate_engagement_score() > 0.7:
                    high_engagement_users.add(session.user_id)
            
            if len(high_engagement_users) > 10:
                insights.append(BehaviorInsight(
                    insight_id=f"high_engagement_opportunity_{datetime.utcnow().date()}",
                    title="高參與度用戶群體識別",
                    description=f"發現{len(high_engagement_users)}個高參與度用戶，平均參與度{avg_engagement:.2f}",
                    insight_type="opportunity",
                    priority="medium",
                    affected_users=len(high_engagement_users),
                    potential_impact="可以作為產品推廣和反饋收集的重點群體",
                    recommendations=[
                        "邀請參與產品測試和反饋",
                        "提供專屬功能或優惠",
                        "鼓勵推薦其他用戶",
                        "收集使用建議和改進意見"
                    ],
                    data_points={
                        "high_engagement_users": len(high_engagement_users),
                        "avg_engagement_score": avg_engagement,
                        "engagement_threshold": 0.7
                    },
                    confidence_level=0.9
                ))
        
        return insights
    
    async def _generate_conversion_insights(self, days: int) -> List[BehaviorInsight]:
        """生成轉換洞察"""
        insights = []
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # 計算轉換相關指標
        recent_actions = [
            a for a in self.collector.actions
            if a.timestamp >= cutoff_time
        ]
        
        conversion_actions = [a for a in recent_actions if a.metadata.get("is_conversion")]
        total_users = len(set(a.user_id for a in recent_actions))
        converting_users = len(set(a.user_id for a in conversion_actions))
        
        if total_users == 0:
            return insights
        
        conversion_rate = converting_users / total_users
        
        # 低轉換率警告
        if conversion_rate < 0.05:  # 5%
            insights.append(BehaviorInsight(
                insight_id=f"low_conversion_{datetime.utcnow().date()}",
                title="轉換率偏低需要關注",
                description=f"最近{days}天的用戶轉換率為{conversion_rate:.2%}，低於行業標準",
                insight_type="risk",
                priority="high",
                affected_users=total_users - converting_users,
                potential_impact="影響業務增長和收入目標",
                recommendations=[
                    "優化轉換漏斗設計",
                    "簡化註冊和購買流程",
                    "增加信任信號和社會證明",
                    "提供限時優惠和激勵",
                    "A/B測試不同的CTA按鈕"
                ],
                data_points={
                    "conversion_rate": conversion_rate,
                    "total_users": total_users,
                    "converting_users": converting_users,
                    "total_conversions": len(conversion_actions)
                },
                confidence_level=0.85
            ))
        
        # 轉換價值分析
        conversion_values = [
            a.metadata.get("conversion_value", 0) 
            for a in conversion_actions 
            if a.metadata.get("conversion_value")
        ]
        
        if conversion_values:
            avg_value = statistics.mean(conversion_values)
            total_value = sum(conversion_values)
            
            insights.append(BehaviorInsight(
                insight_id=f"conversion_value_{datetime.utcnow().date()}",
                title="轉換價值分析",
                description=f"最近{days}天平均轉換價值{avg_value:.2f}，總價值{total_value:.2f}",
                insight_type="trend",
                priority="medium",
                affected_users=converting_users,
                potential_impact=f"當前轉換貢獻總價值{total_value:.2f}",
                recommendations=[
                    "針對高價值用戶提供專屬服務",
                    "分析高價值轉換的共同特徵",
                    "優化低價值轉換的價值提升"
                ],
                data_points={
                    "avg_conversion_value": avg_value,
                    "total_conversion_value": total_value,
                    "high_value_conversions": sum(1 for v in conversion_values if v > avg_value * 1.5)
                },
                confidence_level=0.7
            ))
        
        return insights
    
    async def _generate_retention_insights(self, days: int) -> List[BehaviorInsight]:
        """生成留存洞察"""
        insights = []
        
        # 計算不同時期的用戶留存
        now = datetime.utcnow()
        
        # 7天留存
        week_ago = now - timedelta(days=7)
        users_week_ago = set(
            a.user_ai for a in self.collector.actions
            if week_ago <= a.timestamp < week_ago + timedelta(days=1)
        )
        
        users_still_active = set(
            a.user_id for a in self.collector.actions
            if a.timestamp >= now - timedelta(days=1)
        )
        
        if users_week_ago:
            retention_7d = len(users_week_ago & users_still_active) / len(users_week_ago)
            
            if retention_7d < 0.2:  # 20%
                insights.append(BehaviorInsight(
                    insight_id=f"low_retention_7d_{datetime.utcnow().date()}",
                    title="7天留存率偏低",
                    description=f"7天用戶留存率為{retention_7d:.1%}，需要改善用戶粘性",
                    insight_type="risk",
                    priority="high",
                    affected_users=len(users_week_ago) - len(users_week_ago & users_still_active),
                    potential_impact="新用戶快速流失，影響長期增長",
                    recommendations=[
                        "優化新用戶引導流程",
                        "在關鍵時點發送提醒通知",
                        "提供持續的價值和激勵",
                        "建立用戶習慣養成機制"
                    ],
                    data_points={
                        "retention_7d": retention_7d,
                        "cohort_size": len(users_week_ago),
                        "retained_users": len(users_week_ago & users_still_active)
                    },
                    confidence_level=0.8
                ))
        
        return insights
    
    async def _generate_feature_usage_insights(self, days: int) -> List[BehaviorInsight]:
        """生成功能使用洞察"""
        insights = []
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # 統計功能使用情況
        feature_usage = defaultdict(int)
        feature_users = defaultdict(set)
        
        for action in self.collector.actions:
            if action.timestamp < cutoff_time:
                continue
            
            if action.action_type == ActionType.FEATURE_USE:
                feature_name = action.metadata.get("feature_name", "unknown")
                feature_usage[feature_name] += 1
                feature_users[feature_name].add(action.user_id)
        
        if not feature_usage:
            return insights
        
        total_users = len(set(
            a.user_id for a in self.collector.actions
            if a.timestamp >= cutoff_time
        ))
        
        # 分析功能使用率
        feature_stats = []
        for feature, usage_count in feature_usage.items():
            user_count = len(feature_users[feature])
            usage_rate = user_count / total_users if total_users > 0 else 0
            
            feature_stats.append({
                "feature": feature,
                "usage_count": usage_count,
                "user_count": user_count,
                "usage_rate": usage_rate
            })
        
        # 排序並分析
        feature_stats.sort(key=lambda x: x["usage_rate"], reverse=True)
        
        # 低使用率功能
        low_usage_features = [f for f in feature_stats if f["usage_rate"] < 0.1]  # 10%
        if low_usage_features:
            insights.append(BehaviorInsight(
                insight_id=f"low_feature_usage_{datetime.utcnow().date()}",
                title="部分功能使用率偏低",
                description=f"發現{len(low_usage_features)}個功能使用率低於10%",
                insight_type="opportunity",
                priority="medium",
                affected_users=total_users,
                potential_impact="功能投入未得到充分利用，可能需要優化或推廣",
                recommendations=[
                    "改善功能發現性和入口設計",
                    "提供功能教程和使用指導",
                    "分析功能設計是否符合用戶需求",
                    "考慮功能整合或簡化"
                ],
                data_points={
                    "low_usage_features": [f["feature"] for f in low_usage_features],
                    "avg_usage_rate": statistics.mean([f["usage_rate"] for f in low_usage_features]),
                    "total_features": len(feature_stats)
                },
                confidence_level=0.7
            ))
        
        # 熱門功能
        if feature_stats:
            top_feature = feature_stats[0]
            if top_feature["usage_rate"] > 0.5:  # 50%
                insights.append(BehaviorInsight(
                    insight_id=f"popular_feature_{datetime.utcnow().date()}",
                    title="發現高使用率核心功能",
                    description=f"功能'{top_feature['feature']}'使用率達{top_feature['usage_rate']:.1%}",
                    insight_type="opportunity",
                    priority="medium",
                    affected_users=top_feature["user_count"],
                    potential_impact="核心功能可以作為產品差異化優勢",
                    recommendations=[
                        "進一步優化和增強核心功能",
                        "在營銷中突出展示這一功能",
                        "基於核心功能開發相關功能",
                        "收集用戶對核心功能的深度反饋"
                    ],
                    data_points={
                        "top_feature": top_feature["feature"],
                        "usage_rate": top_feature["usage_rate"],
                        "usage_count": top_feature["usage_count"]
                    },
                    confidence_level=0.9
                ))
        
        return insights
    
    async def _generate_user_segment_insights(self, days: int) -> List[BehaviorInsight]:
        """生成用戶細分洞察"""
        insights = []
        
        # 統計用戶細分分佈
        segment_counts = Counter(
            profile.segment.value for profile in self.collector.user_profiles.values()
        )
        
        total_users = len(self.collector.user_profiles)
        if total_users == 0:
            return insights
        
        # 分析細分分佈
        for segment, count in segment_counts.items():
            ratio = count / total_users
            
            # 新用戶比例過高
            if segment == UserSegment.NEW_USER.value and ratio > 0.6:
                insights.append(BehaviorInsight(
                    insight_id=f"high_new_user_ratio_{datetime.utcnow().date()}",
                    title="新用戶比例較高",
                    description=f"新用戶占比{ratio:.1%}，需要關注用戶激活和留存",
                    insight_type="opportunity",
                    priority="medium",
                    affected_users=count,
                    potential_impact="大量新用戶是增長機會，但需要有效激活",
                    recommendations=[
                        "優化新用戶引導體驗",
                        "設計用戶激活里程碑",
                        "提供新用戶專屬優惠",
                        "建立新用戶社群和支持"
                    ],
                    data_points={
                        "new_user_count": count,
                        "new_user_ratio": ratio,
                        "total_users": total_users
                    },
                    confidence_level=0.8
                ))
            
            # 流失用戶警告
            elif segment == UserSegment.CHURNED_USER.value and ratio > 0.2:
                insights.append(BehaviorInsight(
                    insight_id=f"high_churn_rate_{datetime.utcnow().date()}",
                    title="用戶流失率需要關注",
                    description=f"流失用戶占比{ratio:.1%}，需要實施召回策略",
                    insight_type="risk",
                    priority="high",
                    affected_users=count,
                    potential_impact="高流失率影響用戶基數和業務穩定性",
                    recommendations=[
                        "分析流失用戶的共同特徵",
                        "實施用戶召回活動",
                        "改善產品核心價值傳遞",
                        "建立流失預警機制"
                    ],
                    data_points={
                        "churned_user_count": count,
                        "churn_rate": ratio,
                        "total_users": total_users
                    },
                    confidence_level=0.85
                ))
        
        return insights
    
    async def _generate_performance_insights(self, days: int) -> List[BehaviorInsight]:
        """生成性能洞察"""
        insights = []
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # 分析頁面加載時間
        page_load_times = []
        for action in self.collector.actions:
            if (action.timestamp >= cutoff_time and 
                action.action_type == ActionType.PAGE_VIEW):
                load_time = action.metadata.get("load_time_ms")
                if load_time:
                    page_load_times.append(load_time)
        
        if page_load_times:
            avg_load_time = statistics.mean(page_load_times)
            p95_load_time = sorted(page_load_times)[int(len(page_load_times) * 0.95)] if len(page_load_times) > 1 else page_load_times[0]
            
            # 加載時間過慢警告
            if avg_load_time > 3000:  # 3秒
                insights.append(BehaviorInsight(
                    insight_id=f"slow_page_load_{datetime.utcnow().date()}",
                    title="頁面加載速度需要優化",
                    description=f"平均頁面加載時間{avg_load_time/1000:.1f}秒，P95為{p95_load_time/1000:.1f}秒",
                    insight_type="risk",
                    priority="medium",
                    affected_users=len(set(
                        a.user_id for a in self.collector.actions
                        if a.timestamp >= cutoff_time and a.action_type == ActionType.PAGE_VIEW
                    )),
                    potential_impact="慢加載影響用戶體驗和轉換率",
                    recommendations=[
                        "優化圖片和資源壓縮",
                        "使用CDN加速",
                        "實施延遲加載",
                        "優化服務器響應時間"
                    ],
                    data_points={
                        "avg_load_time_ms": avg_load_time,
                        "p95_load_time_ms": p95_load_time,
                        "slow_loads": sum(1 for t in page_load_times if t > 3000)
                    },
                    confidence_level=0.8
                ))
        
        return insights
    
    async def _generate_trend_insights(self, days: int) -> List[BehaviorInsight]:
        """生成趨勢洞察"""
        insights = []
        
        # 簡化的趋势分析：比較前一周和這一周的指標
        now = datetime.utcnow()
        current_week_start = now - timedelta(days=7)
        previous_week_start = now - timedelta(days=14)
        
        # 當前週活動
        current_week_actions = [
            a for a in self.collector.actions
            if current_week_start <= a.timestamp <= now
        ]
        
        # 前一週活動
        previous_week_actions = [
            a for a in self.collector.actions
            if previous_week_start <= a.timestamp < current_week_start
        ]
        
        if previous_week_actions:
            current_count = len(current_week_actions)
            previous_count = len(previous_week_actions)
            
            if previous_count > 0:
                change_rate = (current_count - previous_count) / previous_count
                
                # 顯著增長
                if change_rate > 0.2:  # 20%增長
                    insights.append(BehaviorInsight(
                        insight_id=f"activity_growth_{datetime.utcnow().date()}",
                        title="用戶活動顯著增長",
                        description=f"本週用戶活動比上週增長{change_rate:.1%}",
                        insight_type="trend",
                        priority="medium",
                        affected_users=len(set(a.user_id for a in current_week_actions)),
                        potential_impact="用戶活躍度提升，是積極的發展趨勢",
                        recommendations=[
                            "分析增長驅動因素並持續優化",
                            "擴大成功策略的應用範圍",
                            "準備應對更高的用戶負載"
                        ],
                        data_points={
                            "current_week_actions": current_count,
                            "previous_week_actions": previous_count,
                            "growth_rate": change_rate
                        },
                        confidence_level=0.7
                    ))
                
                # 顯著下降
                elif change_rate < -0.2:  # 20%下降
                    insights.append(BehaviorInsight(
                        insight_id=f"activity_decline_{datetime.utcnow().date()}",
                        title="用戶活動出現下降",
                        description=f"本週用戶活動比上週下降{abs(change_rate):.1%}",
                        insight_type="risk",
                        priority="high",
                        affected_users=len(set(a.user_id for a in current_week_actions)),
                        potential_impact="用戶活躍度下降可能影響業務指標",
                        recommendations=[
                            "調查活動下降的根本原因",
                            "檢查是否有技術問題或用戶體驗問題",
                            "實施用戶重新激活策略"
                        ],
                        data_points={
                            "current_week_actions": current_count,
                            "previous_week_actions": previous_count,
                            "decline_rate": abs(change_rate)
                        },
                        confidence_level=0.8
                    ))
        
        return insights
    
    async def _generate_anomaly_insights(self, days: int) -> List[BehaviorInsight]:
        """基於異常檢測生成洞察"""
        insights = []
        
        # 調用分析器的異常檢測
        anomalies = await self.analyzer.detect_anomalies(hours=days * 24)
        
        for anomaly in anomalies:
            if anomaly["severity"] in ["high", "critical"]:
                insights.append(BehaviorInsight(
                    insight_id=f"anomaly_{anomaly['type']}_{datetime.utcnow().date()}",
                    title=f"檢測到異常: {anomaly['description']}",
                    description=anomaly["description"],
                    insight_type="anomaly",
                    priority="high" if anomaly["severity"] == "critical" else "medium",
                    affected_users=0,  # 異常檢測通常不直接對應用戶數
                    potential_impact="系統異常可能影響用戶體驗和業務指標",
                    recommendations=[
                        "立即調查異常原因",
                        "檢查系統和服務狀態",
                        "通知相關技術團隊"
                    ],
                    data_points={
                        "anomaly_type": anomaly["type"],
                        "current_value": anomaly["current_value"],
                        "historical_value": anomaly["historical_value"],
                        "detected_at": anomaly["detected_at"]
                    },
                    confidence_level=0.9
                ))
        
        return insights
    
    def _cleanup_old_insights(self):
        """清理舊洞察"""
        cutoff_time = datetime.utcnow() - timedelta(days=self.config["insight_retention_days"])
        
        old_insights = [
            insight_id for insight_id, insight in self.insights.items()
            if insight.created_at < cutoff_time
        ]
        
        for insight_id in old_insights:
            del self.insights[insight_id]
        
        if old_insights:
            logger.info(f"清理了 {len(old_insights)} 個舊洞察")
    
    def _calculate_priority(self, impact: float, confidence: float) -> str:
        """根據影響和置信度計算優先級"""
        score = (impact + confidence) / 2
        
        if score >= self.config["priority_thresholds"]["high"]:
            return "high"
        elif score >= self.config["priority_thresholds"]["medium"]:
            return "medium"
        else:
            return "low"
    
    async def get_insights(self, 
                         insight_type: Optional[str] = None,
                         priority: Optional[str] = None,
                         limit: int = 20) -> List[BehaviorInsight]:
        """獲取洞察"""
        insights = list(self.insights.values())
        
        # 過濾條件
        if insight_type:
            insights = [i for i in insights if i.insight_type == insight_type]
        
        if priority:
            insights = [i for i in insights if i.priority == priority]
        
        # 按創建時間排序
        insights.sort(key=lambda x: x.created_at, reverse=True)
        
        return insights[:limit]
    
    async def get_insight_summary(self) -> Dict[str, Any]:
        """獲取洞察摘要"""
        insights = list(self.insights.values())
        
        # 按類型統計
        type_counts = Counter(i.insight_type for i in insights)
        priority_counts = Counter(i.priority for i in insights)
        
        # 最新洞察
        recent_insights = sorted(insights, key=lambda x: x.created_at, reverse=True)[:5]
        
        return {
            "total_insights": len(insights),
            "by_type": dict(type_counts),
            "by_priority": dict(priority_counts),
            "recent_insights": [
                {
                    "title": i.title,
                    "type": i.insight_type,
                    "priority": i.priority,
                    "created_at": i.created_at.isoformat()
                }
                for i in recent_insights
            ],
            "summary_generated_at": datetime.utcnow().isoformat()
        }
    
    def mark_insight_as_implemented(self, insight_id: str):
        """標記洞察為已實施"""
        if insight_id in self.insights:
            self.insights[insight_id].status = "implemented"
            logger.info(f"洞察 {insight_id} 已標記為已實施")
    
    def dismiss_insight(self, insight_id: str):
        """忽略洞察"""
        if insight_id in self.insights:
            self.insights[insight_id].status = "dismissed"
            logger.info(f"洞察 {insight_id} 已忽略")
    
    def get_insight_stats(self) -> Dict[str, Any]:
        """獲取洞察統計"""
        return {
            "total_insights": len(self.insights),
            "active_insights": sum(1 for i in self.insights.values() if i.status == "active"),
            "implemented_insights": sum(1 for i in self.insights.values() if i.status == "implemented"),
            "dismissed_insights": sum(1 for i in self.insights.values() if i.status == "dismissed"),
            "avg_confidence": statistics.mean([i.confidence_level for i in self.insights.values()]) if self.insights else 0,
            "config": self.config
        }


# 全域洞察生成器實例
insight_generator = None

def init_insight_generator(collector: BehaviorCollector, 
                          analyzer: BehaviorAnalyzer,
                          pattern_detector: PatternDetector):
    """初始化全域洞察生成器"""
    global insight_generator
    insight_generator = InsightGenerator(collector, analyzer, pattern_detector)