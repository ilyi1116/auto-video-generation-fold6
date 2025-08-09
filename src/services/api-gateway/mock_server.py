#!/usr/bin/env python3
"""
模擬後端服務用於前端測試
Mock backend service for frontend testing
"""

import time
import os
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import aiohttp
import asyncio
import re
import urllib.parse

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 創建FastAPI應用
app = FastAPI(
    title="Mock API Gateway",
    version="1.0.0",
    description="Mock backend service for frontend testing",
)

# 添加CORS中介軟體
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 創建音頻文件目錄
audio_dir = "generated_audio"
os.makedirs(audio_dir, exist_ok=True)

# 掛載靜態文件服務器用於音頻文件
app.mount("/audio", StaticFiles(directory=audio_dir), name="audio")

# DeepSeek API 配置
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")  # 从环境变量获取API密钥

# OpenAI TTS API 配置 (用於實際語音生成)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"

# Google 搜索配置
GOOGLE_SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY", "")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID", "")

# DeepSeek API 客户端
async def call_deepseek_api(messages, model="deepseek-chat", temperature=0.7, max_tokens=2000):
    """调用DeepSeek API生成内容"""
    if not DEEPSEEK_API_KEY:
        raise Exception("DeepSeek API key not configured")
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    raise Exception(f"DeepSeek API error {response.status}: {error_text}")
        except asyncio.TimeoutError:
            raise Exception("DeepSeek API timeout")
        except Exception as e:
            raise Exception(f"DeepSeek API call failed: {str(e)}")


# Google 搜索功能
async def search_google_news(query: str, time_range: str = "d", max_results: int = 10) -> List[Dict]:
    """
    搜索Google新聞和網頁內容
    time_range: d=過去一天, w=過去一週, m=過去一個月, y=過去一年
    """
    print(f"🔍 開始Google搜索: {query} (時間範圍: {time_range})")
    
    if not GOOGLE_SEARCH_API_KEY or not GOOGLE_SEARCH_ENGINE_ID:
        print("⚠️ Google搜索API未配置，使用模擬搜索結果")
        return create_mock_search_results(query, time_range)
    
    try:
        # 構建搜索URL
        base_url = "https://www.googleapis.com/customsearch/v1"
        
        # 時間範圍參數
        time_params = {
            "d": "d1",  # 過去1天
            "w": "w1",  # 過去1週  
            "m": "m1",  # 過去1個月
            "y": "y1"   # 過去1年
        }
        
        params = {
            "key": GOOGLE_SEARCH_API_KEY,
            "cx": GOOGLE_SEARCH_ENGINE_ID,
            "q": f"{query} 新聞",
            "num": max_results,
            "dateRestrict": time_params.get(time_range, "w1"),
            "sort": "date",  # 按日期排序
            "lr": "lang_zh-TW|lang_zh-CN",  # 中文結果優先
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for item in data.get("items", [])[:max_results]:
                        results.append({
                            "title": item.get("title", ""),
                            "snippet": item.get("snippet", ""),
                            "link": item.get("link", ""),
                            "displayLink": item.get("displayLink", ""),
                            "formattedUrl": item.get("formattedUrl", "")
                        })
                    
                    print(f"✅ Google搜索成功，獲得 {len(results)} 條結果")
                    return results
                    
                else:
                    print(f"❌ Google搜索API錯誤: {response.status}")
                    return create_mock_search_results(query, time_range)
                    
    except Exception as e:
        print(f"❌ Google搜索異常: {str(e)}")
        return create_mock_search_results(query, time_range)


def create_mock_search_results(query: str, time_range: str) -> List[Dict]:
    """創建模擬搜索結果，用於API未配置或失敗時"""
    
    # 根據查詢關鍵字生成相關的模擬新聞
    mock_results = []
    
    if "比特幣" in query or "bitcoin" in query.lower():
        mock_results = [
            {
                "title": f"比特幣價格突破新高，分析師看好後市發展",
                "snippet": "根據最新市場分析，比特幣價格在過去幾天內持續上漲，多位專家認為這波漲勢可能持續...",
                "link": "https://example.com/bitcoin-news-1",
                "displayLink": "財經新聞網",
                "formattedUrl": "https://example.com/bitcoin-news"
            },
            {
                "title": f"加密貨幣監管政策最新動向，對市場影響分析",
                "snippet": "各國政府對加密貨幣的監管態度逐漸明確，市場參與者需要關注政策變化對投資策略的影響...",
                "link": "https://example.com/crypto-regulation",
                "displayLink": "區塊鏈日報",
                "formattedUrl": "https://example.com/crypto-news"
            }
        ]
    
    elif "人工智慧" in query or "ai" in query.lower():
        mock_results = [
            {
                "title": f"AI技術最新突破，ChatGPT競爭對手湧現",
                "snippet": "人工智慧領域競爭激烈，多家科技公司推出新的AI模型，市場格局正在發生變化...",
                "link": "https://example.com/ai-news-1",
                "displayLink": "科技時報",
                "formattedUrl": "https://example.com/ai-tech"
            }
        ]
    
    else:
        # 通用模擬結果
        mock_results = [
            {
                "title": f"{query}相關最新動態和市場趨勢分析",
                "snippet": f"關於{query}的最新發展趨勢，專家分析認為未來發展前景值得關注，相關產業鏈也將受到影響...",
                "link": "https://example.com/news-1",
                "displayLink": "新聞網",
                "formattedUrl": "https://example.com/general-news"
            },
            {
                "title": f"{query}技術革新帶來的機遇與挑戰",
                "snippet": f"隨著{query}領域的技術不斷進步，為市場帶來新的機遇，同時也面臨一些挑戰需要解決...",
                "link": "https://example.com/tech-analysis",
                "displayLink": "技術分析",
                "formattedUrl": "https://example.com/tech-news"
            }
        ]
    
    print(f"📰 使用模擬搜索結果，生成 {len(mock_results)} 條相關新聞")
    return mock_results


async def summarize_search_results(search_results: List[Dict], topic: str) -> str:
    """使用AI整理搜索結果為摘要"""
    if not search_results:
        return ""
    
    # 構建搜索結果文本
    results_text = ""
    for i, result in enumerate(search_results[:5], 1):  # 只使用前5個結果
        results_text += f"{i}. 【{result['displayLink']}】{result['title']}\n"
        results_text += f"   {result['snippet']}\n\n"
    
    if DEEPSEEK_API_KEY:
        try:
            summary_prompt = f"""請根據以下關於「{topic}」的最新搜索結果，整理出3-5個關鍵要點：

{results_text}

請提供：
1. 最重要的趨勢或發展
2. 關鍵數據或事件
3. 專家觀點或市場反應
4. 對未來的影響預測
5. 值得關注的細節

要求：每個要點1-2句話，總共不超過200字。"""

            messages = [
                {
                    "role": "system",
                    "content": "你是一個專業的新聞分析師，擅長從多個新聞來源中提取關鍵信息並整理成簡潔的要點。"
                },
                {
                    "role": "user",
                    "content": summary_prompt
                }
            ]
            
            summary = await call_deepseek_api(messages, temperature=0.3, max_tokens=300)
            print(f"✅ AI搜索結果摘要生成成功")
            return summary.strip()
            
        except Exception as e:
            print(f"❌ AI摘要生成失敗: {str(e)}")
    
    # 回退到簡單摘要
    key_titles = [result['title'] for result in search_results[:3]]
    simple_summary = f"根據最新搜索，{topic}領域的重要動態包括：" + "；".join(key_titles[:2]) + "等相關發展。"
    return simple_summary


# 脚本生成提示词模板
def create_script_prompt(topic, platform, style, duration, language="zh-TW", description="", latest_news=""):
    """创建脚本生成的提示词，支持最新新闻内容整合"""
    
    platform_specs = {
        "youtube": {
            "name": "YouTube",
            "format": "横屏视频",
            "audience": "广泛观众",
            "tone": "专业但亲切",
            "features": "开头要吸引人，中间要有价值，结尾要有行动呼吁"
        },
        "tiktok": {
            "name": "TikTok",
            "format": "竖屏短视频",
            "audience": "年轻用户",
            "tone": "活泼有趣",
            "features": "开头3秒抓住注意力，节奏要快，要有话题性"
        },
        "instagram": {
            "name": "Instagram",
            "format": "方形或竖屏",
            "audience": "时尚潮流用户",
            "tone": "视觉化强，简洁有力",
            "features": "要有视觉冲击力，适合配图或视频"
        },
        "bilibili": {
            "name": "哔哩哔哩",
            "format": "横屏视频",
            "audience": "年轻创作者和爱好者",
            "tone": "轻松幽默，有梗有料",
            "features": "可以有弹幕互动，要有趣味性"
        }
    }
    
    style_specs = {
        "educational": "教育科普，要有深度和价值",
        "entertainment": "娱乐搞笑，要轻松有趣",
        "promotional": "营销推广，要有说服力",
        "storytelling": "故事叙述，要有情节和情感",
        "review": "评测分析，要客观专业",
        "tutorial": "教程指导，要清晰易懂",
        "lifestyle": "生活分享，要贴近日常"
    }
    
    platform_info = platform_specs.get(platform, platform_specs["youtube"])
    style_info = style_specs.get(style, "有趣且有价值")
    
    # 构建项目描述部分
    description_section = ""
    if description and description.strip():
        description_section = f"""
项目详细描述：{description.strip()}
请根据这个描述来定制脚本内容，确保脚本与描述的内容紧密相关。"""
    
    # 构建最新新闻部分
    news_section = ""
    if latest_news and latest_news.strip():
        news_section = f"""

最新相关资讯（请务必融入脚本中）：
{latest_news.strip()}

请将这些最新资讯自然地融入到脚本中，使内容更加时效性和相关性。不要生硬地列举，而要作为脚本内容的重要组成部分。"""
    
    prompt = f"""請為我創作一個{platform_info['name']}平台的{style_info}影片腳本。

主題：{topic}{description_section}{news_section}
平台：{platform_info['name']} ({platform_info['format']})
目標觀眾：{platform_info['audience']}
影片時長：約{duration}秒
語言：{language}（請使用繁體中文輸出）
風格要求：{style_info}
平台特色：{platform_info['features']}
語調：{platform_info['tone']}

請創作一個生動有趣、吸引人的腳本，要求：

1. 開頭要立刻抓住觀眾注意力（前5秒很關鍵）
2. 內容要緊密圍繞主題{f'和描述中的具體要求' if description else ''}
3. 語言要生動活潑，有人情味，不要套話和廢話
4. 結構要清晰，邏輯要通順
5. 要有適當的停頓和節奏感
6. 結尾要有明確的行動呼籲
7. 適合{duration}秒的影片長度
8. 符合{platform_info['name']}平台的特色
{f'9. 確保腳本內容與項目描述中的要求高度匹配' if description else ''}

**重要：請使用繁體中文回應，並且腳本要自然流暢，就像一個真實的創作者在說話一樣。**"""

    return prompt

# 模擬數據存儲
mock_users = {}
mock_videos = []
mock_analytics = {
    "totalVideos": 156,
    "totalViews": 2847293,
    "totalLikes": 394821,
    "totalShares": 89374,
}


# Pydantic 模型
class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class UserProfile(BaseModel):
    id: int
    email: str
    name: str
    created_at: str


# 健康檢查端點
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "mock-api-gateway",
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    return {
        "message": "Mock Voice Cloning API Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/simple_audio_test.html")
async def simple_audio_test():
    """提供簡單音頻測試頁面"""
    return FileResponse(
        "simple_audio_test.html", 
        media_type="text/html",
        headers={"Cache-Control": "no-cache"}
    )


@app.get("/debug_audio_playback.html")
async def debug_audio_playback():
    """提供音頻播放診斷工具頁面"""
    return FileResponse(
        "debug_audio_playback.html", 
        media_type="text/html",
        headers={"Cache-Control": "no-cache"}
    )


# 認證端點
@app.post("/api/v1/auth/login")
async def login(request: LoginRequest):
    """模擬登入端點"""
    print(f"Mock login attempt: {request.email}")

    # 模擬驗證
    if request.email == "demo@example.com" and request.password == "demo123":
        user_data = {
            "id": 1,
            "email": request.email,
            "name": "Demo User",
            "created_at": "2024-01-01T00:00:00Z",
        }
        mock_users[1] = user_data

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "user": user_data,
                    "token": "mock-jwt-token-12345",
                    "expires_in": 3600,
                },
            },
        )

    # 對於其他認證嘗試，也允許通過（測試目的）
    user_data = {
        "id": 2,
        "email": request.email,
        "name": request.email.split("@")[0].title(),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    mock_users[2] = user_data

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "user": user_data,
                "token": "mock-jwt-token-67890",
                "expires_in": 3600,
            },
        },
    )


@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest):
    """模擬註冊端點"""
    print(f"Mock registration attempt: {request.email}")

    # 檢查用戶是否已存在
    for user in mock_users.values():
        if user["email"] == request.email:
            raise HTTPException(status_code=400, detail="User already exists")

    # 創建新用戶
    user_id = len(mock_users) + 1
    user_data = {
        "id": user_id,
        "email": request.email,
        "name": request.name or request.email.split("@")[0].title(),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    mock_users[user_id] = user_data

    return JSONResponse(
        status_code=201,
        content={
            "success": True,
            "data": {
                "user": user_data,
                "token": f"mock-jwt-token-{user_id}{int(time.time())}",
                "expires_in": 3600,
            },
        },
    )


@app.get("/api/v1/auth/verify")
async def verify_token():
    """模擬驗證 JWT token 端點"""
    # 簡單的 token 驗證模擬
    # 在真實環境中，這裡會驗證 JWT token
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "user": {
                    "id": 1,
                    "email": "demo@example.com",
                    "name": "Demo User",
                    "created_at": "2024-01-01T00:00:00Z",
                }
            },
        },
    )


