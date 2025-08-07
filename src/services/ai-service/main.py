#!/usr/bin/env python3
"""
AI Service - 真實的AI服務整合
提供腳本生成、圖像生成、音樂生成等AI功能
"""

import os
import logging
from datetime import datetime
from typing import Optional, List

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 導入共享模組
import sys
from pathlib import Path

# 添加專案根目錄到Python路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 導入AI客戶端
from .gemini_client import GeminiClient, GeminiGenerationConfig

# 修正music-service路徑（使用sys.path直接導入）
import importlib.util
music_service_path = project_root / "src" / "services" / "music-service" / "suno_client.py"
spec = importlib.util.spec_from_file_location("suno_client", music_service_path)
suno_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(suno_module)
SunoClient = suno_module.SunoClient
try:
    MusicGenerationRequest = suno_module.MusicGenerationRequest
except AttributeError:
    # 如果沒有這個類，建立一個基本的
    from pydantic import BaseModel
    class MusicGenerationRequest(BaseModel):
        prompt: str
        duration: int = 30

# 導入共享模組
from src.shared.config import get_service_settings

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 載入配置
settings = get_service_settings("ai_service")

# 創建FastAPI應用
app = FastAPI(
    title="AI Service",
    version="1.0.0",
    description="AI-powered content generation service",
)

# CORS設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",  # API Gateway
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# API金鑰配置
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUNO_API_KEY = os.getenv("SUNO_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Pydantic模型
class ScriptGenerationRequest(BaseModel):
    topic: str
    platform: str = "youtube"  # youtube, tiktok, instagram
    style: str = "educational"  # educational, entertaining, promotional
    duration: int = 60  # 目標秒數
    language: str = "zh-TW"
    target_audience: str = "general"


class ImageGenerationRequest(BaseModel):
    prompt: str
    style: str = "realistic"  # realistic, artistic, anime, photography
    resolution: str = "1024x1024"
    quantity: int = 1


class MusicGenerationRequest(BaseModel):
    prompt: str
    style: str = "background"
    duration: int = 30
    instrumental: bool = True
    mood: str = "upbeat"  # upbeat, calm, dramatic, mysterious


class VoiceGenerationRequest(BaseModel):
    text: str
    voice_id: str = "female-1"
    speed: float = 1.0
    emotion: str = "neutral"
    language: str = "zh-TW"


# 健康檢查端點
@app.get("/health")
async def health_check():
    """健康檢查"""
    # 檢查API金鑰是否配置
    api_keys_status = {
        "gemini": "configured" if GEMINI_API_KEY else "missing",
        "suno": "configured" if SUNO_API_KEY else "missing",
        "openai": "configured" if OPENAI_API_KEY else "missing",
    }
    
    return {
        "status": "healthy",
        "service": "ai-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "api_keys": api_keys_status,
    }


@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "AI Service - Content Generation Platform",
        "version": "1.0.0",
        "features": [
            "Script Generation (Gemini Pro)",
            "Image Generation (DALL-E/Stable Diffusion)", 
            "Music Generation (Suno AI)",
            "Voice Synthesis (OpenAI TTS)",
        ],
        "docs": "/docs",
        "health": "/health",
    }


