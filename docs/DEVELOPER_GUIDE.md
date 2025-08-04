# 開發者指南

## 微服務開發流程

### 服務創建步驟
1. 在 `src/services/` 下創建新服務目錄
2. 遵循標準結構：
   ```
   service_name/
   ├── __init__.py
   ├── main.py       # 服務主邏輯
   ├── models.py     # 資料模型
   ├── schemas.py    # Pydantic 模式
   ├── crud.py       # 數據操作
   └── tests/        # 服務特定測試
   ```

### 依賴管理
- 使用 Poetry 管理依賴
- 每個服務的特定依賴在 `pyproject.toml` 中定義
- 定期執行 `poetry update` 更新依賴

### 開發最佳實踐
- 所有 API 使用 FastAPI
- 使用型別提示
- 寫詳細的文檔字串
- 100% 測試覆蓋率

## 微服務間通信

### 通信協議
- 內部服務使用 gRPC
- 外部 API 使用 RESTful
- 消息隊列：Celery + Redis

### 範例通信代碼
```python
from services.auth_service.client import AuthClient
from services.voice_service.client import VoiceClient

def process_voice_request(user_id, voice_data):
    # 驗證用戶
    auth_client = AuthClient()
    if not auth_client.validate_user(user_id):
        raise AuthenticationError()
    
    # 語音處理
    voice_client = VoiceClient()
    processed_voice = voice_client.process(voice_data)
    return processed_voice
```

## 安全開發指南

### 身份驗證
- 使用 JWT
- 實作角色權限控制
- 啟用 HTTPS
- 定期輪換密鑰

### 安全配置
- 使用環境變數
- 不在代碼中存儲敏感資訊
- 使用 Vault 管理機密

## 本地開發環境

### 推薦工具
- VSCode
- Poetry
- Docker
- Pre-commit hooks

### 本地開發流程
```bash
# 克隆專案
git clone [repository_url]

# 安裝開發依賴
poetry install --dev

# 啟動開發服務
poetry run uvicorn src.main:app --reload

# 運行測試
poetry run pytest
```

## 持續整合

### GitHub Actions
- 自動測試
- 代碼風格檢查
- 安全掃描
- 建置 Docker 鏡像

### 代碼審查流程
1. 提交 Pull Request
2. 自動測試
3. 代碼審查
4. 團隊批准
5. 合併到主分支

## 效能監控

### 追蹤工具
- OpenTelemetry
- Prometheus
- Grafana

### 性能分析
```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("voice_processing")
def process_voice(audio_data):
    # 處理邏輯
    pass
```

## 常見問題與故障排除

### 微服務通信
- 檢查 gRPC 配置
- 驗證服務發現
- 確認網路設定

### 資料庫連接
- 檢查連接字串
- 驗證權限
- 監控連接池

## 貢獻指南

### 程式碼風格
- 遵循 PEP 8
- Black 代碼格式化
- Flake8 靜態分析
- Mypy 型別檢查

### 提交流程
1. Fork 倉庫
2. 建立功能分支
3. 提交變更
4. 通過所有檢查
5. 提交 Pull Request