"""
行為模式檢測器

使用機器學習和統計方法檢測用戶行為模式。
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter
import statistics
import hashlib

from .collector import BehaviorCollector
from .models import (
    UserAction, BehaviorSession, UserProfile, ActionType, 
    UserSegment, BehaviorPattern
)

logger = logging.getLogger(__name__)


class PatternDetector:
    """行為模式檢測器"""
    
    def __init__(self, collector: BehaviorCollector):
        """
        初始化模式檢測器
        
        Args:
            collector: 行為收集器
        """
        self.collector = collector
        
        # 已檢測的模式
        self.detected_patterns: Dict[str, BehaviorPattern] = {}
        
        # 模式檢測配置
        self.config = {
            "min_pattern_frequency": 3,
            "min_pattern_confidence": 0.6,
            "sequence_max_length": 10,
            "time_window_minutes": 60,
            "min_users_for_pattern": 5
        }
        
        # 序列模式緩存
        self.sequence_cache = {}
        
        # 時間模式緩存
        self.temporal_patterns = defaultdict(list)
    
    async def detect_sequential_patterns(self, 
                                       min_support: int = 3,
                                       max_length: int = 5,
                                       time_window_hours: int = 24) -> List[BehaviorPattern]:
        """檢測序列模式"""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        # 按用戶和會話收集動作序列
        user_sequences = defaultdict(list)
        
        for action in reversed(self.collector.actions):
            if action.timestamp < cutoff_time:
                break
            
            sequence_key = f"{action.user_id}:{action.session_id}"
            user_sequences[sequence_key].append(action)
        
        # 為每個序列按時間排序
        for sequence_key in user_sequences:
            user_sequences[sequence_key].sort(key=lambda x: x.timestamp)
        
        # 提取動作類型序列
        action_sequences = []
        for sequence in user_sequences.values():
            if len(sequence) >= 2:  # 至少2個動作
                action_types = [a.action_type.value for a in sequence[:max_length]]
                action_sequences.append(action_types)
        
        # 查找頻繁序列模式
        frequent_patterns = self._find_frequent_sequences(action_sequences, min_support)
        
        # 轉換為 BehaviorPattern 對象
        patterns = []
        for pattern_seq, frequency in frequent_patterns.items():
            if len(pattern_seq) < 2:  # 跳過單個動作
                continue
            
            confidence = self._calculate_sequence_confidence(pattern_seq, action_sequences)
            impact = self._calculate_pattern_impact(pattern_seq, user_sequences)
            
            pattern_id = self._generate_pattern_id("sequential", pattern_seq)
            
            pattern = BehaviorPattern(
                pattern_id=pattern_id,
                pattern_name=f"序列模式: {' → '.join(pattern_seq)}",
                description=f"用戶經常按此順序執行動作: {' → '.join(pattern_seq)}",
                pattern_type="sequential",
                user_segments=[UserSegment.ACTIVE_USER],  # 簡化處理
                conditions={
                    "sequence": pattern_seq,
                    "time_window_hours": time_window_hours
                },
                frequency=frequency,
                confidence_score=confidence,
                impact_score=impact
            )
            
            patterns.append(pattern)
            self.detected_patterns[pattern_id] = pattern
        
        logger.info(f"檢測到 {len(patterns)} 個序列模式")
        return patterns
    
    def _find_frequent_sequences(self, sequences: List[List[str]], min_support: int) -> Dict[Tuple[str, ...], int]:
        """查找頻繁序列"""
        pattern_counts = defaultdict(int)
        
        # 生成所有可能的子序列
        for sequence in sequences:
            for length in range(2, len(sequence) + 1):
                for start in range(len(sequence) - length + 1):
                    subseq = tuple(sequence[start:start + length])
                    pattern_counts[subseq] += 1
        
        # 過濾低頻模式
        frequent_patterns = {
            pattern: count for pattern, count in pattern_counts.items()
            if count >= min_support
        }
        
        return frequent_patterns
    
    def _calculate_sequence_confidence(self, pattern_seq: Tuple[str, ...], all_sequences: List[List[str]]) -> float:
        """計算序列模式置信度"""
        if len(pattern_seq) < 2:
            return 0.0
        
        # 計算前綴出現次數
        prefix = pattern_seq[:-1]
        prefix_count = 0
        pattern_count = 0
        
        for sequence in all_sequences:
            sequence_tuple = tuple(sequence)
            
            # 檢查是否包含前綴
            for i in range(len(sequence_tuple) - len(prefix) + 1):
                if sequence_tuple[i:i + len(prefix)] == prefix:
                    prefix_count += 1
                    
                    # 檢查是否包含完整模式
                    if i + len(pattern_seq) <= len(sequence_tuple):
                        if sequence_tuple[i:i + len(pattern_seq)] == pattern_seq:
                            pattern_count += 1
                    break
        
        return pattern_count / prefix_count if prefix_count > 0 else 0.0
    
    def _calculate_pattern_impact(self, pattern_seq: Tuple[str, ...], user_sequences: Dict[str, List[UserAction]]) -> float:
        """計算模式影響分數"""
        # 簡化實現：基於包含該模式的用戶數量
        users_with_pattern = 0
        total_users = len(user_sequences)
        
        for sequence in user_sequences.values():
            action_types = [a.action_type.value for a in sequence]
            if self._contains_subsequence(action_types, list(pattern_seq)):
                users_with_pattern += 1
        
        return users_with_pattern / total_users if total_users > 0 else 0.0
    
    def _contains_subsequence(self, sequence: List[str], subseq: List[str]) -> bool:
        """檢查序列是否包含子序列"""
        if len(subseq) > len(sequence):
            return False
        
        for i in range(len(sequence) - len(subseq) + 1):
            if sequence[i:i + len(subseq)] == subseq:
                return True
        
        return False
    
    async def detect_temporal_patterns(self, days: int = 7) -> List[BehaviorPattern]:
        """檢測時間模式"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # 按時間段收集動作
        hourly_patterns = defaultdict(lambda: defaultdict(int))  # hour -> action_type -> count
        daily_patterns = defaultdict(lambda: defaultdict(int))   # weekday -> action_type -> count
        
        for action in self.collector.actions:
            if action.timestamp < cutoff_time:
                continue
            
            hour = action.timestamp.hour
            weekday = action.timestamp.weekday()
            action_type = action.action_type.value
            
            hourly_patterns[hour][action_type] += 1
            daily_patterns[weekday][action_type] += 1
        
        patterns = []
        
        # 分析小時模式
        for hour, action_counts in hourly_patterns.items():
            total_actions = sum(action_counts.values())
            if total_actions < self.config["min_pattern_frequency"]:
                continue
            
            # 找出主要動作類型
            dominant_action = max(action_counts.items(), key=lambda x: x[1])
            dominance_ratio = dominant_action[1] / total_actions
            
            if dominance_ratio > 0.6:  # 60%以上
                pattern_id = self._generate_pattern_id("temporal_hourly", f"{hour}_{dominant_action[0]}")
                
                pattern = BehaviorPattern(
                    pattern_id=pattern_id,
                    pattern_name=f"時間模式: {hour}點主要執行{dominant_action[0]}",
                    description=f"用戶在{hour}點主要執行{dominant_action[0]}動作（{dominance_ratio:.1%}）",
                    pattern_type="temporal",
                    user_segments=[UserSegment.ACTIVE_USER],
                    conditions={
                        "time_type": "hourly",
                        "hour": hour,
                        "dominant_action": dominant_action[0],
                        "dominance_ratio": dominance_ratio
                    },
                    frequency=total_actions,
                    confidence_score=dominance_ratio,
                    impact_score=min(total_actions / 100, 1.0)  # 基於動作數量
                )
                
                patterns.append(pattern)
                self.detected_patterns[pattern_id] = pattern
        
        # 分析星期模式
        weekday_names = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"]
        for weekday, action_counts in daily_patterns.items():
            total_actions = sum(action_counts.values())
            if total_actions < self.config["min_pattern_frequency"]:
                continue
            
            dominant_action = max(action_counts.items(), key=lambda x: x[1])
            dominance_ratio = dominant_action[1] / total_actions
            
            if dominance_ratio > 0.5:  # 50%以上
                pattern_id = self._generate_pattern_id("temporal_daily", f"{weekday}_{dominant_action[0]}")
                
                pattern = BehaviorPattern(
                    pattern_id=pattern_id,
                    pattern_name=f"{weekday_names[weekday]}主要執行{dominant_action[0]}",
                    description=f"用戶在{weekday_names[weekday]}主要執行{dominant_action[0]}動作（{dominance_ratio:.1%}）",
                    pattern_type="temporal",
                    user_segments=[UserSegment.ACTIVE_USER],
                    conditions={
                        "time_type": "daily",
                        "weekday": weekday,
                        "dominant_action": dominant_action[0],
                        "dominance_ratio": dominance_ratio
                    },
                    frequency=total_actions,
                    confidence_score=dominance_ratio,
                    impact_score=min(total_actions / 100, 1.0)
                )
                
                patterns.append(pattern)
                self.detected_patterns[pattern_id] = pattern
        
        logger.info(f"檢測到 {len(patterns)} 個時間模式")
        return patterns
    
    async def detect_user_journey_patterns(self, days: int = 7) -> List[BehaviorPattern]:
        """檢測用戶旅程模式"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # 收集用戶旅程數據
        user_journeys = defaultdict(list)  # user_id -> [page_urls]
        
        for action in self.collector.actions:
            if (action.timestamp < cutoff_time or 
                action.action_type != ActionType.PAGE_VIEW or 
                not action.page_url):
                continue
            
            user_journeys[action.user_id].append(action.page_url)
        
        # 查找常見的頁面遷移模式
        page_transitions = defaultdict(int)
        page_sequences = defaultdict(int)
        
        for user_id, pages in user_journeys.items():
            if len(pages) < 2:
                continue
            
            # 記錄頁面轉換
            for i in range(len(pages) - 1):
                transition = f"{pages[i]} → {pages[i+1]}"
                page_transitions[transition] += 1
            
            # 記錄頁面序列（前3個頁面）
            if len(pages) >= 3:
                sequence = tuple(pages[:3])
                page_sequences[sequence] += 1
        
        patterns = []
        
        # 分析頁面轉換模式
        for transition, count in page_transitions.items():
            if count >= self.config["min_pattern_frequency"]:
                total_transitions = sum(page_transitions.values())
                confidence = count / total_transitions
                
                if confidence > 0.05:  # 5%以上的轉換
                    pattern_id = self._generate_pattern_id("journey_transition", transition)
                    
                    pattern = BehaviorPattern(
                        pattern_id=pattern_id,
                        pattern_name=f"頁面轉換: {transition}",
                        description=f"用戶經常從一個頁面轉到另一個頁面: {transition}",
                        pattern_type="user_journey",
                        user_segments=[UserSegment.ACTIVE_USER],
                        conditions={
                            "pattern_type": "page_transition",
                            "transition": transition
                        },
                        frequency=count,
                        confidence_score=confidence,
                        impact_score=min(count / 50, 1.0)
                    )
                    
                    patterns.append(pattern)
                    self.detected_patterns[pattern_id] = pattern
        
        # 分析頁面序列模式
        for sequence, count in page_sequences.items():
            if count >= self.config["min_pattern_frequency"]:
                total_sequences = sum(page_sequences.values())
                confidence = count / total_sequences
                
                if confidence > 0.03:  # 3%以上的序列
                    sequence_str = " → ".join(sequence)
                    pattern_id = self._generate_pattern_id("journey_sequence", sequence_str)
                    
                    pattern = BehaviorPattern(
                        pattern_id=pattern_id,
                        pattern_name=f"頁面序列: {sequence_str}",
                        description=f"用戶經常按此順序瀏覽頁面: {sequence_str}",
                        pattern_type="user_journey",
                        user_segments=[UserSegment.ACTIVE_USER],
                        conditions={
                            "pattern_type": "page_sequence",
                            "sequence": list(sequence)
                        },
                        frequency=count,
                        confidence_score=confidence,
                        impact_score=min(count / 30, 1.0)
                    )
                    
                    patterns.append(pattern)
                    self.detected_patterns[pattern_id] = pattern
        
        logger.info(f"檢測到 {len(patterns)} 個用戶旅程模式")
        return patterns
    
    async def detect_cohort_patterns(self, days: int = 30) -> List[BehaviorPattern]:
        """檢測用戶群組模式"""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        
        # 按用戶細分分組
        segment_behaviors = defaultdict(lambda: defaultdict(int))  # segment -> action_type -> count
        segment_users = defaultdict(set)  # segment -> {user_ids}
        
        for user_id, profile in self.collector.user_profiles.items():
            segment = profile.segment.value
            segment_users[segment].add(user_id)
            
            # 收集該用戶的動作
            user_actions = [
                a for a in self.collector.actions
                if a.user_id == user_id and a.timestamp >= cutoff_time
            ]
            
            for action in user_actions:
                segment_behaviors[segment][action.action_type.value] += 1
        
        patterns = []
        
        # 分析每個細分的行為特徵
        for segment, action_counts in segment_behaviors.items():
            total_actions = sum(action_counts.values())
            user_count = len(segment_users[segment])
            
            if total_actions < self.config["min_pattern_frequency"] or user_count < 3:
                continue
            
            # 計算動作分佈
            action_distribution = {
                action: count / total_actions
                for action, count in action_counts.items()
            }
            
            # 找出特徵動作（比例較高的動作）
            characteristic_actions = [
                (action, ratio) for action, ratio in action_distribution.items()
                if ratio > 0.2  # 20%以上
            ]
            
            if characteristic_actions:
                pattern_id = self._generate_pattern_id("cohort", f"{segment}_behavior")
                
                action_descriptions = [f"{action}({ratio:.1%})" for action, ratio in characteristic_actions]
                
                pattern = BehaviorPattern(
                    pattern_id=pattern_id,
                    pattern_name=f"{segment}用戶群組行為模式",
                    description=f"{segment}用戶群組的特徵行為: {', '.join(action_descriptions)}",
                    pattern_type="cohort",
                    user_segments=[UserSegment(segment)] if segment in [s.value for s in UserSegment] else [UserSegment.ACTIVE_USER],
                    conditions={
                        "segment": segment,
                        "characteristic_actions": dict(characteristic_actions),
                        "user_count": user_count
                    },
                    frequency=total_actions,
                    confidence_score=max(ratio for _, ratio in characteristic_actions),
                    impact_score=min(user_count / 10, 1.0)
                )
                
                patterns.append(pattern)
                self.detected_patterns[pattern_id] = pattern
        
        logger.info(f"檢測到 {len(patterns)} 個用戶群組模式")
        return patterns
    
    def _generate_pattern_id(self, pattern_type: str, pattern_content: str) -> str:
        """生成模式ID"""
        content = f"{pattern_type}:{pattern_content}:{datetime.utcnow().date()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def get_all_patterns(self, 
                             pattern_type: Optional[str] = None,
                             min_confidence: float = 0.0) -> List[BehaviorPattern]:
        """獲取所有檢測到的模式"""
        patterns = list(self.detected_patterns.values())
        
        # 過濾條件
        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]
        
        if min_confidence > 0:
            patterns = [p for p in patterns if p.confidence_score >= min_confidence]
        
        # 按置信度排序
        patterns.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return patterns
    
    async def analyze_pattern_trends(self, days: int = 30) -> Dict[str, Any]:
        """分析模式趨勢"""
        # 簡化實現：統計不同類型模式的數量和置信度
        pattern_stats = defaultdict(lambda: {
            "count": 0,
            "avg_confidence": 0.0,
            "avg_impact": 0.0,
            "total_frequency": 0
        })
        
        for pattern in self.detected_patterns.values():
            ptype = pattern.pattern_type
            stats = pattern_stats[ptype]
            
            stats["count"] += 1
            stats["avg_confidence"] = (stats["avg_confidence"] * (stats["count"] - 1) + pattern.confidence_score) / stats["count"]
            stats["avg_impact"] = (stats["avg_impact"] * (stats["count"] - 1) + pattern.impact_score) / stats["count"]
            stats["total_frequency"] += pattern.frequency
        
        return {
            "pattern_statistics": dict(pattern_stats),
            "total_patterns": len(self.detected_patterns),
            "analysis_date": datetime.utcnow().isoformat()
        }
    
    def clear_patterns(self, older_than_days: int = 7):
        """清理舊模式"""
        cutoff_time = datetime.utcnow() - timedelta(days=older_than_days)
        
        old_patterns = [
            pattern_id for pattern_id, pattern in self.detected_patterns.items()
            if pattern.created_at < cutoff_time
        ]
        
        for pattern_id in old_patterns:
            del self.detected_patterns[pattern_id]
        
        logger.info(f"清理了 {len(old_patterns)} 個舊模式")
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """獲取模式檢測統計"""
        return {
            "total_patterns": len(self.detected_patterns),
            "pattern_types": Counter(p.pattern_type for p in self.detected_patterns.values()),
            "avg_confidence": statistics.mean([p.confidence_score for p in self.detected_patterns.values()]) if self.detected_patterns else 0,
            "config": self.config
        }


# 全域模式檢測器實例
pattern_detector = None

def init_pattern_detector(collector: BehaviorCollector):
    """初始化全域模式檢測器"""
    global pattern_detector
    pattern_detector = PatternDetector(collector)