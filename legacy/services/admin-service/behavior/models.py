"""
用戶行為追蹤數據模型

定義用戶行為追蹤系統中使用的數據結構和模型。
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib


class ActionType(Enum):
    """用戶動作類型"""
    PAGE_VIEW = "page_view"               # 頁面瀏覽
    CLICK = "click"                       # 點擊
    FORM_SUBMIT = "form_submit"           # 表單提交
    SEARCH = "search"                     # 搜索
    DOWNLOAD = "download"                 # 下載
    UPLOAD = "upload"                     # 上傳
    LOGIN = "login"                       # 登錄
    LOGOUT = "logout"                     # 登出
    VOICE_CLONE = "voice_clone"           # 語音克隆
    MODEL_TRAIN = "model_train"           # 模型訓練
    API_CALL = "api_call"                 # API 調用
    ERROR = "error"                       # 錯誤
    FEATURE_USE = "feature_use"           # 功能使用
    SCROLL = "scroll"                     # 滾動
    HOVER = "hover"                       # 懸停
    RESIZE = "resize"                     # 調整大小
    COPY = "copy"                         # 複製
    PASTE = "paste"                       # 粘貼
    SHARE = "share"                       # 分享
    BOOKMARK = "bookmark"                 # 收藏


class SessionStatus(Enum):
    """會話狀態"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


class UserSegment(Enum):
    """用戶細分"""
    NEW_USER = "new_user"                 # 新用戶
    ACTIVE_USER = "active_user"           # 活躍用戶
    POWER_USER = "power_user"             # 高級用戶
    INACTIVE_USER = "inactive_user"       # 不活躍用戶
    CHURNED_USER = "churned_user"         # 流失用戶
    PREMIUM_USER = "premium_user"         # 付費用戶
    TRIAL_USER = "trial_user"             # 試用用戶


class DeviceType(Enum):
    """設備類型"""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    UNKNOWN = "unknown"


@dataclass
class UserAction:
    """用戶動作"""
    action_id: str
    user_id: str
    session_id: str
    action_type: ActionType
    timestamp: datetime
    page_url: Optional[str] = None
    element_id: Optional[str] = None
    element_text: Optional[str] = None
    coordinates: Optional[Dict[str, int]] = None  # {"x": 100, "y": 200}
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.action_id:
            # 生成唯一ID
            content = f"{self.user_id}:{self.action_type.value}:{self.timestamp.isoformat()}"
            self.action_id = hashlib.md5(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        data = asdict(self)
        data['action_type'] = self.action_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserAction':
        """從字典創建實例"""
        data = data.copy()
        data['action_type'] = ActionType(data['action_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class BehaviorSession:
    """用戶行為會話"""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: SessionStatus = SessionStatus.ACTIVE
    device_info: Dict[str, Any] = field(default_factory=dict)
    location: Optional[Dict[str, str]] = None  # {"country": "TW", "city": "Taipei"}
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    actions: List[UserAction] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.session_id:
            # 生成會話ID
            content = f"{self.user_id}:{self.start_time.isoformat()}"
            self.session_id = hashlib.md5(content.encode()).hexdigest()[:16]
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """會話持續時間（秒）"""
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds())
        return None
    
    @property
    def action_count(self) -> int:
        """動作數量"""
        return len(self.actions)
    
    @property
    def device_type(self) -> DeviceType:
        """設備類型"""
        user_agent = self.user_agent or ""
        if "Mobile" in user_agent:
            return DeviceType.MOBILE
        elif "Tablet" in user_agent:
            return DeviceType.TABLET
        elif any(desktop in user_agent for desktop in ["Windows", "Mac", "Linux"]):
            return DeviceType.DESKTOP
        return DeviceType.UNKNOWN
    
    def add_action(self, action: UserAction):
        """添加用戶動作"""
        self.actions.append(action)
        # 更新會話結束時間
        if not self.end_time or action.timestamp > self.end_time:
            self.end_time = action.timestamp
    
    def get_page_views(self) -> List[UserAction]:
        """獲取頁面瀏覽動作"""
        return [a for a in self.actions if a.action_type == ActionType.PAGE_VIEW]
    
    def get_clicks(self) -> List[UserAction]:
        """獲取點擊動作"""
        return [a for a in self.actions if a.action_type == ActionType.CLICK]
    
    def get_unique_pages(self) -> List[str]:
        """獲取唯一頁面列表"""
        pages = set()
        for action in self.actions:
            if action.page_url:
                pages.add(action.page_url)
        return list(pages)
    
    def calculate_engagement_score(self) -> float:
        """計算參與度分數"""
        if not self.actions:
            return 0.0
        
        # 基於動作數量、會話時長、頁面數等計算
        action_score = min(len(self.actions) / 10.0, 1.0)  # 最多10個動作得滿分
        
        duration_score = 0.0
        if self.duration_seconds:
            duration_score = min(self.duration_seconds / 300.0, 1.0)  # 5分鐘得滿分
        
        page_score = min(len(self.get_unique_pages()) / 5.0, 1.0)  # 5個頁面得滿分
        
        return (action_score + duration_score + page_score) / 3.0
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status.value,
            "device_info": self.device_info,
            "location": self.location,
            "referrer": self.referrer,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "actions": [action.to_dict() for action in self.actions],
            "metadata": self.metadata,
            "duration_seconds": self.duration_seconds,
            "action_count": self.action_count,
            "device_type": self.device_type.value,
            "engagement_score": self.calculate_engagement_score()
        }


@dataclass
class UserProfile:
    """用戶檔案"""
    user_id: str
    first_seen: datetime
    last_seen: datetime
    total_sessions: int = 0
    total_actions: int = 0
    total_time_spent: int = 0  # 秒
    segment: UserSegment = UserSegment.NEW_USER
    preferences: Dict[str, Any] = field(default_factory=dict)
    demographics: Dict[str, Any] = field(default_factory=dict)
    behavior_patterns: Dict[str, Any] = field(default_factory=dict)
    cohort: Optional[str] = None
    ltv_score: float = 0.0  # 終身價值分數
    churn_probability: float = 0.0  # 流失概率
    engagement_score: float = 0.0  # 參與度分數
    
    def update_from_session(self, session: BehaviorSession):
        """從會話更新用戶檔案"""
        self.last_seen = session.end_time or session.start_time
        self.total_sessions += 1
        self.total_actions += session.action_count
        
        if session.duration_seconds:
            self.total_time_spent += session.duration_seconds
        
        # 更新參與度分數
        self.engagement_score = (self.engagement_score + session.calculate_engagement_score()) / 2
    
    @property
    def avg_session_duration(self) -> float:
        """平均會話時長"""
        if self.total_sessions == 0:
            return 0.0
        return self.total_time_spent / self.total_sessions
    
    @property
    def avg_actions_per_session(self) -> float:
        """平均每會話動作數"""
        if self.total_sessions == 0:
            return 0.0
        return self.total_actions / self.total_sessions
    
    @property
    def days_since_first_seen(self) -> int:
        """首次見到後的天數"""
        return (datetime.utcnow() - self.first_seen).days
    
    @property
    def days_since_last_seen(self) -> int:
        """最後見到後的天數"""
        return (datetime.utcnow() - self.last_seen).days
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "user_id": self.user_id,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "total_sessions": self.total_sessions,
            "total_actions": self.total_actions,
            "total_time_spent": self.total_time_spent,
            "segment": self.segment.value,
            "preferences": self.preferences,
            "demographics": self.demographics,
            "behavior_patterns": self.behavior_patterns,
            "cohort": self.cohort,
            "ltv_score": self.ltv_score,
            "churn_probability": self.churn_probability,
            "engagement_score": self.engagement_score,
            "avg_session_duration": self.avg_session_duration,
            "avg_actions_per_session": self.avg_actions_per_session,
            "days_since_first_seen": self.days_since_first_seen,
            "days_since_last_seen": self.days_since_last_seen
        }


