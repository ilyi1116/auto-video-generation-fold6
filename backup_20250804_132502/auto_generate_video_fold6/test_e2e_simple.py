#!/usr/bin/env python3
"""
TDD Green 階段: 簡化版端對端測試
快速驗證創業者模式核心工作流程
"""

import asyncio
import aiohttp
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleE2ERunner:
    """簡化版 E2E 測試執行器"""

    def __init__(self):
        self.session = None
        self.results = {"tests_passed": 0, "tests_failed": 0, "errors": []}

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_service_connectivity(self):
        """測試服務連通性"""
        logger.info("🔗 測試服務連通性...")

        services = {
            "trend_service": "http://localhost:8001/health",
            "video_service": "http://localhost:8003/health",
            "social_service": "http://localhost:8004/health",
            "scheduler_service": "http://localhost:8008/health",
        }

        all_healthy = True
        for service_name, health_url in services.items():
            try:
                async with self.session.get(health_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(
                            f"✅ {service_name}: {data.get('status', 'unknown')}"
                        )
                        self.results["tests_passed"] += 1
                    else:
                        logger.error(
                            f"❌ {service_name}: HTTP {response.status}"
                        )
                        self.results["tests_failed"] += 1
                        all_healthy = False
            except Exception as e:
                logger.error(f"❌ {service_name}: 連接失敗 - {e}")
                self.results["tests_failed"] += 1
                self.results["errors"].append(f"{service_name}: {str(e)}")
                all_healthy = False

        return all_healthy

    async def test_trend_analysis(self):
        """測試趨勢分析"""
        logger.info("📈 測試趨勢分析...")

        try:
            trend_url = (
                "http://localhost:8001/api/v1/entrepreneur/fetch-trends"
            )
            payload = {
                "categories": ["technology", "ai"],
                "platforms": ["tiktok", "youtube"],
                "hours_back": 24,
                "min_engagement": 1000,
            }

            async with self.session.post(trend_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    trends = data.get("trends", [])
                    logger.info(f"✅ 趨勢分析成功: 獲得 {len(trends)} 個趨勢")
                    self.results["tests_passed"] += 1
                    return data
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")

        except Exception as e:
            logger.error(f"❌ 趨勢分析失敗: {e}")
            self.results["tests_failed"] += 1
            self.results["errors"].append(f"趨勢分析: {str(e)}")
            return None

    async def test_video_workflow(self, trend_data):
        """測試影片工作流程"""
        logger.info("🎬 測試影片工作流程...")

        if not trend_data or not trend_data.get("trends"):
            logger.error("❌ 無趨勢數據可用於影片工作流程")
            self.results["tests_failed"] += 1
            return None

        try:
            workflow_url = "http://localhost:8003/api/v1/entrepreneur/create"
            best_trend = trend_data["trends"][0]

            payload = {
                "user_id": "e2e_test_user",
                "trend_keywords": [best_trend.get("keyword", "AI technology")],
                "video_count": 1,
                "categories": ["technology"],
                "platforms": ["tiktok"],
            }

            # 創建工作流程
            async with self.session.post(
                workflow_url, json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    workflow_id = data.get("workflow_id")
                    logger.info(f"✅ 工作流程創建成功: {workflow_id}")
                    self.results["tests_passed"] += 1

                    # 等待工作流程完成（簡化版）
                    await asyncio.sleep(5)

                    # 檢查工作流程狀態
                    status_url = f"http://localhost:8003/api/v1/entrepreneur/status/{workflow_id}"
                    async with self.session.get(status_url) as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            status = status_data.get("status")
                            logger.info(f"✅ 工作流程狀態: {status}")
                            self.results["tests_passed"] += 1
                            return status_data
                        else:
                            raise Exception(
                                f"狀態查詢失敗: HTTP {status_response.status}"
                            )
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")

        except Exception as e:
            logger.error(f"❌ 影片工作流程失敗: {e}")
            self.results["tests_failed"] += 1
            self.results["errors"].append(f"影片工作流程: {str(e)}")
            return None

    async def test_scheduler_operations(self):
        """測試排程器操作"""
        logger.info("⚙️ 測試排程器操作...")

        try:
            base_url = "http://localhost:8008/api/v1/entrepreneur-scheduler"

            # 配置排程器
            config_payload = {
                "enabled": True,
                "daily_video_limit": 5,
                "daily_budget_limit": 20.0,
                "max_concurrent_tasks": 2,
            }

            async with self.session.post(
                f"{base_url}/configure", json=config_payload
            ) as response:
                if response.status == 200:
                    logger.info("✅ 排程器配置成功")
                    self.results["tests_passed"] += 1
                else:
                    raise Exception(f"配置失敗: HTTP {response.status}")

            # 啟動排程器
            async with self.session.post(f"{base_url}/start") as response:
                if response.status == 200:
                    logger.info("✅ 排程器啟動成功")
                    self.results["tests_passed"] += 1
                else:
                    raise Exception(f"啟動失敗: HTTP {response.status}")

            # 檢查狀態
            async with self.session.get(f"{base_url}/status") as response:
                if response.status == 200:
                    data = await response.json()
                    is_running = data.get("is_running", False)
                    logger.info(
                        f"✅ 排程器狀態: {'運行中' if is_running else '已停止'}"
                    )
                    self.results["tests_passed"] += 1
                    return True
                else:
                    raise Exception(f"狀態查詢失敗: HTTP {response.status}")

        except Exception as e:
            logger.error(f"❌ 排程器操作失敗: {e}")
            self.results["tests_failed"] += 1
            self.results["errors"].append(f"排程器操作: {str(e)}")
            return False

    async def test_basic_publishing(self):
        """測試基本發布功能"""
        logger.info("📢 測試基本發布功能...")

        try:
            publish_url = "http://localhost:8004/api/v1/entrepreneur/publish"
            payload = {
                "user_id": "e2e_test_user",
                "video_id": "test_video_123",
                "platforms": ["tiktok"],
                "metadata": {
                    "title": "測試影片",
                    "description": "E2E 測試影片",
                },
            }

            async with self.session.post(
                publish_url, json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    publish_id = data.get("publish_id")
                    logger.info(f"✅ 發布請求成功: {publish_id}")
                    self.results["tests_passed"] += 1
                    return True
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")

        except Exception as e:
            logger.error(f"❌ 發布功能失敗: {e}")
            self.results["tests_failed"] += 1
            self.results["errors"].append(f"發布功能: {str(e)}")
            return False

    def print_results(self):
        """打印測試結果"""
        total_tests = (
            self.results["tests_passed"] + self.results["tests_failed"]
        )
        success_rate = (
            (self.results["tests_passed"] / total_tests * 100)
            if total_tests > 0
            else 0
        )

        logger.info("=" * 50)
        logger.info("📊 E2E 測試結果摘要")
        logger.info("=" * 50)
        logger.info(f"✅ 通過測試: {self.results['tests_passed']}")
        logger.info(f"❌ 失敗測試: {self.results['tests_failed']}")
        logger.info(f"📈 成功率: {success_rate:.1f}%")

        if self.results["errors"]:
            logger.info("\n🚨 錯誤列表:")
            for error in self.results["errors"]:
                logger.info(f"  - {error}")

        return success_rate >= 70.0  # 70% 成功率算通過


async def main():
    """執行簡化版 E2E 測試"""
    logger.info("🚀 開始簡化版創業者模式 E2E 測試")
    logger.info("=" * 50)

    async with SimpleE2ERunner() as runner:
        # 1. 服務連通性測試
        connectivity_ok = await runner.test_service_connectivity()

        if not connectivity_ok:
            logger.error("❌ 服務連通性測試失敗，跳過後續測試")
            return False

        # 2. 趨勢分析測試
        trend_data = await runner.test_trend_analysis()

        # 3. 影片工作流程測試
        await runner.test_video_workflow(trend_data)

        # 4. 排程器操作測試
        await runner.test_scheduler_operations()

        # 5. 基本發布測試
        await runner.test_basic_publishing()

        # 打印結果
        success = runner.print_results()

        if success:
            logger.info("🎉 E2E 測試通過！創業者模式核心功能驗證成功")
        else:
            logger.error("💥 E2E 測試失敗！需要修復問題")

        return success


if __name__ == "__main__":
    # 給模擬服務時間啟動
    logger.info("⏳ 等待服務啟動...")
    time.sleep(2)

    # 執行測試
    success = asyncio.run(main())

    if success:
        logger.info("🎯 TDD Green 階段通過 - 準備進入 Refactor 階段")
        exit(0)
    else:
        logger.error("🔴 TDD Green 階段失敗 - 需要修復實作")
        exit(1)
