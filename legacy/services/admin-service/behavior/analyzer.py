"""
用戶行為分析器

提供深度的用戶行為分析、模式識別和商業洞察功能。
"""

import logging
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np

from .collector import BehaviorCollector
from .models import (
    ActionType,
    BehaviorSession,
    UserAction,
    UserProfile,
    UserSegment,
)

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """分析結果"""

    analysis_type: str
    timestamp: datetime
    summary: str
    details: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    confidence_score: float
    data_points: int


class BehaviorAnalyzer:
    """用戶行為分析器"""

    def __init__(self, collector: BehaviorCollector):
        """
        初始化行為分析器

        Args:
            collector: 行為收集器
        """
        self.collector = collector

        # 分析緩存
        self.analysis_cache = {}
        self.cache_ttl = 300  # 5分鐘緩存

        # 分析配置
        self.config = {
            "min_sessions_for_pattern": 5,
            "min_users_for_cohort": 10,
            "conversion_window_hours": 24,
            "engagement_threshold": 0.6,
        }

    async def analyze_user_behavior(self, user_id: str, days: int = 30) -> AnalysisResult:
        """分析用戶行為"""
        cache_key = f"user_behavior:{user_id}:{days}"

        # 檢查緩存
        if self._is_cache_valid(cache_key):
            return self.analysis_cache[cache_key]["result"]

        start_date = datetime.utcnow() - timedelta(days=days)

        # 獲取用戶數據
        sessions = await self.collector.get_user_sessions(user_id, limit=100, start_date=start_date)
        actions = await self.collector.get_user_actions(user_id, limit=1000, start_date=start_date)
        profile = self.collector.user_profiles.get(user_id)

        if not profile or not sessions:
            return AnalysisResult(
                analysis_type="user_behavior",
                timestamp=datetime.utcnow(),
                summary="用戶數據不足",
                details={},
                insights=[],
                recommendations=[],
                confidence_score=0.0,
                data_points=0,
            )

        # 計算行為指標
        metrics = self._calculate_user_metrics(sessions, actions, profile)

        # 生成洞察
        insights = self._generate_user_insights(metrics, profile)

        # 生成建議
        recommendations = self._generate_user_recommendations(metrics, profile)

        result = AnalysisResult(
            analysis_type="user_behavior",
            timestamp=datetime.utcnow(),
            summary=f"用戶 {user_id} 的行為分析：{len(sessions)} 次會話，{len(actions)} 個動作",
            details=metrics,
            insights=insights,
            recommendations=recommendations,
            confidence_score=min(len(sessions) / 10.0, 1.0),  # 基於會話數量計算置信度
            data_points=len(actions),
        )

        # 緩存結果
        self._cache_result(cache_key, result)

        return result

    def _calculate_user_metrics(
        self, sessions: List[BehaviorSession], actions: List[UserAction], profile: UserProfile
    ) -> Dict[str, Any]:
        """計算用戶指標"""
        if not sessions:
            return {}

        # 基本指標
        total_sessions = len(sessions)
        total_actions = len(actions)

        # 時間指標
        session_durations = [s.duration_seconds for s in sessions if s.duration_seconds]
        avg_session_duration = statistics.mean(session_durations) if session_durations else 0

        # 頁面指標
        unique_pages = set()
        page_views = []
        for session in sessions:
            page_views.extend(session.get_page_views())
            unique_pages.update(session.get_unique_pages())

        # 設備指標
        device_types = Counter(s.device_type.value for s in sessions)

        # 時間模式分析
        hour_distribution = Counter(s.start_time.hour for s in sessions)
        day_distribution = Counter(s.start_time.weekday() for s in sessions)

        # 參與度指標
        engagement_scores = [s.calculate_engagement_score() for s in sessions]
        avg_engagement = statistics.mean(engagement_scores) if engagement_scores else 0

        # 轉換指標
        conversion_actions = [a for a in actions if a.metadata.get("is_conversion")]
        conversion_rate = len(conversion_actions) / total_actions if total_actions > 0 else 0

        # 留存指標
        first_session = min(sessions, key=lambda s: s.start_time)
        last_session = max(sessions, key=lambda s: s.start_time)
        user_lifespan_days = (last_session.start_time - first_session.start_time).days

        # 活躍度指標
        active_days = len(set(s.start_time.date() for s in sessions))

        return {
            "basic_metrics": {
                "total_sessions": total_sessions,
                "total_actions": total_actions,
                "avg_actions_per_session": total_actions / total_sessions,
                "unique_pages_visited": len(unique_pages),
                "total_page_views": len(page_views),
            },
            "time_metrics": {
                "avg_session_duration_seconds": round(avg_session_duration, 2),
                "total_time_spent_seconds": sum(session_durations),
                "user_lifespan_days": user_lifespan_days,
                "active_days": active_days,
                "activity_ratio": round(active_days / max(user_lifespan_days, 1), 2),
            },
            "engagement_metrics": {
                "avg_engagement_score": round(avg_engagement, 2),
                "high_engagement_sessions": sum(1 for s in engagement_scores if s > 0.7),
                "low_engagement_sessions": sum(1 for s in engagement_scores if s < 0.3),
            },
            "conversion_metrics": {
                "conversion_actions": len(conversion_actions),
                "conversion_rate": round(conversion_rate, 4),
                "conversion_value": sum(
                    a.metadata.get("conversion_value", 0) for a in conversion_actions
                ),
            },
            "device_metrics": dict(device_types),
            "temporal_patterns": {
                "hour_distribution": dict(hour_distribution),
                "day_distribution": dict(day_distribution),
                "most_active_hour": (
                    hour_distribution.most_common(1)[0][0] if hour_distribution else None
                ),
                "most_active_day": (
                    day_distribution.most_common(1)[0][0] if day_distribution else None
                ),
            },
            "user_segment": profile.segment.value,
            "churn_probability": profile.churn_probability,
            "ltv_score": profile.ltv_score,
        }

    def _generate_user_insights(self, metrics: Dict[str, Any], profile: UserProfile) -> List[str]:
        """生成用戶洞察"""
        insights = []

        metrics.get("basic_metrics", {})
        time_metrics = metrics.get("time_metrics", {})
        engagement = metrics.get("engagement_metrics", {})
        temporal = metrics.get("temporal_patterns", {})

        # 參與度洞察
        avg_engagement = engagement.get("avg_engagement_score", 0)
        if avg_engagement > 0.7:
            insights.append("用戶參與度很高，是高價值用戶")
        elif avg_engagement < 0.3:
            insights.append("用戶參與度較低，可能存在流失風險")

        # 會話頻率洞察
        activity_ratio = time_metrics.get("activity_ratio", 0)
        if activity_ratio > 0.5:
            insights.append("用戶活躍度很高，經常使用系統")
        elif activity_ratio < 0.1:
            insights.append("用戶使用頻率較低，需要激活策略")

        # 時間模式洞察
        most_active_hour = temporal.get("most_active_hour")
        if most_active_hour is not None:
            if 9 <= most_active_hour <= 17:
                insights.append("用戶主要在工作時間使用系統")
            elif 18 <= most_active_hour <= 22:
                insights.append("用戶主要在晚間使用系統")

        # 轉換洞察
        conversion_rate = metrics.get("conversion_metrics", {}).get("conversion_rate", 0)
        if conversion_rate > 0.1:
            insights.append("用戶轉換率較高，對產品價值認知良好")
        elif conversion_rate == 0:
            insights.append("用戶尚未產生轉換，需要引導")

        # 用戶細分洞察
        if profile.segment == UserSegment.POWER_USER:
            insights.append("高級用戶，是產品推廣的重要支持者")
        elif profile.segment == UserSegment.NEW_USER:
            insights.append("新用戶，正在探索產品功能")
        elif profile.segment == UserSegment.CHURNED_USER:
            insights.append("流失用戶，需要召回策略")

        return insights

    def _generate_user_recommendations(
        self, metrics: Dict[str, Any], profile: UserProfile
    ) -> List[str]:
        """生成用戶建議"""
        recommendations = []

        engagement = metrics.get("engagement_metrics", {})
        conversion = metrics.get("conversion_metrics", {})

        # 基於參與度的建議
        avg_engagement = engagement.get("avg_engagement_score", 0)
        if avg_engagement < 0.3:
            recommendations.extend(
                ["發送個性化內容提升參與度", "提供新手引導和幫助文檔", "簡化用戶界面和操作流程"]
            )
        elif avg_engagement > 0.7:
            recommendations.extend(
                ["邀請用戶參與高級功能測試", "推薦相關高價值功能", "考慮升級為付費用戶"]
            )

        # 基於轉換的建議
        conversion_rate = conversion.get("conversion_rate", 0)
        if conversion_rate == 0:
            recommendations.extend(
                ["設計轉換引導流程", "提供免費試用或體驗機會", "發送相關案例和成功故事"]
            )

        # 基於用戶細分的建議
        if profile.segment == UserSegment.NEW_USER:
            recommendations.extend(["提供新用戶歡迎流程", "推送基礎功能教程", "設置30天激活計劃"])
        elif profile.segment == UserSegment.CHURNED_USER:
            recommendations.extend(["發送召回郵件和優惠", "了解流失原因並改進", "提供重新激活獎勵"])

        return recommendations

    async def analyze_cohort_behavior(self, cohort_name: str, days: int = 30) -> AnalysisResult:
        """分析用戶群組行為"""
        cache_key = f"cohort_behavior:{cohort_name}:{days}"

        if self._is_cache_valid(cache_key):
            return self.analysis_cache[cache_key]["result"]

        # 這裡需要從追蹤器獲取分群數據
        # 簡化實現，返回基本結果
        result = AnalysisResult(
            analysis_type="cohort_behavior",
            timestamp=datetime.utcnow(),
            summary=f"分群 {cohort_name} 的行為分析",
            details={},
            insights=[],
            recommendations=[],
            confidence_score=0.5,
            data_points=0,
        )

        self._cache_result(cache_key, result)
        return result

    async def analyze_funnel_performance(
        self, funnel_steps: List[Dict[str, Any]], time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """分析轉換漏斗性能"""
        # 獲取漏斗數據
        funnel_data = await self.collector.get_conversion_funnel(
            funnel_steps=funnel_steps, time_window_hours=time_window_hours
        )

        # 計算漏斗指標
        conversions = funnel_data.get("conversions", [])
        total_users = funnel_data.get("total_users", 0)

        if not conversions or total_users == 0:
            return {"status": "insufficient_data", "message": "轉換漏斗數據不足"}

        # 計算各步驟的流失率
        drop_off_analysis = []
        for i in range(len(conversions) - 1):
            current_step = conversions[i]
            next_step = conversions[i + 1]

            drop_off_rate = (
                1 - (next_step["users"] / current_step["users"]) if current_step["users"] > 0 else 0
            )
            drop_off_users = current_step["users"] - next_step["users"]

            drop_off_analysis.append(
                {
                    "from_step": current_step["step_name"],
                    "to_step": next_step["step_name"],
                    "drop_off_rate": round(drop_off_rate, 4),
                    "drop_off_users": drop_off_users,
                    "severity": (
                        "high"
                        if drop_off_rate > 0.5
                        else "medium" if drop_off_rate > 0.3 else "low"
                    ),
                }
            )

        # 生成漏斗洞察
        insights = []
        recommendations = []

        # 找出最大流失點
        max_drop_off = (
            max(drop_off_analysis, key=lambda x: x["drop_off_rate"]) if drop_off_analysis else None
        )
        if max_drop_off:
            insights.append(
                f"最大流失點在 {max_drop_off['from_step']} 到 {max_drop_off['to_step']}"
            )
            recommendations.append(f"優化 {max_drop_off['to_step']} 的用戶體驗")

        # 整體轉換率分析
        overall_rate = funnel_data.get("overall_conversion_rate", 0)
        if overall_rate < 0.1:
            insights.append("整體轉換率較低，需要全面優化")
            recommendations.extend(["檢查漏斗設計是否合理", "簡化轉換流程", "提升每一步的價值傳遞"])
        elif overall_rate > 0.3:
            insights.append("轉換漏斗表現良好")
            recommendations.append("維持當前策略並尋找進一步優化空間")

        return {
            "funnel_data": funnel_data,
            "drop_off_analysis": drop_off_analysis,
            "performance_metrics": {
                "total_users": total_users,
                "overall_conversion_rate": overall_rate,
                "avg_drop_off_rate": (
                    statistics.mean([d["drop_off_rate"] for d in drop_off_analysis])
                    if drop_off_analysis
                    else 0
                ),
            },
            "insights": insights,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    async def analyze_page_performance(
        self, page_url: Optional[str] = None, hours: int = 24
    ) -> Dict[str, Any]:
        """分析頁面性能"""
        page_views = await self.collector.get_page_views(hours=hours, page_url=page_url)

        if not page_views:
            return {"status": "no_data", "message": "指定時間範圍內沒有頁面瀏覽數據"}

        # 按頁面分組分析
        page_stats = defaultdict(
            lambda: {
                "total_views": 0,
                "unique_users": set(),
                "bounce_count": 0,
                "total_time_spent": 0,
                "load_times": [],
            }
        )

        for view in page_views:
            url = view.page_url
            if not url:
                continue

            page_stats[url]["total_views"] += 1
            page_stats[url]["unique_users"].add(view.user_id)

            # 檢查是否是跳出（單頁面會話）
            user_session_actions = [
                a
                for a in self.collector.actions
                if a.session_id == view.session_id and a.action_type == ActionType.PAGE_VIEW
            ]
            if len(user_session_actions) == 1:
                page_stats[url]["bounce_count"] += 1

            # 獲取頁面停留時間和加載時間
            if view.duration_ms:
                page_stats[url]["total_time_spent"] += view.duration_ms

            load_time = view.metadata.get("load_time_ms")
            if load_time:
                page_stats[url]["load_times"].append(load_time)

        # 計算頁面指標
        page_analysis = {}
        for url, stats in page_stats.items():
            unique_users_count = len(stats["unique_users"])

            analysis = {
                "url": url,
                "total_views": stats["total_views"],
                "unique_users": unique_users_count,
                "avg_views_per_user": (
                    round(stats["total_views"] / unique_users_count, 2)
                    if unique_users_count > 0
                    else 0
                ),
                "bounce_rate": (
                    round(stats["bounce_count"] / stats["total_views"], 2)
                    if stats["total_views"] > 0
                    else 0
                ),
                "avg_time_on_page_seconds": (
                    round(stats["total_time_spent"] / stats["total_views"] / 1000, 2)
                    if stats["total_views"] > 0
                    else 0
                ),
            }

            if stats["load_times"]:
                analysis["avg_load_time_ms"] = round(statistics.mean(stats["load_times"]), 2)
                analysis["p95_load_time_ms"] = (
                    np.percentile(stats["load_times"], 95)
                    if len(stats["load_times"]) > 1
                    else stats["load_times"][0]
                )

            page_analysis[url] = analysis

        # 排序並生成洞察
        sorted_pages = sorted(page_analysis.values(), key=lambda x: x["total_views"], reverse=True)

        insights = []
        recommendations = []

        if sorted_pages:
            top_page = sorted_pages[0]
            insights.append(
                f"最受歡迎的頁面是 {top_page['url']}，共 {top_page['total_views']} 次瀏覽"
            )

            # 跳出率分析
            high_bounce_pages = [p for p in sorted_pages if p["bounce_rate"] > 0.7]
            if high_bounce_pages:
                insights.append(f"發現 {len(high_bounce_pages)} 個高跳出率頁面")
                recommendations.extend(
                    ["優化高跳出率頁面的內容和設計", "增加相關內容推薦", "改善頁面加載速度"]
                )

            # 加載時間分析
            slow_pages = [p for p in sorted_pages if p.get("avg_load_time_ms", 0) > 3000]  # 3秒
            if slow_pages:
                insights.append(f"發現 {len(slow_pages)} 個加載較慢的頁面")
                recommendations.extend(["優化頁面資源加載", "使用CDN加速", "壓縮圖片和資源文件"])

        return {
            "page_analysis": sorted_pages[:20],  # 返回前20個頁面
            "summary": {
                "total_pages_analyzed": len(page_analysis),
                "total_page_views": sum(p["total_views"] for p in page_analysis.values()),
                "avg_bounce_rate": (
                    round(statistics.mean([p["bounce_rate"] for p in page_analysis.values()]), 2)
                    if page_analysis
                    else 0
                ),
            },
            "insights": insights,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    async def detect_anomalies(self, hours: int = 24) -> List[Dict[str, Any]]:
        """檢測行為異常"""
        anomalies = []

        current_time = datetime.utcnow()
        start_time = current_time - timedelta(hours=hours)

        # 獲取當前和歷史數據進行比較
        current_period_actions = [a for a in self.collector.actions if a.timestamp >= start_time]

        # 比較同期歷史數據（前一天或前一週的同一時段）
        historical_start = start_time - timedelta(days=7)
        historical_end = historical_start + timedelta(hours=hours)

        historical_actions = [
            a for a in self.collector.actions if historical_start <= a.timestamp <= historical_end
        ]

        # 檢測流量異常
        current_traffic = len(current_period_actions)
        historical_traffic = len(historical_actions)

        if historical_traffic > 0:
            traffic_change = (current_traffic - historical_traffic) / historical_traffic

            if abs(traffic_change) > 0.5:  # 50%變化
                anomalies.append(
                    {
                        "type": "traffic_anomaly",
                        "severity": "high" if abs(traffic_change) > 0.8 else "medium",
                        "description": f"流量異常：變化 {traffic_change:.1%}",
                        "current_value": current_traffic,
                        "historical_value": historical_traffic,
                        "detected_at": current_time.isoformat(),
                    }
                )

        # 檢測錯誤率異常
        current_errors = len(
            [a for a in current_period_actions if a.action_type == ActionType.ERROR]
        )
        historical_errors = len(
            [a for a in historical_actions if a.action_type == ActionType.ERROR]
        )

        current_error_rate = current_errors / max(current_traffic, 1)
        historical_error_rate = historical_errors / max(historical_traffic, 1)

        if (
            current_error_rate > historical_error_rate * 2 and current_error_rate > 0.05
        ):  # 錯誤率翻倍且超過5%
            anomalies.append(
                {
                    "type": "error_rate_anomaly",
                    "severity": "critical",
                    "description": f"錯誤率異常：當前 {current_error_rate:.2%}，歷史 {historical_error_rate:.2%}",
                    "current_value": current_error_rate,
                    "historical_value": historical_error_rate,
                    "detected_at": current_time.isoformat(),
                }
            )

        # 檢測用戶行為異常
        current_users = len(set(a.user_id for a in current_period_actions))
        historical_users = len(set(a.user_id for a in historical_actions))

        if historical_users > 0:
            user_change = (current_users - historical_users) / historical_users

            if user_change < -0.3:  # 用戶數下降30%
                anomalies.append(
                    {
                        "type": "user_drop_anomaly",
                        "severity": "medium",
                        "description": f"活躍用戶數異常下降：{user_change:.1%}",
                        "current_value": current_users,
                        "historical_value": historical_users,
                        "detected_at": current_time.isoformat(),
                    }
                )

        return anomalies

    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查緩存是否有效"""
        if cache_key not in self.analysis_cache:
            return False

        cache_time = self.analysis_cache[cache_key]["timestamp"]
        return (datetime.utcnow() - cache_time).seconds < self.cache_ttl

    def _cache_result(self, cache_key: str, result: AnalysisResult):
        """緩存分析結果"""
        self.analysis_cache[cache_key] = {"result": result, "timestamp": datetime.utcnow()}

    def clear_cache(self):
        """清空緩存"""
        self.analysis_cache.clear()

    def get_analysis_stats(self) -> Dict[str, Any]:
        """獲取分析統計"""
        return {
            "cache_size": len(self.analysis_cache),
            "cache_ttl_seconds": self.cache_ttl,
            "total_users": len(self.collector.user_profiles),
            "total_sessions": len(self.collector.sessions),
            "total_actions": len(self.collector.actions),
        }


# 全域行為分析器實例
behavior_analyzer = None


def init_behavior_analyzer(collector: BehaviorCollector):
    """初始化全域行為分析器"""
    global behavior_analyzer
    behavior_analyzer = BehaviorAnalyzer(collector)
