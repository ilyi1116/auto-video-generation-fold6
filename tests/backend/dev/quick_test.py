#!/usr/bin/env python3
"""
快速系統測試
Quick System Test
"""

import requests
import json
import sys

def test_backend():
    """測試後端API"""
    print("🔍 測試後端服務...")
    
    base_url = "http://localhost:8001"
    
    # 1. 健康檢查
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 健康檢查通過")
        else:
            print("❌ 健康檢查失敗")
            return False
    except requests.RequestException as e:
        print(f"❌ 無法連接到後端服務: {e}")
        return False
    
    # 2. 測試登入API
    try:
        login_data = {
            "email": "demo@example.com",
            "password": "demo123"
        }
        response = requests.post(f"{base_url}/api/v1/auth/login", 
                               json=login_data, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("✅ 登入API測試通過")
                return True
            else:
                print("❌ 登入API回應格式錯誤")
        else:
            print(f"❌ 登入API測試失敗: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ 登入API測試錯誤: {e}")
    
    return False

def test_frontend():
    """測試前端服務"""
    print("🌐 測試前端服務...")
    
    frontend_url = "http://localhost:5173"
    
    try:
        response = requests.get(frontend_url, timeout=5)
        if response.status_code == 200:
            if "AutoVideo" in response.text or "vite" in response.text.lower():
                print("✅ 前端服務正常運行")
                return True
            else:
                print("⚠️  前端服務運行但內容異常")
        else:
            print(f"❌ 前端服務回應異常: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ 無法連接到前端服務: {e}")
        print("💡 請確保前端服務正在運行: npm run dev")
    
    return False

if __name__ == "__main__":
    print("🚀 開始系統快速測試...")
    print()
    
    backend_ok = test_backend()
    print()
    frontend_ok = test_frontend()
    print()
    
    if backend_ok:
        print("🎉 後端測試完全通過！")
        print("📋 可用的API端點:")
        print("   - 健康檢查: http://localhost:8001/health")
        print("   - API文檔: http://localhost:8001/docs")
        print("   - 登入: POST http://localhost:8001/api/v1/auth/login")
        print("   - 影片列表: GET http://localhost:8001/api/v1/videos")
        print()
        
        if frontend_ok:
            print("🌟 前後端整合測試完全成功！")
            print("🎯 系統已準備就緒，可以開始使用")
            print()
            print("📱 訪問前端: http://localhost:5173")
            print("🔧 API文檔: http://localhost:8001/docs") 
            print("👤 測試帳號: demo@example.com / demo123")
        else:
            print("⚠️  後端正常，但前端可能需要啟動")
            print("💡 請運行: npm run dev")
    else:
        print("❌ 後端服務異常，請檢查")
        print("💡 請運行: python3 src/services/api-gateway/mock_server.py")
    
    sys.exit(0 if (backend_ok and frontend_ok) else 1)