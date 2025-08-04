# GraphQL Gateway API 文檔

## 概述

GraphQL API 閘道器，統一數據查詢接口

**基礎 URL**: `http://localhost:8012`  
**API 版本**: v1  
**認證方式**: JWT Bearer Token

## 認證

大多數 API 端點需要有效的 JWT token。在請求頭中包含：

```
Authorization: Bearer <your_jwt_token>
```

## 端點列表

### 健康檢查

#### GET /health
檢查服務健康狀態

**響應**:
```json
{"status": "healthy", "service": "graphql-gateway", "version": "1.0.0"}
```

### 指標端點

#### GET /metrics
獲取 Prometheus 格式的服務指標

**響應**: Prometheus 指標格式

---

## 主要 API 端點


### POST /graphql

**描述**: [端點描述]

**請求參數**: 
```json
// TODO: 添加請求參數
```

**響應**: 
```json
// TODO: 添加響應示例
```


### POST /graphql/playground

**描述**: [端點描述]

**請求參數**: 
```json
// TODO: 添加請求參數
```

**響應**: 
```json
// TODO: 添加響應示例
```


## 錯誤處理

### 標準錯誤響應格式

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "Additional error details"
    }
  },
  "request_id": "uuid-string"
}
```

### HTTP 狀態碼

- `200` - 成功
- `201` - 創建成功  
- `400` - 請求錯誤
- `401` - 未認證
- `403` - 無權限
- `404` - 資源不存在
- `422` - 驗證錯誤
- `500` - 服務器內部錯誤

## 數據模式

### 常用模式

// TODO: 添加數據模式定義

## 示例請求

### cURL 示例

```bash
# 健康檢查
curl -X GET "http://localhost:8012/health"

# 認證請求示例
curl -X POST "http://localhost:8012/api/v1/endpoint" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'
```

### Python 示例

```python
import requests

# 配置
BASE_URL = "http://localhost:8012"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 健康檢查
response = requests.get(f"{BASE_URL}/health")
print(response.json())

# API 調用示例
data = {"key": "value"}
response = requests.post(
    f"{BASE_URL}/api/v1/endpoint",
    headers=headers,
    json=data
)
print(response.json())
```

## 限制

- **請求頻率**: 1000 requests/minute per IP
- **請求大小**: 最大 10MB
- **超時時間**: 30 seconds
- **並發連接**: 100 per IP

## 變更日誌

### v1.0.0 (2025-01-01)
- 初始 API 版本
- 基礎 CRUD 操作
- 認證和授權支持

---

**生成時間**: 2025-08-04  
**API 版本**: 1.0.0
