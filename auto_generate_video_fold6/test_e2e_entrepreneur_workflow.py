#!/usr/bin/env python3
"""
TDD Red 階段: 端對端創業者工作流程整合測試
測試完整的創業者模式從啟動到影片發布的整個流程

測試範圍：
1. 系統啟動和服務發現
2. 趨勢抓取和關鍵字分析
3. 排程任務創建和執行
4. 影片生成工作流程
5. 多平台自動發布
6. 錯誤處理和恢復機制
"""

import asyncio
import pytest
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging
import sys

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 服務端點配置
SERVICES = {
    "trend_service": "http://localhost:8001",
    "video_service": "http://localhost:8003", 
    "social_service": "http://localhost:8004",
    "scheduler_service": "http://localhost:8008"
}

# 測試配置
TEST_CONFIG = {
    "user_id": "e2e_test_user",
    "entrepreneur_config": {
        "enabled": True,
        "work_hours_start": "00:00",
        "work_hours_end": "23:59",
        "daily_video_limit": 3,
        "daily_budget_limit": 15.0,
        "max_concurrent_tasks": 2,
        "check_interval_minutes": 1,
        "categories": ["technology", "ai"],
        "platforms": ["tiktok", "youtube-shorts"],
        "auto_publish": True
    },
    "expected_workflow_steps": [
        "trend_analysis",
        "keyword_extraction", 
        "script_generation",
        "image_generation",
        "voice_synthesis",
        "video_composition",
        "platform_publishing"
    ]
}

