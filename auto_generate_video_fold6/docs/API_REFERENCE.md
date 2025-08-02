# API 參考文檔

## 概述

Auto Video Generation System 提供 RESTful API 接口，支援影片生成、管理和分析功能。

## 認證

所有 API 請求都需要在 Header 中包含 JWT 令牌：

```
Authorization: Bearer <your-jwt-token>
```

## 基礎 URL

- 開發環境: `http://localhost:8000`
- 生產環境: `https://api.video-system.com`

## 通用響應格式

### 成功響應
```json
{
  "success": true,
  "data": {},
  "message": "操作成功"
}
```

### 錯誤響應
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "錯誤描述"
  }
}
```

## 用戶認證 API

### 註冊用戶
```
POST /auth/register
```

**請求體:**
```json
{
  "username": "user@example.com",
  "password": "password123",
  "email": "user@example.com"
}
```

**響應:**
```json
{
  "success": true,
  "data": {
    "user_id": "123",
    "username": "user@example.com",
    "email": "user@example.com"
  }
}
```

### 用戶登入
```
POST /auth/login
```

**請求體:**
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**響應:**
```json
{
  "success": true,
  "data": {
    "access_token": "jwt-token-here",
    "refresh_token": "refresh-token-here",
    "expires_in": 3600
  }
}
```

## 影片生成 API

### 創建影片生成任務
```
POST /video/generate
```

**請求體:**
```json
{
  "title": "影片標題",
  "description": "影片描述",
  "template": "template_id",
  "settings": {
    "duration": 60,
    "resolution": "1080p",
    "format": "mp4"
  }
}
```

**響應:**
```json
{
  "success": true,
  "data": {
    "task_id": "task_123",
    "status": "pending",
    "estimated_time": 300
  }
}
```

### 獲取任務狀態
```
GET /video/task/{task_id}
```

**響應:**
```json
{
  "success": true,
  "data": {
    "task_id": "task_123",
    "status": "completed",
    "progress": 100,
    "video_url": "https://example.com/video.mp4"
  }
}
```

## AI 服務 API

### 獲取可用模型
```
GET /ai/models
```

**響應:**
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "id": "model_1",
        "name": "GPT-4",
        "type": "text_generation",
        "status": "available"
      }
    ]
  }
}
```

### 執行 AI 推理
```
POST /ai/inference
```

**請求體:**
```json
{
  "model_id": "model_1",
  "input": {
    "text": "生成影片腳本",
    "parameters": {
      "max_length": 1000,
      "temperature": 0.7
    }
  }
}
```

## 趨勢分析 API

### 獲取熱門趨勢
```
GET /trends/hot
```

**查詢參數:**
- `platform`: 平台 (youtube, tiktok, instagram)
- `category`: 分類
- `time_range`: 時間範圍 (1d, 7d, 30d)

**響應:**
```json
{
  "success": true,
  "data": {
    "trends": [
      {
        "keyword": "熱門關鍵詞",
        "volume": 10000,
        "growth": 15.5,
        "platform": "youtube"
      }
    ]
  }
}
```

## 社群媒體 API

### 發布內容
```
POST /social/publish
```

**請求體:**
```json
{
  "platform": "youtube",
  "content": {
    "title": "影片標題",
    "description": "影片描述",
    "tags": ["標籤1", "標籤2"],
    "video_url": "https://example.com/video.mp4"
  }
}
```

## 錯誤代碼

| 代碼 | 描述 |
|------|------|
| 400 | 請求參數錯誤 |
| 401 | 未授權 |
| 403 | 權限不足 |
| 404 | 資源不存在 |
| 429 | 請求過於頻繁 |
| 500 | 服務器內部錯誤 |

## 速率限制

- 免費用戶: 100 請求/小時
- 付費用戶: 1000 請求/小時
- API 密鑰用戶: 10000 請求/小時

## SDK 和工具

### Python SDK
```python
from video_system import VideoSystemClient

client = VideoSystemClient(api_key="your-api-key")
result = client.generate_video(title="影片標題")
```

### JavaScript SDK
```javascript
import { VideoSystemClient } from 'video-system-sdk';

const client = new VideoSystemClient('your-api-key');
const result = await client.generateVideo({ title: '影片標題' });
```