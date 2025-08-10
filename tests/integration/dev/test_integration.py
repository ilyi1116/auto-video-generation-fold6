#!/usr/bin/env python3
"""
整合測試腳本
測試前後端整合功能
"""

import asyncio
import httpx
import json
import sys
from pathlib import Path
import os

# 添加專案根目錄到路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.shared.database.init_data import init_database

# API配置
API_BASE_URL = "http://localhost:8000"
API_TIMEOUT = 30.0

class APITester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=API_TIMEOUT)
        self.token = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def test_health_check(self):
        """測試健康檢查端點"""
        print("🏥 Testing health check...")
        try:
            response = await self.client.get(f"{API_BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            print(f"✅ Health check passed: {data.get('status', 'unknown')}")
            return True
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def test_login(self):
        """測試用戶登入"""
        print("🔐 Testing user login...")
        try:
            login_data = {
                "email": "test1@example.com",
                "password": "password123"
            }
            response = await self.client.post(f"{API_BASE_URL}/api/v1/auth/login", json=login_data)
            
            if response.status_code != 200:
                print(f"❌ Login failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            if data.get("success"):
                self.token = data["data"]["access_token"]
                print(f"✅ Login successful")
                return True
            else:
                print(f"❌ Login failed: {data.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    async def test_script_generation(self):
        """測試腳本生成"""
        print("📝 Testing script generation...")
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            script_data = {
                "topic": "AI技術的未來發展",
                "platform": "youtube",
                "style": "educational",
                "duration": 60,
                "language": "zh-TW"
            }
            response = await self.client.post(
                f"{API_BASE_URL}/api/v1/ai/generate-script", 
                json=script_data,
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"❌ Script generation failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            if data.get("success"):
                script_content = data["data"].get("script", data["data"].get("content", ""))
                print(f"✅ Script generated successfully ({len(script_content)} characters)")
                if len(script_content) > 0:
                    print(f"Preview: {script_content[:100]}...")
                return True
            else:
                print(f"❌ Script generation failed: {data.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Script generation failed: {e}")
            return False
    
    async def test_image_generation(self):
        """測試圖像生成"""
        print("🎨 Testing image generation...")
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            image_data = {
                "prompt": "未來科技城市景觀",
                "style": "realistic",
                "size": "1024x1024"
            }
            response = await self.client.post(
                f"{API_BASE_URL}/api/v1/ai/generate-image", 
                json=image_data,
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"❌ Image generation failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            if data.get("success"):
                image_url = data["data"].get("url", "")
                print(f"✅ Image generated successfully")
                if image_url:
                    print(f"Image URL: {image_url}")
                return True
            else:
                print(f"❌ Image generation failed: {data.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Image generation failed: {e}")
            return False
    
    async def test_voice_synthesis(self):
        """測試語音合成"""
        print("🎤 Testing voice synthesis...")
        if not self.token:
            print("❌ No authentication token available")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            voice_data = {
                "text": "這是一個測試語音合成的例子。人工智能技術正在快速發展。",
                "voice": "alloy",
                "speed": 1.0
            }
            response = await self.client.post(
                f"{API_BASE_URL}/api/v1/ai/generate-voice", 
                json=voice_data,
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"❌ Voice synthesis failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return False
            
            data = response.json()
            if data.get("success"):
                audio_url = data["data"].get("url", "")
                print(f"✅ Voice synthesis successful")
                if audio_url:
                    print(f"Audio URL: {audio_url}")
                return True
            else:
                print(f"❌ Voice synthesis failed: {data.get('error', 'Unknown error')}")
                return False
        except Exception as e:
            print(f"❌ Voice synthesis failed: {e}")
            return False
    
    async def run_all_tests(self):
        """運行所有測試"""
        print("🚀 Starting integration tests...\n")
        
        tests = [
            ("Health Check", self.test_health_check),
            ("User Login", self.test_login),
            ("Script Generation", self.test_script_generation),
            ("Image Generation", self.test_image_generation),
            ("Voice Synthesis", self.test_voice_synthesis),
        ]
        
        results = {}
        for test_name, test_func in tests:
            print(f"\n--- {test_name} ---")
            try:
                results[test_name] = await test_func()
            except Exception as e:
                print(f"❌ {test_name} crashed: {e}")
                results[test_name] = False
        
        # 總結報告
        print("\n" + "="*50)
        print("📊 TEST RESULTS SUMMARY")
        print("="*50)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<20} {status}")
            if result:
                passed += 1
        
        print("-"*50)
        print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed! System integration is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the API Gateway and services.")
        
        return passed == total

async def main():
    """主要測試函數"""
    print("🔧 Initializing database...")
    try:
        init_database()
        print("✅ Database initialized successfully\n")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("Please make sure the database is accessible and try again.")
        return
    
    print("🌐 Testing API integration...")
    print(f"API Base URL: {API_BASE_URL}")
    print("Make sure the API Gateway is running on port 8000\n")
    
    async with APITester() as tester:
        success = await tester.run_all_tests()
        
        if success:
            print("\n🎯 Next steps:")
            print("1. Start the frontend development server: cd src/frontend && npm run dev")
            print("2. Open http://localhost:5173 in your browser")
            print("3. Try logging in with: test1@example.com / password123")
            print("4. Test the AI script generation and other features")
        else:
            print("\n🔧 Troubleshooting:")
            print("1. Make sure API Gateway is running: python src/services/api-gateway/main.py")
            print("2. Check if AI service is running: python src/services/ai-service/main.py")
            print("3. Check database connection and initialization")
            print("4. Review error messages above for specific issues")

if __name__ == "__main__":
    asyncio.run(main())