@app.get("/api/v1/auth/me")
async def get_profile():
    """模擬獲取用戶資料端點"""
    # 返回預設用戶資料
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "id": 1,
                "email": "demo@example.com",
                "name": "Demo User",
                "created_at": "2024-01-01T00:00:00Z",
                "settings": {"theme": "light", "notifications": True},
            },
        },
    )


# 影片管理端點
@app.get("/api/v1/videos")
async def list_videos():
    """模擬影片列表端點"""
    # 生成一些模擬影片數據
    mock_videos_data = [
        {
            "id": 1,
            "title": "AI生成的第一支影片",
            "description": "使用AI技術生成的示範影片",
            "duration": "00:45",
            "views": 1250,
            "likes": 89,
            "shares": 12,
            "thumbnail": "https://via.placeholder.com/320x180/4f46e5/ffffff?text=Video+1",
            "created_at": "2024-01-15T10:30:00Z",
            "status": "published",
        },
        {
            "id": 2,
            "title": "創意內容製作演示",
            "description": "展示如何使用平台創建創意內容",
            "duration": "01:23",
            "views": 2340,
            "likes": 156,
            "shares": 28,
            "thumbnail": "https://via.placeholder.com/320x180/7c3aed/ffffff?text=Video+2",
            "created_at": "2024-01-20T14:20:00Z",
            "status": "published",
        },
        {
            "id": 3,
            "title": "語音克隆技術介紹",
            "description": "深入了解我們的語音克隆技術",
            "duration": "02:15",
            "views": 890,
            "likes": 67,
            "shares": 8,
            "thumbnail": "https://via.placeholder.com/320x180/059669/ffffff?text=Video+3",
            "created_at": "2024-01-25T09:15:00Z",
            "status": "draft",
        },
    ]

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "videos": mock_videos_data,
                "total": len(mock_videos_data),
                "page": 1,
                "per_page": 10,
            },
        },
    )


# 分析端點
@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_analytics():
    """模擬儀表板分析數據端點"""
    return JSONResponse(status_code=200, content={"success": True, "data": mock_analytics})


# AI服務端點
@app.post("/api/v1/generate/script")
async def generate_script(request: Request):
    """AI腳本生成端點 - 整合Google搜索和DeepSeek API"""
    body = await request.json()
    topic = body.get("topic", "未指定主題")
    description = body.get("description", "")
    platform = body.get("platform", "youtube")
    style = body.get("style", "educational")
    duration = body.get("duration", 60)
    language = body.get("language", "zh-TW")
    time_range = body.get("time_range", "w")  # 新增時間範圍參數
    enable_search = body.get("enable_search", True)  # 是否啟用搜索

    print(f"🤖 智能腳本生成請求 - 主題: {topic}, 描述: {description[:50]}{'...' if len(description) > 50 else ''}, 平台: {platform}, 風格: {style}")
    
    latest_news = ""
    search_results = []
    
    try:
        # Step 1: 如果啟用搜索，先獲取最新資訊
        if enable_search:
            print(f"🔍 Step 1: 搜索最新資訊...")
            search_query = f"{topic} {description[:30]}" if description else topic
            search_results = await search_google_news(search_query, time_range, max_results=8)
            
            # Step 2: 整理搜索結果為摘要
            if search_results:
                print(f"📊 Step 2: 整理搜索結果...")
                latest_news = await summarize_search_results(search_results, topic)
                print(f"✅ 搜索摘要生成完成，長度: {len(latest_news)}")
            else:
                print("⚠️ 未獲得有效搜索結果")
        
        # Step 3: 使用DeepSeek API生成增強腳本
        print(f"🎬 Step 3: 生成AI腳本...")
        if DEEPSEEK_API_KEY:
            # 使用增強的提示詞，包含最新資訊
            prompt = create_script_prompt(topic, platform, style, duration, language, description, latest_news)
            
            # 更新系統提示詞，強調最新資訊的使用
            system_content = """你是一個專業的影片腳本創作者，擅長為不同平台創作吸引人的內容。你的腳本總是生動有趣，富有創意，能夠抓住觀眾的注意力。

特別要求：
1. 如果提供了最新資訊，請自然地融入到腳本中，讓內容更具時效性
2. 不要生硬地列舉資訊，而要巧妙地編織到故事或論述中
3. 確保腳本既有最新觀點，又保持流暢自然
4. 使用最新資訊來支持你的觀點或增加內容的說服力"""
            
            messages = [
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            # 調用DeepSeek API
            generated_script = await call_deepseek_api(messages, temperature=0.8, max_tokens=1800)
            
            print(f"✅ DeepSeek API調用成功，生成腳本長度: {len(generated_script)}")
            
            # 構建回應數據
            response_data = {
                "script": generated_script.strip(),
                "word_count": len(generated_script.split()),
                "estimated_duration": f"{duration}-{duration+15} seconds",
                "tone": style,
                "platform": platform,
                "language": language,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "provider": "DeepSeek + Google Search",
                "model": "deepseek-chat",
                "search_enabled": enable_search,
                "search_summary": latest_news if latest_news else "未使用搜索功能",
                "search_results_count": len(search_results),
                "time_range": time_range
            }
            
            # 如果有搜索結果，添加搜索詳情
            if search_results:
                response_data["search_sources"] = [
                    {
                        "title": result["title"],
                        "source": result["displayLink"],
                        "snippet": result["snippet"][:100] + "..." if len(result["snippet"]) > 100 else result["snippet"]
                    }
                    for result in search_results[:3]  # 只返回前3個來源
                ]
            
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": response_data
                }
            )
            
        else:
            # 如果没有配置DeepSeek API，抛出异常进入回退模式
            raise Exception("DeepSeek API key not configured")
            
    except Exception as e:
        # 错误处理和回退机制
        print(f"⚠️ DeepSeek API失败: {str(e)}")
        print("🔄 使用增强版回退脚本生成")
        
        # 增强版回退脚本 - 比原来更生动有趣
        enhanced_fallback_script = create_enhanced_fallback_script(topic, platform, style, duration, language, description)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "script": enhanced_fallback_script.strip(),
                    "word_count": len(enhanced_fallback_script.split()),
                    "estimated_duration": f"{duration}-{duration+15} seconds",
                    "tone": style,
                    "platform": platform,
                    "language": language,
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "provider": "Enhanced Fallback",
                    "model": "template-enhanced",
                    "note": "使用增强版本地生成（DeepSeek API不可用）"
                },
            },
        )