# 腳本生成端點
@app.post("/api/v1/generate/script")
async def generate_script(request: ScriptGenerationRequest):
    """使用Gemini Pro生成影片腳本"""
    
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured"
        )
    
    logger.info(f"Generating script for topic: {request.topic}")
    
    try:
        # 根據平台和風格調整系統指令
        platform_styles = {
            "youtube": "創作適合YouTube的教育性內容，包含引人入勝的開場、清晰的結構和號召行動",
            "tiktok": "創作適合TikTok的短影片內容，節奏快、抓住注意力、適合垂直螢幕",
            "instagram": "創作適合Instagram的視覺導向內容，美觀、簡潔、適合方形格式"
        }
        
        style_instructions = {
            "educational": "採用教育性風格，清楚解釋概念，提供有價值的資訊",
            "entertaining": "採用娛樂性風格，幽默風趣，讓觀眾感到愉快",
            "promotional": "採用宣傳性風格，突出產品或服務的優勢，說服觀眾採取行動"
        }
        
        system_instruction = f"""
        你是專業的{request.platform}內容創作者。
        
        任務：為主題「{request.topic}」創作一個{request.style}風格的{request.duration}秒影片腳本。
        
        要求：
        1. {platform_styles.get(request.platform, '創作高品質內容')}
        2. {style_instructions.get(request.style, '保持專業風格')}
        3. 目標觀眾：{request.target_audience}
        4. 語言：{request.language}
        5. 時長控制在{request.duration}秒左右
        6. 包含明確的開場、主要內容和結尾
        
        請以自然的說話方式撰寫，避免過於正式的書面語。
        """
        
        # 調用Gemini API
        async with GeminiClient(api_key=GEMINI_API_KEY) as client:
            result = await client.generate_content(
                prompt=f"請為主題「{request.topic}」創作影片腳本",
                system_instruction=system_instruction,
                generation_config=GeminiGenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1024,
                    top_p=0.8
                )
            )
            
            if not result.success:
                raise HTTPException(
                    status_code=500,
                    detail=f"Script generation failed: {result.error_message}"
                )
            
            # 估算說話時間 (假設每分鐘150個中文字)
            word_count = len(result.text)
            estimated_duration = round((word_count / 150) * 60)
            
            return {
                "success": True,
                "data": {
                    "script": result.text,
                    "word_count": word_count,
                    "estimated_duration_seconds": estimated_duration,
                    "platform": request.platform,
                    "style": request.style,
                    "generated_at": datetime.utcnow().isoformat(),
                    "usage_metadata": result.usage_metadata,
                }
            }
            
    except Exception as e:
        logger.error(f"Script generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Script generation failed: {str(e)}"
        )


# 圖像生成端點
@app.post("/api/v1/generate/image")
async def generate_image(request: ImageGenerationRequest):
    """生成圖像（目前使用Placeholder服務，可替換為DALL-E等）"""
    
    logger.info(f"Generating image for prompt: {request.prompt}")
    
    try:
        # TODO: 整合真實的圖像生成服務 (DALL-E, Stable Diffusion等)
        # 目前使用高品質的placeholder服務
        
        import hashlib
        
        # 基於提示創建唯一的圖像ID
        prompt_hash = hashlib.md5(request.prompt.encode()).hexdigest()[:8]
        
        # 根據風格選擇不同的圖像源
        style_seeds = {
            "realistic": 100,
            "artistic": 200, 
            "anime": 300,
            "photography": 400
        }
        
        seed = style_seeds.get(request.style, 100) + int(prompt_hash, 16) % 100
        
        # 解析解析度
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
                "generated_at": datetime.utcnow().isoformat(),
                "note": "Using placeholder service. Integrate with DALL-E or Stable Diffusion for production."
            }
        }
        
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Image generation failed: {str(e)}"
        )


# 音樂生成端點
@app.post("/api/v1/generate/music")
async def generate_music(request: MusicGenerationRequest):
    """使用Suno AI生成音樂"""
    
    if not SUNO_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Suno API key not configured"
        )
    
    logger.info(f"Generating music for prompt: {request.prompt}")
    
    try:
        # 構建詳細的音樂生成提示
        mood_descriptors = {
            "upbeat": "energetic, positive, lively",
            "calm": "peaceful, relaxing, gentle", 
            "dramatic": "intense, powerful, emotional",
            "mysterious": "dark, intriguing, suspenseful"
        }
        
        style_descriptors = {
            "background": "ambient, subtle, non-intrusive",
            "cinematic": "epic, orchestral, movie-like",
            "electronic": "modern, synthesized, digital",
            "acoustic": "organic, natural instruments"
        }
        
        enhanced_prompt = f"{request.prompt}, {mood_descriptors.get(request.mood, 'balanced')}, {style_descriptors.get(request.style, 'versatile')}"
        if request.instrumental:
            enhanced_prompt += ", instrumental, no vocals"
        
        # 調用Suno API
        suno_request = SunoMusicRequest(
            prompt=enhanced_prompt,
            style=request.style,
            duration=request.duration,
            instrumental=request.instrumental,
            title=f"AI Music - {request.prompt[:30]}"
        )
        
        async with SunoClient(api_key=SUNO_API_KEY) as client:
            result = await client.generate_music(suno_request)
            
            if result.status == "failed":
                raise HTTPException(
                    status_code=500,
                    detail=f"Music generation failed: {result.error_message}"
                )
            elif result.status == "timeout":
                raise HTTPException(
                    status_code=408,
                    detail="Music generation timed out"
                )
            
            return {
                "success": True,
                "data": {
                    "id": result.id,
                    "status": result.status,
                    "audio_url": result.audio_url,
                    "video_url": result.video_url,
                    "title": result.title,
                    "duration": result.duration,
                    "prompt": enhanced_prompt,
                    "style": request.style,
                    "mood": request.mood,
                    "instrumental": request.instrumental,
                    "generated_at": result.created_at or datetime.utcnow().isoformat(),
                }
            }
            
    except Exception as e:
        logger.error(f"Music generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Music generation failed: {str(e)}"
        )


