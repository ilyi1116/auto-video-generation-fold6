#!/usr/bin/env python3
"""
API 成本監控與預算控制系統
支援多供應商成本追蹤與智能預算管理
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import aiofiles

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """AI 服務供應商類型"""

    OPENAI = "openai"
    STABILITY_AI = "stability_ai"
    ELEVENLABS = "elevenlabs"
    ANTHROPIC = "anthropic"
    GOOGLE_VERTEX = "google_vertex"
    GEMINI = "google"
    SUNO = "suno"


@dataclass
class APICallRecord:
    """API 呼叫記錄"""

    timestamp: datetime
    provider: str
    model: str
    operation_type: str  # text_generation, image_generation, voice_synthesis
    tokens_used: int
    cost_usd: float
    request_id: str
    success: bool
    metadata: Dict[str, Any] = None

    def to_dict(self):
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata or {},
        }


@dataclass
class DailyCostSummary:
    """每日成本摘要"""

    date: date
    total_cost: float
    api_calls_count: int
    providers_breakdown: Dict[str, float]
    operations_breakdown: Dict[str, float]
    budget_limit: float
    budget_remaining: float
    is_over_budget: bool


class CostTracker:
    """成本追蹤器"""

    def __init__(self, config_manager=None, db_path: str = None):
        self.config_manager = config_manager
        self.db_path = Path(db_path or "monitoring/cost_tracking.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 成本費率表 (USD)
        self.cost_rates = {
            ProviderType.OPENAI.value: {
                "gpt-4": {"input_per_1k": 0.03, "output_per_1k": 0.06},
                "gpt-3.5-turbo": {"input_per_1k": 0.0015, "output_per_1k": 0.002},
                "gpt-4-turbo": {"input_per_1k": 0.01, "output_per_1k": 0.03},
            },
            ProviderType.STABILITY_AI.value: {
                "stable-diffusion-xl": {"per_image": 0.04},
                "stable-diffusion-3": {"per_image": 0.065},
            },
            ProviderType.ELEVENLABS.value: {"voice_synthesis": {"per_character": 0.00003}},
            ProviderType.ANTHROPIC.value: {
                "claude-3-opus": {"input_per_1k": 0.015, "output_per_1k": 0.075},
                "claude-3-sonnet": {"input_per_1k": 0.003, "output_per_1k": 0.015},
            },
            ProviderType.GEMINI.value: {
                "gemini-pro": {"input_per_1k": 0.0005, "output_per_1k": 0.0015},
                "gemini-1.5-pro": {"input_per_1k": 0.0035, "output_per_1k": 0.0105},
                "gemini-1.5-flash": {"input_per_1k": 0.000075, "output_per_1k": 0.0003},
            },
            ProviderType.SUNO.value: {
                "chirp-v3": {"per_minute": 0.5},  # 估算價格
                "chirp-v3-5": {"per_minute": 0.7},
            },
        }

        # 初始化資料庫
        self._init_database()

        # 當日成本快取
        self._daily_cache = {}
        self._last_cache_update = None

    def _init_database(self):
        """初始化資料庫"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    tokens_used INTEGER DEFAULT 0,
                    cost_usd REAL NOT NULL,
                    request_id TEXT,
                    success BOOLEAN DEFAULT 1,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_summaries (
                    date TEXT PRIMARY KEY,
                    total_cost REAL NOT NULL,
                    api_calls_count INTEGER NOT NULL,
                    providers_breakdown TEXT,
                    operations_breakdown TEXT,
                    budget_limit REAL,
                    budget_remaining REAL,
                    is_over_budget BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_api_calls_date 
                ON api_calls(date(timestamp))
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_api_calls_provider 
                ON api_calls(provider)
            """
            )

        logger.info("成本追蹤資料庫初始化完成")

    async def track_api_call(
        self,
        provider: str,
        model: str,
        operation_type: str,
        tokens_used: int = 0,
        characters_used: int = 0,
        images_generated: int = 0,
        request_id: str = None,
        success: bool = True,
        metadata: Dict[str, Any] = None,
    ) -> float:
        """追蹤 API 呼叫並計算成本"""

        # 計算成本
        cost = self._calculate_cost(
            provider, model, operation_type, tokens_used, characters_used, images_generated
        )

        # 建立記錄
        record = APICallRecord(
            timestamp=datetime.now(),
            provider=provider,
            model=model,
            operation_type=operation_type,
            tokens_used=tokens_used,
            cost_usd=cost,
            request_id=request_id or f"{provider}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            success=success,
            metadata=metadata,
        )

        # 儲存到資料庫
        await self._save_api_call(record)

        # 更新快取
        await self._update_daily_cache()

        # 檢查預算警告
        await self._check_budget_alerts(cost)

        logger.info(f"追蹤 API 呼叫: {provider}.{model} 成本 ${cost:.4f}")
        return cost

    def _calculate_cost(
        self,
        provider: str,
        model: str,
        operation_type: str,
        tokens_used: int,
        characters_used: int,
        images_generated: int,
    ) -> float:
        """計算 API 呼叫成本"""

        if provider not in self.cost_rates:
            logger.warning(f"未知供應商 {provider}，使用預設成本計算")
            return 0.01  # 預設成本

        provider_rates = self.cost_rates[provider]

        if model not in provider_rates:
            logger.warning(f"未知模型 {provider}.{model}，使用預設成本")
            return 0.01

        model_rates = provider_rates[model]

        # 根據操作類型計算成本
        if operation_type == "text_generation":
            # 假設輸入輸出比例 1:1
            input_cost = (tokens_used / 2 / 1000) * model_rates.get("input_per_1k", 0)
            output_cost = (tokens_used / 2 / 1000) * model_rates.get("output_per_1k", 0)
            return input_cost + output_cost

        elif operation_type == "image_generation":
            return images_generated * model_rates.get("per_image", 0.04)

        elif operation_type == "voice_synthesis":
            return characters_used * model_rates.get("per_character", 0.00003)

        elif operation_type == "music_generation":
            # Suno 音樂生成成本按分鐘計算
            duration_minutes = tokens_used / 60.0 if tokens_used > 0 else 0.5  # 預設30秒
            return duration_minutes * model_rates.get("per_minute", 0.5)

        else:
            logger.warning(f"未知操作類型: {operation_type}")
            return 0.01

    async def _save_api_call(self, record: APICallRecord):
        """保存 API 呼叫記錄"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO api_calls 
                (timestamp, provider, model, operation_type, tokens_used, 
                 cost_usd, request_id, success, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    record.timestamp.isoformat(),
                    record.provider,
                    record.model,
                    record.operation_type,
                    record.tokens_used,
                    record.cost_usd,
                    record.request_id,
                    record.success,
                    json.dumps(record.metadata or {}),
                ),
            )

    async def _update_daily_cache(self):
        """更新每日成本快取"""
        today = date.today()

        if (
            self._last_cache_update
            and self._last_cache_update.date() == today
            and (datetime.now() - self._last_cache_update).seconds < 300
        ):  # 5分鐘快取
            return

        # 查詢今日成本
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT 
                    SUM(cost_usd) as total_cost,
                    COUNT(*) as call_count,
                    provider,
                    operation_type
                FROM api_calls 
                WHERE date(timestamp) = ?
                GROUP BY provider, operation_type
            """,
                (today.isoformat(),),
            )

            results = cursor.fetchall()

        # 重建快取
        self._daily_cache = {"total_cost": 0.0, "call_count": 0, "providers": {}, "operations": {}}

        for row in results:
            total_cost, call_count, provider, operation_type = row
            self._daily_cache["total_cost"] += total_cost or 0
            self._daily_cache["call_count"] += call_count or 0

            if provider not in self._daily_cache["providers"]:
                self._daily_cache["providers"][provider] = 0
            if operation_type not in self._daily_cache["operations"]:
                self._daily_cache["operations"][operation_type] = 0

            self._daily_cache["providers"][provider] += total_cost or 0
            self._daily_cache["operations"][operation_type] += total_cost or 0

        self._last_cache_update = datetime.now()

    async def _check_budget_alerts(self, new_cost: float):
        """檢查預算警告"""
        if not self.config_manager:
            return

        daily_budget = self.config_manager.get("cost_control.daily_budget_usd", 100.0)
        current_cost = self._daily_cache.get("total_cost", 0) + new_cost

        # 預算使用率警告
        usage_rate = current_cost / daily_budget

        if usage_rate >= 0.9:
            logger.warning(
                f"⚠️  預算警告: 已使用 {usage_rate:.1%} ({current_cost:.2f}/${daily_budget})"
            )
            await self._send_budget_alert("critical", usage_rate, current_cost, daily_budget)
        elif usage_rate >= 0.8:
            logger.warning(
                f"📊 預算提醒: 已使用 {usage_rate:.1%} ({current_cost:.2f}/${daily_budget})"
            )
            await self._send_budget_alert("warning", usage_rate, current_cost, daily_budget)

    async def _send_budget_alert(
        self, level: str, usage_rate: float, current_cost: float, budget: float
    ):
        """發送預算警告"""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "usage_rate": usage_rate,
            "current_cost": current_cost,
            "daily_budget": budget,
            "message": f"預算使用率達到 {usage_rate:.1%}",
        }

        # 儲存警告記錄
        alert_file = Path("monitoring/budget_alerts.json")
        alert_file.parent.mkdir(parents=True, exist_ok=True)

        alerts = []
        if alert_file.exists():
            async with aiofiles.open(alert_file, "r", encoding="utf-8") as f:
                content = await f.read()
                alerts = json.loads(content) if content else []

        alerts.append(alert_data)

        # 只保留最近100筆警告
        alerts = alerts[-100:]

        async with aiofiles.open(alert_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(alerts, indent=2, ensure_ascii=False))

    async def get_daily_summary(self, target_date: date = None) -> DailyCostSummary:
        """獲取每日成本摘要"""
        if target_date is None:
            target_date = date.today()

        # 如果是今天，使用快取
        if target_date == date.today():
            await self._update_daily_cache()

            daily_budget = 100.0
            if self.config_manager:
                daily_budget = self.config_manager.get("cost_control.daily_budget_usd", 100.0)

            total_cost = self._daily_cache.get("total_cost", 0)

            return DailyCostSummary(
                date=target_date,
                total_cost=total_cost,
                api_calls_count=self._daily_cache.get("call_count", 0),
                providers_breakdown=self._daily_cache.get("providers", {}),
                operations_breakdown=self._daily_cache.get("operations", {}),
                budget_limit=daily_budget,
                budget_remaining=max(0, daily_budget - total_cost),
                is_over_budget=total_cost > daily_budget,
            )

        # 歷史資料查詢
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT 
                    SUM(cost_usd) as total_cost,
                    COUNT(*) as call_count
                FROM api_calls 
                WHERE date(timestamp) = ?
            """,
                (target_date.isoformat(),),
            )

            result = cursor.fetchone()
            total_cost = result[0] or 0
            call_count = result[1] or 0

        return DailyCostSummary(
            date=target_date,
            total_cost=total_cost,
            api_calls_count=call_count,
            providers_breakdown={},
            operations_breakdown={},
            budget_limit=100.0,
            budget_remaining=max(0, 100.0 - total_cost),
            is_over_budget=total_cost > 100.0,
        )

    async def get_weekly_report(self) -> Dict[str, Any]:
        """獲取週報告"""
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT 
                    date(timestamp) as call_date,
                    SUM(cost_usd) as daily_cost,
                    COUNT(*) as daily_calls,
                    provider,
                    operation_type
                FROM api_calls 
                WHERE date(timestamp) BETWEEN ? AND ?
                GROUP BY call_date, provider, operation_type
                ORDER BY call_date DESC
            """,
                (start_date.isoformat(), end_date.isoformat()),
            )

            results = cursor.fetchall()

        # 組織資料
        daily_stats = {}
        total_cost = 0
        total_calls = 0

        for row in results:
            call_date, daily_cost, daily_calls, provider, operation_type = row
            if call_date not in daily_stats:
                daily_stats[call_date] = {"cost": 0, "calls": 0, "providers": {}, "operations": {}}

            daily_stats[call_date]["cost"] += daily_cost or 0
            daily_stats[call_date]["calls"] += daily_calls or 0

            if provider not in daily_stats[call_date]["providers"]:
                daily_stats[call_date]["providers"][provider] = 0
            if operation_type not in daily_stats[call_date]["operations"]:
                daily_stats[call_date]["operations"][operation_type] = 0

            daily_stats[call_date]["providers"][provider] += daily_cost or 0
            daily_stats[call_date]["operations"][operation_type] += daily_cost or 0

            total_cost += daily_cost or 0
            total_calls += daily_calls or 0

        return {
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_cost": total_cost,
            "total_calls": total_calls,
            "average_daily_cost": total_cost / 7,
            "daily_stats": daily_stats,
            "generated_at": datetime.now().isoformat(),
        }

    async def check_budget_status(self) -> Dict[str, Any]:
        """檢查預算狀態"""
        summary = await self.get_daily_summary()

        return {
            "current_cost": summary.total_cost,
            "budget_limit": summary.budget_limit,
            "budget_remaining": summary.budget_remaining,
            "usage_percentage": (summary.total_cost / summary.budget_limit) * 100,
            "is_over_budget": summary.is_over_budget,
            "can_continue": not summary.is_over_budget
            or not self._should_stop_on_budget_exceeded(),
            "providers_breakdown": summary.providers_breakdown,
            "operations_breakdown": summary.operations_breakdown,
        }

    def _should_stop_on_budget_exceeded(self) -> bool:
        """檢查是否應該在預算超支時停止"""
        if not self.config_manager:
            return True
        return self.config_manager.get("cost_control.stop_on_budget_exceeded", True)

    async def export_cost_data(self, days: int = 30) -> str:
        """匯出成本資料"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT * FROM api_calls 
                WHERE date(timestamp) BETWEEN ? AND ?
                ORDER BY timestamp DESC
            """,
                (start_date.isoformat(), end_date.isoformat()),
            )

            columns = [description[0] for description in cursor.description]
            results = cursor.fetchall()

        # 轉換為字典列表
        data = []
        for row in results:
            record = dict(zip(columns, row))
            if record["metadata"]:
                record["metadata"] = json.loads(record["metadata"])
            data.append(record)

        # 儲存匯出資料
        export_file = Path(
            f"monitoring/cost_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        export_file.parent.mkdir(parents=True, exist_ok=True)

        export_data = {
            "export_date": datetime.now().isoformat(),
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "total_records": len(data),
            "records": data,
        }

        async with aiofiles.open(export_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(export_data, indent=2, ensure_ascii=False))

        logger.info(f"成本資料已匯出至: {export_file}")
        return str(export_file)


# 全域成本追蹤器實例
cost_tracker = None


def get_cost_tracker(config_manager=None):
    """獲取成本追蹤器實例"""
    global cost_tracker
    if cost_tracker is None:
        cost_tracker = CostTracker(config_manager)
    return cost_tracker


async def main():
    """測試成本追蹤器"""
    tracker = CostTracker()

    print("=== 成本追蹤器測試 ===")

    # 模擬一些 API 呼叫
    await tracker.track_api_call("openai", "gpt-4", "text_generation", tokens_used=1000)
    await tracker.track_api_call(
        "stability_ai", "stable-diffusion-xl", "image_generation", images_generated=2
    )
    await tracker.track_api_call(
        "elevenlabs", "voice_synthesis", "voice_synthesis", characters_used=500
    )

    # 獲取今日摘要
    summary = await tracker.get_daily_summary()
    print(f"\n今日成本摘要:")
    print(f"總成本: ${summary.total_cost:.4f}")
    print(f"API 呼叫次數: {summary.api_calls_count}")
    print(f"預算剩餘: ${summary.budget_remaining:.2f}")

    # 檢查預算狀態
    budget_status = await tracker.check_budget_status()
    print(f"\n預算狀態:")
    print(f"使用率: {budget_status['usage_percentage']:.1f}%")
    print(f"可繼續操作: {budget_status['can_continue']}")


if __name__ == "__main__":
    asyncio.run(main())
