#!/usr/bin/env python3
"""
預算控制器 - 智能預算管理與自動限制系統
整合成本追蹤器實現動態預算控制
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
import json
from pathlib import Path

from cost_tracker import CostTracker, get_cost_tracker

logger = logging.getLogger(__name__)

class BudgetStatus(Enum):
    """預算狀態枚舉"""
    NORMAL = "normal"          # 正常範圍
    WARNING = "warning"        # 警告範圍 (80-90%)
    CRITICAL = "critical"      # 臨界範圍 (90-100%)
    EXCEEDED = "exceeded"      # 已超支
    EMERGENCY_STOP = "emergency_stop"  # 緊急停止

class ActionType(Enum):
    """行動類型枚舉"""
    CONTINUE = "continue"
    THROTTLE = "throttle"      # 限流
    PAUSE = "pause"            # 暫停
    STOP = "stop"              # 停止

@dataclass
class BudgetRule:
    """預算規則"""
    threshold_percentage: float  # 觸發閾值 (百分比)
    action: ActionType          # 觸發行動
    message: str               # 提示訊息
    metadata: Dict[str, Any] = None

@dataclass
class BudgetDecision:
    """預算決策結果"""
    status: BudgetStatus
    action: ActionType
    can_continue: bool
    message: str
    current_usage: float
    remaining_budget: float
    suggested_actions: List[str]
    metadata: Dict[str, Any] = None

class BudgetController:
    """預算控制器"""
    
    def __init__(self, config_manager=None, cost_tracker: CostTracker = None):
        self.config_manager = config_manager
        self.cost_tracker = cost_tracker or get_cost_tracker(config_manager)
        
        # 預設預算規則
        self.default_rules = [
            BudgetRule(0.8, ActionType.CONTINUE, "預算使用達到 80%，請注意成本控制"),
            BudgetRule(0.9, ActionType.THROTTLE, "預算使用達到 90%，啟動限流模式"),
            BudgetRule(0.95, ActionType.PAUSE, "預算使用達到 95%，暫停非必要操作"),
            BudgetRule(1.0, ActionType.STOP, "預算已用完，停止所有付費操作")
        ]
        
        # 載入自訂規則
        self.rules = self._load_budget_rules()
        
        # 當前狀態
        self.current_status = BudgetStatus.NORMAL
        self.last_check_time = None
        
        # 統計資訊
        self.daily_stats = {
            'decisions_count': 0,
            'throttle_events': 0,
            'pause_events': 0,
            'stop_events': 0
        }

    def _load_budget_rules(self) -> List[BudgetRule]:
        """載入預算規則"""
        if not self.config_manager:
            return self.default_rules
            
        custom_rules = self.config_manager.get("cost_control.budget_rules", [])
        
        if not custom_rules:
            return self.default_rules
            
        rules = []
        for rule_data in custom_rules:
            try:
                rule = BudgetRule(
                    threshold_percentage=rule_data["threshold"],
                    action=ActionType(rule_data["action"]),
                    message=rule_data["message"],
                    metadata=rule_data.get("metadata", {})
                )
                rules.append(rule)
            except (KeyError, ValueError) as e:
                logger.warning(f"無效的預算規則: {rule_data}, 錯誤: {e}")
                
        # 按閾值排序
        rules.sort(key=lambda x: x.threshold_percentage)
        return rules if rules else self.default_rules

    async def check_budget_and_decide(self, estimated_cost: float = 0) -> BudgetDecision:
        """檢查預算並做出決策"""
        try:
            # 獲取當前預算狀態
            budget_status = await self.cost_tracker.check_budget_status()
            
            # 計算預估使用率
            current_cost = budget_status["current_cost"]
            budget_limit = budget_status["budget_limit"]
            estimated_total = current_cost + estimated_cost
            usage_rate = estimated_total / budget_limit if budget_limit > 0 else 0
            
            # 根據規則決定行動
            decision = self._make_decision(usage_rate, budget_status, estimated_cost)
            
            # 更新統計
            self._update_stats(decision)
            
            # 記錄決策
            await self._log_decision(decision, budget_status)
            
            self.current_status = decision.status
            self.last_check_time = datetime.now()
            
            return decision
            
        except Exception as e:
            logger.error(f"預算檢查失敗: {e}")
            # 返回安全的預設決策
            return BudgetDecision(
                status=BudgetStatus.NORMAL,
                action=ActionType.CONTINUE,
                can_continue=True,
                message="預算檢查失敗，使用預設策略",
                current_usage=0.0,
                remaining_budget=100.0,
                suggested_actions=["檢查成本追蹤器狀態"],
                metadata={"error": str(e)}
            )

    def _make_decision(self, usage_rate: float, budget_status: Dict[str, Any], 
                      estimated_cost: float) -> BudgetDecision:
        """根據使用率和規則做出決策"""
        
        current_cost = budget_status["current_cost"]
        budget_limit = budget_status["budget_limit"]
        remaining_budget = budget_status["budget_remaining"]
        
        # 找到適用的規則
        applicable_rule = None
        for rule in self.rules:
            if usage_rate >= rule.threshold_percentage:
                applicable_rule = rule
            else:
                break  # 規則已排序，找到第一個不適用的就停止
                
        if not applicable_rule:
            # 正常狀態
            return BudgetDecision(
                status=BudgetStatus.NORMAL,
                action=ActionType.CONTINUE,
                can_continue=True,
                message=f"預算使用正常 ({usage_rate:.1%})",
                current_usage=current_cost,
                remaining_budget=remaining_budget,
                suggested_actions=[]
            )
            
        # 根據規則生成決策
        status = self._determine_status(usage_rate)
        can_continue = self._can_continue(applicable_rule.action, usage_rate)
        suggested_actions = self._generate_suggestions(status, usage_rate, estimated_cost)
        
        return BudgetDecision(
            status=status,
            action=applicable_rule.action,
            can_continue=can_continue,
            message=applicable_rule.message,
            current_usage=current_cost,
            remaining_budget=remaining_budget,
            suggested_actions=suggested_actions,
            metadata={
                "usage_rate": usage_rate,
                "estimated_cost": estimated_cost,
                "rule_threshold": applicable_rule.threshold_percentage
            }
        )

    def _determine_status(self, usage_rate: float) -> BudgetStatus:
        """根據使用率決定狀態"""
        if usage_rate >= 1.1:
            return BudgetStatus.EMERGENCY_STOP
        elif usage_rate >= 1.0:
            return BudgetStatus.EXCEEDED
        elif usage_rate >= 0.95:
            return BudgetStatus.CRITICAL
        elif usage_rate >= 0.8:
            return BudgetStatus.WARNING
        else:
            return BudgetStatus.NORMAL

    def _can_continue(self, action: ActionType, usage_rate: float) -> bool:
        """判斷是否可繼續操作"""
        if action == ActionType.STOP:
            return False
            
        if action == ActionType.PAUSE and usage_rate >= 0.98:
            return False
            
        # 檢查配置中的停止設定
        if self.config_manager:
            stop_on_exceeded = self.config_manager.get("cost_control.stop_on_budget_exceeded", True)
            if stop_on_exceeded and usage_rate >= 1.0:
                return False
                
        return True

    def _generate_suggestions(self, status: BudgetStatus, usage_rate: float, 
                            estimated_cost: float) -> List[str]:
        """生成建議行動"""
        suggestions = []
        
        if status == BudgetStatus.WARNING:
            suggestions.extend([
                "考慮降低影片生成品質以節省成本",
                "減少同時進行的影片數量",
                "檢查是否有不必要的 API 呼叫"
            ])
            
        elif status == BudgetStatus.CRITICAL:
            suggestions.extend([
                "立即暫停非必要的影片生成",
                "檢查成本異常高的操作",
                "考慮增加每日預算限制",
                "切換到成本更低的 AI 模型"
            ])
            
        elif status in [BudgetStatus.EXCEEDED, BudgetStatus.EMERGENCY_STOP]:
            suggestions.extend([
                "停止所有付費操作",
                "分析今日成本支出明細",
                "調整明日預算配置",
                "檢查是否有成本異常"
            ])
            
        # 基於預估成本的建議
        if estimated_cost > 5.0:  # 高成本操作
            suggestions.append("當前操作成本較高，考慮分批執行")
            
        return suggestions

    async def pre_operation_check(self, operation_type: str, estimated_cost: float = 0) -> Tuple[bool, str]:
        """操作前預算檢查"""
        decision = await self.check_budget_and_decide(estimated_cost)
        
        if not decision.can_continue:
            return False, decision.message
            
        # 特殊檢查
        if decision.action == ActionType.THROTTLE:
            # 限流模式下的額外檢查
            if estimated_cost > decision.remaining_budget * 0.1:  # 超過剩餘預算的10%
                return False, "限流模式下，單次操作成本過高"
                
        return True, decision.message

    async def post_operation_update(self, actual_cost: float, operation_result: bool = True):
        """操作後更新"""
        if actual_cost > 0:
            # 記錄實際成本（這應該由 CostTracker 處理）
            logger.info(f"操作完成，實際成本: ${actual_cost:.4f}")
            
        # 重新檢查預算狀態
        await self.check_budget_and_decide()

    def _update_stats(self, decision: BudgetDecision):
        """更新統計資訊"""
        self.daily_stats['decisions_count'] += 1
        
        if decision.action == ActionType.THROTTLE:
            self.daily_stats['throttle_events'] += 1
        elif decision.action == ActionType.PAUSE:
            self.daily_stats['pause_events'] += 1
        elif decision.action == ActionType.STOP:
            self.daily_stats['stop_events'] += 1

    async def _log_decision(self, decision: BudgetDecision, budget_status: Dict[str, Any]):
        """記錄預算決策"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "status": decision.status.value,
            "action": decision.action.value,
            "can_continue": decision.can_continue,
            "message": decision.message,
            "usage_rate": decision.metadata.get("usage_rate", 0) if decision.metadata else 0,
            "current_cost": decision.current_usage,
            "remaining_budget": decision.remaining_budget,
            "budget_limit": budget_status.get("budget_limit", 0)
        }
        
        # 儲存決策日誌
        log_file = Path("monitoring/budget_decisions.json")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except Exception:
                logs = []
                
        logs.append(log_entry)
        
        # 只保留最近1000筆記錄
        logs = logs[-1000:]
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)

    async def get_daily_budget_report(self) -> Dict[str, Any]:
        """獲取每日預算報告"""
        budget_status = await self.cost_tracker.check_budget_status()
        
        return {
            "date": date.today().isoformat(),
            "budget_status": budget_status,
            "current_status": self.current_status.value,
            "daily_stats": self.daily_stats,
            "rules_summary": [
                {
                    "threshold": rule.threshold_percentage,
                    "action": rule.action.value,
                    "message": rule.message
                }
                for rule in self.rules
            ],
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None,
            "generated_at": datetime.now().isoformat()
        }

    async def adjust_budget_dynamically(self, new_budget: float, reason: str = ""):
        """動態調整預算"""
        if not self.config_manager:
            logger.warning("無配置管理器，無法動態調整預算")
            return False
            
        old_budget = self.config_manager.get("cost_control.daily_budget_usd", 100.0)
        
        # 更新配置
        self.config_manager.set("cost_control.daily_budget_usd", new_budget)
        
        # 記錄調整
        adjustment_log = {
            "timestamp": datetime.now().isoformat(),
            "old_budget": old_budget,
            "new_budget": new_budget,
            "change": new_budget - old_budget,
            "reason": reason,
            "adjusted_by": "budget_controller"
        }
        
        log_file = Path("monitoring/budget_adjustments.json")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        adjustments = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    adjustments = json.load(f)
            except Exception:
                adjustments = []
                
        adjustments.append(adjustment_log)
        adjustments = adjustments[-100:]  # 保留最近100筆
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(adjustments, f, indent=2, ensure_ascii=False)
            
        logger.info(f"預算已調整: ${old_budget} -> ${new_budget} ({reason})")
        return True

    def get_current_status(self) -> Dict[str, Any]:
        """獲取當前狀態"""
        return {
            "status": self.current_status.value,
            "last_check": self.last_check_time.isoformat() if self.last_check_time else None,
            "daily_stats": self.daily_stats,
            "rules_count": len(self.rules)
        }


# 全域預算控制器實例
budget_controller = None

def get_budget_controller(config_manager=None):
    """獲取預算控制器實例"""
    global budget_controller
    if budget_controller is None:
        budget_controller = BudgetController(config_manager)
    return budget_controller


async def main():
    """測試預算控制器"""
    controller = BudgetController()
    
    print("=== 預算控制器測試 ===")
    
    # 模擬操作前檢查
    can_proceed, message = await controller.pre_operation_check("video_generation", 2.5)
    print(f"操作前檢查: {can_proceed}, 訊息: {message}")
    
    # 模擬預算決策
    decision = await controller.check_budget_and_decide(1.0)
    print(f"\n預算決策:")
    print(f"狀態: {decision.status.value}")
    print(f"行動: {decision.action.value}")
    print(f"可繼續: {decision.can_continue}")
    print(f"訊息: {decision.message}")
    print(f"建議: {decision.suggested_actions}")
    
    # 獲取報告
    report = await controller.get_daily_budget_report()
    print(f"\n每日報告生成完成")


if __name__ == "__main__":
    asyncio.run(main())