# 語音合成端點
@app.post("/api/v1/generate/voice")
async def generate_voice(request: VoiceGenerationRequest):
    """語音合成（可整合OpenAI TTS或其他語音服務）"""
    
    logger.info(f"Generating voice for text: {request.text[:50]}...")
    
    try:
        # TODO: 整合真實的語音合成服務 (OpenAI TTS, Azure Speech等)
        
        # 估算音頻時長（中文約每分鐘200字）
        char_count = len(request.text)
        estimated_duration = round((char_count / 200) * 60, 1)
        
        return {
            "success": True,
            "data": {
                "audio_url": "#",  # TODO: 實際生成的音頻URL
                "text": request.text,
                "voice_id": request.voice_id,
                "language": request.language,
                "speed": request.speed,
                "emotion": request.emotion,
                "duration_seconds": estimated_duration,
                "character_count": char_count,
                "generated_at": datetime.utcnow().isoformat(),
                "note": "Voice synthesis service not yet implemented. Integrate with OpenAI TTS or Azure Speech."
            }
        }
        
    except Exception as e:
        logger.error(f"Voice generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Voice generation failed: {str(e)}"
        )


# 批量生成端點
@app.post("/api/v1/generate/batch")
async def generate_batch(
    script_request: Optional[ScriptGenerationRequest] = None,
    image_request: Optional[ImageGenerationRequest] = None,
    music_request: Optional[MusicGenerationRequest] = None,
    voice_request: Optional[VoiceGenerationRequest] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """批量生成多種內容"""
    
    logger.info("Starting batch generation")
    
    results = {}
    
    try:
        # 依序執行各項生成任務
        if script_request:
            logger.info("Generating script...")
            script_result = await generate_script(script_request)
            results["script"] = script_result["data"]
            
        if image_request:
            logger.info("Generating images...")
            image_result = await generate_image(image_request)
            results["images"] = image_result["data"]
            
        if music_request:
            logger.info("Generating music...")
            music_result = await generate_music(music_request)
            results["music"] = music_result["data"]
            
        if voice_request:
            logger.info("Generating voice...")
            voice_result = await generate_voice(voice_request)
            results["voice"] = voice_result["data"]
        
        return {
            "success": True,
            "data": results,
            "generated_at": datetime.utcnow().isoformat(),
            "batch_id": f"batch_{int(datetime.utcnow().timestamp())}",
        }
        
    except Exception as e:
        logger.error(f"Batch generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch generation failed: {str(e)}"
        )


if __name__ == "__main__":
    print("🤖 Starting AI Service...")
    print("🔧 Features:")
    print("   - Script Generation (Gemini Pro)")
    print("   - Image Generation (Placeholder)")
    print("   - Music Generation (Suno AI)")
    print("   - Voice Synthesis (Placeholder)")
    print(f"   - Docs: http://localhost:8005/docs")
    print(f"   - Health: http://localhost:8005/health")
    
    print("\n🔑 API Keys Status:")
    print(f"   - Gemini: {'✅' if GEMINI_API_KEY else '❌'}")
    print(f"   - Suno: {'✅' if SUNO_API_KEY else '❌'}")
    print(f"   - OpenAI: {'✅' if OPENAI_API_KEY else '❌'}")
    
    if not any([GEMINI_API_KEY, SUNO_API_KEY, OPENAI_API_KEY]):
        print("\n⚠️  Warning: No API keys configured. Some features will be limited.")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8005,
        reload=True,
        log_level="info",
    )