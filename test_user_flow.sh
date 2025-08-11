#!/bin/bash

# 測試完整用戶流程
echo "🧪 Testing complete user flow..."

API_BASE="http://localhost:8000/api/v1"
AI_BASE="http://localhost:8005/api/v1"
FRONTEND="http://localhost:5173"

echo "📋 Test Summary:"
echo "  1. User Registration"
echo "  2. User Login" 
echo "  3. AI Script Generation"
echo "  4. Video Creation"
echo "  5. Video Status Check"
echo ""

# 1. 測試用戶註冊
echo "1️⃣ Testing User Registration..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User"
  }')

echo "Registration Response: $REGISTER_RESPONSE" | head -3
echo ""

# 2. 測試用戶登入
echo "2️⃣ Testing User Login..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com", 
    "password": "testpass123"
  }')

echo "Login Response: $LOGIN_RESPONSE" | head -3

# 提取access token
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
echo "Access Token: ${ACCESS_TOKEN:0:20}..."
echo ""

# 3. 測試AI腳本生成
echo "3️⃣ Testing AI Script Generation..."
SCRIPT_RESPONSE=$(curl -s -X POST "$AI_BASE/generate/script" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "如何使用AI生成影片",
    "platform": "tiktok",
    "style": "educational",
    "duration": 15
  }')

echo "Script Generation Response: $SCRIPT_RESPONSE" | head -5
echo ""

# 4. 測試影片創建
echo "4️⃣ Testing Video Creation..."
if [ -n "$ACCESS_TOKEN" ]; then
  VIDEO_RESPONSE=$(curl -s -X POST "$API_BASE/videos" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d '{
      "title": "AI影片生成測試",
      "description": "這是一個測試影片",
      "topic": "AI技術",
      "style": "modern",
      "duration": 15,
      "platform": "tiktok"
    }')
  
  echo "Video Creation Response: $VIDEO_RESPONSE" | head -3
  
  # 提取video ID
  VIDEO_ID=$(echo "$VIDEO_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
  echo "Video ID: $VIDEO_ID"
  echo ""
  
  # 5. 測試影片狀態查詢
  echo "5️⃣ Testing Video Status Check..."
  sleep 2  # 等待處理
  
  VIDEOS_RESPONSE=$(curl -s -X GET "$API_BASE/videos" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  
  echo "Videos List Response: $VIDEOS_RESPONSE" | head -5
else
  echo "❌ No access token available, skipping video tests"
fi

echo ""
echo "📊 Service Status Summary:"
echo "  🌐 Frontend: $FRONTEND"
echo "  🛠️  API Gateway: http://localhost:8000"
echo "  🤖 AI Service: http://localhost:8005"
echo ""
echo "✅ User flow test completed!"
echo ""
echo "🎯 Next Steps:"
echo "  1. Visit $FRONTEND to test the web interface"
echo "  2. Configure real AI API keys in .env.local for full functionality"
echo "  3. Test video generation with actual AI content"