def create_enhanced_fallback_script(topic, platform, style, duration, language, description=""):
    """创建增强版回退脚本 - 比原来更生动有趣，支持项目描述"""
    
    # 根據平台和風格選擇不同的開頭（繁體中文）
    openings = {
        "youtube": {
            "educational": f"等等！你知道{topic}其實比你想像的更有趣嗎？",
            "entertainment": f"哈囉大家好！今天我要跟你們聊一個超級有意思的話題——{topic}！",
            "tutorial": f"想要快速掌握{topic}？這個影片絕對不能錯過！",
            "review": f"最近大家都在討論{topic}，但真相到底是什麼呢？"
        },
        "tiktok": {
            "educational": f"3秒鐘告訴你{topic}的秘密！",
            "entertainment": f"我賭你不知道{topic}的這個事實！",
            "tutorial": f"學會這招，{topic}從此不是問題！",
            "lifestyle": f"分享一個關於{topic}的生活小技巧！"
        },
        "bilibili": {
            "educational": f"UP主今天要科普一個關於{topic}的冷知識！",
            "entertainment": f"兄弟們，{topic}居然還有這種操作？！",
            "review": f"測評時間！今天我們來深度分析{topic}！"
        }
    }
    
    # 選擇合適的開頭
    platform_openings = openings.get(platform, openings["youtube"])
    opening = platform_openings.get(style, f"今天我們來聊聊{topic}這個話題！")
    
    # 構建基於描述的個性化內容
    description_content = ""
    if description and description.strip():
        description_content = f"\n\n根據你的具體需求：{description.strip()}\n讓我為你詳細解釋一下："
    
    # 核心内容模板
    core_content_templates = {
        "educational": f"""
{opening}

首先，讓我來告訴你{topic}為什麼這麼重要。很多人都以為自己了解{topic}，但實際上，這裡面有很多你不知道的門道。{description_content}

我先給你分享三個關鍵要點：

第一個要點，也是最容易被忽略的——很多人在處理{topic}的時候，都會犯一個共同的錯誤。我之前也是這樣，直到我發現了正確的方法。

第二個要點特別實用，這個方法可能會顛覆你之前的認知。當你掌握了這個技巧，你會發現{topic}其實並沒有想像中那麼複雜。

第三個要點是進階技巧，這是我從實踐中總結出來的經驗。用好這一點，你就能比90%的人做得更好。

最後，我想說的是，{topic}不僅僅是一個話題，更是一種思維方式。掌握了這種思維，你在很多方面都會有新的突破。
        """,
        "entertainment": f"""
{opening}

你們絕對想不到，{topic}背後居然有這麼多有趣的故事！{description_content}

我先跟你們分享一個超搞笑的事情——前幾天我朋友跟我說，他以為{topic}就是xxx，結果鬧出了大笑話！這讓我意識到，原來大家對{topic}的誤解這麼深。

更有趣的是，我發現了{topic}的幾個神奇特點：

第一個特點讓我震驚了！原來{topic}還能這樣用，這個發現簡直改變了我的世界觀。

第二個特點更是讓人意想不到，當我把這個分享給朋友的時候，他們都不敢相信！

第三個特點是我偶然發現的，現在想起來還覺得很神奇。

最搞笑的是，當我開始深入了解{topic}之後，我發現自己之前的想法有多麼天真。現在的我已經完全是{topic}的忠實粉絲了！
        """,
        "tutorial": f"""
{opening}

我知道很多人都想學會{topic}，但總是覺得很困難。今天我就來手把手教你，讓你輕鬆掌握這個技能！{description_content}

我把整個過程分解成了幾個簡單的步驟，保證你學會：

步驟一：準備工作。這一步很關鍵，很多人失敗就是因為準備不充分。我來告訴你具體要注意什麼。

步驟二：核心操作。這是最重要的部分，我會詳細演示給你看。記住，一定要按照我說的順序來做。

步驟三：優化細節。這些小技巧能讓你的效果提升一個層次，是我實踐總結出來的精華。

步驟四：避坑指南。我會告訴你常見的錯誤，讓你少走彎路。

按照這個方法，我相信你很快就能掌握{topic}。記住，關鍵是要多練習，熟能生巧！
        """
    }
    
    # 选择内容模板
    core_content = core_content_templates.get(style, core_content_templates["educational"])
    
    # 根據平台選擇結尾（繁體中文）
    endings = {
        "youtube": "如果這個影片對你有幫助，別忘了點讚訂閱！有任何問題歡迎在評論區留言，我們下期見！",
        "tiktok": "覺得有用的話雙擊小愛心！還想看什麼內容記得評論告訴我哦！",
        "bilibili": "如果覺得UP主講得不錯，記得一鍵三連支持一下！我們評論區見！",
        "instagram": "喜歡的話記得保存分享！想看更多內容記得關注我哦！"
    }
    
    ending = endings.get(platform, endings["youtube"])
    
    return f"{core_content.strip()}\n\n{ending}"


def create_image_prompts_from_script(script, topic, platform, style, description=""):
    """使用DeepSeek根據腳本內容和專案描述生成精確的圖像提示詞"""
    
    # 構建完整的上下文資訊
    context_info = f"主題：{topic}\n"
    if description and description.strip():
        context_info += f"專案描述：{description.strip()}\n"
    context_info += f"平台：{platform}\n風格：{style}\n"
    
    prompt = f"""你是專業的視覺創意指導，請根據以下完整資訊生成精確的AI圖像提示詞。

{context_info}

腳本內容：
{script[:800]}

請仔細分析腳本內容和專案描述，生成4個高度相關的圖像提示詞：

1. **主視覺圖/縮圖** - 必須體現專案的核心主題和描述中的關鍵元素
2. **背景場景1** - 直接對應腳本中提到的具體場景或情境
3. **背景場景2** - 呼應專案描述中的特定要求或氛圍
4. **輔助圖解** - 支持腳本內容的視覺化元素

重要要求：
- 每個提示詞必須包含專案描述中的關鍵元素
- 提示詞要具體描述視覺細節（顏色、構圖、風格）
- 適合{platform}平台的視覺特色
- 符合{style}風格的視覺調性
- 用英文輸出，適合AI圖像生成工具
- 每個提示詞50-120字

請按照JSON格式回應（只回傳JSON，不要額外文字）：
{{
  "prompts": [
    {{"type": "thumbnail", "description": "具體詳細的英文提示詞"}},
    {{"type": "background1", "description": "具體詳細的英文提示詞"}},
    {{"type": "background2", "description": "具體詳細的英文提示詞"}},
    {{"type": "illustration", "description": "具體詳細的英文提示詞"}}
  ]
}}"""
    
    return prompt

