#!/usr/bin/env python3
"""
簡化版API Gateway - MVP快速啟動
不依賴複雜的導入，直接在根目錄運行
"""

import os
import logging
import hashlib
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List
import asyncio
import aiohttp

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
import jwt
from passlib.context import CryptContext

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 創建FastAPI應用
app = FastAPI(
    title="Auto Video API Gateway - Simple",
    version="1.0.0",
    description="AI-powered video generation platform API Gateway",
)

# CORS設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000", 
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 靜態文件服務
if os.path.exists("uploads/dev"):
    app.mount("/static", StaticFiles(directory="uploads/dev"), name="static")

# 安全設置
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 配置
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "development-jwt-secret-key-change-in-production-32chars")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# AI服務配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# 簡單的SQLite資料庫
DB_FILE = "auto_video_simple.db"

def init_database():
    """初始化SQLite資料庫"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 創建用戶表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 創建影片表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            topic TEXT,
            status TEXT DEFAULT 'pending',
            progress_percentage REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            video_url TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# 初始化資料庫
init_database()

# Pydantic模型
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class VideoCreate(BaseModel):
    title: str
    description: Optional[str] = None
    topic: str
    style: str = "modern"
    duration: int = 15
    platform: str = "tiktok"

class AIGenerateRequest(BaseModel):
    prompt: str
    type: str  # script, image, voice, music

# 工具函數
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """獲取當前用戶"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return int(user_id)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# API端點

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "service": "api-gateway-simple",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": ["user_auth", "video_management", "ai_services"],
        "database": "sqlite",
    }

@app.get("/")
async def root():
    """根端點"""
    return {
        "message": "Auto Video API Gateway - Simple",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }

# 認證端點
@app.post("/api/v1/auth/register")
async def register(request: UserCreate):
    """用戶註冊"""
    logger.info(f"Registration attempt: {request.email}")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 檢查用戶是否已存在
    cursor.execute("SELECT id FROM users WHERE email = ?", (request.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="User already exists")
    
    # 創建新用戶
    hashed_password = get_password_hash(request.password)
    full_name = f"{request.first_name or ''} {request.last_name or ''}".strip()
    
    cursor.execute(
        "INSERT INTO users (email, hashed_password, full_name) VALUES (?, ?, ?)",
        (request.email, hashed_password, full_name)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # 創建訪問令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_id)}, 
        expires_delta=access_token_expires
    )
    
    return {
        "success": True,
        "data": {
            "user": {
                "id": user_id,
                "email": request.email,
                "full_name": full_name,
            },
            "access_token": access_token,
            "token_type": "bearer",
        }
    }

@app.post("/api/v1/auth/login")
async def login(request: UserLogin):
    """用戶登入"""
    logger.info(f"Login attempt: {request.email}")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, hashed_password, full_name FROM users WHERE email = ?", (request.email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not verify_password(request.password, user[1]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # 創建訪問令牌
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user[0])}, 
        expires_delta=access_token_expires
    )
    
    return {
        "success": True,
        "data": {
            "user": {
                "id": user[0],
                "email": request.email,
                "full_name": user[2],
            },
            "access_token": access_token,
            "token_type": "bearer",
        }
    }

@app.get("/api/v1/auth/verify")
async def verify_token(user_id: int = Depends(get_current_user)):
    """驗證令牌"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT email, full_name FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "success": True,
        "data": {
            "user": {
                "id": user_id,
                "email": user[0],
                "full_name": user[1],
            }
        }
    }

# 影片管理端點
@app.get("/api/v1/videos")
async def list_videos(user_id: int = Depends(get_current_user)):
    """獲取用戶影片列表"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, title, description, topic, status, progress_percentage, created_at, video_url FROM videos WHERE user_id = ?",
        (user_id,)
    )
    videos = cursor.fetchall()
    conn.close()
    
    video_list = []
    for video in videos:
        video_list.append({
            "id": video[0],
            "title": video[1],
            "description": video[2], 
            "topic": video[3],
            "status": video[4],
            "progress_percentage": video[5],
            "created_at": video[6],
            "video_url": video[7],
        })
    
    return {
        "success": True,
        "data": {
            "videos": video_list,
            "total": len(video_list),
        }
    }

@app.post("/api/v1/videos")
async def create_video(
    request: VideoCreate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user)
):
    """創建新影片"""
    logger.info(f"Creating video: {request.title} for user {user_id}")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO videos (user_id, title, description, topic, status) VALUES (?, ?, ?, ?, ?)",
        (user_id, request.title, request.description, request.topic, "pending")
    )
    video_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # 在背景任務中處理影片生成
    background_tasks.add_task(process_video_generation, video_id, request)
    
    return {
        "success": True,
        "data": {
            "id": video_id,
            "title": request.title,
            "status": "pending",
            "message": "Video generation started"
        }
    }