class E2ETestResult:
    """E2E 測試結果追蹤"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.service_health_checks: Dict[str, bool] = {}
        self.workflow_steps: Dict[str, Dict] = {}
        self.errors: List[str] = []
        self.success_rate = 0.0
        self.total_execution_time = 0.0
        
    def add_error(self, error: str):
        self.errors.append(f"[{datetime.utcnow().isoformat()}] {error}")
        logger.error(error)
        
    def add_step_result(self, step: str, success: bool, duration: float, details: Dict = None):
        self.workflow_steps[step] = {
            "success": success,
            "duration": duration,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        
    def finalize(self):
        self.total_execution_time = (datetime.utcnow() - self.start_time).total_seconds()
        successful_steps = sum(1 for step in self.workflow_steps.values() if step["success"])
        self.success_rate = (successful_steps / len(self.workflow_steps)) * 100 if self.workflow_steps else 0


class E2ETestRunner:
    """端對端測試執行器"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.result = E2ETestResult()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300)  # 5分鐘超時
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def health_check_services(self) -> bool:
        """檢查所有服務健康狀態"""
        logger.info("🏥 開始服務健康檢查...")
        
        all_healthy = True
        for service_name, base_url in SERVICES.items():
            try:
                async with self.session.get(f"{base_url}/health") as response:
                    is_healthy = response.status == 200
                    self.result.service_health_checks[service_name] = is_healthy
                    
                    if is_healthy:
                        logger.info(f"✅ {service_name} 健康狀態正常")
                    else:
                        logger.error(f"❌ {service_name} 健康檢查失敗 (HTTP {response.status})")
                        all_healthy = False
                        
            except Exception as e:
                self.result.service_health_checks[service_name] = False
                self.result.add_error(f"{service_name} 連接失敗: {str(e)}")
                all_healthy = False
                
        return all_healthy
        
    async def test_trend_analysis_flow(self) -> Dict[str, Any]:
        """測試趨勢分析流程"""
        logger.info("📈 測試趨勢分析流程...")
        start_time = time.time()
        
        try:
            # 1. 觸發趨勢抓取
            trend_url = f"{SERVICES['trend_service']}/api/v1/entrepreneur/fetch-trends"
            trend_payload = {
                "categories": TEST_CONFIG["entrepreneur_config"]["categories"],
                "platforms": ["tiktok", "youtube"],
                "hours_back": 24,
                "min_engagement": 1000
            }
            
            async with self.session.post(trend_url, json=trend_payload) as response:
                if response.status != 200:
                    raise Exception(f"趨勢抓取失敗: HTTP {response.status}")
                    
                trend_data = await response.json()
                
            # 2. 驗證趨勢數據格式
            required_fields = ["trends", "total_count", "categories_analyzed"]
            for field in required_fields:
                if field not in trend_data:
                    raise Exception(f"趨勢數據缺少必要欄位: {field}")
                    
            # 3. 檢查趨勢品質
            trends = trend_data.get("trends", [])
            if len(trends) < 3:
                raise Exception(f"趨勢數量不足，僅獲得 {len(trends)} 個趨勢")
                
            high_quality_trends = [
                t for t in trends 
                if t.get("engagement_score", 0) >= 0.7
            ]
            
            duration = time.time() - start_time
            self.result.add_step_result("trend_analysis", True, duration, {
                "trends_found": len(trends),
                "high_quality_trends": len(high_quality_trends),
                "categories": trend_data.get("categories_analyzed", [])
            })
            
            return trend_data
            
        except Exception as e:
            duration = time.time() - start_time
            self.result.add_step_result("trend_analysis", False, duration)
            self.result.add_error(f"趨勢分析失敗: {str(e)}")
            raise
            
    async def test_scheduler_configuration(self) -> str:
        """測試排程器配置"""
        logger.info("⚙️ 測試排程器配置...")
        start_time = time.time()
        
        try:
            # 配置排程器
            config_url = f"{SERVICES['scheduler_service']}/api/v1/entrepreneur-scheduler/configure"
            config_payload = TEST_CONFIG["entrepreneur_config"]
            
            # 添加測試用戶認證頭 (在實際環境中會從認證服務獲取)
            headers = {
                "Authorization": "Bearer test_token_e2e",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(config_url, json=config_payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"排程器配置失敗: HTTP {response.status}")
                    
                config_result = await response.json()
                
            # 啟動排程器
            start_url = f"{SERVICES['scheduler_service']}/api/v1/entrepreneur-scheduler/start"
            async with self.session.post(start_url, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"排程器啟動失敗: HTTP {response.status}")
                    
                start_result = await response.json()
                
            duration = time.time() - start_time
            self.result.add_step_result("scheduler_config", True, duration, {
                "config_status": config_result.get("status"),
                "scheduler_status": start_result.get("status")
            })
            
            return start_result.get("message", "排程器已啟動")
            
        except Exception as e:
            duration = time.time() - start_time
            self.result.add_step_result("scheduler_config", False, duration)
            self.result.add_error(f"排程器配置失敗: {str(e)}")
            raise
            
    async def test_video_workflow_execution(self, trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """測試影片工作流程執行"""
        logger.info("🎬 測試影片工作流程執行...")
        start_time = time.time()
        
        try:
            # 選擇最高分趨勢
            trends = trend_data.get("trends", [])
            if not trends:
                raise Exception("沒有可用的趨勢數據")
                
            best_trend = max(trends, key=lambda t: t.get("engagement_score", 0))
            
            # 創建影片工作流程
            workflow_url = f"{SERVICES['video_service']}/api/v1/entrepreneur/create"
            workflow_payload = {
                "user_id": TEST_CONFIG["user_id"],
                "trend_keywords": best_trend.get("keywords", []),
                "video_count": 1,
                "categories": TEST_CONFIG["entrepreneur_config"]["categories"],
                "platforms": TEST_CONFIG["entrepreneur_config"]["platforms"],
                "quality_threshold": 0.8
            }
            
            headers = {
                "Authorization": "Bearer test_token_e2e",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(workflow_url, json=workflow_payload, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"影片工作流程創建失敗: HTTP {response.status}, 錯誤: {error_text}")
                    
                workflow_result = await response.json()
                
            workflow_id = workflow_result.get("workflow_id")
            if not workflow_id:
                raise Exception("工作流程ID未返回")
                
            # 監控工作流程進度
            progress_url = f"{SERVICES['video_service']}/api/v1/entrepreneur/status/{workflow_id}"
            max_wait_time = 300  # 5分鐘最大等待時間
            start_wait = time.time()
            
            final_status = None
            while time.time() - start_wait < max_wait_time:
                async with self.session.get(progress_url, headers=headers) as response:
                    if response.status == 200:
                        status_data = await response.json()
                        current_status = status_data.get("status")
                        
                        logger.info(f"工作流程 {workflow_id} 狀態: {current_status}")
                        
                        if current_status in ["completed", "failed"]:
                            final_status = status_data
                            break
                            
                await asyncio.sleep(10)  # 每10秒檢查一次
                
            if not final_status:
                raise Exception("工作流程執行超時")
                
            if final_status.get("status") != "completed":
                raise Exception(f"工作流程執行失敗: {final_status.get('error')}")
                
            duration = time.time() - start_time
            self.result.add_step_result("video_workflow", True, duration, {
                "workflow_id": workflow_id,
                "videos_generated": final_status.get("videos_generated", 0),
                "total_steps": len(final_status.get("step_results", {}))
            })
            
            return final_status
            
        except Exception as e:
            duration = time.time() - start_time
            self.result.add_step_result("video_workflow", False, duration)
            self.result.add_error(f"影片工作流程失敗: {str(e)}")
            raise
            
    async def test_publishing_workflow(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """測試發布工作流程"""
        logger.info("📢 測試發布工作流程...")
        start_time = time.time()
        
        try:
            videos = video_data.get("generated_videos", [])
            if not videos:
                raise Exception("沒有可發布的影片")
                
            video = videos[0]  # 取第一個影片
            
            # 發布到各個平台
            publish_url = f"{SERVICES['social_service']}/api/v1/entrepreneur/publish"
            publish_payload = {
                "user_id": TEST_CONFIG["user_id"],
                "video_id": video.get("video_id"),
                "platforms": TEST_CONFIG["entrepreneur_config"]["platforms"],
                "scheduled_time": None,  # 立即發布
                "metadata": {
                    "title": video.get("title"),
                    "description": video.get("description"),
                    "tags": video.get("tags", [])
                }
            }
            
            headers = {
                "Authorization": "Bearer test_token_e2e",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(publish_url, json=publish_payload, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"發布請求失敗: HTTP {response.status}")
                    
                publish_result = await response.json()
                
            publish_id = publish_result.get("publish_id")
            
            # 監控發布狀態
            status_url = f"{SERVICES['social_service']}/api/v1/entrepreneur/publish-status/{publish_id}"
            max_wait_time = 120  # 2分鐘等待發布完成
            start_wait = time.time()
            
            final_publish_status = None
            while time.time() - start_wait < max_wait_time:
                async with self.session.get(status_url, headers=headers) as response:
                    if response.status == 200:
                        status_data = await response.json()
                        
                        if status_data.get("all_completed", False):
                            final_publish_status = status_data
                            break
                            
                await asyncio.sleep(5)  # 每5秒檢查一次
                
            if not final_publish_status:
                raise Exception("發布流程監控超時")
                
            successful_platforms = [
                p for p in final_publish_status.get("platform_results", {}).values()
                if p.get("status") == "success"
            ]
            
            if len(successful_platforms) == 0:
                raise Exception("所有平台發布都失敗")
                
            duration = time.time() - start_time
            self.result.add_step_result("publishing_workflow", True, duration, {
                "publish_id": publish_id,
                "successful_platforms": len(successful_platforms),
                "total_platforms": len(TEST_CONFIG["entrepreneur_config"]["platforms"])
            })
            
            return final_publish_status
            
        except Exception as e:
            duration = time.time() - start_time
            self.result.add_step_result("publishing_workflow", False, duration)
            self.result.add_error(f"發布工作流程失敗: {str(e)}")
            raise
            
    async def test_error_recovery(self) -> bool:
        """測試錯誤恢復機制"""
        logger.info("🔄 測試錯誤恢復機制...")
        start_time = time.time()
        
        try:
            # 創建一個預期會失敗的任務
            workflow_url = f"{SERVICES['video_service']}/api/v1/entrepreneur/create"
            invalid_payload = {
                "user_id": TEST_CONFIG["user_id"],
                "trend_keywords": [],  # 空關鍵字應該導致失敗
                "video_count": 0,      # 無效數量
                "categories": [],
                "platforms": []
            }
            
            headers = {
                "Authorization": "Bearer test_token_e2e",
                "Content-Type": "application/json"
            }
            
            async with self.session.post(workflow_url, json=invalid_payload, headers=headers) as response:
                error_response = await response.json()
                
                # 驗證系統正確返回錯誤
                if response.status == 200:
                    raise Exception("系統應該拒絕無效請求但沒有")
                    
                if response.status not in [400, 422]:
                    raise Exception(f"錯誤狀態碼不正確: {response.status}")
                    
            # 測試排程器對失敗任務的處理
            status_url = f"{SERVICES['scheduler_service']}/api/v1/entrepreneur-scheduler/status"
            async with self.session.get(status_url, headers=headers) as response:
                if response.status == 200:
                    scheduler_status = await response.json()
                    
                    # 驗證排程器仍在正常運行
                    if not scheduler_status.get("is_running", False):
                        raise Exception("排程器因錯誤停止運行")
                        
            duration = time.time() - start_time
            self.result.add_step_result("error_recovery", True, duration, {
                "error_handled": True,
                "scheduler_stable": True
            })
            
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.result.add_step_result("error_recovery", False, duration)
            self.result.add_error(f"錯誤恢復測試失敗: {str(e)}")
            return False


async def run_e2e_tests():
    """執行完整的端對端測試"""
    logger.info("🚀 開始創業者模式端對端整合測試")
    logger.info("=" * 60)
    
    async with E2ETestRunner() as runner:
        try:
            # 1. 服務健康檢查
            if not await runner.health_check_services():
                logger.error("❌ 服務健康檢查失敗，停止測試")
                return False
                
            logger.info("✅ 所有服務健康檢查通過")
            
            # 2. 趨勢分析流程測試
            trend_data = await runner.test_trend_analysis_flow()
            logger.info("✅ 趨勢分析流程測試通過")
            
            # 3. 排程器配置測試
            await runner.test_scheduler_configuration()
            logger.info("✅ 排程器配置測試通過")
            
            # 4. 影片工作流程測試
            video_data = await runner.test_video_workflow_execution(trend_data)
            logger.info("✅ 影片工作流程測試通過")
            
            # 5. 發布工作流程測試
            publish_data = await runner.test_publishing_workflow(video_data)
            logger.info("✅ 發布工作流程測試通過")
            
            # 6. 錯誤恢復測試
            await runner.test_error_recovery()
            logger.info("✅ 錯誤恢復機制測試通過")
            
            # 完成測試並生成報告
            runner.result.finalize()
            
            logger.info("=" * 60)
            logger.info("🎉 端對端整合測試完成！")
            logger.info(f"📊 測試成功率: {runner.result.success_rate:.1f}%")
            logger.info(f"⏱️  總執行時間: {runner.result.total_execution_time:.2f}秒")
            
            if runner.result.errors:
                logger.info("⚠️  發現的問題:")
                for error in runner.result.errors:
                    logger.info(f"   - {error}")
                    
            return runner.result.success_rate >= 80.0  # 80%成功率算通過
            
        except Exception as e:
            runner.result.add_error(f"E2E測試執行異常: {str(e)}")
            runner.result.finalize()
            
            logger.error("❌ 端對端整合測試失敗")
            logger.error(f"錯誤詳情: {str(e)}")
            return False


if __name__ == "__main__":
    # 執行端對端測試
    success = asyncio.run(run_e2e_tests())
    
    if success:
        logger.info("🎯 E2E測試通過 - 系統準備就緒！")
        sys.exit(0)
    else:
        logger.error("💥 E2E測試失敗 - 需要修復問題")
        sys.exit(1)