def create_enhanced_local_prompt(prompt, script, topic, platform, style, description=""):
    """創建智能的本地圖像提示詞增強"""
    
    # 基礎風格增強
    style_enhancements = {
        "realistic": "photorealistic, high resolution, professional photography, cinematic lighting",
        "artistic": "digital art, creative, stylized, artistic rendering, vibrant colors",
        "cartoon": "cartoon style, colorful, fun, animated, clean illustration",
        "minimalist": "clean, simple, minimal design, modern, elegant composition",
        "educational": "educational content, clear visual, informative, professional design",
        "entertainment": "exciting, dynamic, eye-catching, fun atmosphere",
        "lifestyle": "lifestyle photography, natural lighting, cozy atmosphere, relatable",
        "tutorial": "step-by-step visual, instructional design, clear demonstration"
    }
    
    # 平台特色增強
    platform_enhancements = {
        "youtube": "youtube thumbnail style, bold text overlay, dramatic composition, 16:9 aspect ratio",
        "tiktok": "vertical composition, mobile-friendly, trendy aesthetic, 9:16 aspect ratio", 
        "bilibili": "anime-inspired style, vibrant colors, eye-catching design, Chinese aesthetic",
        "instagram": "instagram-worthy, square composition, aesthetic appeal, lifestyle photography"
    }
    
    # 從腳本內容提取關鍵詞
    script_keywords = []
    if script:
        # 尋找腳本中的關鍵詞彙
        keywords_patterns = [
            "步驟", "方法", "技巧", "要點", "關鍵", "重要", "基礎", "進階",
            "準備", "開始", "結束", "過程", "程序", "操作", "實踐",
            "環境", "場景", "背景", "氛圍", "情境", "設定"
        ]
        
        for keyword in keywords_patterns:
            if keyword in script:
                script_keywords.append(keyword)
    
    # 從專案描述提取視覺元素
    visual_elements = []
    if description:
        description_lower = description.lower()
        visual_mapping = {
            "簡單": "simple and clear",
            "專業": "professional and polished", 
            "創意": "creative and innovative",
            "實用": "practical and useful",
            "基礎": "beginner-friendly and accessible",
            "進階": "advanced and sophisticated",
            "快速": "dynamic and energetic",
            "詳細": "detailed and comprehensive",
            "零基礎": "beginner tutorial style",
            "上班族": "office worker, professional setting",
            "學生": "student-friendly, educational environment",
            "居家": "home setting, cozy environment",
            "計算機": "computer programming, coding setup",
            "早餐": "breakfast food, kitchen setting, morning light",
            "食材": "ingredients, food preparation, cooking",
            "健身": "fitness equipment, gym environment, exercise",
            "腹肌": "fitness training, workout setting, exercise demonstration"
        }
        
        for key, visual in visual_mapping.items():
            if key in description:
                visual_elements.append(visual)
    
    # 構建增強的提示詞
    enhanced_parts = [prompt]
    
    # 添加主題相關的視覺描述
    if topic and topic not in prompt:
        enhanced_parts.append(f"related to {topic}")
    
    # 添加從描述提取的視覺元素
    if visual_elements:
        enhanced_parts.extend(visual_elements[:3])  # 最多3個元素避免過長
    
    # 添加風格增強
    style_enhancement = style_enhancements.get(style, "high quality, detailed")
    enhanced_parts.append(style_enhancement)
    
    # 添加平台特色
    platform_enhancement = platform_enhancements.get(platform, "")
    if platform_enhancement:
        enhanced_parts.append(platform_enhancement)
    
    # 組合所有部分
    enhanced_prompt = ", ".join(enhanced_parts)
    
    return enhanced_prompt

# === 語音優化相關函數 ===

async def optimize_voice_with_deepseek(text, platform, style, topic=""):
    """使用DeepSeek優化語音生成參數"""
    print(f"🤖 使用DeepSeek優化語音參數...")
    
    if not DEEPSEEK_API_KEY:
        print("⚠️ DeepSeek API未配置，使用本地優化邏輯")
        return optimize_voice_locally(text, platform, style, topic)
    
    try:
        # 創建DeepSeek提示詞
        messages = [{
            "role": "user",
            "content": f"""作為專業的語音製作專家，請為以下文本分析並推薦最佳的語音合成參數：

文本內容：{text[:300]}...
平台：{platform}
風格：{style}
主題：{topic}

請分析文本的情緒、語調、節奏，並推薦：
1. 最適合的語音類型（從alloy, echo, fable, onyx, nova, shimmer中選擇）
2. 語速設置（0.5-2.0之間）
3. 情感調性
4. 語音優化建議

請按照JSON格式回應：
{{
  "recommended_voice": "語音ID",
  "recommended_speed": 速度數值,
  "emotion": "情感描述",
  "tone": "語調描述", 
  "pronunciation_notes": ["發音要點1", "發音要點2"],
  "optimization_reason": "推薦理由"
}}"""
        }]
        
        response = await call_deepseek_api(messages, temperature=0.3)
        
        if response and 'choices' in response:
            content = response['choices'][0]['message']['content']
            
            # 嘗試解析JSON回應
            try:
                import re
                json_match = re.search(r'\{.*?\}', content, re.DOTALL)
                if json_match:
                    voice_params = json.loads(json_match.group())
                    print(f"✅ DeepSeek語音優化成功: {voice_params.get('recommended_voice', 'alloy')}")
                    return voice_params
                else:
                    print("⚠️ DeepSeek回應格式異常，使用本地優化")
                    return optimize_voice_locally(text, platform, style, topic)
            except json.JSONDecodeError:
                print("⚠️ DeepSeek JSON解析失敗，使用本地優化")
                return optimize_voice_locally(text, platform, style, topic)
        
    except Exception as e:
        print(f"⚠️ DeepSeek API調用失敗: {e}")
        return optimize_voice_locally(text, platform, style, topic)
    
    return optimize_voice_locally(text, platform, style, topic)

def optimize_voice_locally(text, platform, style, topic=""):
    """本地語音參數優化邏輯"""
    # 基於內容長度和類型的智能分析
    text_length = len(text)
    word_count = len(text.split())
    
    # 平台優化
    platform_voice_map = {
        "youtube": {"voice": "alloy", "speed": 1.0, "tone": "專業友善"},
        "tiktok": {"voice": "nova", "speed": 1.2, "tone": "活潑年輕"},
        "bilibili": {"voice": "fable", "speed": 1.1, "tone": "輕鬆有趣"},
        "instagram": {"voice": "shimmer", "speed": 1.0, "tone": "時尚自然"}
    }
    
    # 風格優化
    style_voice_map = {
        "educational": {"voice": "alloy", "speed": 0.9, "emotion": "專業沈穩"},
        "entertainment": {"voice": "nova", "speed": 1.3, "emotion": "活潑興奮"},
        "tutorial": {"voice": "echo", "speed": 0.8, "emotion": "清晰耐心"},
        "review": {"voice": "onyx", "speed": 1.0, "emotion": "客觀理性"},
        "lifestyle": {"voice": "shimmer", "speed": 1.1, "emotion": "親切自然"},
        "promotional": {"voice": "fable", "speed": 1.2, "emotion": "熱情積極"}
    }
    
    # 組合推薦
    platform_rec = platform_voice_map.get(platform, {"voice": "alloy", "speed": 1.0, "tone": "自然"})
    style_rec = style_voice_map.get(style, {"voice": "alloy", "speed": 1.0, "emotion": "自然"})
    
    # 智能選擇最佳語音
    final_voice = style_rec["voice"]  # 風格優先
    final_speed = (platform_rec["speed"] + style_rec["speed"]) / 2  # 平均速度
    
    # 內容長度調整
    if word_count > 500:
        final_speed = max(0.8, final_speed - 0.1)  # 長內容稍慢
    elif word_count < 100:
        final_speed = min(1.5, final_speed + 0.2)  # 短內容可稍快
    
    return {
        "recommended_voice": final_voice,
        "recommended_speed": round(final_speed, 1),
        "emotion": style_rec.get("emotion", "自然"),
        "tone": platform_rec.get("tone", "自然"),
        "pronunciation_notes": [
            "注意語調自然停頓",
            "重點詞彙適當加重",
            "保持整體節奏感"
        ],
        "optimization_reason": f"基於{platform}平台和{style}風格的本地優化建議"
    }

