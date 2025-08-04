"""
用戶行為追蹤器

提供高級的用戶行為追蹤和實時分析功能。
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict, deque
import statistics

from .collector import BehaviorCollector
from .models import UserAction, BehaviorSession, UserProfile, ActionType, UserSegment

logger = logging.getLogger(__name__)


class BehaviorTracker:
    """用戶行為追蹤器"""
    
    def __init__(self, collector: BehaviorCollector):
        """
        初始化行為追蹤器
        
        Args:
            collector: 行為收集器
        """
        self.collector = collector
        
        # 實時事件監聽器
        self.event_listeners: Dict[str, List[Callable]] = defaultdict(list)
        
        # 實時統計
        self.real_time_stats = {
            "page_views_per_minute": deque(maxlen=60),
            "unique_visitors_per_hour": deque(maxlen=24),
            "bounce_rate_per_hour": deque(maxlen=24),
            "conversion_events": deque(maxlen=1000)
        }
        
        # 熱圖數據
        self.heatmap_data = defaultdict(list)  # page_url -> [{"x": 100, "y": 200, "count": 5}]
        
        # A/B 測試數據
        self.ab_tests = {}  # test_id -> test_config
        self.ab_results = defaultdict(lambda: defaultdict(list))  # test_id -> variant -> [results]
        
        # 用戶分群
        self.user_cohorts = defaultdict(set)  # cohort_name -> {user_ids}
        
        # 預警規則
        self.alert_rules = []
        
        # 啟動實時處理任務
        self._real_time_task = asyncio.create_task(self._real_time_processing_loop())
    
    async def track_action(self, 
                         user_id: str,
                         action_type: str,
                         page_url: Optional[str] = None,
                         element_id: Optional[str] = None,
                         element_text: Optional[str] = None,
                         coordinates: Optional[Dict[str, int]] = None,
                         duration_ms: Optional[int] = None,
                         metadata: Optional[Dict[str, Any]] = None,
                         context: Optional[Dict[str, Any]] = None,
                         request_info: Optional[Dict[str, Any]] = None) -> UserAction:
        """
        追蹤用戶動作
        
        Args:
            user_id: 用戶ID
            action_type: 動作類型
            page_url: 頁面URL
            element_id: 元素ID
            element_text: 元素文本
            coordinates: 坐標
            duration_ms: 持續時間
            metadata: 元數據
            context: 上下文
            request_info: 請求信息
            
        Returns:
            創建的用戶動作
        """
        # 收集動作
        action = await self.collector.collect_action(
            user_id=user_id,
            action_type=action_type,
            page_url=page_url,
            element_id=element_id,
            element_text=element_text,
            coordinates=coordinates,
            duration_ms=duration_ms,
            metadata=metadata,
            context=context,
            request_info=request_info
        )
        
        if action:
            # 觸發事件監聽器
            await self._trigger_event_listeners(action)
            
            # 更新熱圖數據
            self._update_heatmap_data(action)
            
            # 處理 A/B 測試
            await self._process_ab_test(action)
            
            # 檢查預警規則
            await self._check_alert_rules(action)
        
        return action
    
    async def track_page_view(self,
                            user_id: str,
                            page_url: str,
                            page_title: Optional[str] = None,
                            referrer: Optional[str] = None,
                            load_time_ms: Optional[int] = None,
                            request_info: Optional[Dict[str, Any]] = None) -> UserAction:
        """追蹤頁面瀏覽"""
        metadata = {}
        if page_title:
            metadata["page_title"] = page_title
        if referrer:
            metadata["referrer"] = referrer
        if load_time_ms:
            metadata["load_time_ms"] = load_time_ms
        
        return await self.track_action(
            user_id=user_id,
            action_type=ActionType.PAGE_VIEW.value,
            page_url=page_url,
            metadata=metadata,
            request_info=request_info
        )
    
    async def track_click(self,
                        user_id: str,
                        page_url: str,
                        element_id: Optional[str] = None,
                        element_text: Optional[str] = None,
                        coordinates: Optional[Dict[str, int]] = None,
                        request_info: Optional[Dict[str, Any]] = None) -> UserAction:
        """追蹤點擊事件"""
        return await self.track_action(
            user_id=user_id,
            action_type=ActionType.CLICK.value,
            page_url=page_url,
            element_id=element_id,
            element_text=element_text,
            coordinates=coordinates,
            request_info=request_info
        )
    
    async def track_form_submit(self,
                              user_id: str,
                              page_url: str,
                              form_id: Optional[str] = None,
                              form_data: Optional[Dict[str, Any]] = None,
                              validation_errors: Optional[List[str]] = None,
                              request_info: Optional[Dict[str, Any]] = None) -> UserAction:
        """追蹤表單提交"""
        metadata = {}
        if form_data:
            # 不記錄敏感數據，只記錄字段名稱
            metadata["form_fields"] = list(form_data.keys())
        if validation_errors:
            metadata["validation_errors"] = validation_errors
        
        return await self.track_action(
            user_id=user_id,
            action_type=ActionType.FORM_SUBMIT.value,
            page_url=page_url,
            element_id=form_id,
            metadata=metadata,
            request_info=request_info
        )
    
    async def track_search(self,
                         user_id: str,
                         query: str,
                         results_count: Optional[int] = None,
                         page_url: Optional[str] = None,
                         request_info: Optional[Dict[str, Any]] = None) -> UserAction:
        """追蹤搜索事件"""
        metadata = {
            "query": query,
            "query_length": len(query)
        }
        if results_count is not None:
            metadata["results_count"] = results_count
        
        return await self.track_action(
            user_id=user_id,
            action_type=ActionType.SEARCH.value,
            page_url=page_url,
            metadata=metadata,
            request_info=request_info
        )
    
    async def track_conversion(self,
                             user_id: str,
                             conversion_type: str,
                             conversion_value: Optional[float] = None,
                             page_url: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None,
                             request_info: Optional[Dict[str, Any]] = None) -> UserAction:
        """追蹤轉換事件"""
        conversion_metadata = metadata or {}
        conversion_metadata.update({
            "conversion_type": conversion_type,
            "is_conversion": True
        })
        
        if conversion_value is not None:
            conversion_metadata["conversion_value"] = conversion_value
        
        action = await self.track_action(
            user_id=user_id,
            action_type=ActionType.FEATURE_USE.value,
            page_url=page_url,
            metadata=conversion_metadata,
            request_info=request_info
        )
        
        # 記錄轉換事件到實時統計
        if action:
            self.real_time_stats["conversion_events"].append({
                "timestamp": action.timestamp,
                "user_id": user_id,
                "conversion_type": conversion_type,
                "conversion_value": conversion_value
            })
        
        return action
    
    def add_event_listener(self, event_type: str, callback: Callable):
        """添加事件監聽器"""
        self.event_listeners[event_type].append(callback)
    
    def remove_event_listener(self, event_type: str, callback: Callable):
        """移除事件監聽器"""
        if callback in self.event_listeners[event_type]:
            self.event_listeners[event_type].remove(callback)
    
    async def _trigger_event_listeners(self, action: UserAction):
        """觸發事件監聽器"""
        event_type = action.action_type.value
        
        # 觸發特定動作類型的監聽器
        for callback in self.event_listeners.get(event_type, []):
            try:
                await callback(action)
            except Exception as e:
                logger.error(f"事件監聽器執行失敗 ({event_type}): {e}")
        
        # 觸發通用監聽器
        for callback in self.event_listeners.get("*", []):
            try:
                await callback(action)
            except Exception as e:
                logger.error(f"通用事件監聽器執行失敗: {e}")
    
    def _update_heatmap_data(self, action: UserAction):
        """更新熱圖數據"""
        if action.coordinates and action.page_url:
            x, y = action.coordinates.get("x", 0), action.coordinates.get("y", 0)
            
            # 找到相同位置的點或創建新點
            page_heatmap = self.heatmap_data[action.page_url]
            
            for point in page_heatmap:
                if abs(point["x"] - x) <= 10 and abs(point["y"] - y) <= 10:  # 10px 容差
                    point["count"] += 1
                    return
            
            # 新位置
            page_heatmap.append({"x": x, "y": y, "count": 1, "action_type": action.action_type.value})
    
    async def get_heatmap_data(self, page_url: str, hours: int = 24) -> List[Dict[str, Any]]:
        """獲取熱圖數據"""
        return self.heatmap_data.get(page_url, [])
    
    def create_ab_test(self,
                      test_id: str,
                      test_name: str,
                      variants: List[str],
                      traffic_allocation: Dict[str, float],
                      success_metrics: List[str],
                      description: Optional[str] = None):
        """創建 A/B 測試"""
        self.ab_tests[test_id] = {
            "test_name": test_name,
            "variants": variants,
            "traffic_allocation": traffic_allocation,
            "success_metrics": success_metrics,
            "description": description,
            "created_at": datetime.utcnow(),
            "status": "active"
        }
        
        logger.info(f"創建 A/B 測試: {test_name} ({test_id})")
    
    def assign_user_to_variant(self, test_id: str, user_id: str) -> Optional[str]:
        """將用戶分配到 A/B 測試變體"""
        if test_id not in self.ab_tests:
            return None
        
        test_config = self.ab_tests[test_id]
        
        # 簡單的哈希分配算法
        user_hash = hash(f"{test_id}:{user_id}") % 100
        cumulative_prob = 0
        
        for variant, allocation in test_config["traffic_allocation"].items():
            cumulative_prob += allocation * 100
            if user_hash < cumulative_prob:
                return variant
        
        return test_config["variants"][0]  # 默認第一個變體
    
    async def _process_ab_test(self, action: UserAction):
        """處理 A/B 測試數據"""
        for test_id, test_config in self.ab_tests.items():
            if test_config["status"] != "active":
                continue
            
            # 檢查是否是成功指標
            for metric in test_config["success_metrics"]:
                if self._action_matches_metric(action, metric):
                    variant = self.assign_user_to_variant(test_id, action.user_id)
                    if variant:
                        self.ab_results[test_id][variant].append({
                            "user_id": action.user_id,
                            "timestamp": action.timestamp,
                            "metric": metric,
                            "value": action.metadata.get("conversion_value", 1)
                        })
    
    def _action_matches_metric(self, action: UserAction, metric: str) -> bool:
        """檢查動作是否匹配成功指標"""
        if metric == "page_view":
            return action.action_type == ActionType.PAGE_VIEW
        elif metric == "click":
            return action.action_type == ActionType.CLICK
        elif metric == "conversion":
            return action.metadata.get("is_conversion", False)
        elif metric == "form_submit":
            return action.action_type == ActionType.FORM_SUBMIT
        
        return False
    
    async def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """獲取 A/B 測試結果"""
        if test_id not in self.ab_tests:
            return {}
        
        test_config = self.ab_tests[test_id]
        results = self.ab_results[test_id]
        
        variant_stats = {}
        for variant in test_config["variants"]:
            variant_data = results.get(variant, [])
            
            variant_stats[variant] = {
                "total_events": len(variant_data),
                "unique_users": len(set(d["user_id"] for d in variant_data)),
                "total_value": sum(d["value"] for d in variant_data),
                "avg_value": statistics.mean([d["value"] for d in variant_data]) if variant_data else 0
            }
        
        return {
            "test_config": test_config,
            "variant_stats": variant_stats,
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    def create_user_cohort(self, cohort_name: str, user_ids: List[str]):
        """創建用戶分群"""
        self.user_cohorts[cohort_name] = set(user_ids)
        logger.info(f"創建用戶分群: {cohort_name} ({len(user_ids)} 用戶)")
    
    async def get_cohort_analysis(self, cohort_name: str, days: int = 30) -> Dict[str, Any]:
        """獲取分群分析"""
        if cohort_name not in self.user_cohorts:
            return {}
        
        cohort_users = self.user_cohorts[cohort_name]
        start_date = datetime.utcnow() - timedelta(days=days)
        
        cohort_stats = {
            "total_users": len(cohort_users),
            "active_users": 0,
            "total_actions": 0,
            "avg_actions_per_user": 0,
            "retention_rates": {},
            "top_pages": defaultdict(int),
            "conversion_rate": 0
        }
        
        # 計算分群統計
        user_actions = defaultdict(list)
        conversions = 0
        
        for action in self.collector.actions:
            if action.user_id in cohort_users and action.timestamp >= start_date:
                user_actions[action.user_id].append(action)
                cohort_stats["total_actions"] += 1
                
                if action.page_url:
                    cohort_stats["top_pages"][action.page_url] += 1
                
                if action.metadata.get("is_conversion"):
                    conversions += 1
        
        cohort_stats["active_users"] = len(user_actions)
        if cohort_stats["active_users"] > 0:
            cohort_stats["avg_actions_per_user"] = cohort_stats["total_actions"] / cohort_stats["active_users"]
            cohort_stats["conversion_rate"] = conversions / cohort_stats["active_users"]
        
        # 轉換為列表並排序
        cohort_stats["top_pages"] = sorted(
            [{"page": page, "views": count} for page, count in cohort_stats["top_pages"].items()],
            key=lambda x: x["views"],
            reverse=True
        )[:10]
        
        return cohort_stats
    
    def add_alert_rule(self, 
                      rule_name: str,
                      condition: Dict[str, Any],
                      threshold: float,
                      callback: Callable):
        """添加預警規則"""
        self.alert_rules.append({
            "rule_name": rule_name,
            "condition": condition,
            "threshold": threshold,
            "callback": callback,
            "created_at": datetime.utcnow()
        })
    
    async def _check_alert_rules(self, action: UserAction):
        """檢查預警規則"""
        for rule in self.alert_rules:
            try:
                if self._evaluate_alert_condition(action, rule["condition"], rule["threshold"]):
                    await rule["callback"](action, rule)
            except Exception as e:
                logger.error(f"預警規則執行失敗 ({rule['rule_name']}): {e}")
    
    def _evaluate_alert_condition(self, action: UserAction, condition: Dict[str, Any], threshold: float) -> bool:
        """評估預警條件"""
        condition_type = condition.get("type")
        
        if condition_type == "error_rate":
            # 計算最近5分鐘的錯誤率
            recent_actions = [
                a for a in list(self.collector.actions)[-100:]  # 最近100個動作
                if (datetime.utcnow() - a.timestamp).seconds <= 300  # 5分鐘內
            ]
            
            if len(recent_actions) == 0:
                return False
            
            error_actions = [a for a in recent_actions if a.action_type == ActionType.ERROR]
            error_rate = len(error_actions) / len(recent_actions)
            
            return error_rate > threshold
        
        elif condition_type == "bounce_rate":
            # 檢查單頁面會話率
            # 這裡簡化處理，實際需要更複雜的邏輯
            return False
        
        return False
    
    async def _real_time_processing_loop(self):
        """實時處理循環"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分鐘更新一次
                await self._update_real_time_stats()
            except Exception as e:
                logger.error(f"實時處理循環失敗: {e}")
    
    async def _update_real_time_stats(self):
        """更新實時統計"""
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)
        
        # 計算每分鐘頁面瀏覽數
        page_views = sum(
            1 for action in self.collector.actions
            if (action.action_type == ActionType.PAGE_VIEW and 
                action.timestamp >= one_minute_ago)
        )
        self.real_time_stats["page_views_per_minute"].append(page_views)
        
        # 計算每小時唯一訪客數
        unique_visitors = len(set(
            action.user_id for action in self.collector.actions
            if action.timestamp >= one_hour_ago
        ))
        self.real_time_stats["unique_visitors_per_hour"].append(unique_visitors)
    
    async def get_real_time_stats(self) -> Dict[str, Any]:
        """獲取實時統計"""
        current_page_views = list(self.real_time_stats["page_views_per_minute"])
        current_visitors = list(self.real_time_stats["unique_visitors_per_hour"])
        
        return {
            "current_minute": {
                "page_views": current_page_views[-1] if current_page_views else 0,
                "active_users": await self.collector.get_active_users_count(minutes=5)
            },
            "last_hour": {
                "total_page_views": sum(current_page_views[-60:]) if current_page_views else 0,
                "avg_page_views_per_minute": statistics.mean(current_page_views[-60:]) if current_page_views else 0,
                "unique_visitors": current_visitors[-1] if current_visitors else 0
            },
            "trends": {
                "page_views_trend": current_page_views[-10:],  # 最近10分鐘
                "visitors_trend": current_visitors[-6:]  # 最近6小時
            }
        }
    
    async def get_user_journey(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """獲取用戶行為路徑"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 獲取用戶動作
        actions = await self.collector.get_user_actions(
            user_id=user_id,
            start_date=start_date,
            limit=1000
        )
        
        # 按時間排序
        actions.sort(key=lambda x: x.timestamp)
        
        # 構建路徑
        journey = {
            "user_id": user_id,
            "date_range": {
                "start": start_date.isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "total_actions": len(actions),
            "sessions": [],
            "page_flow": [],
            "funnel_progression": []
        }
        
        # 按會話分組
        sessions_dict = defaultdict(list)
        for action in actions:
            sessions_dict[action.session_id].append(action)
        
        # 處理每個會話
        for session_id, session_actions in sessions_dict.items():
            session_actions.sort(key=lambda x: x.timestamp)
            
            session_info = {
                "session_id": session_id,
                "start_time": session_actions[0].timestamp.isoformat(),
                "end_time": session_actions[-1].timestamp.isoformat(),
                "duration_minutes": (session_actions[-1].timestamp - session_actions[0].timestamp).seconds / 60,
                "actions": [
                    {
                        "action_type": a.action_type.value,
                        "timestamp": a.timestamp.isoformat(),
                        "page_url": a.page_url,
                        "element_id": a.element_id
                    }
                    for a in session_actions
                ]
            }
            
            journey["sessions"].append(session_info)
        
        # 構建頁面流
        page_sequence = []
        for action in actions:
            if action.action_type == ActionType.PAGE_VIEW and action.page_url:
                page_sequence.append(action.page_url)
        
        # 計算頁面轉換
        page_transitions = defaultdict(int)
        for i in range(len(page_sequence) - 1):
            transition = f"{page_sequence[i]} -> {page_sequence[i+1]}"
            page_transitions[transition] += 1
        
        journey["page_flow"] = [
            {"transition": transition, "count": count}
            for transition, count in page_transitions.items()
        ]
        
        return journey
    
    async def close(self):
        """關閉追蹤器"""
        try:
            if self._real_time_task:
                self._real_time_task.cancel()
                try:
                    await self._real_time_task
                except asyncio.CancelledError:
                    pass
        except Exception as e:
            logger.error(f"關閉行為追蹤器失敗: {e}")


# 全域行為追蹤器實例
behavior_tracker = None

def init_behavior_tracker(collector: BehaviorCollector):
    """初始化全域行為追蹤器"""
    global behavior_tracker
    behavior_tracker = BehaviorTracker(collector)