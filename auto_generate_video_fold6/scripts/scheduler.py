#!/usr/bin/env python3
"""
排程器服務 - 自動化影片生成任務調度
支援配置管理器和成本監控整合
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import json
import time
import signal

# 添加專案路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.config_manager import get_config, get_current_mode

    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

try:
    from monitoring.cost_tracker import get_cost_tracker
    from monitoring.budget_controller import get_budget_controller

    COST_MONITORING_AVAILABLE = True
except ImportError:
    COST_MONITORING_AVAILABLE = False

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/app/logs/scheduler.log"), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class VideoScheduler:
    """影片生成排程器"""

    def __init__(self):
        self.running = True
        self.schedule_config = self._load_schedule_config()
        self.last_run = {}

        # 初始化成本監控 (如果可用)
        if COST_MONITORING_AVAILABLE:
            try:
                config_manager = None
                if CONFIG_MANAGER_AVAILABLE:
                    from config.config_manager import config_manager
                self.cost_tracker = get_cost_tracker(config_manager)
                self.budget_controller = get_budget_controller(config_manager)
                logger.info("成本監控系統已啟用")
            except Exception as e:
                logger.warning(f"成本監控初始化失敗: {e}")
                self.cost_tracker = None
                self.budget_controller = None
        else:
            self.cost_tracker = None
            self.budget_controller = None

    def _load_schedule_config(self):
        """載入排程配置"""
        try:
            if CONFIG_MANAGER_AVAILABLE:
                scheduling = get_config("scheduling", {})
                return {
                    "enabled": scheduling.get("enabled", True),
                    "auto_generation_interval": scheduling.get(
                        "auto_generation_interval", 6
                    ),  # 小時
                    "work_hours_only": scheduling.get("work_hours_only", False),
                    "work_hours": scheduling.get("work_hours", {"start": "09:00", "end": "18:00"}),
                    "max_daily_videos": get_config("generation.daily_video_limit", 10),
                    "batch_size": get_config("generation.batch_size", 3),
                }
            else:
                # 預設配置
                return {
                    "enabled": True,
                    "auto_generation_interval": 6,
                    "work_hours_only": False,
                    "work_hours": {"start": "09:00", "end": "18:00"},
                    "max_daily_videos": 10,
                    "batch_size": 3,
                }
        except Exception as e:
            logger.error(f"載入排程配置失敗: {e}")
            return {"enabled": False}

    def _is_within_work_hours(self):
        """檢查是否在工作時間內"""
        if not self.schedule_config.get("work_hours_only", False):
            return True

        now = datetime.now()
        current_time = now.strftime("%H:%M")

        work_hours = self.schedule_config.get("work_hours", {})
        start_time = work_hours.get("start", "00:00")
        end_time = work_hours.get("end", "23:59")

        return start_time <= current_time <= end_time

    async def _check_budget_permission(self):
        """檢查預算是否允許生成影片"""
        if not self.budget_controller:
            return True, "預算監控未啟用"

        try:
            # 估算批次成本
            estimated_cost = self._estimate_batch_cost()

            can_proceed, message = await self.budget_controller.pre_operation_check(
                "scheduled_generation", estimated_cost
            )

            return can_proceed, message
        except Exception as e:
            logger.error(f"預算檢查失敗: {e}")
            return True, "預算檢查異常，允許繼續"

    def _estimate_batch_cost(self):
        """估算批次生成成本"""
        batch_size = self.schedule_config.get("batch_size", 3)

        # 基於歷史數據的估算
        estimated_cost_per_video = 1.5  # 美元 (腳本 + 圖像 + 語音)

        return batch_size * estimated_cost_per_video

    async def _get_daily_video_count(self):
        """獲取今日已生成影片數量"""
        try:
            # 檢查今日生成記錄
            today = datetime.now().date()
            log_file = Path(f"/app/logs/generation_{today.isoformat()}.json")

            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return len(data.get("generated_videos", []))

            return 0
        except Exception as e:
            logger.error(f"獲取今日影片數量失敗: {e}")
            return 0

    async def _should_run_generation(self):
        """判斷是否應該執行影片生成"""
        # 檢查排程是否啟用
        if not self.schedule_config.get("enabled", True):
            return False, "排程已停用"

        # 檢查工作時間
        if not self._is_within_work_hours():
            return False, "不在工作時間內"

        # 檢查每日限制
        daily_count = await self._get_daily_video_count()
        max_daily = self.schedule_config.get("max_daily_videos", 10)

        if daily_count >= max_daily:
            return False, f"已達每日限制 ({daily_count}/{max_daily})"

        # 檢查間隔時間
        last_run_key = "auto_generation"
        if last_run_key in self.last_run:
            interval_hours = self.schedule_config.get("auto_generation_interval", 6)
            time_since_last = datetime.now() - self.last_run[last_run_key]

            if time_since_last < timedelta(hours=interval_hours):
                remaining = timedelta(hours=interval_hours) - time_since_last
                return False, f"間隔時間未到，剩餘 {remaining}"

        # 檢查預算
        can_proceed, budget_message = await self._check_budget_permission()
        if not can_proceed:
            return False, f"預算限制: {budget_message}"

        return True, "所有檢查通過"

    async def _run_video_generation(self):
        """執行影片生成"""
        try:
            logger.info("開始執行自動影片生成...")

            # 更新最後執行時間
            self.last_run["auto_generation"] = datetime.now()

            # 執行自動生成腳本
            import subprocess

            script_path = project_root / "scripts" / "auto_trends_video.py"
            batch_size = self.schedule_config.get("batch_size", 3)

            cmd = [
                "python",
                str(script_path),
                "--count",
                str(batch_size),
                "--mode",
                "auto",
                "--log-level",
                "INFO",
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(project_root),
            )

            stdout, stderr = process.communicate(timeout=3600)  # 1小時超時

            if process.returncode == 0:
                logger.info("影片生成成功完成")
                logger.info(f"輸出: {stdout}")

                # 記錄成功
                await self._log_generation_result(True, stdout)

            else:
                logger.error(f"影片生成失敗 (退出代碼: {process.returncode})")
                logger.error(f"錯誤: {stderr}")

                # 記錄失敗
                await self._log_generation_result(False, stderr)

        except subprocess.TimeoutExpired:
            logger.error("影片生成超時")
            process.kill()
            await self._log_generation_result(False, "生成超時")

        except Exception as e:
            logger.error(f"執行影片生成時發生錯誤: {e}")
            await self._log_generation_result(False, str(e))

    async def _log_generation_result(self, success: bool, message: str):
        """記錄生成結果"""
        try:
            today = datetime.now().date()
            log_file = Path(f"/app/logs/generation_{today.isoformat()}.json")

            # 載入現有記錄
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = {"date": today.isoformat(), "generation_runs": []}

            # 添加新記錄
            data["generation_runs"].append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "success": success,
                    "message": message,
                    "batch_size": self.schedule_config.get("batch_size", 3),
                }
            )

            # 保存記錄
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"記錄生成結果失敗: {e}")

    async def _check_system_health(self):
        """檢查系統健康狀態"""
        try:
            health_status = {
                "timestamp": datetime.now().isoformat(),
                "services": {},
                "resources": {},
            }

            # 檢查 Redis 連接
            try:
                import redis

                r = redis.Redis(host="redis", port=6379, decode_responses=True)
                r.ping()
                health_status["services"]["redis"] = "healthy"
            except Exception:
                health_status["services"]["redis"] = "unhealthy"

            # 檢查磁盤空間
            import shutil

            total, used, free = shutil.disk_usage("/app")
            health_status["resources"]["disk"] = {
                "total": total,
                "used": used,
                "free": free,
                "usage_percent": (used / total) * 100,
            }

            # 保存健康檢查結果
            health_file = Path("/app/logs/health_check.json")
            with open(health_file, "w", encoding="utf-8") as f:
                json.dump(health_status, f, indent=2, ensure_ascii=False)

            logger.info("系統健康檢查完成")

        except Exception as e:
            logger.error(f"系統健康檢查失敗: {e}")

    async def run(self):
        """主執行迴圈"""
        logger.info("排程器服務已啟動")
        logger.info(f"當前配置: {self.schedule_config}")

        while self.running:
            try:
                # 檢查是否應該執行生成
                should_run, reason = await self._should_run_generation()

                if should_run:
                    logger.info("觸發自動影片生成")
                    await self._run_video_generation()
                else:
                    logger.debug(f"跳過影片生成: {reason}")

                # 執行系統健康檢查
                await self._check_system_health()

                # 等待下次檢查 (每30分鐘檢查一次)
                await asyncio.sleep(1800)

            except Exception as e:
                logger.error(f"排程器執行錯誤: {e}")
                await asyncio.sleep(300)  # 錯誤時等待5分鐘

    def stop(self):
        """停止排程器"""
        logger.info("正在停止排程器服務...")
        self.running = False


def signal_handler(signum, frame):
    """信號處理器"""
    logger.info(f"收到信號 {signum}，正在關閉...")
    if hasattr(signal_handler, "scheduler"):
        signal_handler.scheduler.stop()


async def main():
    """主函數"""
    # 設置信號處理
    scheduler = VideoScheduler()
    signal_handler.scheduler = scheduler

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        await scheduler.run()
    except KeyboardInterrupt:
        logger.info("收到中斷信號，正在關閉...")
    finally:
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
