#!/usr/bin/env python3
"""
臨時 API Gateway - 用於測試前端連接
"""

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import bcrypt
import jwt
import json
from datetime import datetime, timedelta

# 創建 FastAPI 應用
app = FastAPI(
    title="Temp Auto Video API Gateway",
    version="1.0.0",
    description="臨時 API Gateway 用於測試前端連接"
)

# CORS 設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT 設定
JWT_SECRET = "temp_secret_key_for_testing"
JWT_ALGORITHM = "HS256"

# 請求模型
class UserRegister(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    subscribe_newsletter: Optional[bool] = False

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# 模擬資料庫 (僅用於測試)
users_db = {}

def hash_password(password: str) -> str:
    """雜湊密碼"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """驗證密碼"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(user_data: dict) -> str:
    """創建 JWT token"""
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {
        "sub": user_data["email"],
        "user_id": user_data["id"],
        "exp": expire
    }
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy", "service": "temp-api-gateway", "version": "1.0.0"}

@app.post("/api/v1/auth/register")
async def register(user_data: UserRegister):
    """用戶註冊"""
    try:
        # 檢查用戶是否已存在
        if user_data.email in users_db:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"success": False, "error": "User already exists"}
            )
        
        # 創建用戶
        user_id = len(users_db) + 1
        hashed_password = hash_password(user_data.password)
        
        user = {
            "id": user_id,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "email": user_data.email,
            "password": hashed_password,
            "subscribe_newsletter": user_data.subscribe_newsletter,
            "created_at": datetime.utcnow().isoformat()
        }
        
        users_db[user_data.email] = user
        
        # 創建 JWT token
        access_token = create_access_token(user)
        
        # 返回成功響應
        return {
            "success": True,
            "data": {
                "user": {
                    "id": user["id"],
                    "first_name": user["first_name"],
                    "last_name": user["last_name"],
                    "email": user["email"],
                    "subscribe_newsletter": user["subscribe_newsletter"]
                },
                "access_token": access_token
            },
            "message": "User registered successfully"
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "error": f"Registration failed: {str(e)}"}
        )

@app.post("/api/v1/auth/login")
async def login(login_data: UserLogin):
    """用戶登入"""
    try:
        # 檢查用戶是否存在
        user = users_db.get(login_data.email)
        if not user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"success": False, "error": "Invalid credentials"}
            )
        
        # 驗證密碼
        if not verify_password(login_data.password, user["password"]):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"success": False, "error": "Invalid credentials"}
            )
        
        # 創建 JWT token
        access_token = create_access_token(user)
        
        # 返回成功響應
        return {
            "success": True,
            "data": {
                "user": {
                    "id": user["id"],
                    "first_name": user["first_name"],
                    "last_name": user["last_name"],
                    "email": user["email"],
                    "subscribe_newsletter": user["subscribe_newsletter"]
                },
                "access_token": access_token
            },
            "message": "Login successful"
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"success": False, "error": f"Login failed: {str(e)}"}
        )

@app.get("/api/v1/auth/verify")
async def verify_token():
    """驗證 token"""
    return {"success": True, "data": {"valid": True}}

@app.get("/")
async def root():
    """根路徑"""
    return {
        "message": "Temp Auto Video API Gateway",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "register": "/api/v1/auth/register",
            "login": "/api/v1/auth/login",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    print("🚀 啟動臨時 API Gateway...")
    print("📍 地址: http://localhost:8000")
    print("📚 API 文檔: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )