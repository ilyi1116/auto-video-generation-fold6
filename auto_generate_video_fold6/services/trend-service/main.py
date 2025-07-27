"""
Google Trends 關鍵字自動採集服務
自動獲取熱門關鍵字並觸發短影音生成
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import aiohttp
import json
from pytrends.request import TrendReq
import pandas as pd
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Google Trends 採集服務", version="1.0.0")

# CORS 設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://ai-service:8000")
VIDEO_SERVICE_URL = os.getenv("VIDEO_SERVICE_URL", "http://video-service:8000")

# 全域變數
redis_client = None
pytrends = None

@app.on_event("startup")
async def startup_event():
    """啟動事件"""
    global redis_client, pytrends
    
    # 初始化 Redis
    redis_client = redis.from_url(REDIS_URL)
    
    # 初始化 Google Trends
    pytrends = TrendReq(hl='zh-TW', tz=480)
    
    logger.info("Google Trends 採集服務已啟動")

@app.on_event("shutdown")
async def shutdown_event():
    """關閉事件"""
    if redis_client:
        await redis_client.close()
    logger.info("Google Trends 採集服務已關閉")

class TrendCollector:
    """Google Trends 關鍵字採集器"""
    
    def __init__(self):
        self.categories = {
            'technology': '5',      # 科技
            'entertainment': '3',   # 娱樂
            'sports': '20',        # 運動
            'business': '12',      # 商業
            'health': '45',        # 健康
            'lifestyle': '11',     # 生活風格
        }
        
    async def get_trending_keywords(self, category: str = 'all', geo: str = 'TW') -> List[Dict]:
        """獲取熱門關鍵字"""
        try:
            trending_data = []
            
            if category == 'all':
                # 獲取所有類別的熱門關鍵字
                for cat_name, cat_id in self.categories.items():
                    keywords = await self._fetch_category_trends(cat_id, geo)
                    for keyword in keywords:
                        keyword['category'] = cat_name
                        trending_data.append(keyword)
            else:
                # 獲取特定類別
                cat_id = self.categories.get(category)
                if cat_id:
                    keywords = await self._fetch_category_trends(cat_id, geo)
                    for keyword in keywords:
                        keyword['category'] = category
                        trending_data.append(keyword)
            
            # 按熱度排序
            trending_data.sort(key=lambda x: x.get('traffic', 0), reverse=True)
            
            return trending_data[:20]  # 返回前20個
            
        except Exception as e:
            logger.error(f"獲取熱門關鍵字失敗: {e}")
            return []
    
    async def _fetch_category_trends(self, category_id: str, geo: str) -> List[Dict]:
        """獲取特定類別的趨勢"""
        try:
            # 獲取今日趨勢
            pytrends.trending_searches(pn=geo)
            trending_searches_df = pytrends.trending_searches(pn=geo)
            
            keywords = []
            for idx, keyword in enumerate(trending_searches_df[0][:10]):
                # 獲取關鍵字詳細數據
                pytrends.build_payload([keyword], cat=int(category_id), timeframe='now 7-d', geo=geo)
                interest_over_time_df = pytrends.interest_over_time()
                
                if not interest_over_time_df.empty:
                    avg_interest = interest_over_time_df[keyword].mean()
                    keywords.append({
                        'keyword': keyword,
                        'traffic': float(avg_interest) if avg_interest else 0,
                        'rank': idx + 1,
                        'timestamp': datetime.now().isoformat(),
                        'geo': geo
                    })
            
            return keywords
            
        except Exception as e:
            logger.error(f"獲取類別 {category_id} 趨勢失敗: {e}")
            return []

class VideoContentGenerator:
    """短影音內容生成器"""
    
    def __init__(self):
        self.video_templates = {
            'technology': {
                'style': 'modern',
                'duration': 30,
                'format': 'vertical',
                'effects': ['tech_overlay', 'code_animation']
            },
            'entertainment': {
                'style': 'dynamic',
                'duration': 45,
                'format': 'vertical',
                'effects': ['flashy_transitions', 'music_visualizer']
            },
            'lifestyle': {
                'style': 'minimal',
                'duration': 60,
                'format': 'vertical',
                'effects': ['smooth_transitions', 'text_overlay']
            }
        }
    
    async def generate_short_video(self, keyword_data: Dict) -> Dict:
        """基於關鍵字生成短影音"""
        try:
            keyword = keyword_data['keyword']
            category = keyword_data.get('category', 'lifestyle')
            
            # 1. 生成腳本
            script = await self._generate_script(keyword, category)
            
            # 2. 生成視覺內容
            visuals = await self._generate_visuals(keyword, category)
            
            # 3. 生成語音
            audio = await self._generate_audio(script)
            
            # 4. 組裝影片
            video_config = {
                'keyword': keyword,
                'category': category,
                'script': script,
                'visuals': visuals,
                'audio': audio,
                'template': self.video_templates.get(category, self.video_templates['lifestyle']),
                'created_at': datetime.now().isoformat()
            }
            
            # 發送到影片生成服務
            video_result = await self._request_video_generation(video_config)
            
            return {
                'status': 'success',
                'keyword': keyword,
                'video_id': video_result.get('video_id'),
                'video_url': video_result.get('video_url'),
                'config': video_config
            }
            
        except Exception as e:
            logger.error(f"生成短影音失敗: {e}")
            return {
                'status': 'error',
                'keyword': keyword_data.get('keyword'),
                'error': str(e)
            }
    
    async def _generate_script(self, keyword: str, category: str) -> str:
        """生成腳本"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'keyword': keyword,
                    'category': category,
                    'style': 'short_video',
                    'duration': 30,
                    'platform': 'tiktok'
                }
                
                async with session.post(f"{AI_SERVICE_URL}/api/script/generate", json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get('script', f"關於 {keyword} 的精彩內容...")
                    else:
                        return f"探索 {keyword} 的奇妙世界！這個話題正在網路上爆紅..."
                        
        except Exception as e:
            logger.error(f"生成腳本失敗: {e}")
            return f"關於 {keyword} 你不知道的事..."
    
    async def _generate_visuals(self, keyword: str, category: str) -> List[Dict]:
        """生成視覺內容"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'keyword': keyword,
                    'category': category,
                    'style': 'modern',
                    'format': 'vertical',
                    'count': 5
                }
                
                async with session.post(f"{AI_SERVICE_URL}/api/images/generate", json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get('images', [])
                    else:
                        return []
                        
        except Exception as e:
            logger.error(f"生成視覺內容失敗: {e}")
            return []
    
    async def _generate_audio(self, script: str) -> Dict:
        """生成語音"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    'text': script,
                    'voice': 'zh-TW-Standard-A',
                    'speed': 1.0,
                    'emotion': 'excited'
                }
                
                async with session.post(f"{AI_SERVICE_URL}/api/voice/synthesize", json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get('audio', {})
                    else:
                        return {}
                        
        except Exception as e:
            logger.error(f"生成語音失敗: {e}")
            return {}
    
    async def _request_video_generation(self, config: Dict) -> Dict:
        """請求影片生成"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{VIDEO_SERVICE_URL}/api/videos/generate", json=config) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {}
                        
        except Exception as e:
            logger.error(f"請求影片生成失敗: {e}")
            return {}

# 初始化服務
trend_collector = TrendCollector()
video_generator = VideoContentGenerator()

@app.get("/api/trends/keywords")
async def get_trending_keywords(category: str = "all", geo: str = "TW"):
    """獲取熱門關鍵字"""
    try:
        keywords = await trend_collector.get_trending_keywords(category, geo)
        
        # 儲存到 Redis
        cache_key = f"trends:{category}:{geo}"
        await redis_client.setex(cache_key, 300, json.dumps(keywords))  # 5分鐘快取
        
        return {
            "status": "success",
            "keywords": keywords,
            "count": len(keywords),
            "category": category,
            "geo": geo,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取關鍵字失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/videos/auto-generate")
async def auto_generate_videos(background_tasks: BackgroundTasks, limit: int = 5):
    """自動生成短影音"""
    try:
        # 獲取熱門關鍵字
        keywords = await trend_collector.get_trending_keywords()
        
        # 選擇前N個關鍵字生成影片
        selected_keywords = keywords[:limit]
        
        results = []
        for keyword_data in selected_keywords:
            # 背景任務生成影片
            background_tasks.add_task(generate_video_task, keyword_data)
            results.append({
                'keyword': keyword_data['keyword'],
                'status': 'queued',
                'category': keyword_data.get('category')
            })
        
        return {
            "status": "success",
            "message": f"已排隊 {len(results)} 個影片生成任務",
            "tasks": results
        }
        
    except Exception as e:
        logger.error(f"自動生成影片失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def generate_video_task(keyword_data: Dict):
    """背景任務：生成影片"""
    try:
        logger.info(f"開始為關鍵字 '{keyword_data['keyword']}' 生成影片")
        
        result = await video_generator.generate_short_video(keyword_data)
        
        # 儲存結果到 Redis
        task_key = f"video_task:{keyword_data['keyword']}"
        await redis_client.setex(task_key, 3600, json.dumps(result))  # 1小時快取
        
        logger.info(f"關鍵字 '{keyword_data['keyword']}' 影片生成完成")
        
    except Exception as e:
        logger.error(f"影片生成任務失敗: {e}")

@app.get("/api/videos/status/{keyword}")
async def get_video_status(keyword: str):
    """查詢影片生成狀態"""
    try:
        task_key = f"video_task:{keyword}"
        result = await redis_client.get(task_key)
        
        if result:
            return json.loads(result)
        else:
            return {"status": "not_found", "keyword": keyword}
            
    except Exception as e:
        logger.error(f"查詢狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/trends/schedule")
async def schedule_auto_collection():
    """排程自動採集"""
    try:
        # 啟動定時任務
        asyncio.create_task(auto_collection_loop())
        
        return {
            "status": "success",
            "message": "自動採集排程已啟動"
        }
        
    except Exception as e:
        logger.error(f"啟動排程失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def auto_collection_loop():
    """自動採集循環"""
    while True:
        try:
            logger.info("開始自動採集熱門關鍵字...")
            
            # 獲取熱門關鍵字
            keywords = await trend_collector.get_trending_keywords()
            
            if keywords:
                # 選擇前3個最熱門的關鍵字生成影片
                top_keywords = keywords[:3]
                
                for keyword_data in top_keywords:
                    # 檢查是否已經生成過
                    cache_key = f"generated:{keyword_data['keyword']}"
                    exists = await redis_client.exists(cache_key)
                    
                    if not exists:
                        # 生成影片
                        await generate_video_task(keyword_data)
                        # 標記已生成，避免重複
                        await redis_client.setex(cache_key, 86400, "1")  # 24小時
            
            # 等待30分鐘再次執行
            await asyncio.sleep(1800)
            
        except Exception as e:
            logger.error(f"自動採集循環錯誤: {e}")
            await asyncio.sleep(300)  # 錯誤時等待5分鐘

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "service": "Google Trends 採集服務",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)