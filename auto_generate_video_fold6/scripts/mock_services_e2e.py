#!/usr/bin/env python3
"""
TDD Green 階段: Mock 服務實作
為 E2E 測試提供輕量級的模擬服務
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import aiohttp
from aiohttp import web
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局狀態存儲
MOCK_DATA = {
    "users": {
        "e2e_test_user": {
            "user_id": "e2e_test_user",
            "email": "e2e@test.com",
            "username": "e2e_tester",
            "created_at": datetime.utcnow().isoformat()
        }
    },
    "trends": [
        {
            "id": 1,
            "keyword": "AI technology breakthrough",
            "platform": "tiktok",
            "engagement_score": 0.855,
            "view_count": 1250000,
            "hashtags": ["#AI", "#technology", "#innovation"],
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": 2,
            "keyword": "Machine learning tutorial",
            "platform": "youtube",
            "engagement_score": 0.782,
            "view_count": 890000,
            "hashtags": ["#ML", "#tutorial", "#coding"],
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": 3,
            "keyword": "Automation tools for business",
            "platform": "tiktok",
            "engagement_score": 0.921,
            "view_count": 2100000,
            "hashtags": ["#automation", "#business", "#tools"],
            "created_at": datetime.utcnow().isoformat()
        }
    ],
    "workflows": {},
    "scheduled_tasks": {},
    "publish_records": {}
}

class MockTrendService:
    """趨勢服務模擬"""
    
    async def handle_health(self, request):
        return web.json_response({"status": "healthy", "service": "trend-service"})
    
    async def handle_fetch_trends(self, request):
        data = await request.json()
        categories = data.get("categories", [])
        platforms = data.get("platforms", [])
        hours_back = data.get("hours_back", 24)
        min_engagement = data.get("min_engagement", 1000)
        
        # 根據參數篩選趨勢
        filtered_trends = []
        for trend in MOCK_DATA["trends"]:
            if platforms and trend["platform"] not in platforms:
                continue
            if trend["view_count"] < min_engagement:
                continue
            filtered_trends.append(trend)
        
        # 模擬處理延遲
        await asyncio.sleep(0.5)
        
        return web.json_response({
            "trends": filtered_trends,
            "total_count": len(filtered_trends),
            "categories_analyzed": categories or ["technology", "ai"],
            "processing_time": 0.5
        })

class MockVideoService:
    """影片服務模擬"""
    
    async def handle_health(self, request):
        return web.json_response({"status": "healthy", "service": "video-service"})
    
    async def handle_create_workflow(self, request):
        data = await request.json()
        user_id = data.get("user_id")
        trend_keywords = data.get("trend_keywords", [])
        video_count = data.get("video_count", 1)
        
        logger.info(f"收到工作流程創建請求: {data}")
        
        if not user_id:
            return web.json_response(
                {"error": "Missing user_id"}, 
                status=400
            )
        
        if video_count <= 0:
            return web.json_response(
                {"error": "Invalid video_count"}, 
                status=400
            )
        
        # trend_keywords 可以為空，系統會自動抓取
        
        workflow_id = str(uuid.uuid4())
        workflow_data = {
            "workflow_id": workflow_id,
            "user_id": user_id,
            "status": "in_progress",
            "current_step": "trend_analysis",
            "total_steps": 7,
            "completed_steps": 0,
            "step_results": {},
            "videos_generated": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        MOCK_DATA["workflows"][workflow_id] = workflow_data
        
        # 啟動模擬工作流程
        asyncio.create_task(self._simulate_workflow(workflow_id, video_count))
        
        return web.json_response({
            "workflow_id": workflow_id,
            "status": "started",
            "estimated_duration": 60,
            "message": "影片工作流程已啟動"
        })
    
    async def handle_workflow_status(self, request):
        workflow_id = request.match_info['workflow_id']
        
        if workflow_id not in MOCK_DATA["workflows"]:
            return web.json_response(
                {"error": "Workflow not found"}, 
                status=404
            )
        
        workflow = MOCK_DATA["workflows"][workflow_id]
        return web.json_response(workflow)
    
    async def _simulate_workflow(self, workflow_id: str, video_count: int):
        """模擬工作流程執行"""
        workflow = MOCK_DATA["workflows"][workflow_id]
        steps = [
            "trend_analysis",
            "keyword_extraction", 
            "script_generation",
            "image_generation",
            "voice_synthesis",
            "video_composition",
            "quality_check"
        ]
        
        try:
            for i, step in enumerate(steps, 1):
                # 模擬每步驟處理時間
                await asyncio.sleep(2)
                
                workflow["current_step"] = step
                workflow["completed_steps"] = i
                workflow["step_results"][step] = {
                    "success": True,
                    "duration": 2.0,
                    "details": f"Mock {step} completed successfully"
                }
                workflow["updated_at"] = datetime.utcnow().isoformat()
                
                logger.info(f"工作流程 {workflow_id} 完成步驟: {step}")
            
            # 工作流程完成
            workflow["status"] = "completed"
            workflow["videos_generated"] = video_count
            workflow["generated_videos"] = [
                {
                    "video_id": f"video_{uuid.uuid4()}",
                    "title": f"AI 趨勢分析影片 {i+1}",
                    "description": "基於最新趨勢數據生成的影片",
                    "duration": 30,
                    "quality": "1080p",
                    "tags": ["AI", "technology", "trends"]
                }
                for i in range(video_count)
            ]
            
            logger.info(f"工作流程 {workflow_id} 完成，生成 {video_count} 個影片")
            
        except Exception as e:
            workflow["status"] = "failed"
            workflow["error"] = str(e)
            logger.error(f"工作流程 {workflow_id} 失敗: {e}")

class MockSocialService:
    """社群服務模擬"""
    
    async def handle_health(self, request):
        return web.json_response({"status": "healthy", "service": "social-service"})
    
    async def handle_publish(self, request):
        data = await request.json()
        user_id = data.get("user_id")
        video_id = data.get("video_id")
        platforms = data.get("platforms", [])
        
        if not all([user_id, video_id, platforms]):
            return web.json_response(
                {"error": "Missing required parameters"}, 
                status=400
            )
        
        publish_id = str(uuid.uuid4())
        publish_data = {
            "publish_id": publish_id,
            "user_id": user_id,
            "video_id": video_id,
            "platforms": platforms,
            "status": "in_progress",
            "platform_results": {},
            "all_completed": False,
            "created_at": datetime.utcnow().isoformat()
        }
        
        MOCK_DATA["publish_records"][publish_id] = publish_data
        
        # 啟動模擬發布流程
        asyncio.create_task(self._simulate_publishing(publish_id, platforms))
        
        return web.json_response({
            "publish_id": publish_id,
            "status": "started",
            "message": "發布流程已啟動"
        })
    
    async def handle_publish_status(self, request):
        publish_id = request.match_info['publish_id']
        
        if publish_id not in MOCK_DATA["publish_records"]:
            return web.json_response(
                {"error": "Publish record not found"}, 
                status=404
            )
        
        publish_record = MOCK_DATA["publish_records"][publish_id]
        return web.json_response(publish_record)
    
    async def _simulate_publishing(self, publish_id: str, platforms: List[str]):
        """模擬發布流程"""
        publish_record = MOCK_DATA["publish_records"][publish_id]
        
        try:
            for platform in platforms:
                # 模擬發布延遲
                await asyncio.sleep(3)
                
                # 模擬成功發布
                publish_record["platform_results"][platform] = {
                    "status": "success",
                    "platform_post_id": f"{platform}_{uuid.uuid4()}",
                    "published_at": datetime.utcnow().isoformat(),
                    "url": f"https://{platform}.com/post/{uuid.uuid4()}"
                }
                
                logger.info(f"發布 {publish_id} 到 {platform} 成功")
            
            publish_record["status"] = "completed"
            publish_record["all_completed"] = True
            
        except Exception as e:
            publish_record["status"] = "failed"
            publish_record["error"] = str(e)
            logger.error(f"發布 {publish_id} 失敗: {e}")

class MockSchedulerService:
    """排程服務模擬"""
    
    def __init__(self):
        self.is_running = False
        self.config = {}
    
    async def handle_health(self, request):
        return web.json_response({
            "status": "healthy", 
            "service": "scheduler-service",
            "is_running": self.is_running
        })
    
    async def handle_configure(self, request):
        self.config = await request.json()
        return web.json_response({
            "message": "排程器配置已更新",
            "config": self.config,
            "status": "configured"
        })
    
    async def handle_start(self, request):
        self.is_running = True
        return web.json_response({
            "message": "排程器已啟動",
            "status": "running",
            "started_at": datetime.utcnow().isoformat()
        })
    
    async def handle_stop(self, request):
        self.is_running = False
        return web.json_response({
            "message": "排程器已停止",
            "status": "stopped",
            "stopped_at": datetime.utcnow().isoformat()
        })
    
    async def handle_status(self, request):
        return web.json_response({
            "is_running": self.is_running,
            "daily_stats": {
                "videos_generated": 0,
                "budget_used": 0.0,
                "tasks_completed": 0,
                "tasks_failed": 0
            },
            "active_tasks_count": 0,
            "scheduled_tasks_count": len(MOCK_DATA["scheduled_tasks"]),
            "config": self.config
        })

async def create_mock_services():
    """創建所有模擬服務"""
    
    # 趨勢服務 (端口 8001)
    trend_service = MockTrendService()
    trend_app = web.Application()
    trend_app.router.add_get('/health', trend_service.handle_health)
    trend_app.router.add_post('/api/v1/entrepreneur/fetch-trends', trend_service.handle_fetch_trends)
    
    # 影片服務 (端口 8003)
    video_service = MockVideoService()
    video_app = web.Application()
    video_app.router.add_get('/health', video_service.handle_health)
    video_app.router.add_post('/api/v1/entrepreneur/create', video_service.handle_create_workflow)
    video_app.router.add_get('/api/v1/entrepreneur/status/{workflow_id}', video_service.handle_workflow_status)
    
    # 社群服務 (端口 8004)
    social_service = MockSocialService()
    social_app = web.Application()
    social_app.router.add_get('/health', social_service.handle_health)
    social_app.router.add_post('/api/v1/entrepreneur/publish', social_service.handle_publish)
    social_app.router.add_get('/api/v1/entrepreneur/publish-status/{publish_id}', social_service.handle_publish_status)
    
    # 排程服務 (端口 8008)
    scheduler_service = MockSchedulerService()
    scheduler_app = web.Application()
    scheduler_app.router.add_get('/health', scheduler_service.handle_health)
    scheduler_app.router.add_post('/api/v1/entrepreneur-scheduler/configure', scheduler_service.handle_configure)
    scheduler_app.router.add_post('/api/v1/entrepreneur-scheduler/start', scheduler_service.handle_start)
    scheduler_app.router.add_post('/api/v1/entrepreneur-scheduler/stop', scheduler_service.handle_stop)
    scheduler_app.router.add_get('/api/v1/entrepreneur-scheduler/status', scheduler_service.handle_status)
    
    # 啟動所有服務
    runners = []
    
    services = [
        (trend_app, 8001, "Trend Service"),
        (video_app, 8003, "Video Service"),
        (social_app, 8004, "Social Service"),
        (scheduler_app, 8008, "Scheduler Service")
    ]
    
    for app, port, name in services:
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', port)
        await site.start()
        runners.append(runner)
        logger.info(f"🚀 {name} 啟動在端口 {port}")
    
    return runners

async def main():
    """啟動所有模擬服務"""
    logger.info("🎭 啟動 E2E 測試模擬服務...")
    
    runners = await create_mock_services()
    
    logger.info("✅ 所有模擬服務已啟動")
    logger.info("📋 服務列表:")
    logger.info("  - Trend Service: http://localhost:8001")
    logger.info("  - Video Service: http://localhost:8003")
    logger.info("  - Social Service: http://localhost:8004")
    logger.info("  - Scheduler Service: http://localhost:8008")
    
    try:
        # 保持服務運行
        while True:
            await asyncio.sleep(60)
            logger.info("🔄 模擬服務運行中...")
    except KeyboardInterrupt:
        logger.info("🛑 停止模擬服務...")
        for runner in runners:
            await runner.cleanup()

def run_mock_services():
    """在背景執行緒中運行模擬服務"""
    asyncio.run(main())

if __name__ == "__main__":
    # 在背景啟動模擬服務
    service_thread = threading.Thread(target=run_mock_services, daemon=True)
    service_thread.start()
    
    # 給服務時間啟動
    time.sleep(3)
    
    logger.info("🧪 模擬服務已準備就緒，可以運行 E2E 測試")
    
    # 保持主程序運行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("🏁 退出模擬服務")