# AI服務代理端點
@app.post("/api/v1/ai/generate-script")
async def generate_script_proxy(request: dict):
    """代理AI腳本生成請求"""
    topic = request.get("topic", "未指定主題")
    platform = request.get("platform", "tiktok")
    style = request.get("style", "educational")
    
    logger.info(f"Script generation request: {topic}")
    
    # 如果有AI服務在運行，代理請求
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8005/api/v1/generate/script",
                json=request,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
    except Exception as e:
        logger.warning(f"AI service unavailable, using fallback: {e}")
    
    # 回退到簡單模板
    fallback_script = f"""
【{topic}】短影片腳本

🎬 開場 (0-3秒)
大家好！今天我們來聊聊{topic}！

📖 主要內容 (3-12秒)
{topic}其實很有趣，讓我來告訴你幾個重要的點：

第一，{topic}在日常生活中很常見
第二，了解{topic}對我們很有幫助
第三，{topic}有很多實用的應用

💡 結尾 (12-15秒)
希望這個分享對你有幫助！記得點讚訂閱！

#適合{platform}平台#{style}風格#
    """
    
    return {
        "success": True,
        "data": {
            "script": fallback_script.strip(),
            "word_count": len(fallback_script),
            "estimated_duration_seconds": 15,
            "platform": platform,
            "style": style,
            "generated_at": datetime.utcnow().isoformat(),
            "generation_source": "fallback_template"
        }
    }

@app.post("/api/v1/ai/generate-image")
async def generate_image_proxy(request: dict):
    """代理AI圖片生成請求"""
    prompt = request.get("prompt", "beautiful image")
    
    logger.info(f"Image generation request: {prompt}")
    
    # 嘗試代理到AI服務
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8005/api/v1/generate/image",
                json=request,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
    except Exception as e:
        logger.warning(f"AI service unavailable, using fallback: {e}")
    
    # 回退到placeholder圖片
    seed = abs(hash(prompt)) % 1000
    resolution = request.get("resolution", "1080x1920")
    width, height = resolution.split("x")
    
    return {
        "success": True,
        "data": {
            "images": [{
                "url": f"https://picsum.photos/{width}/{height}?random={seed}",
                "prompt": prompt,
                "resolution": resolution,
            }],
            "generation_source": "placeholder"
        }
    }

@app.post("/api/v1/ai/generate-voice")
async def generate_voice_proxy(request: dict):
    """代理AI語音合成請求"""
    text = request.get("text", "")
    
    logger.info(f"Voice generation request: {text[:50]}...")
    
    # 嘗試代理到AI服務
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8005/api/v1/generate/voice",
                json=request,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
    except Exception as e:
        logger.warning(f"AI service unavailable, using fallback: {e}")
    
    # 回退響應
    char_count = len(text)
    estimated_duration = round((char_count / 200) * 60, 1)
    
    return {
        "success": True,
        "data": {
            "audio_url": "#",
            "text": text,
            "duration_seconds": estimated_duration,
            "character_count": char_count,
            "generated_at": datetime.utcnow().isoformat(),
            "generation_source": "placeholder"
        }
    }

# 分析端點
@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_analytics(user_id: int = Depends(get_current_user)):
    """獲取儀表板分析數據"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM videos WHERE user_id = ?", (user_id,))
    total_videos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM videos WHERE user_id = ? AND status = 'completed'", (user_id,))
    completed_videos = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "success": True,
        "data": {
            "totalVideos": total_videos,
            "completedVideos": completed_videos,
            "totalViews": total_videos * 127,  # 假設平均觀看數
            "totalLikes": total_videos * 23,   # 假設平均點讚數  
        }
    }

# 背景任務
async def process_video_generation(video_id: int, request: VideoCreate):
    """背景處理影片生成"""
    try:
        logger.info(f"Processing video generation for video {video_id}")
        
        # 模擬影片生成過程
        await asyncio.sleep(2)  # 模擬處理時間
        
        # 更新資料庫狀態
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE videos SET status = ?, progress_percentage = ? WHERE id = ?",
            ("completed", 100.0, video_id)
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Video {video_id} generation completed")
        
    except Exception as e:
        logger.error(f"Video generation failed for {video_id}: {e}")
        
        # 更新失敗狀態
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE videos SET status = ? WHERE id = ?", ("failed", video_id))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    print("🚀 Starting Simple API Gateway...")
    print("📋 Features:")
    print("   - User authentication (SQLite)")
    print("   - Video management")
    print("   - AI service proxy")
    print("   - Analytics dashboard")
    print(f"   - Docs: http://localhost:8000/docs")
    print(f"   - Health: http://localhost:8000/health")
    
    print("\n🔑 AI Service Status:")
    print(f"   - OpenAI: {'✅' if OPENAI_API_KEY and len(OPENAI_API_KEY) > 10 else '❌'}")
    print(f"   - DeepSeek: {'✅' if DEEPSEEK_API_KEY and len(DEEPSEEK_API_KEY) > 10 else '❌'}")
    
    if not any([
        OPENAI_API_KEY and len(OPENAI_API_KEY) > 10,
        DEEPSEEK_API_KEY and len(DEEPSEEK_API_KEY) > 10
    ]):
        print("\n⚠️  Note: No AI API keys configured. Using fallback responses.")
        print("   Set API keys in .env.local to enable full AI features")
    
    print("\n📊 Database: SQLite (auto_video_simple.db)")
    
    uvicorn.run(
        "api_gateway_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )