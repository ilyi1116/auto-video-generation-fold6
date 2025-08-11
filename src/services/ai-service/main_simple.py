#!/usr/bin/env python3
"""
AI Service - 簡化版實現
整合OpenAI、Gemini等AI服務，提供腳本生成、TTS語音合成等功能
"""

import os
import logging
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
import asyncio
import aiohttp

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建FastAPI應用
app = FastAPI(
    title="AI Service - Simplified",
    version="1.0.0",
    description="AI-powered content generation service",
)

# CORS設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# API金鑰配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# Pydantic模型
class ScriptGenerationRequest(BaseModel):
    topic: str
    platform: str = "youtube"
    style: str = "educational"
    duration: int = 60
    language: str = "zh-TW"
    target_audience: str = "general"

class ImageGenerationRequest(BaseModel):
    prompt: str
    style: str = "realistic"
    resolution: str = "1024x1024"
    quantity: int = 1

class VoiceGenerationRequest(BaseModel):
    text: str
    voice_id: str = "alloy"
    speed: float = 1.0
    language: str = "zh-TW"

class MusicGenerationRequest(BaseModel):
    prompt: str
    style: str = "background"
    duration: int = 30
    mood: str = "upbeat"

# OpenAI API 調用函數
async def call_openai_api(endpoint: str, data: dict, headers: dict) -> dict:
    """調用OpenAI API的通用函數"""
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"https://api.openai.com/v1/{endpoint}",
            json=data,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                raise HTTPException(
                    status_code=response.status, 
                    detail=f"OpenAI API error: {error_text}"
                )

# DeepSeek API 調用函數  
async def call_deepseek_api(messages: list) -> dict:
    """調用DeepSeek API生成腳本"""
    if not DEEPSEEK_API_KEY:
        return None
        
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.7
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.deepseek.com/v1/chat/completions",
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    logger.error(f"DeepSeek API error: {response.status}")
                    return None
    except Exception as e:
        logger.error(f"DeepSeek API call failed: {e}")
        return None

# 健康檢查端點
@app.get("/health")
async def health_check():
    """健康檢查"""
    api_keys_status = {
        "openai": "configured" if OPENAI_API_KEY and len(OPENAI_API_KEY) > 10 else "missing",
        "deepseek": "configured" if DEEPSEEK_API_KEY and len(DEEPSEEK_API_KEY) > 10 else "missing", 
        "gemini": "configured" if GEMINI_API_KEY and len(GEMINI_API_KEY) > 10 else "missing",
    }
    
    return {
        "status": "healthy",
        "service": "ai-service",
        "version": "1.0.0", 
        "timestamp": datetime.utcnow().isoformat(),
        "api_keys": api_keys_status,
        "features": [
            "Script Generation (DeepSeek/OpenAI)",
            "Voice Synthesis (OpenAI TTS)",
            "Image Generation (Placeholder)",
            "Music Generation (Placeholder)"
        ]
    }

@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "AI Service - Content Generation Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }

# 腳本生成端點
@app.post("/api/v1/generate/script")
async def generate_script(request: ScriptGenerationRequest):
    """生成影片腳本"""
    logger.info(f"Generating script for topic: {request.topic}")
    
    # 構建系統提示
    platform_guide = {
        "youtube": "適合YouTube長影片，需要詳細解說和教育性內容",
        "tiktok": "適合TikTok短影片，需要快節奏和吸引注意力",
        "instagram": "適合Instagram Reels，需要視覺化和時尚感"
    }
    
    style_guide = {
        "educational": "教育性風格，提供有價值的知識和見解",
        "entertaining": "娛樂性風格，輕鬆幽默，容易理解",
        "promotional": "推廣性風格，突出產品優勢和價值"
    }
    
    system_prompt = f"""
    你是專業的{request.platform}內容創作者。請為主題「{request.topic}」創作一個{request.style}風格的影片腳本。
    
    要求：
    1. {platform_guide.get(request.platform, '創作高品質內容')}
    2. {style_guide.get(request.style, '保持專業風格')}
    3. 目標觀眾：{request.target_audience}
    4. 預期時長：{request.duration}秒
    5. 語言：{request.language}
    6. 包含吸引人的開場、主要內容和強有力的結尾
    
    請直接輸出腳本內容，使用自然的口語化表達。
    """
    
    user_message = f"請為「{request.topic}」創作一個{request.platform}平台的{request.style}風格影片腳本，時長約{request.duration}秒。"
    
    # 嘗試使用DeepSeek API
    script_content = None
    generation_source = "fallback"
    
    if DEEPSEEK_API_KEY and len(DEEPSEEK_API_KEY) > 10:
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            deepseek_result = await call_deepseek_api(messages)
            if deepseek_result and "choices" in deepseek_result:
                script_content = deepseek_result["choices"][0]["message"]["content"]
                generation_source = "deepseek"
                logger.info("Script generated using DeepSeek API")
        except Exception as e:
            logger.error(f"DeepSeek API failed: {e}")
    
    # 如果DeepSeek失敗，嘗試OpenAI
    if not script_content and OPENAI_API_KEY and len(OPENAI_API_KEY) > 10:
        try:
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            openai_result = await call_openai_api("chat/completions", data, headers)
            if openai_result and "choices" in openai_result:
                script_content = openai_result["choices"][0]["message"]["content"]
                generation_source = "openai"
                logger.info("Script generated using OpenAI API")
        except Exception as e:
            logger.error(f"OpenAI API failed: {e}")
    
    # 回退到本地生成
    if not script_content:
        logger.info("Using fallback script generation")
        script_content = f"""【{request.topic}】影片腳本

🎬 開場 (0-5秒)
嗨大家好！今天我們要來聊聊{request.topic}，這是一個非常有趣且實用的話題。

📖 主要內容 (5-{request.duration-10}秒)
首先，讓我們了解什麼是{request.topic}。{request.topic}在現代生活中扮演著重要的角色，它可以幫助我們...

接下來，我想和大家分享幾個關於{request.topic}的重要觀點：

1. 第一個重點是...
2. 第二個要注意的是...
3. 最後一個關鍵因素...

💡 實用建議
基於我的經驗，我建議大家在處理{request.topic}相關問題時，要記住這幾個要點...

🎯 結尾 ({request.duration-10}-{request.duration}秒)
總結來說，{request.topic}確實值得我們深入了解。希望今天的分享對你有幫助，如果喜歡這個內容，記得點讚訂閱，我們下次見！

#記得根據實際內容調整時間分配和詳細程度#
"""
        generation_source = "template"
    
    # 估算時長 (假設每分鐘150個中文字)
    word_count = len(script_content)
    estimated_duration = round((word_count / 150) * 60)
    
    return {
        "success": True,
        "data": {
            "script": script_content,
            "word_count": word_count,
            "estimated_duration_seconds": estimated_duration,
            "platform": request.platform,
            "style": request.style,
            "language": request.language,
            "generation_source": generation_source,
            "generated_at": datetime.utcnow().isoformat(),
        }
    }

# 語音合成端點  
@app.post("/api/v1/generate/voice")
async def generate_voice(request: VoiceGenerationRequest):
    """使用OpenAI TTS生成語音"""
    logger.info(f"Generating voice for text: {request.text[:50]}...")
    
    if not OPENAI_API_KEY or len(OPENAI_API_KEY) < 10:
        logger.warning("OpenAI API key not configured, using placeholder")
        return await generate_voice_placeholder(request)
    
    try:
        # 準備OpenAI TTS請求
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 映射語言
        voice_mapping = {
            "zh-TW": request.voice_id,  # 使用指定的聲音
            "zh-CN": request.voice_id,
            "en-US": request.voice_id,
        }
        
        data = {
            "model": "tts-1",
            "input": request.text,
            "voice": voice_mapping.get(request.language, request.voice_id),
            "speed": request.speed
        }
        
        # 調用OpenAI TTS API
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/audio/speech",
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    # 保存音頻文件
                    import tempfile
                    import base64
                    
                    audio_data = await response.read()
                    
                    # 創建臨時文件
                    temp_file = tempfile.NamedTemporaryFile(
                        delete=False, 
                        suffix=".mp3",
                        dir="./uploads/dev" if os.path.exists("./uploads/dev") else None
                    )
                    temp_file.write(audio_data)
                    temp_file.close()
                    
                    # 估算時長
                    char_count = len(request.text)
                    estimated_duration = round((char_count / 200) * 60, 1)
                    
                    return {
                        "success": True,
                        "data": {
                            "audio_url": f"/static/{os.path.basename(temp_file.name)}",
                            "audio_file": temp_file.name,
                            "text": request.text,
                            "voice_id": request.voice_id,
                            "language": request.language,
                            "speed": request.speed,
                            "duration_seconds": estimated_duration,
                            "character_count": char_count,
                            "generation_source": "openai_tts",
                            "generated_at": datetime.utcnow().isoformat(),
                        }
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"OpenAI TTS API error: {error_text}")
                    return await generate_voice_placeholder(request)
                    
    except Exception as e:
        logger.error(f"Voice generation failed: {e}")
        return await generate_voice_placeholder(request)

async def generate_voice_placeholder(request: VoiceGenerationRequest):
    """語音生成的Placeholder實現"""
    char_count = len(request.text)
    estimated_duration = round((char_count / 200) * 60, 1)
    
    return {
        "success": True,
        "data": {
            "audio_url": "#",  # Placeholder - 實際應該是音頻文件URL
            "text": request.text,
            "voice_id": request.voice_id,
            "language": request.language,
            "speed": request.speed,
            "duration_seconds": estimated_duration,
            "character_count": char_count,
            "generation_source": "placeholder",
            "generated_at": datetime.utcnow().isoformat(),
            "note": "Voice synthesis requires valid OpenAI API key"
        }
    }

