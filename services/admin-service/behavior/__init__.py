"""
用戶行為追蹤系統

提供用戶行為收集、分析、模式識別和洞察生成功能。
"""

from .collector import behavior_collector, init_behavior_collector, BehaviorCollector
from .tracker import behavior_tracker, init_behavior_tracker
from .analyzer import behavior_analyzer, init_behavior_analyzer  
from .pattern import pattern_detector, init_pattern_detector
from .insights import insight_generator, init_insight_generator
from .models import UserAction, BehaviorSession, UserSegment

# 初始化所有組件的便捷函數
def init_behavior_system(config=None):
    """初始化整個用戶行為追蹤系統"""
    init_behavior_collector(config)
    init_behavior_tracker(behavior_collector)
    init_behavior_analyzer(behavior_collector)
    init_pattern_detector(behavior_collector)
    init_insight_generator(behavior_collector, behavior_analyzer, pattern_detector)

__all__ = [
    'behavior_collector',
    'behavior_tracker',
    'behavior_analyzer', 
    'pattern_detector',
    'insight_generator',
    'BehaviorCollector',
    'UserAction',
    'BehaviorSession', 
    'UserSegment',
    'init_behavior_collector',
    'init_behavior_tracker',
    'init_behavior_analyzer',
    'init_pattern_detector',
    'init_insight_generator',
    'init_behavior_system'
]