async def generate_voice_with_openai(text, voice="alloy", speed=1.0):
    """使用OpenAI TTS API生成真實語音"""
    if not OPENAI_API_KEY:
        raise Exception("OpenAI API key not configured")
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "tts-1",
        "input": text,
        "voice": voice,
        "speed": speed
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(OPENAI_TTS_URL, headers=headers, json=data) as response:
            if response.status == 200:
                audio_content = await response.read()
                
                # 創建音頻存儲目錄
                audio_dir = "generated_audio"
                os.makedirs(audio_dir, exist_ok=True)
                
                # 生成唯一的文件名
                timestamp = int(time.time())
                filename = f"voice_{timestamp}_{voice}_{speed}.mp3"
                filepath = os.path.join(audio_dir, filename)
                
                # 保存音頻文件
                with open(filepath, 'wb') as f:
                    f.write(audio_content)
                
                print(f"✅ 音頻文件已保存: {filepath}")
                
                return {
                    "success": True,
                    "audio_data": len(audio_content),
                    "format": "mp3",
                    "filepath": filepath,
                    "filename": filename,
                    "url": f"http://localhost:8001/audio/{filename}"
                }
            else:
                error_text = await response.text()
                raise Exception(f"OpenAI TTS API error: {error_text}")

async def generate_voice_with_edge_tts(text, voice="zh-TW-HsiaoChenNeural", rate="+0%"):
    """使用Edge TTS生成免費語音（支援繁體中文）"""
    try:
        import edge_tts
        
        # 語音映射：將標準語音ID映射到Edge TTS語音
        voice_mapping = {
            "alloy": "zh-TW-HsiaoChenNeural",      # 繁體中文女聲
            "echo": "zh-TW-YunJheNeural",         # 繁體中文男聲
            "fable": "zh-TW-HsiaoYuNeural",       # 繁體中文女聲
            "onyx": "zh-TW-YunJheNeural",         # 繁體中文男聲
            "nova": "zh-TW-HsiaoChenNeural",      # 繁體中文女聲
            "shimmer": "zh-TW-HsiaoYuNeural"      # 繁體中文女聲
        }
        
        edge_voice = voice_mapping.get(voice, "zh-TW-HsiaoChenNeural")
        
        # 速度轉換
        speed_map = {
            0.5: "-50%", 0.6: "-40%", 0.7: "-30%", 0.8: "-20%", 0.9: "-10%",
            1.0: "+0%", 1.1: "+10%", 1.2: "+20%", 1.3: "+30%", 1.4: "+40%", 1.5: "+50%"
        }
        edge_rate = speed_map.get(round(float(rate) if isinstance(rate, (int, float)) else 1.0, 1), "+0%")
        
        # 創建音頻存儲目錄
        audio_dir = "generated_audio"
        os.makedirs(audio_dir, exist_ok=True)
        
        # 生成唯一的文件名
        timestamp = int(time.time())
        filename = f"voice_{timestamp}_{voice}_edge.mp3"
        filepath = os.path.join(audio_dir, filename)
        
        # 使用Edge TTS生成語音
        communicate = edge_tts.Communicate(text, edge_voice, rate=edge_rate)
        await communicate.save(filepath)
        
        # 檢查文件是否成功生成
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            print(f"✅ Edge TTS音頻文件已生成: {filepath}")
            return {
                "success": True,
                "format": "mp3",
                "filepath": filepath,
                "filename": filename,
                "url": f"http://localhost:8001/audio/{filename}",
                "edge_voice": edge_voice,
                "edge_rate": edge_rate
            }
        else:
            raise Exception("Edge TTS音頻文件生成失敗")
            
    except ImportError:
        raise Exception("Edge TTS未安裝，請運行: pip install edge-tts")
    except Exception as e:
        raise Exception(f"Edge TTS生成失敗: {str(e)}")

async def generate_voice_with_gtts(text, lang='zh-tw'):
    """使用gTTS生成免費語音（Google Text-to-Speech）"""
    try:
        from gtts import gTTS
        
        # 創建音頻存儲目錄
        audio_dir = "generated_audio"
        os.makedirs(audio_dir, exist_ok=True)
        
        # 生成唯一的文件名
        timestamp = int(time.time())
        filename = f"voice_{timestamp}_gtts.mp3"
        filepath = os.path.join(audio_dir, filename)
        
        # 使用gTTS生成語音
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(filepath)
        
        # 檢查文件是否成功生成
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            print(f"✅ gTTS音頻文件已生成: {filepath}")
            return {
                "success": True,
                "format": "mp3",
                "filepath": filepath,
                "filename": filename,
                "url": f"http://localhost:8001/audio/{filename}",
                "language": lang
            }
        else:
            raise Exception("gTTS音頻文件生成失敗")
            
    except ImportError:
        raise Exception("gTTS未安裝，請運行: pip install gtts")
    except Exception as e:
        raise Exception(f"gTTS生成失敗: {str(e)}")

# === 圖像增強相關函數 ===

def create_basic_enhanced_prompt(prompt, topic, platform, style, description=""):
    """創建基礎的圖像提示詞增強"""
    
    enhanced_parts = [prompt]
    
    if topic:
        enhanced_parts.append(f"themed around {topic}")
    
    if description and len(description.strip()) > 10:
        # 從描述中提取簡單的視覺提示
        desc_words = description[:100].split()
        enhanced_parts.append("detailed and specific to project requirements")
    
    style_map = {
        "realistic": "photorealistic, professional quality",
        "artistic": "artistic rendering, creative design",
        "cartoon": "cartoon illustration, colorful",
        "educational": "educational content, clear design",
        "entertainment": "engaging and fun visual",
        "lifestyle": "lifestyle aesthetic, natural"
    }
    
    enhancement = style_map.get(style, "high quality")
    enhanced_parts.append(enhancement)
    
    return ", ".join(enhanced_parts)