# 圖片生成端點
@app.post("/api/v1/generate/image")
async def generate_image(request: ImageGenerationRequest):
    """生成圖片 (目前使用高品質placeholder)"""
    logger.info(f"Generating image for prompt: {request.prompt}")
    
    try:
        # 如果有DALL-E API金鑰，可以調用真實API
        if OPENAI_API_KEY and len(OPENAI_API_KEY) > 10:
            # TODO: 實現DALL-E API調用
            pass
        
        # 使用高品質placeholder
        prompt_hash = hashlib.md5(request.prompt.encode()).hexdigest()[:8]
        seed = int(prompt_hash, 16) % 1000
        width, height = request.resolution.split("x")
        
        images = []
        for i in range(request.quantity):
            image_url = f"https://picsum.photos/{width}/{height}?random={seed + i}"
            images.append({
                "url": image_url,
                "prompt": request.prompt,
                "style": request.style,
                "resolution": request.resolution,
                "seed": seed + i,
            })
        
        return {
            "success": True,
            "data": {
                "images": images,
                "prompt": request.prompt,
                "style": request.style,
                "resolution": request.resolution,
                "quantity": request.quantity,
                "generation_source": "placeholder",
                "generated_at": datetime.utcnow().isoformat(),
                "note": "Using high-quality placeholder images. Integrate DALL-E for production."
            }
        }
        
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")

# 音樂生成端點
@app.post("/api/v1/generate/music") 
async def generate_music(request: MusicGenerationRequest):
    """生成背景音樂 (placeholder實現)"""
    logger.info(f"Generating music for prompt: {request.prompt}")
    
    return {
        "success": True,
        "data": {
            "audio_url": "#",  # Placeholder音樂URL
            "prompt": request.prompt,
            "style": request.style, 
            "duration": request.duration,
            "mood": request.mood,
            "generation_source": "placeholder",
            "generated_at": datetime.utcnow().isoformat(),
            "note": "Music generation requires Suno AI or similar service integration"
        }
    }

# 批量生成端點
@app.post("/api/v1/generate/batch")
async def generate_batch(
    script_request: Optional[ScriptGenerationRequest] = None,
    image_request: Optional[ImageGenerationRequest] = None,
    voice_request: Optional[VoiceGenerationRequest] = None,
    music_request: Optional[MusicGenerationRequest] = None,
):
    """批量生成多種內容"""
    logger.info("Starting batch generation")
    
    results = {}
    
    try:
        if script_request:
            script_result = await generate_script(script_request)
            results["script"] = script_result["data"]
            
        if image_request:
            image_result = await generate_image(image_request)
            results["images"] = image_result["data"]
            
        if voice_request:
            voice_result = await generate_voice(voice_request)
            results["voice"] = voice_result["data"]
            
        if music_request:
            music_result = await generate_music(music_request)
            results["music"] = music_result["data"]
        
        return {
            "success": True,
            "data": results,
            "generated_at": datetime.utcnow().isoformat(),
            "batch_id": f"batch_{int(datetime.utcnow().timestamp())}",
        }
        
    except Exception as e:
        logger.error(f"Batch generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch generation failed: {str(e)}")

if __name__ == "__main__":
    print("🤖 Starting AI Service (Simplified)...")
    print("🔧 Features:")
    print("   - Script Generation (DeepSeek/OpenAI)")
    print("   - Voice Synthesis (OpenAI TTS)")  
    print("   - Image Generation (Placeholder)")
    print("   - Music Generation (Placeholder)")
    print(f"   - Docs: http://localhost:8005/docs")
    print(f"   - Health: http://localhost:8005/health")
    
    print("\n🔑 API Keys Status:")
    print(f"   - OpenAI: {'✅' if OPENAI_API_KEY and len(OPENAI_API_KEY) > 10 else '❌'}")
    print(f"   - DeepSeek: {'✅' if DEEPSEEK_API_KEY and len(DEEPSEEK_API_KEY) > 10 else '❌'}")
    print(f"   - Gemini: {'✅' if GEMINI_API_KEY and len(GEMINI_API_KEY) > 10 else '❌'}")
    
    if not any([
        OPENAI_API_KEY and len(OPENAI_API_KEY) > 10,
        DEEPSEEK_API_KEY and len(DEEPSEEK_API_KEY) > 10
    ]):
        print("\n⚠️  Warning: No valid API keys configured. Using placeholder responses.")
        print("   請在 .env.local 中配置真實的API金鑰以啟用完整功能")
    
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info",
    )