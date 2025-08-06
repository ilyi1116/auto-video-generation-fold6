#!/usr/bin/env python3
"""
統一配置管理系統
支援多層次配置繼承與動態載入
"""

import copy
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ConfigManager:
    """統一配置管理器"""

    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or os.path.join(os.path.dirname(__file__)))
        self.current_config: Dict[str, Any] = {}
        self.base_config: Dict[str, Any] = {}
        self.mode_config: Dict[str, Any] = {}
        self.current_mode: str = "base"

        # 載入基礎配置
        self._load_base_config()

    def _load_base_config(self) -> None:
        """載入基礎配置"""
        base_config_path = self.config_dir / "base-config.json"

        if not base_config_path.exists():
            logger.error(f"基礎配置檔案不存在: {base_config_path}")
            raise FileNotFoundError(f"Base config not found: {base_config_path}")

        with open(base_config_path, "r", encoding="utf-8") as f:
            self.base_config = json.load(f)

        logger.info("已載入基礎配置")

    def load_mode_config(self, mode: str) -> Dict[str, Any]:
        """載入特定模式配置"""
        mode_config_path = self.config_dir / f"{mode}-config.json"

        if not mode_config_path.exists():
            logger.warning(f"模式配置檔案不存在: {mode_config_path}")
            return {}

        with open(mode_config_path, "r", encoding="utf-8") as f:
            mode_config = json.load(f)

        logger.info(f"已載入 {mode} 模式配置")
        return mode_config

    def set_mode(self, mode: str) -> None:
        """設置當前模式"""
        if mode == self.current_mode:
            logger.info(f"已經是 {mode} 模式")
            return

        self.mode_config = self.load_mode_config(mode)
        self.current_mode = mode

        # 合併配置
        self._merge_configs()

        logger.info(f"已切換到 {mode} 模式")

    def _merge_configs(self) -> None:
        """合併基礎配置與模式配置"""
        self.current_config = copy.deepcopy(self.base_config)

        # 深度合併模式配置
        self._deep_merge(self.current_config, self.mode_config)

        # 添加元信息
        self.current_config["_metadata"] = {
            "mode": self.current_mode,
            "merged_at": datetime.now().isoformat(),
            "config_dir": str(self.config_dir),
        }

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """深度合併字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, key_path: str, default: Any = None) -> Any:
        """獲取配置值 (支援點記法)"""
        keys = key_path.split(".")
        current = self.current_config

        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any) -> None:
        """設置配置值 (支援點記法)"""
        keys = key_path.split(".")
        current = self.current_config

        # 導航到目標位置
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # 設置值
        current[keys[-1]] = value

    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """獲取特定服務配置"""
        return self.get(f"services.{service_name}", {})

    def get_generation_config(self) -> Dict[str, Any]:
        """獲取生成配置"""
        return self.get("generation", {})

    def get_cost_config(self) -> Dict[str, Any]:
        """獲取成本控制配置"""
        return self.get("cost_control", {})

    def get_resource_config(self) -> Dict[str, Any]:
        """獲取資源配置"""
        return self.get("resources", {})

    def is_within_work_hours(self) -> bool:
        """檢查是否在工作時間內"""
        scheduling = self.get("scheduling", {})

        if not scheduling.get("enabled", True):
            return True

        work_hours = scheduling.get("work_hours", {})
        if not work_hours:
            return True

        # 簡化實現 - 實際應該考慮時區
        now = datetime.now()
        current_time = now.strftime("%H:%M")

        start_time = work_hours.get("start", "00:00")
        end_time = work_hours.get("end", "23:59")

        return start_time <= current_time <= end_time

    def check_daily_limit(self, current_count: int) -> bool:
        """檢查是否達到每日限制"""
        daily_limit = self.get("generation.daily_video_limit", 999)
        return current_count < daily_limit

    def check_budget_limit(self, current_cost: float) -> bool:
        """檢查是否超出預算"""
        daily_budget = self.get("cost_control.daily_budget_usd", 999.0)
        return current_cost < daily_budget

    def get_api_rate_limit(self, provider: str) -> int:
        """獲取 API 速率限制"""
        return self.get(f"cost_control.api_rate_limits.{provider}_requests_per_hour", 100)

    def save_current_config(self, filename: str = None) -> str:
        """保存當前配置到檔案"""
        if filename is None:
            filename = f"current-config-{self.current_mode}.json"

        output_path = self.config_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.current_config, f, indent=2, ensure_ascii=False)

        logger.info(f"已保存當前配置到: {output_path}")
        return str(output_path)

    def validate_config(self) -> List[str]:
        """驗證配置完整性"""
        errors = []

        # 檢查必要欄位
        required_fields = [
            "generation.daily_video_limit",
            "generation.platforms",
            "ai_services.text_generation.provider",
            "ai_services.image_generation.provider",
        ]

        for field in required_fields:
            if self.get(field) is None:
                errors.append(f"缺少必要配置: {field}")

        # 檢查數值範圍
        daily_limit = self.get("generation.daily_video_limit", 0)
        if daily_limit <= 0:
            errors.append("每日影片限制必須大於 0")

        budget = self.get("cost_control.daily_budget_usd", 0)
        if budget <= 0:
            errors.append("每日預算必須大於 0")

        return errors

    def get_platform_config(self, platform: str) -> Dict[str, Any]:
        """獲取特定平台配置"""
        return self.get(f"video_styles.{platform}", {})

    def get_content_template(self, category: str, template_type: str = "intro") -> List[str]:
        """獲取內容模板"""
        return self.get(f"content_templates.{category}.{template_type}_templates", [])

    def get_enabled_platforms(self) -> List[str]:
        """獲取啟用的平台列表"""
        return self.get("generation.platforms", [])

    def export_config(self, export_path: str = None) -> str:
        """匯出完整配置"""
        if export_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = self.config_dir / f"config_export_{timestamp}.json"
        else:
            export_path = Path(export_path)

        export_data = {
            "base_config": self.base_config,
            "mode_config": self.mode_config,
            "current_config": self.current_config,
            "current_mode": self.current_mode,
            "export_timestamp": datetime.now().isoformat(),
        }

        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"已匯出配置到: {export_path}")
        return str(export_path)

    def get_summary(self) -> Dict[str, Any]:
        """獲取配置摘要"""
        return {
            "current_mode": self.current_mode,
            "daily_video_limit": self.get("generation.daily_video_limit"),
            "daily_budget": self.get("cost_control.daily_budget_usd"),
            "enabled_platforms": self.get_enabled_platforms(),
            "resource_limits": {
                "memory": self.get("resources.max_memory_usage"),
                "cpu_cores": self.get("resources.max_cpu_cores"),
            },
            "scheduling_enabled": self.get("scheduling.enabled"),
            "work_hours": self.get("scheduling.work_hours", {}),
            "auto_publish": self.get("social_publishing.auto_publish"),
            "monitoring_enabled": self.get("monitoring.basic_logging"),
        }


# 全域配置管理器實例
config_manager = ConfigManager()


# 便利函數
def get_config(key_path: str, default: Any = None) -> Any:
    """獲取配置值的便利函數"""
    return config_manager.get(key_path, default)


def set_mode(mode: str) -> None:
    """設置模式的便利函數"""
    config_manager.set_mode(mode)


def get_current_mode() -> str:
    """獲取當前模式"""
    return config_manager.current_mode


if __name__ == "__main__":
    # 測試配置管理器
    cm = ConfigManager()

    print("=== 配置管理器測試 ===")
    print(f"當前模式: {cm.current_mode}")
    print(f"每日限制: {cm.get('generation.daily_video_limit')}")
    print(f"預算: {cm.get('cost_control.daily_budget_usd')}")

    # 測試模式切換
    print("\n=== 測試模式切換 ===")
    try:
        cm.set_mode("startup")
        print(f"切換後模式: {cm.current_mode}")
        print(f"每日限制: {cm.get('generation.daily_video_limit')}")

        cm.set_mode("enterprise")
        print(f"切換後模式: {cm.current_mode}")
        print(f"每日限制: {cm.get('generation.daily_video_limit')}")
    except Exception as e:
        print(f"模式切換測試失敗: {e}")

    # 驗證配置
    print("\n=== 配置驗證 ===")
    errors = cm.validate_config()
    if errors:
        print("配置錯誤:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("配置驗證通過")

    # 顯示摘要
    print("\n=== 配置摘要 ===")
    summary = cm.get_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")