@app.post("/api/v1/generate/image")
async def generate_image(request: Request):
    """AI圖像生成端點 - 支援DeepSeek智能提示詞生成"""
    body = await request.json()
    prompt = body.get("prompt", "beautiful landscape")
    style = body.get("style", "realistic")
    size = body.get("size", "1024x1024")
    script = body.get("script", "")  # 腳本內容
    topic = body.get("topic", "")
    platform = body.get("platform", "youtube")
    description = body.get("description", "")  # 新增：專案描述
    
    print(f"🎨 圖像生成請求 - 提示詞: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
    if description:
        print(f"📝 專案描述: {description[:100]}{'...' if len(description) > 100 else ''}")
    
    enhanced_prompt = prompt
    provider = "Mock Generator"
    
    # 優先使用腳本和描述生成智能提示詞
    if script and len(script.strip()) > 50:
        try:
            if DEEPSEEK_API_KEY:
                print("🤖 使用DeepSeek根據腳本和專案描述生成智能圖像提示詞...")
                
                script_to_image_prompt = create_image_prompts_from_script(script, topic, platform, style, description)
                
                messages = [
                    {
                        "role": "system",
                        "content": "你是專業的視覺創意指導，擅長根據影片腳本和專案描述生成精確的AI圖像提示詞。"
                    },
                    {
                        "role": "user",
                        "content": script_to_image_prompt
                    }
                ]
                
                # 調用DeepSeek API生成智能提示詞
                deepseek_response = await call_deepseek_api(messages, temperature=0.7, max_tokens=800)
            
            # 嘗試解析JSON回應
            try:
                import json
                import re
                
                # 提取JSON部分
                json_match = re.search(r'\{.*\}', deepseek_response, re.DOTALL)
                if json_match:
                    json_data = json.loads(json_match.group())
                    if "prompts" in json_data and len(json_data["prompts"]) > 0:
                        # 使用第一個生成的提示詞，或根據原始prompt選擇最合適的
                        for p in json_data["prompts"]:
                            if "thumbnail" in prompt.lower() and p["type"] == "thumbnail":
                                enhanced_prompt = p["description"]
                                break
                            elif "background" in prompt.lower() and "background" in p["type"]:
                                enhanced_prompt = p["description"]
                                break
                        else:
                            # 如果沒有匹配的，使用第一個
                            enhanced_prompt = json_data["prompts"][0]["description"]
                        
                        provider = "DeepSeek Enhanced"
                        print(f"✅ DeepSeek圖像提示詞生成成功: {enhanced_prompt[:100]}...")
                    
            except Exception as parse_error:
                print(f"⚠️ DeepSeek回應解析失敗，使用原始提示詞: {str(parse_error)}")
                enhanced_prompt = f"{prompt}, {style} style, high quality, detailed"
                provider = "DeepSeek Fallback"
                
        except Exception as e:
            print(f"⚠️ DeepSeek圖像生成失敗: {str(e)}")
            # 使用本地智能增強
            enhanced_prompt = create_enhanced_local_prompt(prompt, script, topic, platform, style, description)
            provider = "Enhanced Fallback"
        
        else:
            # 沒有 DeepSeek API，使用本地智能增強
            print("💡 使用本地智能圖像提示詞增強...")
            enhanced_prompt = create_enhanced_local_prompt(prompt, script, topic, platform, style, description)
            provider = "Smart Local"
            
    else:
        # 沒有腳本內容，使用基礎增強
        enhanced_prompt = create_basic_enhanced_prompt(prompt, topic, platform, style, description)
        provider = "Basic Enhanced"

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "url": f"https://picsum.photos/800/600?random={int(time.time())}",
                "image_url": f"https://picsum.photos/800/600?random={int(time.time())}",
                "prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "style": style,
                "resolution": size,
                "size": size,
                "provider": provider,
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        },
    )


@app.post("/api/v1/generate/voice")
async def synthesize_voice(request: Request):
    """增強的AI語音合成端點 - 支援DeepSeek優化"""
    print(f"🎤 收到語音合成請求...")
    body = await request.json()
    
    text = body.get("text", "")
    voice = body.get("voice", "alloy")  
    speed = body.get("speed", 1.0)
    platform = body.get("platform", "youtube")
    style = body.get("style", "educational")
    topic = body.get("topic", "")
    optimize_with_ai = body.get("optimize_with_ai", True)  # 是否使用AI優化
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text content is required")
    
    # 1. 使用DeepSeek優化語音參數（如果啟用）
    voice_optimization = None
    if optimize_with_ai:
        try:
            voice_optimization = await optimize_voice_with_deepseek(text, platform, style, topic)
            # 應用優化建議
            if voice_optimization:
                voice = voice_optimization.get("recommended_voice", voice)
                speed = voice_optimization.get("recommended_speed", speed)
                print(f"✅ 語音參數已優化: {voice} @ {speed}x")
        except Exception as e:
            print(f"⚠️ 語音優化失敗，使用預設參數: {e}")
    
    # 2. 多層語音生成策略 - 優先級：OpenAI TTS > Edge TTS > gTTS
    provider = "Mock TTS"
    audio_quality = "Simulated"
    audio_url = f"https://example.com/audio/voice_{int(time.time())}.mp3"
    actual_filepath = None
    
    # 策略1：OpenAI TTS（最高品質）
    try:
        if OPENAI_API_KEY and len(text) < 4000:
            print("🔊 嘗試使用OpenAI TTS生成真實語音...")
            tts_result = await generate_voice_with_openai(text, voice, speed)
            if tts_result["success"]:
                print("✅ OpenAI TTS語音生成成功！")
                provider = "OpenAI TTS"
                audio_quality = "High"
                audio_url = tts_result["url"]
                actual_filepath = tts_result["filepath"]
            else:
                raise Exception("OpenAI TTS generation failed")
        else:
            raise Exception("OpenAI TTS not available or text too long")
    except Exception as e:
        print(f"⚠️ OpenAI TTS失敗: {e}")
        
        # 策略2：Edge TTS（免費，支援繁體中文）
        try:
            print("🔊 嘗試使用Edge TTS生成免費語音...")
            edge_result = await generate_voice_with_edge_tts(text, voice, speed)
            if edge_result["success"]:
                print("✅ Edge TTS語音生成成功！")
                provider = "Edge TTS (免費)"
                audio_quality = "Good"
                audio_url = edge_result["url"]
                actual_filepath = edge_result["filepath"]
            else:
                raise Exception("Edge TTS generation failed")
        except Exception as e2:
            print(f"⚠️ Edge TTS失敗: {e2}")
            
            # 策略3：gTTS（Google免費TTS）
            try:
                print("🔊 嘗試使用gTTS生成免費語音...")
                gtts_result = await generate_voice_with_gtts(text, 'zh-tw')
                if gtts_result["success"]:
                    print("✅ gTTS語音生成成功！")
                    provider = "Google TTS (免費)"
                    audio_quality = "Standard"
                    audio_url = gtts_result["url"]
                    actual_filepath = gtts_result["filepath"]
                else:
                    raise Exception("gTTS generation failed")
            except Exception as e3:
                print(f"⚠️ gTTS失敗: {e3}")
                print("❌ 所有真實語音生成方式都失敗，使用模擬模式")
    
    # 3. 計算語音統計信息
    chinese_char_count = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
    word_count = len(text.split())
    
    # 繁體中文語音時長計算（比英文慢）
    if chinese_char_count > word_count * 0.5:  # 主要是中文
        estimated_duration = max(8, chinese_char_count * 0.4)  # 中文約每秒2.5字
    else:
        estimated_duration = max(8, word_count * 0.6)  # 英文約每秒1.6字
    
    # 根據語速調整
    estimated_duration = estimated_duration / speed
    
    # 4. 構建增強回應
    response_data = {
        "success": True,
        "data": {
            "url": audio_url,
            "audio_url": audio_url,
            "provider": provider,
            "voice": voice,
            "speed": speed,
            "quality": audio_quality,
            "duration": round(estimated_duration, 1),
            "text_length": len(text),
            "word_count": word_count,
            "chinese_char_count": chinese_char_count,
            "platform": platform,
            "style": style,
            "filepath": actual_filepath,
            "has_real_audio": actual_filepath is not None,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
    }
    
    # 5. 添加優化信息
    if voice_optimization:
        response_data["data"]["optimization"] = {
            "ai_optimized": True,
            "original_voice": body.get("voice", "alloy"),
            "original_speed": body.get("speed", 1.0),
            "optimized_voice": voice,
            "optimized_speed": speed,
            "emotion": voice_optimization.get("emotion", "自然"),
            "tone": voice_optimization.get("tone", "自然"),
            "optimization_reason": voice_optimization.get("optimization_reason", "AI智能優化"),
            "pronunciation_notes": voice_optimization.get("pronunciation_notes", [])
        }
        print(f"📊 語音優化詳情已添加到回應")
    else:
        response_data["data"]["optimization"] = {
            "ai_optimized": False,
            "note": "使用預設參數或優化失敗"
        }
    
    print(f"✅ 語音合成請求完成: {provider}, 時長{estimated_duration:.1f}秒")
    return JSONResponse(status_code=200, content=response_data)


@app.post("/api/v1/generate/music")
async def generate_music(request: Request):
    """模擬AI音樂生成端點"""
    body = await request.json()
    prompt = body.get("prompt", "ambient background music")
    style = body.get("style", "ambient")
    duration = body.get("duration", 60)

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "url": f"https://example.com/audio/music_{int(time.time())}.mp3",
                "audio_url": f"https://example.com/audio/music_{int(time.time())}.mp3",
                "prompt": prompt,
                "style": style,
                "duration": duration,
                "format": "MP3",
                "sample_rate": "44.1kHz",
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        },
    )


