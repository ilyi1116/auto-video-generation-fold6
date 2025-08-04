"""
用戶行為數據收集器

負責收集、驗證、存儲和管理用戶行為數據。
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from collections import defaultdict, deque
import statistics
import geoip2.database

from .models import (
    UserAction, BehaviorSession, UserProfile, ActionType, 
    SessionStatus, UserSegment, DeviceType
)

logger = logging.getLogger(__name__)


class BehaviorCollector:
    """用戶行為數據收集器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化行為收集器
        
        Args:
            config: 配置參數
        """
        self.config = config or {}
        
        # 內存存儲（生產環境應使用數據庫）
        self.sessions: Dict[str, BehaviorSession] = {}
        self.user_profiles: Dict[str, UserProfile] = {}
        self.actions: deque = deque(maxlen=50000)  # 最近5萬個動作
        
        # 實時會話跟蹤
        self.active_sessions: Dict[str, str] = {}  # user_id -> session_id
        
        # 統計數據
        self.stats = {
            "total_actions": 0,
            "total_sessions": 0,
            "total_users": 0,
            "actions_per_minute": deque(maxlen=60),  # 最近60分鐘
            "last_stats_update": datetime.utcnow()
        }
        
        # 配置參數
        self.session_timeout_minutes = self.config.get("session_timeout_minutes", 30)
        self.max_session_duration_hours = self.config.get("max_session_duration_hours", 8)
        self.enable_geolocation = self.config.get("enable_geolocation", False)
        self.geoip_db_path = self.config.get("geoip_db_path")
        
        # GeoIP 數據庫
        self.geoip_reader = None
        if self.enable_geolocation and self.geoip_db_path:
            try:
                self.geoip_reader = geoip2.database.Reader(self.geoip_db_path)
            except Exception as e:
                logger.warning(f"無法加載 GeoIP 數據庫: {e}")
        
        # 啟動清理任務
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def collect_action(self, 
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
        收集用戶動作
        
        Args:
            user_id: 用戶ID
            action_type: 動作類型
            page_url: 頁面URL
            element_id: 元素ID
            element_text: 元素文本
            coordinates: 坐標 {"x": 100, "y": 200}
            duration_ms: 持續時間（毫秒）
            metadata: 元數據
            context: 上下文信息
            request_info: 請求信息（IP、User-Agent等）
            
        Returns:
            創建的用戶動作
        """
        try:
            # 驗證動作類型
            try:
                action_type_enum = ActionType(action_type)
            except ValueError:
                logger.warning(f"未知的動作類型: {action_type}")
                return None
            
            # 獲取或創建會話
            session = await self._get_or_create_session(user_id, request_info)
            
            # 創建用戶動作
            action = UserAction(
                action_id="",  # 將在 __post_init__ 中生成
                user_id=user_id,
                session_id=session.session_id,
                action_type=action_type_enum,
                timestamp=datetime.utcnow(),
                page_url=page_url,
                element_id=element_id,
                element_text=element_text,
                coordinates=coordinates,
                duration_ms=duration_ms,
                metadata=metadata or {},
                context=context or {}
            )
            
            # 添加動作到會話
            session.add_action(action)
            
            # 添加到動作隊列
            self.actions.append(action)
            
            # 更新統計
            self._update_stats()
            
            # 更新用戶檔案
            await self._update_user_profile(user_id, session, action)
            
            logger.debug(f"收集用戶動作: {user_id} - {action_type} - {page_url}")
            
            return action
            
        except Exception as e:
            logger.error(f"收集用戶動作失敗: {e}")
            return None
    
    async def _get_or_create_session(self, 
                                   user_id: str,
                                   request_info: Optional[Dict[str, Any]] = None) -> BehaviorSession:
        """獲取或創建用戶會話"""
        now = datetime.utcnow()
        
        # 檢查是否有活躍會話
        if user_id in self.active_sessions:
            session_id = self.active_sessions[user_id]
            if session_id in self.sessions:
                session = self.sessions[session_id]
                
                # 檢查會話是否過期
                last_action_time = session.end_time or session.start_time
                if now - last_action_time < timedelta(minutes=self.session_timeout_minutes):
                    # 會話仍然活躍
                    return session
                else:
                    # 會話已過期，標記為過期
                    session.status = SessionStatus.EXPIRED
                    session.end_time = last_action_time
        
        # 創建新會話
        session = BehaviorSession(
            session_id="",  # 將在 __post_init__ 中生成
            user_id=user_id,
            start_time=now,
            status=SessionStatus.ACTIVE
        )
        
        # 設置請求信息
        if request_info:
            session.user_agent = request_info.get("user_agent")
            session.ip_address = request_info.get("ip_address")
            session.referrer = request_info.get("referrer")
            
            # 設置設備信息
            user_agent = session.user_agent or ""
            session.device_info = self._parse_user_agent(user_agent)
            
            # 設置地理位置
            if self.geoip_reader and session.ip_address:
                session.location = self._get_location_from_ip(session.ip_address)
        
        # 存儲會話
        self.sessions[session.session_id] = session
        self.active_sessions[user_id] = session.session_id
        
        # 更新統計
        self.stats["total_sessions"] += 1
        
        logger.debug(f"創建新會話: {user_id} - {session.session_id}")
        
        return session
    
    def _parse_user_agent(self, user_agent: str) -> Dict[str, Any]:
        """解析 User-Agent"""
        device_info = {
            "user_agent": user_agent,
            "browser": "unknown",
            "os": "unknown",
            "device": "unknown"
        }
        
        user_agent_lower = user_agent.lower()
        
        # 檢測瀏覽器
        if "chrome" in user_agent_lower:
            device_info["browser"] = "Chrome"
        elif "firefox" in user_agent_lower:
            device_info["browser"] = "Firefox"
        elif "safari" in user_agent_lower and "chrome" not in user_agent_lower:
            device_info["browser"] = "Safari"
        elif "edge" in user_agent_lower:
            device_info["browser"] = "Edge"
        
        # 檢測操作系統
        if "windows" in user_agent_lower:
            device_info["os"] = "Windows"
        elif "mac" in user_agent_lower:
            device_info["os"] = "macOS"
        elif "linux" in user_agent_lower:
            device_info["os"] = "Linux"
        elif "android" in user_agent_lower:
            device_info["os"] = "Android"
        elif "ios" in user_agent_lower:
            device_info["os"] = "iOS"
        
        # 檢測設備類型
        if "mobile" in user_agent_lower:
            device_info["device"] = "Mobile"
        elif "tablet" in user_agent_lower:
            device_info["device"] = "Tablet"
        else:
            device_info["device"] = "Desktop"
        
        return device_info
    
    def _get_location_from_ip(self, ip_address: str) -> Optional[Dict[str, str]]:
        """從IP地址獲取地理位置"""
        if not self.geoip_reader:
            return None
        
        try:
            response = self.geoip_reader.city(ip_address)
            return {
                "country": response.country.name,
                "country_code": response.country.iso_code,
                "city": response.city.name,
                "region": response.subdivisions.most_specific.name
            }
        except Exception as e:
            logger.debug(f"無法獲取IP地理位置 {ip_address}: {e}")
            return None
    
    async def _update_user_profile(self, user_id: str, session: BehaviorSession, action: UserAction):
        """更新用戶檔案"""
        if user_id not in self.user_profiles:
            # 創建新用戶檔案
            self.user_profiles[user_id] = UserProfile(
                user_id=user_id,
                first_seen=action.timestamp,
                last_seen=action.timestamp,
                segment=UserSegment.NEW_USER
            )
            self.stats["total_users"] += 1
        
        profile = self.user_profiles[user_id]
        profile.update_from_session(session)
        
        # 更新用戶細分
        profile.segment = self._calculate_user_segment(profile)
    
    def _calculate_user_segment(self, profile: UserProfile) -> UserSegment:
        """計算用戶細分"""
        days_active = profile.days_since_first_seen
        days_inactive = profile.days_since_last_seen
        
        # 新用戶（7天內首次見到）
        if days_active <= 7:
            return UserSegment.NEW_USER
        
        # 流失用戶（30天未活躍）
        if days_inactive > 30:
            return UserSegment.CHURNED_USER
        
        # 不活躍用戶（7天未活躍）
        if days_inactive > 7:
            return UserSegment.INACTIVE_USER
        
        # 高級用戶（高參與度和使用頻率）
        if (profile.engagement_score > 0.7 and 
            profile.total_sessions > 20 and
            profile.avg_actions_per_session > 10):
            return UserSegment.POWER_USER
        
        # 活躍用戶
        if profile.engagement_score > 0.3 and profile.total_sessions > 5:
            return UserSegment.ACTIVE_USER
        
        return UserSegment.NEW_USER
    
    def _update_stats(self):
        """更新統計數據"""
        self.stats["total_actions"] += 1
        now = datetime.utcnow()
        
        # 更新每分鐘動作數
        if (now - self.stats["last_stats_update"]).seconds >= 60:
            current_minute_actions = sum(1 for _ in range(60))  # 簡化計算
            self.stats["actions_per_minute"].append(current_minute_actions)
            self.stats["last_stats_update"] = now
    
    async def get_user_sessions(self, 
                              user_id: str,
                              limit: int = 10,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> List[BehaviorSession]:
        """獲取用戶會話"""
        sessions = []
        
        for session in self.sessions.values():
            if session.user_id != user_id:
                continue
            
            if start_date and session.start_time < start_date:
                continue
            
            if end_date and session.start_time > end_date:
                continue
            
            sessions.append(session)
        
        # 按開始時間倒序排列
        sessions.sort(key=lambda x: x.start_time, reverse=True)
        return sessions[:limit]
    
    async def get_user_actions(self,
                             user_id: str,
                             action_types: Optional[List[str]] = None,
                             limit: int = 100,
                             start_date: Optional[datetime] = None,
                             end_date: Optional[datetime] = None) -> List[UserAction]:
        """獲取用戶動作"""
        actions = []
        action_type_enums = None
        
        if action_types:
            action_type_enums = [ActionType(at) for at in action_types]
        
        for action in reversed(self.actions):  # 最新的在前
            if action.user_id != user_id:
                continue
            
            if action_type_enums and action.action_type not in action_type_enums:
                continue
            
            if start_date and action.timestamp < start_date:
                continue
            
            if end_date and action.timestamp > end_date:
                continue
            
            actions.append(action)
            
            if len(actions) >= limit:
                break
        
        return actions
    
    async def get_active_users_count(self, minutes: int = 30) -> int:
        """獲取活躍用戶數"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        active_users = set()
        
        for action in reversed(self.actions):
            if action.timestamp < cutoff_time:
                break
            active_users.add(action.user_id)
        
        return len(active_users)
    
    async def get_page_views(self, 
                           hours: int = 24,
                           page_url: Optional[str] = None) -> List[UserAction]:
        """獲取頁面瀏覽數據"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        page_views = []
        
        for action in reversed(self.actions):
            if action.timestamp < cutoff_time:
                break
            
            if action.action_type != ActionType.PAGE_VIEW:
                continue
            
            if page_url and action.page_url != page_url:
                continue
            
            page_views.append(action)
        
        return page_views
    
    async def get_conversion_funnel(self, 
                                  funnel_steps: List[Dict[str, Any]],
                                  time_window_hours: int = 24) -> Dict[str, Any]:
        """計算轉換漏斗"""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        # 獲取符合第一步條件的用戶
        first_step = funnel_steps[0]
        step_users = [set()]  # 每一步的用戶集合
        
        for action in reversed(self.actions):
            if action.timestamp < cutoff_time:
                break
            
            if self._action_matches_condition(action, first_step):
                step_users[0].add(action.user_id)
        
        # 計算後續步驟的轉換
        for i, step in enumerate(funnel_steps[1:], 1):
            step_users.append(set())
            prev_users = step_users[i-1]
            
            for action in reversed(self.actions):
                if action.timestamp < cutoff_time:
                    break
                
                if (action.user_id in prev_users and 
                    self._action_matches_condition(action, step)):
                    step_users[i].add(action.user_id)
        
        # 計算轉換率
        total_users = len(step_users[0]) if step_users else 0
        conversions = []
        
        for i, users in enumerate(step_users):
            conversion_rate = len(users) / total_users if total_users > 0 else 0
            conversions.append({
                "step": i + 1,
                "step_name": funnel_steps[i].get("name", f"Step {i+1}"),
                "users": len(users),
                "conversion_rate": conversion_rate
            })
        
        return {
            "total_users": total_users,
            "conversions": conversions,
            "overall_conversion_rate": conversions[-1]["conversion_rate"] if conversions else 0
        }
    
    def _action_matches_condition(self, action: UserAction, condition: Dict[str, Any]) -> bool:
        """檢查動作是否匹配條件"""
        # 檢查動作類型
        if "action_type" in condition:
            if action.action_type.value != condition["action_type"]:
                return False
        
        # 檢查頁面URL
        if "page_url" in condition:
            page_pattern = condition["page_url"]
            if not action.page_url or page_pattern not in action.page_url:
                return False
        
        # 檢查元素ID
        if "element_id" in condition:
            if action.element_id != condition["element_id"]:
                return False
        
        return True
    
    async def export_data(self, 
                        user_id: Optional[str] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        format: str = "json") -> Dict[str, Any]:
        """導出數據"""
        export_data = {
            "export_time": datetime.utcnow().isoformat(),
            "filters": {
                "user_id": user_id,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            },
            "sessions": [],
            "actions": [],
            "user_profiles": []
        }
        
        # 導出會話
        for session in self.sessions.values():
            if user_id and session.user_id != user_id:
                continue
            
            if start_date and session.start_time < start_date:
                continue
            
            if end_date and session.start_time > end_date:
                continue
            
            export_data["sessions"].append(session.to_dict())
        
        # 導出動作
        for action in self.actions:
            if user_id and action.user_id != user_id:
                continue
            
            if start_date and action.timestamp < start_date:
                continue
            
            if end_date and action.timestamp > end_date:
                continue
            
            export_data["actions"].append(action.to_dict())
        
        # 導出用戶檔案
        for profile in self.user_profiles.values():
            if user_id and profile.user_id != user_id:
                continue
            
            export_data["user_profiles"].append(profile.to_dict())
        
        return export_data
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計數據"""
        active_sessions = len([
            s for s in self.sessions.values() 
            if s.status == SessionStatus.ACTIVE
        ])
        
        avg_actions_per_minute = 0
        if self.stats["actions_per_minute"]:
            avg_actions_per_minute = statistics.mean(self.stats["actions_per_minute"])
        
        return {
            "total_actions": self.stats["total_actions"],
            "total_sessions": self.stats["total_sessions"],
            "total_users": self.stats["total_users"],
            "active_sessions": active_sessions,
            "avg_actions_per_minute": round(avg_actions_per_minute, 2),
            "memory_usage": {
                "sessions": len(self.sessions),
                "actions": len(self.actions),
                "user_profiles": len(self.user_profiles)
            }
        }
    
    async def _cleanup_loop(self):
        """清理循環"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小時清理一次
                await self._cleanup_old_data()
            except Exception as e:
                logger.error(f"清理任務失敗: {e}")
    
    async def _cleanup_old_data(self):
        """清理舊數據"""
        now = datetime.utcnow()
        cutoff_time = now - timedelta(days=7)  # 保留7天數據
        
        # 清理舊會話
        old_sessions = [
            sid for sid, session in self.sessions.items()
            if session.start_time < cutoff_time
        ]
        
        for session_id in old_sessions:
            del self.sessions[session_id]
        
        # 清理用戶檔案中的舊會話引用
        for user_id, session_id in list(self.active_sessions.items()):
            if session_id not in self.sessions:
                del self.active_sessions[user_id]
        
        logger.info(f"清理了 {len(old_sessions)} 個舊會話")
    
    async def close(self):
        """關閉收集器"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            if self.geoip_reader:
                self.geoip_reader.close()
        except Exception as e:
            logger.error(f"關閉行為收集器失敗: {e}")


# 全域行為收集器實例
behavior_collector = None

def init_behavior_collector(config: Optional[Dict[str, Any]] = None):
    """初始化全域行為收集器"""
    global behavior_collector
    behavior_collector = BehaviorCollector(config)