@dataclass
class BehaviorPattern:
    """行為模式"""
    pattern_id: str
    pattern_name: str
    description: str
    pattern_type: str  # "sequential", "frequent", "temporal", "cohort"
    user_segments: List[UserSegment]
    conditions: Dict[str, Any]
    frequency: int = 0
    confidence_score: float = 0.0
    impact_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "pattern_id": self.pattern_id,
            "pattern_name": self.pattern_name,
            "description": self.description,
            "pattern_type": self.pattern_type,
            "user_segments": [s.value for s in self.user_segments],
            "conditions": self.conditions,
            "frequency": self.frequency,
            "confidence_score": self.confidence_score,
            "impact_score": self.impact_score,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class BehaviorInsight:
    """行為洞察"""
    insight_id: str
    title: str
    description: str
    insight_type: str  # "opportunity", "risk", "trend", "anomaly"
    priority: str  # "high", "medium", "low"
    affected_users: int
    potential_impact: str
    recommendations: List[str]
    data_points: Dict[str, Any]
    confidence_level: float
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: str = "active"  # "active", "implemented", "dismissed"
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "insight_id": self.insight_id,
            "title": self.title,
            "description": self.description,
            "insight_type": self.insight_type,
            "priority": self.priority,
            "affected_users": self.affected_users,
            "potential_impact": self.potential_impact,
            "recommendations": self.recommendations,
            "data_points": self.data_points,
            "confidence_level": self.confidence_level,
            "created_at": self.created_at.isoformat(),
            "status": self.status
        }


@dataclass
class Funnel:
    """轉換漏斗"""
    funnel_id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]  # [{"name": "step1", "condition": {...}}]
    time_window_hours: int = 24
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "funnel_id": self.funnel_id,
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "time_window_hours": self.time_window_hours,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class FunnelAnalysis:
    """漏斗分析結果"""
    funnel_id: str
    analysis_date: datetime
    total_users: int
    step_conversions: List[Dict[str, Any]]  # [{"step": "step1", "users": 100, "conversion_rate": 0.5}]
    drop_off_points: List[Dict[str, Any]]
    overall_conversion_rate: float
    insights: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "funnel_id": self.funnel_id,
            "analysis_date": self.analysis_date.isoformat(),
            "total_users": self.total_users,
            "step_conversions": self.step_conversions,
            "drop_off_points": self.drop_off_points,
            "overall_conversion_rate": self.overall_conversion_rate,
            "insights": self.insights
        }