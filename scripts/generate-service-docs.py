#!/usr/bin/env python3
"""
服務文檔標準化生成器
為所有微服務創建統一的 README 和 API 文檔
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import json
import re


class ServiceDocumentationGenerator:
    """服務文檔生成器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.services_dir = self.project_root / "src" / "services"
        self.template_dir = self.project_root / "templates" / "service-docs"
        
        # 服務配置
        self.service_configs = {
            "api-gateway": {
                "name": "API Gateway",
                "description": "統一 API 入口點，處理路由、認證和負載均衡",
                "port": 8000,
                "dependencies": ["auth-service", "data-service", "inference-service"],
                "main_endpoints": ["/api/v1/health", "/api/v1/auth", "/api/v1/proxy"],
                "tech_stack": ["FastAPI", "Uvicorn", "JWT", "Redis"]
            },
            "auth-service": {
                "name": "Authentication Service", 
                "description": "用戶認證、授權和會話管理服務",
                "port": 8001,
                "dependencies": ["database", "redis"],
                "main_endpoints": ["/auth/login", "/auth/register", "/auth/refresh"],
                "tech_stack": ["FastAPI", "SQLAlchemy", "PostgreSQL", "JWT", "Alembic"]
            },
            "data-service": {
                "name": "Data Processing Service",
                "description": "音頻數據處理、驗證和存儲服務", 
                "port": 8002,
                "dependencies": ["storage-service", "celery"],
                "main_endpoints": ["/data/upload", "/data/process", "/data/validate"],
                "tech_stack": ["FastAPI", "Celery", "Redis", "Audio Processing"]
            },
            "inference-service": {
                "name": "Model Inference Service",
                "description": "機器學習模型推論和語音合成服務",
                "port": 8003, 
                "dependencies": ["storage-service", "ai-service"],
                "main_endpoints": ["/inference/synthesize", "/inference/models"],
                "tech_stack": ["FastAPI", "PyTorch", "TensorFlow", "CUDA"]
            },
            "video-service": {
                "name": "Video Generation Service",
                "description": "視頻生成、編輯和處理服務",
                "port": 8004,
                "dependencies": ["ai-service", "storage-service"],
                "main_endpoints": ["/video/generate", "/video/process", "/video/export"],
                "tech_stack": ["FastAPI", "FFmpeg", "OpenCV", "AI Integration"]
            },
            "ai-service": {
                "name": "AI Orchestration Service", 
                "description": "AI 服務編排，整合多個 AI 模型和 API",
                "port": 8005,
                "dependencies": ["gemini-api", "stable-diffusion", "suno-api"],
                "main_endpoints": ["/ai/text", "/ai/image", "/ai/audio", "/ai/orchestrate"],
                "tech_stack": ["FastAPI", "Gemini API", "Stable Diffusion", "Suno API"]
            },
            "social-service": {
                "name": "Social Media Service",
                "description": "社交媒體平台整合和內容發布服務",
                "port": 8006,
                "dependencies": ["storage-service"],
                "main_endpoints": ["/social/publish", "/social/analytics", "/social/platforms"],
                "tech_stack": ["FastAPI", "Platform APIs", "OAuth2"]
            },
            "trend-service": {
                "name": "Trend Analysis Service",
                "description": "趨勢分析、關鍵字挖掘和競爭對手分析服務", 
                "port": 8007,
                "dependencies": ["database", "external-apis"],
                "main_endpoints": ["/trends/analyze", "/trends/keywords", "/trends/competitors"],
                "tech_stack": ["FastAPI", "Data Analytics", "External APIs"]
            },
            "scheduler-service": {
                "name": "Task Scheduler Service",
                "description": "任務調度、工作流程管理和自動化服務",
                "port": 8008,
                "dependencies": ["database", "celery"],
                "main_endpoints": ["/scheduler/jobs", "/scheduler/workflows", "/scheduler/triggers"],
                "tech_stack": ["FastAPI", "Celery", "Cron", "Workflow Engine"]
            },
            "storage-service": {
                "name": "File Storage Service",
                "description": "文件存儲、管理和 CDN 服務",
                "port": 8009,
                "dependencies": ["s3", "database"],
                "main_endpoints": ["/storage/upload", "/storage/download", "/storage/manage"],
                "tech_stack": ["FastAPI", "S3", "CDN", "File Processing"]
            },
            "training-worker": {
                "name": "Model Training Worker",
                "description": "機器學習模型訓練和優化後台服務",
                "port": 8010,
                "dependencies": ["storage-service", "database", "gpu"],
                "main_endpoints": ["/training/start", "/training/status", "/training/models"],
                "tech_stack": ["Python", "PyTorch", "Celery", "GPU Computing"]
            },
            "data-ingestion": {
                "name": "Data Ingestion Service", 
                "description": "數據收集、清理和預處理服務",
                "port": 8011,
                "dependencies": ["storage-service", "database"],
                "main_endpoints": ["/ingest/batch", "/ingest/stream", "/ingest/validate"],
                "tech_stack": ["FastAPI", "Apache Kafka", "Data Pipeline"]
            },
            "graphql-gateway": {
                "name": "GraphQL Gateway",
                "description": "GraphQL API 閘道器，統一數據查詢接口",
                "port": 8012,
                "dependencies": ["api-gateway", "all-services"],
                "main_endpoints": ["/graphql", "/graphql/playground"],
                "tech_stack": ["FastAPI", "GraphQL", "Schema Federation"]
            },
            "voice-enhancement": {
                "name": "Voice Enhancement Service",
                "description": "語音增強、降噪和音質優化服務", 
                "port": 8013,
                "dependencies": ["inference-service"],
                "main_endpoints": ["/voice/enhance", "/voice/denoise", "/voice/clone"],
                "tech_stack": ["FastAPI", "Audio Processing", "Voice Cloning"]
            }
        }
        
    def create_templates_directory(self):
        """創建模板目錄"""
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_readme_template(self) -> str:
        """生成 README 模板"""
        return """# {service_name}

## 📋 服務概述

{description}

## 🚀 快速開始

### 開發環境啟動

```bash
# 1. 安裝依賴
cd src/services/{service_dir}
pip install -e .

# 2. 設置環境變量
cp .env.example .env
# 編輯 .env 文件配置必要參數

# 3. 啟動服務
uvicorn app.main:app --reload --port {port}
```

### Docker 啟動

```bash
# 構建鏡像
docker build -t {service_dir} .

# 運行容器
docker run -p {port}:{port} --env-file .env {service_dir}
```

## 🏗️ 技術架構

### 技術棧
{tech_stack_list}

### 服務依賴
{dependencies_list}

### 端口配置
- **服務端口**: {port}
- **健康檢查**: `GET /health`
- **指標端點**: `GET /metrics` 

## 📚 API 文檔

### 主要端點
{endpoints_list}

### API 文檔訪問
- **Swagger UI**: http://localhost:{port}/docs
- **ReDoc**: http://localhost:{port}/redoc
- **OpenAPI JSON**: http://localhost:{port}/openapi.json

## 🧪 測試

### 運行測試
```bash
# 單元測試
pytest tests/ -v

# 測試覆蓋率
pytest tests/ --cov=app --cov-report=html

# 集成測試
pytest tests/integration/ -v
```

### 測試數據
測試數據位於 `tests/fixtures/` 目錄中。

## 📦 部署

### 環境變量
參考 `.env.example` 文件，主要配置項：

```bash
# 基礎配置
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# 服務配置
SERVICE_PORT={port}
SERVICE_NAME={service_dir}

# 數據庫配置（如適用）
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0

# 安全配置
JWT_SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### 健康檢查
```bash
curl http://localhost:{port}/health
```

預期響應：
```json
{{"status": "healthy", "service": "{service_dir}", "version": "1.0.0"}}
```

## 🔧 開發指南

### 代碼結構
```
{service_dir}/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 應用入口
│   ├── config.py        # 配置管理
│   ├── routers/         # API 路由
│   ├── services/        # 業務邏輯
│   ├── models/          # 數據模型
│   └── schemas/         # Pydantic 模式
├── tests/               # 測試文件
├── Dockerfile          # Docker 配置
└── README.md           # 本文檔
```

### 添加新功能
1. 在 `app/routers/` 中添加新的路由模組
2. 在 `app/services/` 中實現業務邏輯
3. 在 `app/schemas/` 中定義數據模式
4. 在 `tests/` 中添加相應測試
5. 更新 API 文檔

### 代碼規範
- 使用 Black 進行代碼格式化
- 使用 Flake8 進行靜態檢查
- 使用 mypy 進行類型檢查
- 保持測試覆蓋率 > 80%

## 🐛 故障排除

### 常見問題

#### 服務無法啟動
```bash
# 檢查端口是否被占用
lsof -i :{port}

# 檢查環境變量
env | grep -E "(DATABASE|REDIS|JWT)"

# 查看日誌
docker logs {service_dir}
```

#### 依賴服務連接失敗
```bash
# 檢查網絡連接
curl http://dependency-service:port/health

# 檢查 Docker 網絡
docker network ls
docker network inspect myproject_default
```

### 日誌查看
```bash
# 本地開發
tail -f logs/{service_dir}.log

# Docker 環境
docker logs -f {service_dir}

# Kubernetes 環境
kubectl logs -f deployment/{service_dir}
```

## 📈 監控與可觀測性

### 指標
- **健康狀態**: `/health` 端點
- **性能指標**: `/metrics` 端點（Prometheus 格式）
- **自定義指標**: 業務相關指標

### 日誌
- **結構化日誌**: JSON 格式輸出
- **日誌級別**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **追蹤標識**: Request ID 追蹤

### 分佈式追蹤
- **OpenTelemetry**: 分佈式追蹤支持
- **Jaeger**: 追蹤可視化
- **服務映射**: 依賴關係可視化

## 🔗 相關文檔

- [架構設計文檔](../../docs/architecture.md)
- [API 設計規範](../../docs/api-guidelines.md)
- [部署指南](../../docs/deployment.md)
- [監控配置](../../docs/monitoring.md)

## 📞 支持

如有問題或需要支持，請：

1. 查看 [故障排除](#-故障排除) 部分
2. 檢查 [GitHub Issues](https://github.com/yourorg/project/issues)
3. 聯繫開發團隊

---

**版本**: 1.0.0  
**最後更新**: {current_date}  
**維護者**: 開發團隊
"""

    def generate_api_doc_template(self) -> str:
        """生成 API 文檔模板"""
        return """# {service_name} API 文檔

## 概述

{description}

**基礎 URL**: `http://localhost:{port}`  
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
{{"status": "healthy", "service": "{service_dir}", "version": "1.0.0"}}
```

### 指標端點

#### GET /metrics
獲取 Prometheus 格式的服務指標

**響應**: Prometheus 指標格式

---

## 主要 API 端點

{api_endpoints_details}

## 錯誤處理

### 標準錯誤響應格式

```json
{{
  "error": {{
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {{
      "field": "Additional error details"
    }}
  }},
  "request_id": "uuid-string"
}}
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

{data_schemas}

## 示例請求

### cURL 示例

```bash
# 健康檢查
curl -X GET "http://localhost:{port}/health"

# 認證請求示例
curl -X POST "http://localhost:{port}/api/v1/endpoint" \\
  -H "Authorization: Bearer $TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{{"key": "value"}}'
```

### Python 示例

```python
import requests

# 配置
BASE_URL = "http://localhost:{port}"
TOKEN = "your_jwt_token"

headers = {{
    "Authorization": f"Bearer {{TOKEN}}",
    "Content-Type": "application/json"
}}

# 健康檢查
response = requests.get(f"{{BASE_URL}}/health")
print(response.json())

# API 調用示例
data = {{"key": "value"}}
response = requests.post(
    f"{{BASE_URL}}/api/v1/endpoint",
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

**生成時間**: {current_date}  
**API 版本**: 1.0.0
"""

    def analyze_service_structure(self, service_path: Path) -> Dict:
        """分析服務結構"""
        structure = {
            "has_main": False,
            "has_config": False, 
            "has_routers": False,
            "has_tests": False,
            "has_dockerfile": False,
            "routers": [],
            "models": [],
            "endpoints": []
        }
        
        # 檢查主要文件
        main_file = service_path / "app" / "main.py"
        if main_file.exists():
            structure["has_main"] = True
            
        config_file = service_path / "app" / "config.py"  
        if config_file.exists():
            structure["has_config"] = True
            
        dockerfile = service_path / "Dockerfile"
        if dockerfile.exists():
            structure["has_dockerfile"] = True
            
        # 檢查路由器
        routers_dir = service_path / "app" / "routers"
        if routers_dir.exists():
            structure["has_routers"] = True
            for router_file in routers_dir.glob("*.py"):
                if router_file.name != "__init__.py":
                    structure["routers"].append(router_file.stem)
                    
        # 檢查測試
        tests_dir = service_path / "tests" 
        if tests_dir.exists():
            structure["has_tests"] = True
            
        return structure
        
    def generate_service_docs(self, service_name: str, config: Dict):
        """為單個服務生成文檔"""
        service_path = self.services_dir / service_name
        if not service_path.exists():
            print(f"⚠️  服務目錄不存在: {service_name}")
            return False
            
        print(f"📝 生成 {config['name']} 文檔...")
        
        # 分析服務結構
        structure = self.analyze_service_structure(service_path)
        
        # 準備模板變量
        from datetime import datetime
        template_vars = {
            "service_name": config["name"],
            "service_dir": service_name,
            "description": config["description"],
            "port": config["port"],
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "tech_stack_list": "\n".join([f"- **{tech}**" for tech in config["tech_stack"]]),
            "dependencies_list": "\n".join([f"- {dep}" for dep in config["dependencies"]]),
            "endpoints_list": "\n".join([f"- `{endpoint}`" for endpoint in config["main_endpoints"]]),
            "api_endpoints_details": self.generate_endpoints_details(config["main_endpoints"]),
            "data_schemas": "// TODO: 添加數據模式定義"
        }
        
        # 生成 README.md
        readme_content = self.generate_readme_template().format(**template_vars)
        readme_path = service_path / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"   ✅ 已生成: {readme_path.relative_to(self.project_root)}")
        
        # 生成 API.md  
        api_content = self.generate_api_doc_template().format(**template_vars)
        api_path = service_path / "API.md"
        with open(api_path, 'w', encoding='utf-8') as f:
            f.write(api_content)
        print(f"   ✅ 已生成: {api_path.relative_to(self.project_root)}")
        
        return True
        
    def generate_endpoints_details(self, endpoints: List[str]) -> str:
        """生成端點詳細說明"""
        details = []
        for endpoint in endpoints:
            method = "GET" if "/health" in endpoint or "/metrics" in endpoint else "POST"
            details.append(f"""
### {method} {endpoint}

**描述**: [端點描述]

**請求參數**: 
```json
// TODO: 添加請求參數
```

**響應**: 
```json
// TODO: 添加響應示例
```
""")
        return "\n".join(details)
        
    def generate_all_docs(self):
        """為所有服務生成文檔"""
        print("🚀 開始生成服務文檔...")
        print("=" * 60)
        
        generated_count = 0
        total_services = len(self.service_configs)
        
        for service_name, config in self.service_configs.items():
            if self.generate_service_docs(service_name, config):
                generated_count += 1
                
        print("\n" + "=" * 60)
        print(f"📊 文檔生成統計:")
        print(f"   總服務數: {total_services}")
        print(f"   成功生成: {generated_count}")
        print(f"   跳過/錯誤: {total_services - generated_count}")
        
        if generated_count == total_services:
            print("   🎉 所有服務文檔生成完成！")
        else:
            print("   ⚠️  部分服務文檔生成失敗，請檢查服務目錄。")
            
        return generated_count
        
    def create_index_document(self):
        """創建服務索引文檔"""
        print("\n📋 生成服務索引文檔...")
        
        index_content = """# 微服務文檔索引

## 📚 服務列表

本項目包含以下微服務，每個服務都有完整的文檔和 API 說明：

| 服務名稱 | 描述 | 端口 | 文檔 | API |
|---------|------|------|------|-----|
"""
        
        for service_name, config in self.service_configs.items():
            service_path = self.services_dir / service_name
            if service_path.exists():
                readme_link = f"[README](./src/services/{service_name}/README.md)"
                api_link = f"[API 文檔](./src/services/{service_name}/API.md)"
                index_content += f"| {config['name']} | {config['description']} | {config['port']} | {readme_link} | {api_link} |\n"
        
        index_content += """
## 🏗️ 系統架構

```mermaid
graph TB
    Client[客戶端] --> Gateway[API Gateway :8000]
    Gateway --> Auth[Auth Service :8001] 
    Gateway --> Data[Data Service :8002]
    Gateway --> Inference[Inference Service :8003]
    Gateway --> Video[Video Service :8004]
    Gateway --> AI[AI Service :8005]
    Gateway --> Social[Social Service :8006]
    Gateway --> Trend[Trend Service :8007]
    Gateway --> Scheduler[Scheduler Service :8008]
    Gateway --> Storage[Storage Service :8009]
    
    Data --> Storage
    Inference --> Storage
    Video --> AI
    Video --> Storage
    Social --> Storage
    Trend --> Storage
    Scheduler --> Data
    
    Training[Training Worker :8010] --> Storage
    Ingestion[Data Ingestion :8011] --> Data
    GraphQL[GraphQL Gateway :8012] --> Gateway
    Voice[Voice Enhancement :8013] --> Inference
```

## 🚀 快速導航

### 核心服務
- **[API Gateway](./src/services/api-gateway/README.md)** - 統一入口點
- **[Auth Service](./src/services/auth-service/README.md)** - 認證授權
- **[Data Service](./src/services/data-service/README.md)** - 數據處理

### AI & ML 服務  
- **[AI Service](./src/services/ai-service/README.md)** - AI 編排
- **[Inference Service](./src/services/inference-service/README.md)** - 模型推論
- **[Training Worker](./src/services/training-worker/README.md)** - 模型訓練
- **[Voice Enhancement](./src/services/voice-enhancement/README.md)** - 語音增強

### 內容處理服務
- **[Video Service](./src/services/video-service/README.md)** - 視頻生成
- **[Storage Service](./src/services/storage-service/README.md)** - 文件存儲
- **[Social Service](./src/services/social-service/README.md)** - 社交媒體

### 數據分析服務
- **[Trend Service](./src/services/trend-service/README.md)** - 趨勢分析
- **[Data Ingestion](./src/services/data-ingestion/README.md)** - 數據收集

### 基礎設施服務
- **[Scheduler Service](./src/services/scheduler-service/README.md)** - 任務調度
- **[GraphQL Gateway](./src/services/graphql-gateway/README.md)** - GraphQL API

## 📖 開發指南

1. **[架構設計](./docs/architecture.md)** - 系統架構說明
2. **[開發規範](./docs/development.md)** - 代碼規範和最佳實踐  
3. **[部署指南](./docs/deployment.md)** - 部署和運維
4. **[API 規範](./docs/api-guidelines.md)** - API 設計規範

## 🔧 開發工具

- **Docker Compose**: `docker-compose up -d`
- **健康檢查**: `./scripts/health-check.sh`
- **文檔生成**: `python scripts/generate-service-docs.py`
- **測試運行**: `./scripts/run-tests.sh`

---

**生成時間**: {current_date}  
**項目版本**: 1.0.0
""".format(current_date=__import__('datetime').datetime.now().strftime('%Y-%m-%d'))
        
        index_path = self.project_root / "SERVICES.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        print(f"   ✅ 已生成: {index_path.relative_to(self.project_root)}")


def main():
    generator = ServiceDocumentationGenerator()
    
    # 生成所有服務文檔
    generated_count = generator.generate_all_docs()
    
    # 生成索引文檔
    generator.create_index_document()
    
    print(f"\n🎉 服務文檔標準化完成！")
    print(f"共為 {generated_count} 個服務生成了標準化文檔。")
    print(f"\n📋 查看完整服務列表: SERVICES.md")


if __name__ == "__main__":
    main()