@app.post("/api/v1/generate/video")
async def generate_video(request: Request):
    """模擬影片生成端點"""
    body = await request.json()
    project_data = body.get("project_data", {})
    
    # 檢查必要元素
    if not project_data.get("script"):
        raise HTTPException(status_code=400, detail="Script is required for video generation")
    if not project_data.get("images") or len(project_data.get("images", [])) == 0:
        raise HTTPException(status_code=400, detail="Images are required for video generation")
    if not project_data.get("audio"):
        raise HTTPException(status_code=400, detail="Audio is required for video generation")
    
    # 模擬影片生成過程
    video_id = f"video_{int(time.time())}"
    title = project_data.get("title", "AI Generated Video")
    duration = project_data.get("duration", 60)
    resolution = project_data.get("resolution", "1920x1080")
    
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "video_id": video_id,
                "title": title,
                "url": f"https://example.com/videos/{video_id}.mp4",
                "download_url": f"https://example.com/videos/{video_id}.mp4",
                "thumbnail": f"https://picsum.photos/320/180?random={int(time.time())}",
                "duration": duration,
                "resolution": resolution,
                "format": "MP4",
                "fileSize": f"{duration * 2} MB",  # 模擬檔案大小
                "status": "completed",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "elements": {
                    "script_length": len(project_data.get("script", "")),
                    "image_count": len(project_data.get("images", [])),
                    "audio_duration": project_data.get("audio", {}).get("duration", 0),
                }
            },
        },
    )


@app.get("/api/v1/videos/{video_id}/download")
async def download_video(video_id: str):
    """模擬影片下載端點"""
    # 檢查影片是否存在（模擬）
    if not video_id.startswith("video_"):
        raise HTTPException(status_code=404, detail="Video not found")
    
    # 在真實環境中，這裡會返回實際的影片檔案
    # 現在返回下載資訊
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "video_id": video_id,
                "download_url": f"https://example.com/videos/{video_id}.mp4",
                "filename": f"{video_id}.mp4",
                "size": "25.6 MB",
                "format": "MP4",
                "expires_at": datetime.utcnow().isoformat() + "Z",
                "message": "Download URL generated successfully"
            },
        },
    )


@app.get("/api/v1/videos/{video_id}")
async def get_video_details(video_id: str):
    """模擬獲取影片詳情端點"""
    if not video_id.startswith("video_"):
        raise HTTPException(status_code=404, detail="Video not found")
    
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "video_id": video_id,
                "title": "AI Generated Video",
                "description": "Generated using AI video creation system",
                "url": f"https://example.com/videos/{video_id}.mp4",
                "download_url": f"https://example.com/videos/{video_id}.mp4",
                "thumbnail": f"https://picsum.photos/320/180?random={video_id.split('_')[1]}",
                "duration": 60,
                "resolution": "1920x1080",
                "format": "MP4",
                "fileSize": "25.6 MB",
                "status": "completed",
                "views": 0,
                "likes": 0,
                "shares": 0,
                "created_at": datetime.utcnow().isoformat() + "Z",
            },
        },
    )


# 錯誤處理
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Endpoint not found",
            "message": f"The requested endpoint {request.url.path} was not found",
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred",
        },
    )


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Mock API Gateway...")
    print("📋 Available endpoints:")
    print("   - Health: http://localhost:8001/health")
    print("   - Docs: http://localhost:8001/docs")
    print("   - Login: POST http://localhost:8001/api/v1/auth/login")
    print("   - Register: POST http://localhost:8001/api/v1/auth/register")
    print("   - Videos: GET http://localhost:8001/api/v1/videos")
    print("   - Analytics: GET http://localhost:8001/api/v1/analytics/dashboard")
    print("   🤖 AI Generation:")
    print("   - Script: POST http://localhost:8001/api/v1/generate/script")
    print("   - Image: POST http://localhost:8001/api/v1/generate/image")
    print("   - Voice: POST http://localhost:8001/api/v1/generate/voice")
    print("   - Music: POST http://localhost:8001/api/v1/generate/music")
    print("   - Video: POST http://localhost:8001/api/v1/generate/video")
    print("   📥 Video Management:")
    print("   - Download: GET http://localhost:8001/api/v1/videos/{video_id}/download")
    print("   - Details: GET http://localhost:8001/api/v1/videos/{video_id}")
    print("\n🌐 CORS enabled for:")
    print("   - http://localhost:3000 (SvelteKit dev)")
    print("   - http://localhost:5173 (Vite dev)")
    print("\n📧 Demo credentials:")
    print("   Email: demo@example.com")
    print("   Password: demo123")

    uvicorn.run(
        "mock_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )
