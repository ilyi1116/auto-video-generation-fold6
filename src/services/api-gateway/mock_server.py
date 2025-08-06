#!/usr/bin/env python3
"""
模擬後端服務用於前端測試
Mock backend service for frontend testing
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

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
    return JSONResponse(
        status_code=200, content={"success": True, "data": mock_analytics}
    )


# AI服務端點
@app.post("/api/v1/ai/generate-script")
async def generate_script(request: Request):
    """模擬AI腳本生成端點"""
    body = await request.json()
    topic = body.get("topic", "未指定主題")

    # 模擬AI生成的腳本
    mock_script = f"""
歡迎來到{topic}的精彩世界！

在今天的內容中，我們將探索{topic}的各個面向，
為您帶來最新的資訊和深入的見解。

無論您是初學者還是專家，這個內容都將為您提供
有價值的知識和實用的建議。

讓我們一起開始這段學習之旅吧！

記得訂閱我們的頻道，
獲取更多{topic}相關的精彩內容。

感謝您的觀看，我們下次見！
"""

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "script": mock_script.strip(),
                "word_count": len(mock_script.split()),
                "estimated_duration": "45-60 seconds",
                "tone": "friendly",
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        },
    )


@app.post("/api/v1/ai/generate-image")
async def generate_image(request: Request):
    """模擬AI圖像生成端點"""
    body = await request.json()
    prompt = body.get("prompt", "beautiful landscape")

    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "image_url": f"https://picsum.photos/800/600?random={int(time.time())}",
                "prompt": prompt,
                "style": "realistic",
                "resolution": "800x600",
                "generated_at": datetime.utcnow().isoformat() + "Z",
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
    print("   - Health: http://localhost:8000/health")
    print("   - Docs: http://localhost:8000/docs")
    print("   - Login: POST http://localhost:8000/api/v1/auth/login")
    print("   - Register: POST http://localhost:8000/api/v1/auth/register")
    print("   - Videos: GET http://localhost:8000/api/v1/videos")
    print(
        "   - Analytics: GET http://localhost:8000/api/v1/analytics/dashboard"
    )
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
