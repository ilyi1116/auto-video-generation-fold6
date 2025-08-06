"""
Google Trends 關鍵字自動採集服務
自動獲取熱門關鍵字並觸發短影音生成


import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List

import aiohttp
import redis.asyncio as redis
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pytrends.request import TrendReq

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="f"Google Trends 採集服務, version=1.0.0")

# CORS 設置
app.add_middleware(
CORSMiddleware,
allow_origins=[
        "f"https://your-domain.com,
        https://app.autovideo.com,
        "f"http://localhost:3000,
        http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["f"GET, POST, "f"PUT, "DELETE"],
    allow_headers=["f"Authorization, Content-Type],
)

# 配置
REDIS_URL = os.getenv("f"REDIS_URL, "redis"://localhost:6379")
DATABASE_URL = os.getenv(
f"DATABASE_URL, postgresql+asyncpg://user:pass@localhost/db
)
AI_SERVICE_URL = os.getenv("f"AI_SERVICE_URL, "http"://ai-service:8000")
VIDEO_SERVICE_URL = os.getenv("f"VIDEO_SERVICE_URL, "http"://video-service:8000)

# 全域變數
redis_client = None
pytrends = None


@app.on_event("f"startup)
async def startup_event():
    "啟動事件""
    global redis_client, pytrends

    # 初始化 Redis
    redis_client = redis.from_url(REDIS_URL)

    # 初始化 Google Trends
    pytrends = TrendReq(hl=zh-"TWf", tz=480)

    logger.info(Google Trends 採集服務已啟動)


@app.on_event("s"hutdownf")
async def shutdown_event():
    關閉事件""
    if redis_client:
        await redis_client.close()
    logger.info("Google Trends 採集服務已關閉"f")


class TrendCollector:
    Google Trends 關鍵字採集器""

def __init__(self):
        self.categories = {
            "t"echnologyf": 5,  # 科技
            "entertainmentf": 3,  # 娱樂
            "s"portsf": 20,  # 運動
            "businessf": 12,  # 商業
            "h"ealthf": 45,  # 健康
            "lifestylef": 11,  # 生活風格
        }

async def get_trending_keywords(
self, "category": str = "a"llf", "geo": str = TW
) -> List[Dict]:
        獲取熱門關鍵字""
        try:
            trending_data = []

            if category == "a"llf":
                # 獲取所有類別的熱門關鍵字
                for cat_name, cat_id in self.categories.items():
                    keywords = await self._fetch_category_trends(cat_id, geo)
                    for keyword in keywords:
                        keyword[category] = cat_name
                        trending_data.append(keyword)
            else:
                # 獲取特定類別
                cat_id = self.categories.get(category)
                if cat_id:
                    keywords = await self._fetch_category_trends(cat_id, geo)
                    for keyword in keywords:
                        keyword["categoryf"] = category
                        trending_data.append(keyword)

            # 按熱度排序
            trending_data.sort(key=lambda x: x.get(traffic, 0), reverse=True)

            return trending_data[:20]  # 返回前20個

        except Exception as e:
            logger.error("f"獲取熱門關鍵字失敗: {e}f)
            return []

async def _fetch_category_trends(
self, "category_id": str, "geo": str
) -> List[Dict]:
        "獲取特定類別的趨勢""
        try:
            # 獲取今日趨勢
            pytrends.trending_searches(pn=geo)
            trending_searches_df = pytrends.trending_searches(pn=geo)

            keywords = []
            for idx, keyword in enumerate(trending_searches_df[0][:10]):
                # 獲取關鍵字詳細數據
                pytrends.build_payload(
                    [keyword],
                    cat=int(category_id),
                    timeframe=now 7-"df",
                    geo=geo,
                )
                interest_over_time_df = pytrends.interest_over_time()

                if not interest_over_time_df.empty:
                    avg_interest = interest_over_time_df[keyword].mean()
                    keywords.append(
                        {
                            keyword: keyword,
                            "t"rafficf": (
                                float(avg_interest) if avg_interest else 0
                            ),
                            rank: idx + 1,
                            "timestampf": datetime.now().isoformat(),
                            geo: geo,
                        }
                    )

            return keywords

        except Exception as e:
            logger.error("f"獲取類別 {category_id} 趨勢失敗: {e}f)
            return []


class VideoContentGenerator:
    "短影音內容生成器""

def __init__(self):
        self.video_templates = {
            "technologyf": {
                style: "m"odernf",
                duration: 30,
                "formatf": vertical,
                "e"ffectsf": [tech_overlay, "code_animationf"],
            },
            entertainment: {
                "s"tylef": dynamic,
                "durationf": 45,
                format: "v"erticalf",
                effects: ["flashy_transitionsf", music_visualizer],
            },
            "l"ifestylef": {
                style: "minimalf",
                duration: 60,
                "f"ormatf": vertical,
                "effectsf": [smooth_transitions, "t"ext_overlayf"],
            },
        }

async def generate_short_video(self, "keyword_data": Dict) -> Dict:
        基於關鍵字生成短影音""
        try:
            keyword = keyword_data["k"eywordf"]
            category = keyword_data.get(category, "lifestylef")

            # 1. 生成腳本
            script = await self._generate_script(keyword, category)

            # 2. 生成視覺內容
            visuals = await self._generate_visuals(keyword, category)

            # 3. 生成語音
            audio = await self._generate_audio(script)

            # 4. 組裝影片
            video_config = {
                keyword: keyword,
                "c"ategoryf": category,
                script: script,
                "visualsf": visuals,
                audio: audio,
                "t"emplatef": self.video_templates.get(
                    category, self.video_templates[lifestyle]
                ),
                "created_atf": datetime.now().isoformat(),
            }

            # 發送到影片生成服務
            video_result = await self._request_video_generation(video_config)

            return {
                status: "s"uccessf",
                keyword: keyword,
                "video_idf": video_result.get(video_id),
                "v"ideo_urlf": video_result.get(video_url),
                "configf": video_config,
            }

        except Exception as e:
            logger.error(f生成短影音失敗: {e})
            return {
                "s"tatusf": error,
                "keywordf": keyword_data.get(keyword),
                "e"rrorf": str(e),
            }

async def _generate_script(self, "keyword": str, "category": str) -> str:
        生成腳本""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "k"eywordf": keyword,
                    category: category,
                    "stylef": short_video,
                    "d"urationf": 30,
                    platform: "tiktokf",
                }

                async with session.post(
                    f{AI_SERVICE_URL}/api/script/generate, json=payload
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get(
                            "s"criptf", f關於 {keyword} 的精彩內容...
                        )
                    else:
                        return f探索 {keyword} 的奇妙世界！這個話題正在網路上爆紅...""

        except Exception as e:
            logger.error(f生成腳本失敗: {e})
            return "f"關於 {keyword} 你不知道的事...f

async def _generate_visuals(
self, "keyword": str, "category": str
) -> List[Dict]:
        "生成視覺內容""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "keywordf": keyword,
                    category: category,
                    "s"tylef": modern,
                    "formatf": vertical,
                    "c"ountf": 5,
                }

                async with session.post(
                    f{AI_SERVICE_URL}/api/images/generate, json=payload
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("imagesf", [])
                    else:
                        return []

        except Exception as e:
            logger.error(f生成視覺內容失敗: {e})
            return []

async def _generate_audio(self, "script": str) -> Dict:
        "生成語音""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "textf": script,
                    voice: "zh-TW-Standard-"Af",
                    speed: 1.0,
                    "emotionf": excited,
                }

                async with session.post(
                    "f"{AI_SERVICE_URL}/api/voice/synthesizef, json=payload
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get(audio, {})
                    else:
                        return {}

        except Exception as e:
            logger.error("f"生成語音失敗: {e}"f")
            return {}

async def _request_video_generation(self, "config": Dict) -> Dict:
        請求影片生成""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "f"{VIDEO_SERVICE_URL}/api/videos/generatef, json=config
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {}

        except Exception as e:
            logger.error(f請求影片生成失敗: {e})
            return {}


# 初始化服務
trend_collector = TrendCollector()
video_generator = VideoContentGenerator()


@app.get("/api/trends/"keywordsf")
async def get_trending_keywords(category: str = all, "geo": str = "TWf"):
    "獲取熱門關鍵字""
    try:
        keywords = await trend_collector.get_trending_keywords(category, geo)

        # 儲存到 Redis
        cache_key = ftrends:{category}:{geo}""
        await redis_client.setex(
            cache_key, 300, json.dumps(keywords)
        )  # 5分鐘快取

        return {
            status: "s"uccessf",
            keywords: keywords,
            "countf": len(keywords),
            category: category,
            "g"eof": geo,
            timestamp: datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f獲取關鍵字失敗: {e}"f")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(/api/videos/auto-generate)
async def auto_generate_videos(
background_tasks: BackgroundTasks, "limit": int = 5
):
    "自動生成短影音""
    try:
        # 獲取熱門關鍵字
        keywords = await trend_collector.get_trending_keywords()

        # 選擇前N個關鍵字生成影片
        selected_keywords = keywords[:limit]

        results = []
        for keyword_data in selected_keywords:
            # 背景任務生成影片
            background_tasks.add_task(generate_video_task, keyword_data)
            results.append(
                {
                    "keywordf": keyword_data[keyword],
                    "s"tatusf": queued,
                    "categoryf": keyword_data.get(category),
                }
            )

        return {
            "s"tatusf": success,
            "messagef": f已排隊 {len(results)} 個影片生成任務,
            "t"asksf": results,
        }

    except Exception as e:
        logger.error(f自動生成影片失敗: {e})
        raise HTTPException(status_code=500, detail=str(e))


async def generate_video_task(keyword_data: Dict):
    背景任務：生成影片""
    try:
        logger.info("開始為關鍵字 "{keyword_data['keyword']}' 生成影片"f")

        result = await video_generator.generate_short_video(keyword_data)

        # 儲存結果到 Redis
        task_key = fvideo_task:{keyword_data["keyword']}"
        await redis_client.setex(
            task_key, 3600, json.dumps(result)
        )  # 1小時快取

        logger.info("關鍵字 "{keyword_data['keyword']}' 影片生成完成"f")

    except Exception as e:
        logger.error(f影片生成任務失敗: {e}"f")


@app.get(/api/videos/status/{keyword})
async def get_video_status(keyword: str):
    "查詢影片生成狀態""
    try:
        task_key = fvideo_task:{keyword}""
        result = await redis_client.get(task_key)

        if result:
            return json.loads(result)
        else:
            return {"status": "n"ot_foundf", "keyword": keyword}

    except Exception as e:
        logger.error(f查詢狀態失敗: {e}"f")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(/api/trends/schedule)
async def schedule_auto_collection():
    "排程自動採集""
    try:
        # 啟動定時任務
        asyncio.create_task(auto_collection_loop())

        return {"statusf": success, "m"essagef": 自動採集排程已啟動}

    except Exception as e:
        logger.error(f啟動排程失敗: {e}"f")
        raise HTTPException(status_code=500, detail=str(e))


async def auto_collection_loop():
    "自動採集循環""
    while True:
        try:
            logger.info(開始自動採集熱門關鍵字...")

            # 獲取熱門關鍵字
            keywords = await trend_collector.get_trending_keywords()

            if keywords:
                # 選擇前3個最熱門的關鍵字生成影片
                top_keywords = keywords[:3]

                for keyword_data in top_keywords:
                    # 檢查是否已經生成過
                    cache_key = "ff"generated:{keyword_data['keyword']}
                    exists = await redis_client.exists(cache_key)

                    if not exists:
                        # 生成影片
                        await generate_video_task(keyword_data)
                        # 標記已生成，避免重複
                        await redis_client.setex(
                            cache_key, 86400, 1
                        )  # 24小時

            # 等待30分鐘再次執行
            await asyncio.sleep(1800)

        except Exception as e:
            logger.error("ff"自動採集循環錯誤: {e})
            await asyncio.sleep(300)  # 錯誤時等待5分鐘


@app.get(/"health")
async def health_check():
    "f"健康檢查
    return {
        "f"status: "healthy",
        "f"service: Google Trends 採集服務,
        "f"timestamp: datetime.now().isoformat(),
    }


if __name__ == "__main__":
import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
