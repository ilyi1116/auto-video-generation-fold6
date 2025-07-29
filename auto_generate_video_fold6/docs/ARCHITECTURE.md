# 🏗️ Auto Video 系統架構設計文檔

## 📋 目錄

- [系統概覽](#-系統概覽)
- [架構原則](#-架構原則)
- [技術棧選擇](#-技術棧選擇)
- [微服務架構](#-微服務架構)
- [資料庫設計](#-資料庫設計)
- [API 設計](#-api-設計)
- [安全架構](#-安全架構)
- [效能與擴展性](#-效能與擴展性)
- [監控與可觀察性](#-監控與可觀察性)
- [部署架構](#-部署架構)

## 🎯 系統概覽

Auto Video 是一個現代化的 AI 驅動影片生成平台，採用雲原生微服務架構，提供從內容創作到社群媒體發布的完整解決方案。

### 系統目標

- **高可用性**: 99.9% 系統可用性保證
- **高擴展性**: 支援水平擴展至數十萬用戶
- **高效能**: API 回應時間 < 200ms
- **安全性**: 企業級安全防護
- **易維護性**: 模組化設計，便於開發和維護

### 核心功能域

```mermaid
mindmap
  root((Auto Video))
    用戶管理
      身份認證
      權限控制
      個人檔案
    內容創作
      腳本生成
      語音合成
      視覺生成
      影片組裝
    AI 服務
      文字生成
      圖像生成
      語音克隆
      內容優化
    社群整合
      平台連接
      內容發布
      數據分析
    監控運維
      系統監控
      日誌分析
      告警管理
```

## 🎨 架構原則

### 1. 微服務原則

**單一職責原則**: 每個微服務專注於特定的業務功能
- 認證服務：專門處理用戶認證和授權
- 影片服務：專門處理影片生成和管理
- AI 服務：專門處理 AI 模型調用和管理

**服務自治**: 每個服務獨立開發、部署和擴展
- 獨立的資料庫和資料模型
- 獨立的技術棧選擇
- 獨立的發布週期

**去中心化治理**: 服務團隊擁有完整的技術決策權
- 技術棧選擇自由
- 資料管理自主
- 部署策略獨立

### 2. 雲原生原則

**容器化**: 所有服務均採用 Docker 容器化
```dockerfile
# 多階段構建範例
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
CMD ["python", "main.py"]
```

**無狀態設計**: 服務不保存本地狀態
- 會話資訊存儲在 Redis
- 檔案存儲使用 S3
- 資料庫狀態外部化

**彈性伸縮**: 基於負載自動調整實例數量
- Kubernetes HPA 自動擴展
- 資源使用率監控
- 預測性擴展

### 3. API-First 原則

**契約優先**: API 設計先於實現
- OpenAPI 規範定義
- API 文檔自動生成
- 契約測試驗證

**版本化管理**: 向後相容的 API 演進
- 語義化版本控制
- 多版本並存支援
- 平滑升級策略

**統一介面**: 一致的 API 設計模式
- RESTful 設計風格
- 標準 HTTP 狀態碼
- 統一錯誤處理格式

## 🛠️ 技術棧選擇

### 後端技術棧

```mermaid
graph TB
    subgraph "應用層"
        FastAPI[FastAPI Framework]
        Pydantic[Pydantic Validation]
        SQLAlchemy[SQLAlchemy ORM]
    end
    
    subgraph "服務層"
        Celery[Celery Task Queue]
        Redis[Redis Cache]
        PostgreSQL[PostgreSQL DB]
    end
    
    subgraph "基礎設施層"
        Docker[Docker Container]
        Kubernetes[Kubernetes Orchestration]
        Nginx[Nginx Load Balancer]
    end
    
    FastAPI --> Celery
    FastAPI --> Redis
    FastAPI --> PostgreSQL
    Celery --> Redis
    SQLAlchemy --> PostgreSQL
```

**選擇理由：**

| 技術 | 選擇理由 | 替代方案 |
|------|----------|----------|
| FastAPI | 高效能、自動文檔生成、Type Hints 支援 | Django REST, Flask |
| PostgreSQL | ACID 支援、複雜查詢能力、JSON 支援 | MySQL, MongoDB |
| Redis | 高效能快取、豐富數據結構、持久化選項 | Memcached, Hazelcast |
| Celery | 成熟的分散式任務佇列、監控工具豐富 | RQ, Dramatiq |

### 前端技術棧

```mermaid
graph LR
    subgraph "框架層"
        SvelteKit[SvelteKit]
        TypeScript[TypeScript]
    end
    
    subgraph "樣式層"
        TailwindCSS[Tailwind CSS]
        PostCSS[PostCSS]
    end
    
    subgraph "工具層"
        Vite[Vite Build Tool]
        ESLint[ESLint Linter]
        Prettier[Prettier Formatter]
    end
    
    SvelteKit --> TypeScript
    SvelteKit --> TailwindCSS
    TypeScript --> Vite
    TailwindCSS --> PostCSS
```

**選擇理由：**
- **SvelteKit**: 編譯時優化、小包體積、優秀的開發體驗
- **TypeScript**: 類型安全、IDE 支援、重構友好
- **Tailwind CSS**: 原子化 CSS、設計系統一致性、維護便利

### AI 服務整合

```mermaid
graph TB
    subgraph "文字生成"
        OpenAI[OpenAI GPT]
        Gemini[Google Gemini]
        Claude[Anthropic Claude]
    end
    
    subgraph "圖像生成"
        DALL-E[DALL-E 3]
        Midjourney[Midjourney]
        StableDiffusion[Stable Diffusion]
    end
    
    subgraph "語音合成"
        ElevenLabs[ElevenLabs]
        Azure[Azure Speech]
        AWS[AWS Polly]
    end
    
    AIService[AI Service] --> OpenAI
    AIService --> DALL-E
    AIService --> ElevenLabs
```

## 🔧 微服務架構

### 服務分層架構

```mermaid
graph TB
    subgraph "用戶介面層"
        WebApp[Web Application]
        MobileApp[Mobile App]
        API[Public API]
    end
    
    subgraph "API 閘道器層"
        Gateway[API Gateway]
        Auth[Authentication]
        RateLimit[Rate Limiting]
        LoadBalancer[Load Balancer]
    end
    
    subgraph "業務服務層"
        UserService[User Service]
        VideoService[Video Service]
        AIService[AI Service]
        SocialService[Social Service]
        AnalyticsService[Analytics Service]
    end
    
    subgraph "平台服務層"
        NotificationService[Notification Service]
        FileService[File Service]
        ConfigService[Config Service]
        SchedulerService[Scheduler Service]
    end
    
    subgraph "資料存儲層"
        PostgreSQL[PostgreSQL]
        Redis[Redis]
        ElasticSearch[ElasticSearch]
        S3[Object Storage]
    end
    
    WebApp --> Gateway
    MobileApp --> Gateway
    API --> Gateway
    
    Gateway --> UserService
    Gateway --> VideoService
    Gateway --> AIService
    Gateway --> SocialService
    Gateway --> AnalyticsService
    
    UserService --> PostgreSQL
    VideoService --> PostgreSQL
    VideoService --> S3
    AIService --> Redis
    AnalyticsService --> ElasticSearch
```

### 核心服務詳解

#### 1. API Gateway (Port: 8000)

**職責範圍：**
- 請求路由和轉發
- 身份認證和授權
- 請求限流和熔斷
- 日誌記錄和監控
- API 版本管理

**技術實現：**
```python
# API Gateway 核心路由實現
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import time

app = FastAPI(title="Auto Video API Gateway")

# 服務註冊表
SERVICE_REGISTRY = {
    "auth": "http://auth-service:8001",
    "video": "http://video-service:8004", 
    "ai": "http://ai-service:8005",
    "social": "http://social-service:8006",
    "analytics": "http://analytics-service:8007"
}

@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    start_time = time.time()
    
    # 路由解析
    path_parts = request.url.path.strip("/").split("/")
    if len(path_parts) >= 3 and path_parts[0] == "api" and path_parts[1] == "v1":
        service_name = path_parts[2]
        
        if service_name in SERVICE_REGISTRY:
            # 轉發到對應服務
            target_url = SERVICE_REGISTRY[service_name]
            new_path = "/" + "/".join(path_parts[3:])
            
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=request.method,
                    url=f"{target_url}{new_path}",
                    headers=dict(request.headers),
                    content=await request.body()
                )
                
                # 記錄指標
                process_time = time.time() - start_time
                # 發送到 Prometheus...
                
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
    
    # 如果不是 API 請求，繼續正常處理
    response = await call_next(request)
    return response
```

#### 2. Video Service (Port: 8004)

**職責範圍：**
- 影片創建和管理
- 影片處理狀態追蹤
- 檔案上傳和存儲
- 影片元數據管理

**資料模型：**
```python
# Video Service 資料模型
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()

class VideoStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    script_content = Column(Text)
    status = Column(Enum(VideoStatus), default=VideoStatus.PENDING)
    duration = Column(Integer)  # 秒
    file_url = Column(String)
    thumbnail_url = Column(String)
    platforms = Column(JSON)  # 目標平台列表
    tags = Column(JSON)  # 標籤列表
    processing_progress = Column(Integer, default=0)
    processing_stages = Column(JSON)  # 處理階段詳情
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    published_at = Column(DateTime)
    
    # 性能指標
    statistics = Column(JSON)  # 觀看數、按讚數等
    
    # SEO 優化
    seo_title = Column(String(100))
    seo_description = Column(Text)
    seo_keywords = Column(JSON)
```

**處理流程：**
```mermaid
sequenceDiagram
    participant User
    participant VideoService
    participant AIService
    participant FileStorage
    participant TaskQueue
    
    User->>VideoService: 創建影片請求
    VideoService->>VideoService: 創建影片記錄
    VideoService->>TaskQueue: 提交處理任務
    VideoService-->>User: 返回影片 ID
    
    TaskQueue->>AIService: 生成腳本
    AIService-->>TaskQueue: 腳本內容
    
    TaskQueue->>AIService: 生成語音
    AIService-->>TaskQueue: 語音檔案
    
    TaskQueue->>AIService: 生成視覺內容
    AIService-->>TaskQueue: 圖像/影片素材
    
    TaskQueue->>VideoService: 組裝影片
    VideoService->>FileStorage: 上傳最終影片
    VideoService->>VideoService: 更新狀態為完成
```

#### 3. AI Service (Port: 8005)

**職責範圍：**
- AI 模型調用管理
- 請求隊列和限流
- 結果快取和優化
- 多提供商故障轉移

**提供商抽象層：**
```python
# AI Service 提供商抽象
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import asyncio

class AIProvider(ABC):
    """AI 提供商抽象基類"""
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def generate_image(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def synthesize_speech(self, text: str, **kwargs) -> str:
        pass

class OpenAIProvider(AIProvider):
    """OpenAI 提供商實現"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
    
    async def generate_text(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=kwargs.get("model", "gpt-4"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get("max_tokens", 2000)
        )
        return response.choices[0].message.content
    
    async def generate_image(self, prompt: str, **kwargs) -> str:
        response = await self.client.images.generate(
            model=kwargs.get("model", "dall-e-3"),
            prompt=prompt,
            size=kwargs.get("resolution", "1024x1024"),
            quality=kwargs.get("quality", "standard")
        )
        return response.data[0].url

class AIServiceManager:
    """AI 服務管理器"""
    
    def __init__(self):
        self.providers = {}
        self.fallback_chain = []
        self.cache = {}
    
    def register_provider(self, name: str, provider: AIProvider, priority: int = 0):
        """註冊 AI 提供商"""
        self.providers[name] = {
            "provider": provider,
            "priority": priority,
            "health": True
        }
        self._update_fallback_chain()
    
    def _update_fallback_chain(self):
        """更新故障轉移鏈"""
        self.fallback_chain = sorted(
            self.providers.items(), 
            key=lambda x: x[1]["priority"], 
            reverse=True
        )
    
    async def generate_with_fallback(self, method: str, *args, **kwargs) -> Any:
        """帶故障轉移的生成方法"""
        last_error = None
        
        for provider_name, provider_info in self.fallback_chain:
            if not provider_info["health"]:
                continue
                
            try:
                provider = provider_info["provider"]
                method_func = getattr(provider, method)
                result = await method_func(*args, **kwargs)
                
                # 記錄成功
                self._record_success(provider_name)
                return result
                
            except Exception as e:
                last_error = e
                self._record_failure(provider_name, e)
                continue
        
        # 所有提供商都失敗
        raise Exception(f"All AI providers failed. Last error: {last_error}")
    
    def _record_success(self, provider_name: str):
        """記錄成功調用"""
        self.providers[provider_name]["health"] = True
    
    def _record_failure(self, provider_name: str, error: Exception):
        """記錄失敗調用"""
        # 實現熔斷邏輯
        # 如果失敗率超過閾值，暫時標記為不健康
        pass
```

## 🗄️ 資料庫設計

### 資料庫架構選擇

```mermaid
graph TB
    subgraph "關聯式資料庫"
        UserDB[(User Database)]
        VideoDB[(Video Database)]
        AnalyticsDB[(Analytics Database)]
    end
    
    subgraph "非關聯式資料庫"
        Redis[(Redis Cache)]
        S3[(Object Storage)]
        ES[(ElasticSearch)]
    end
    
    subgraph "分析資料庫"
        ClickHouse[(ClickHouse)]
        TimeSeries[(Time Series DB)]
    end
    
    App[Application Layer] --> UserDB
    App --> VideoDB
    App --> Redis
    App --> S3
    VideoDB --> ES
    Analytics --> ClickHouse
```

### 核心資料模型

#### 用戶領域模型

```sql
-- 用戶基本資訊表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    bio TEXT,
    avatar_url VARCHAR(500),
    website VARCHAR(500),
    location VARCHAR(100),
    email_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE
);

-- 用戶角色表
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID REFERENCES users(id),
    expires_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, role)
);

-- 用戶訂閱表
CREATE TABLE user_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    start_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP WITH TIME ZONE,
    auto_renew BOOLEAN DEFAULT TRUE,
    payment_method JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引優化
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_subscriptions_user_id ON user_subscriptions(user_id);
```

#### 影片領域模型

```sql
-- 影片主表
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    script_content TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    duration INTEGER, -- 秒
    file_url VARCHAR(500),
    file_size BIGINT,
    thumbnail_url VARCHAR(500),
    resolution VARCHAR(20),
    format VARCHAR(10),
    platforms JSONB DEFAULT '[]',
    tags JSONB DEFAULT '[]',
    processing_progress INTEGER DEFAULT 0,
    processing_stages JSONB DEFAULT '{}',
    processing_error TEXT,
    seo_title VARCHAR(100),
    seo_description TEXT,
    seo_keywords JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP WITH TIME ZONE
);

-- 影片統計表
CREATE TABLE video_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    dislikes INTEGER DEFAULT 0,
    shares INTEGER DEFAULT 0,
    comments INTEGER DEFAULT 0,
    watch_time_seconds BIGINT DEFAULT 0,
    engagement_rate DECIMAL(5,2),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(video_id, platform)
);

-- 影片處理歷史表  
CREATE TABLE video_processing_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    stage VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    progress INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB DEFAULT '{}'
);

-- 影片版本表（支援版本管理）
CREATE TABLE video_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    file_size BIGINT,
    changes TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(video_id, version)
);

-- 索引優化
CREATE INDEX idx_videos_user_id ON videos(user_id);
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_created_at ON videos(created_at);
CREATE INDEX idx_videos_published_at ON videos(published_at);
CREATE INDEX idx_videos_tags ON videos USING GIN(tags);
CREATE INDEX idx_video_statistics_video_id ON video_statistics(video_id);
CREATE INDEX idx_video_statistics_platform ON video_statistics(platform);
```

#### AI 服務模型

```sql
-- AI 生成記錄表
CREATE TABLE ai_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- text, image, audio
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100),
    prompt TEXT NOT NULL,
    parameters JSONB DEFAULT '{}',
    result_url VARCHAR(500),
    result_metadata JSONB DEFAULT '{}',
    tokens_used INTEGER,
    cost_usd DECIMAL(10,4),
    processing_time_ms INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- AI 配額管理表
CREATE TABLE ai_quotas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- text, image, audio
    period VARCHAR(20) NOT NULL, -- daily, monthly
    limit_amount INTEGER NOT NULL,
    used_amount INTEGER DEFAULT 0,
    reset_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, type, period)
);

-- 索引
CREATE INDEX idx_ai_generations_user_id ON ai_generations(user_id);
CREATE INDEX idx_ai_generations_type ON ai_generations(type);
CREATE INDEX idx_ai_generations_created_at ON ai_generations(created_at);
CREATE INDEX idx_ai_quotas_user_id ON ai_quotas(user_id);
```

### 資料庫效能優化

#### 1. 查詢優化策略

```sql
-- 複合索引設計
CREATE INDEX idx_videos_user_status_created ON videos(user_id, status, created_at DESC);

-- 部分索引（只索引活躍數據）
CREATE INDEX idx_videos_active ON videos(created_at) WHERE status != 'deleted';

-- 表達式索引
CREATE INDEX idx_videos_title_search ON videos USING gin(to_tsvector('english', title));

-- 覆蓋索引（避免回表查詢）
CREATE INDEX idx_videos_list_cover ON videos(user_id, created_at DESC) 
INCLUDE (title, status, duration, thumbnail_url);
```

#### 2. 分區策略

```sql
-- 按時間分區的影片統計表
CREATE TABLE video_statistics_partitioned (
    id UUID NOT NULL,
    video_id UUID NOT NULL,
    platform VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) PARTITION BY RANGE (date);

-- 創建月度分區
CREATE TABLE video_statistics_2024_01 PARTITION OF video_statistics_partitioned
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE video_statistics_2024_02 PARTITION OF video_statistics_partitioned  
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

#### 3. 讀寫分離

```python
# 資料庫連接管理
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class DatabaseManager:
    def __init__(self):
        # 主庫（讀寫）
        self.master_engine = create_engine(
            "postgresql://user:pass@master-db:5432/autovideo",
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True
        )
        
        # 從庫（只讀）
        self.slave_engines = [
            create_engine(
                "postgresql://user:pass@slave1-db:5432/autovideo",
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            ),
            create_engine(
                "postgresql://user:pass@slave2-db:5432/autovideo", 
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )
        ]
        
        self.master_session = sessionmaker(bind=self.master_engine)
        self.slave_sessions = [
            sessionmaker(bind=engine) for engine in self.slave_engines
        ]
    
    def get_write_session(self):
        """獲取寫會話"""
        return self.master_session()
    
    def get_read_session(self):
        """獲取讀會話（負載均衡）"""
        import random
        session_factory = random.choice(self.slave_sessions)
        return session_factory()
```

## 🔒 安全架構

### 多層安全防護

```mermaid
graph TB
    subgraph "邊界安全"
        WAF[Web Application Firewall]
        DDoS[DDoS Protection]
        CDN[CDN & Rate Limiting]
    end
    
    subgraph "網路安全"
        LB[Load Balancer]
        VPC[Virtual Private Cloud]
        Firewall[Network Firewall]
    end
    
    subgraph "應用安全"
        Auth[Authentication]
        AuthZ[Authorization]
        Encryption[Data Encryption]
        Validation[Input Validation]
    end
    
    subgraph "資料安全"
        DBEncryption[Database Encryption]
        Backup[Encrypted Backup]
        Audit[Audit Logging]
    end
    
    Internet --> WAF
    WAF --> CDN
    CDN --> LB
    LB --> VPC
    VPC --> Auth
    Auth --> DBEncryption
```

### 身份認證與授權

#### JWT Token 架構

```python
# JWT 令牌管理
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext

class JWTManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_tokens(self, user_data: Dict[str, Any]) -> Dict[str, str]:
        """創建訪問令牌和刷新令牌"""
        now = datetime.utcnow()
        
        # 訪問令牌（短期）
        access_payload = {
            "user_id": user_data["id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "roles": user_data.get("roles", ["user"]),
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=15),
            "jti": self._generate_jti()
        }
        
        # 刷新令牌（長期）
        refresh_payload = {
            "user_id": user_data["id"],
            "type": "refresh", 
            "iat": now,
            "exp": now + timedelta(days=30),
            "jti": self._generate_jti()
        }
        
        return {
            "access_token": jwt.encode(access_payload, self.secret_key, self.algorithm),
            "refresh_token": jwt.encode(refresh_payload, self.secret_key, self.algorithm),
            "token_type": "bearer",
            "expires_in": 900  # 15 minutes
        }
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """驗證令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != token_type:
                return None
            
            # 檢查令牌是否在黑名單中
            if self._is_token_blacklisted(payload.get("jti")):
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """刷新訪問令牌"""
        payload = self.verify_token(refresh_token, "refresh")
        if not payload:
            return None
        
        # 從資料庫獲取最新用戶資訊
        user_data = self._get_user_data(payload["user_id"])
        if not user_data or not user_data.get("is_active"):
            return None
        
        return self.create_tokens(user_data)
    
    def _generate_jti(self) -> str:
        """生成令牌 ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _is_token_blacklisted(self, jti: str) -> bool:
        """檢查令牌是否在黑名單中"""
        # 從 Redis 檢查黑名單
        import redis
        r = redis.Redis()
        return r.exists(f"blacklist:{jti}")
    
    def blacklist_token(self, jti: str, expiry: int):
        """將令牌加入黑名單"""
        import redis
        r = redis.Redis()
        r.setex(f"blacklist:{jti}", expiry, "1")
```

#### 基於角色的訪問控制 (RBAC)

```python
# RBAC 權限管理
from enum import Enum
from typing import List, Set
from functools import wraps

class Permission(Enum):
    # 用戶權限
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # 影片權限
    VIDEO_CREATE = "video:create"
    VIDEO_READ = "video:read"
    VIDEO_UPDATE = "video:update"
    VIDEO_DELETE = "video:delete"
    VIDEO_PUBLISH = "video:publish"
    
    # AI 權限
    AI_GENERATE_TEXT = "ai:generate:text"
    AI_GENERATE_IMAGE = "ai:generate:image"
    AI_GENERATE_AUDIO = "ai:generate:audio"
    
    # 管理員權限
    ADMIN_USER_MANAGE = "admin:user:manage"
    ADMIN_SYSTEM_CONFIG = "admin:system:config"
    ADMIN_ANALYTICS_VIEW = "admin:analytics:view"

class Role(Enum):
    GUEST = "guest"
    USER = "user"
    CREATOR = "creator"
    PREMIUM = "premium"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

# 角色權限映射
ROLE_PERMISSIONS = {
    Role.GUEST: set(),
    Role.USER: {
        Permission.USER_READ,
        Permission.VIDEO_READ,
    },
    Role.CREATOR: {
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.VIDEO_CREATE,
        Permission.VIDEO_READ,
        Permission.VIDEO_UPDATE,
        Permission.VIDEO_DELETE,
        Permission.AI_GENERATE_TEXT,
    },
    Role.PREMIUM: {
        # 包含 CREATOR 的所有權限
        *ROLE_PERMISSIONS[Role.CREATOR],
        Permission.AI_GENERATE_IMAGE,
        Permission.AI_GENERATE_AUDIO,
        Permission.VIDEO_PUBLISH,
    },
    Role.ADMIN: {
        # 包含 PREMIUM 的所有權限
        *ROLE_PERMISSIONS[Role.PREMIUM],
        Permission.ADMIN_USER_MANAGE,
        Permission.ADMIN_ANALYTICS_VIEW,
    },
    Role.SUPER_ADMIN: {
        # 所有權限
        *[p for p in Permission],
    }
}

class PermissionChecker:
    """權限檢查器"""
    
    @staticmethod
    def user_has_permission(user_roles: List[Role], required_permission: Permission) -> bool:
        """檢查用戶是否具有指定權限"""
        user_permissions = set()
        for role in user_roles:
            user_permissions.update(ROLE_PERMISSIONS.get(role, set()))
        
        return required_permission in user_permissions
    
    @staticmethod
    def require_permission(permission: Permission):
        """權限裝飾器"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 從請求上下文獲取當前用戶
                current_user = get_current_user()
                
                if not current_user:
                    raise HTTPException(status_code=401, detail="未認證")
                
                user_roles = [Role(role) for role in current_user.get("roles", [])]
                
                if not PermissionChecker.user_has_permission(user_roles, permission):
                    raise HTTPException(status_code=403, detail="權限不足")
                
                return await func(*args, **kwargs)
            return wrapper
        return decorator

# 使用範例
@require_permission(Permission.VIDEO_CREATE)
async def create_video(video_data: VideoCreateRequest):
    """創建影片（需要創建權限）"""
    pass

@require_permission(Permission.ADMIN_USER_MANAGE)
async def manage_users():
    """管理用戶（需要管理員權限）"""
    pass
```

### 資料加密

#### 敏感資料加密

```python
# 資料加密服務
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class EncryptionService:
    """資料加密服務"""
    
    def __init__(self, password: str):
        # 從密碼生成金鑰
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.fernet = Fernet(key)
        self.salt = salt
    
    def encrypt(self, data: str) -> str:
        """加密數據"""
        encrypted_data = self.fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """解密數據"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
        decrypted_data = self.fernet.decrypt(encrypted_bytes)
        return decrypted_data.decode()
    
    def encrypt_sensitive_fields(self, data: dict, sensitive_fields: list) -> dict:
        """加密敏感欄位"""
        encrypted_data = data.copy()
        for field in sensitive_fields:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_data[field] = self.encrypt(str(encrypted_data[field]))
        return encrypted_data
    
    def decrypt_sensitive_fields(self, data: dict, sensitive_fields: list) -> dict:
        """解密敏感欄位"""
        decrypted_data = data.copy()
        for field in sensitive_fields:
            if field in decrypted_data and decrypted_data[field]:
                try:
                    decrypted_data[field] = self.decrypt(decrypted_data[field])
                except Exception:
                    # 如果解密失敗，保持原值（可能是未加密的舊數據）
                    pass
        return decrypted_data

# 在模型中使用加密
class EncryptedUser(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)  # 加密存儲
    phone = Column(String(20))  # 加密存儲
    api_keys = Column(JSON)  # 加密存儲
    
    @property
    def decrypted_email(self):
        """解密後的郵箱"""
        encryption_service = get_encryption_service()
        return encryption_service.decrypt(self.email)
    
    @decrypted_email.setter
    def decrypted_email(self, value):
        """設置加密郵箱"""
        encryption_service = get_encryption_service()
        self.email = encryption_service.encrypt(value)
```

## ⚡ 效能與擴展性

### 系統效能目標

| 指標 | 目標值 | 監控方式 |
|------|---------|----------|
| API 回應時間 | P95 < 200ms | Prometheus + Grafana |
| 資料庫查詢時間 | P95 < 50ms | pg_stat_statements |
| 系統可用性 | 99.9% | 健康檢查 + 告警 |
| 併發用戶數 | 10,000+ | 負載測試 |
| 影片處理時間 | < 5 分鐘 | 處理佇列監控 |

### 快取策略

#### 多層快取架構

```mermaid
graph TB
    subgraph "應用層快取"
        AppCache[Application Cache]
        QueryCache[Query Result Cache]
    end
    
    subgraph "分散式快取"
        Redis[Redis Cluster]
        CDN[CDN Cache]
    end
    
    subgraph "資料庫快取"
        DBCache[Database Buffer Pool]
        QueryPlan[Query Plan Cache]
    end
    
    Client --> CDN
    CDN --> AppCache
    AppCache --> Redis
    Redis --> DBCache
```

#### 快取實現策略

```python
# 智能快取管理
import asyncio
import json
from typing import Any, Optional, Callable
from datetime import datetime, timedelta
import redis.asyncio as redis

class CacheManager:
    """多層快取管理器"""
    
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)
        self.local_cache = {}  # 本地記憶體快取
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "local_hits": 0,
            "redis_hits": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """多層快取獲取"""
        # L1: 本地記憶體快取
        if key in self.local_cache:
            entry = self.local_cache[key]
            if not self._is_expired(entry):
                self.cache_stats["hits"] += 1
                self.cache_stats["local_hits"] += 1
                return entry["value"]
            else:
                del self.local_cache[key]
        
        # L2: Redis 分散式快取
        try:
            redis_value = await self.redis_client.get(key)
            if redis_value:
                value = json.loads(redis_value)
                # 回填到本地快取
                self._set_local_cache(key, value, ttl=300)
                self.cache_stats["hits"] += 1
                self.cache_stats["redis_hits"] += 1
                return value
        except Exception as e:
            print(f"Redis error: {e}")
        
        self.cache_stats["misses"] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """設置多層快取"""
        # 設置本地快取
        self._set_local_cache(key, value, ttl=min(ttl, 300))
        
        # 設置 Redis 快取
        try:
            await self.redis_client.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            print(f"Redis set error: {e}")
    
    def _set_local_cache(self, key: str, value: Any, ttl: int):
        """設置本地快取"""
        self.local_cache[key] = {
            "value": value,
            "expires_at": datetime.now() + timedelta(seconds=ttl)
        }
        
        # 限制本地快取大小
        if len(self.local_cache) > 1000:
            # 移除最舊的條目
            oldest_key = min(self.local_cache.keys(), 
                           key=lambda k: self.local_cache[k]["expires_at"])
            del self.local_cache[oldest_key]
    
    def _is_expired(self, entry: dict) -> bool:
        """檢查快取條目是否過期"""
        return datetime.now() > entry["expires_at"]
    
    async def invalidate_pattern(self, pattern: str):
        """按模式失效快取"""
        # 清理本地快取
        keys_to_remove = [k for k in self.local_cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.local_cache[key]
        
        # 清理 Redis 快取
        try:
            keys = await self.redis_client.keys(f"*{pattern}*")
            if keys:
                await self.redis_client.delete(*keys)
        except Exception as e:
            print(f"Redis invalidate error: {e}")
    
    def get_stats(self) -> dict:
        """獲取快取統計"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.cache_stats,
            "hit_rate": round(hit_rate, 2),
            "local_cache_size": len(self.local_cache)
        }

# 快取裝飾器
def cached(ttl: int = 3600, key_prefix: str = ""):
    """快取裝飾器"""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # 生成快取鍵
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 嘗試從快取獲取
            cache_manager = get_cache_manager()
            cached_result = await cache_manager.get(cache_key)
            
            if cached_result is not None:
                return cached_result
            
            # 執行原函數
            result = await func(*args, **kwargs)
            
            # 儲存到快取
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

# 使用範例
@cached(ttl=1800, key_prefix="video")
async def get_video_details(video_id: str):
    """獲取影片詳情（帶快取）"""
    # 從資料庫查詢...
    pass
```

### 資料庫效能優化

#### 連接池管理

```python
# 資料庫連接池優化
from sqlalchemy.pool import QueuePool
from sqlalchemy import create_engine
import asyncpg

class DatabasePoolManager:
    """資料庫連接池管理器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.pools = {}
        self._create_pools()
    
    def _create_pools(self):
        """創建連接池"""
        # 主庫連接池（讀寫）
        self.pools["master"] = create_engine(
            self.config["master_url"],
            poolclass=QueuePool,
            pool_size=20,  # 常駐連接數
            max_overflow=30,  # 最大溢出連接數
            pool_timeout=30,  # 獲取連接超時
            pool_recycle=3600,  # 連接回收時間
            pool_pre_ping=True,  # 連接前測試
            echo=False
        )
        
        # 從庫連接池（只讀）
        for i, slave_url in enumerate(self.config["slave_urls"]):
            self.pools[f"slave_{i}"] = create_engine(
                slave_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,
                pool_pre_ping=True,
                echo=False
            )
    
    def get_read_engine(self):
        """獲取讀連接（負載均衡）"""
        import random
        slave_pools = [pool for name, pool in self.pools.items() if name.startswith("slave_")]
        return random.choice(slave_pools) if slave_pools else self.pools["master"]
    
    def get_write_engine(self):
        """獲取寫連接"""
        return self.pools["master"]
    
    def get_pool_status(self):
        """獲取連接池狀態"""
        status = {}
        for name, pool in self.pools.items():
            status[name] = {
                "size": pool.pool.size(),
                "checked_in": pool.pool.checkedin(),
                "checked_out": pool.pool.checkedout(),
                "overflow": pool.pool.overflow(),
                "invalid": pool.pool.invalid()
            }
        return status

# 非同步連接池
class AsyncDatabasePool:
    """非同步資料庫連接池"""
    
    def __init__(self, dsn: str, min_size: int = 10, max_size: int = 20):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.pool = None
    
    async def create_pool(self):
        """創建連接池"""
        self.pool = await asyncpg.create_pool(
            self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            command_timeout=30,
            server_settings={
                'application_name': 'autovideo_backend',
                'timezone': 'UTC'
            }
        )
    
    async def execute_query(self, query: str, *args):
        """執行查詢"""
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)
    
    async def execute_transaction(self, queries: list):
        """執行事務"""
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                results = []
                for query, args in queries:
                    result = await connection.fetch(query, *args)
                    results.append(result)
                return results
    
    async def close_pool(self):
        """關閉連接池"""
        if self.pool:
            await self.pool.close()
```

### 非同步處理架構

#### 任務佇列設計

```python
# Celery 任務佇列配置
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
import logging

# Celery 應用配置
celery_app = Celery(
    'autovideo',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0',
    include=[
        'tasks.video_processing',
        'tasks.ai_generation', 
        'tasks.social_publishing',
        'tasks.analytics'
    ]
)

# 配置設定
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # 任務路由
    task_routes={
        'tasks.video_processing.*': {'queue': 'video_queue'},
        'tasks.ai_generation.*': {'queue': 'ai_queue'},
        'tasks.social_publishing.*': {'queue': 'social_queue'},
        'tasks.analytics.*': {'queue': 'analytics_queue'},
    },
    
    # 工作器配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # 結果過期時間
    result_expires=3600,
    
    # 重試配置
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # 監控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# 任務優先級隊列
celery_app.conf.task_routes = {
    'tasks.urgent.*': {
        'queue': 'urgent',
        'routing_key': 'urgent',
        'priority': 10
    },
    'tasks.normal.*': {
        'queue': 'normal', 
        'routing_key': 'normal',
        'priority': 5
    },
    'tasks.low.*': {
        'queue': 'low',
        'routing_key': 'low', 
        'priority': 1
    }
}

# 影片處理任務
@celery_app.task(bind=True, max_retries=3)
def process_video_task(self, video_id: str, processing_config: dict):
    """影片處理任務"""
    try:
        # 更新處理狀態
        update_video_status(video_id, "processing", 0)
        
        # 階段1: 腳本生成
        update_video_status(video_id, "processing", 10)
        script_content = generate_script.delay(video_id, processing_config["script"]).get()
        
        # 階段2: 語音合成
        update_video_status(video_id, "processing", 30)
        audio_url = synthesize_speech.delay(script_content, processing_config["voice"]).get()
        
        # 階段3: 視覺生成
        update_video_status(video_id, "processing", 50)
        visual_assets = generate_visuals.delay(script_content, processing_config["visual"]).get()
        
        # 階段4: 影片組裝
        update_video_status(video_id, "processing", 80)
        video_url = assemble_video.delay(audio_url, visual_assets, processing_config).get()
        
        # 完成處理
        update_video_status(video_id, "completed", 100, video_url=video_url)
        
        return {"status": "success", "video_url": video_url}
        
    except Exception as exc:
        # 記錄錯誤
        logging.error(f"Video processing failed for {video_id}: {exc}")
        
        # 更新錯誤狀態
        update_video_status(video_id, "failed", error_message=str(exc))
        
        # 重試邏輯
        if self.request.retries < self.max_retries:
            # 指數退避重試
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(countdown=countdown, exc=exc)
        
        raise exc

# 任務監控
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """任務開始前的處理"""
    logging.info(f"Task {task.name}[{task_id}] started")

@task_postrun.connect  
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """任務完成後的處理"""
    logging.info(f"Task {task.name}[{task_id}] finished with state: {state}")

@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, einfo=None, **kwds):
    """任務失敗處理"""
    logging.error(f"Task {sender.name}[{task_id}] failed: {exception}")
    
    # 發送告警通知
    send_alert.delay(
        level="error",
        message=f"Task {sender.name} failed: {exception}",
        task_id=task_id
    )
```

## 📊 監控與可觀察性

### 監控架構設計

```mermaid
graph TB
    subgraph "資料收集層"
        App[Application Metrics]
        Infra[Infrastructure Metrics]
        Logs[Application Logs]
        Traces[Distributed Traces]
    end
    
    subgraph "資料處理層"
        Prometheus[Prometheus]
        Loki[Loki]
        Jaeger[Jaeger]
        ElasticSearch[ElasticSearch]
    end
    
    subgraph "可視化層"
        Grafana[Grafana Dashboards]
        Kibana[Kibana]
        AlertManager[Alert Manager]
    end
    
    subgraph "通知層"
        Slack[Slack]
        Email[Email]
        PagerDuty[PagerDuty]
        SMS[SMS]
    end
    
    App --> Prometheus
    Infra --> Prometheus
    Logs --> Loki
    Logs --> ElasticSearch
    Traces --> Jaeger
    
    Prometheus --> Grafana
    Loki --> Grafana
    ElasticSearch --> Kibana
    Jaeger --> Grafana
    
    Prometheus --> AlertManager
    AlertManager --> Slack
    AlertManager --> Email
    AlertManager --> PagerDuty
```

### 應用指標監控

```python
# Prometheus 指標收集
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from functools import wraps
import time

# 定義指標
REQUEST_COUNT = Counter(
    'http_requests_total',
    '總 HTTP 請求數',
    ['method', 'endpoint', 'status_code', 'service']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP 請求持續時間',
    ['method', 'endpoint', 'service'],
    buckets=[0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    '當前活躍連接數',
    ['service']
)

VIDEO_PROCESSING_DURATION = Histogram(
    'video_processing_duration_seconds',
    '影片處理持續時間',
    ['stage', 'status'],
    buckets=[30, 60, 120, 300, 600, 1200, 1800]
)

AI_API_CALLS = Counter(
    'ai_api_calls_total',
    'AI API 調用總數',
    ['provider', 'model', 'type', 'status']
)

DATABASE_QUERY_DURATION = Histogram(
    'database_query_duration_seconds',
    '資料庫查詢持續時間',
    ['query_type', 'table'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]
)

# 監控裝飾器
def monitor_requests(service_name: str):
    """HTTP 請求監控裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            start_time = time.time()
            status_code = 200
            
            try:
                response = await func(request, *args, **kwargs)
                if hasattr(response, 'status_code'):
                    status_code = response.status_code
                return response
            except Exception as e:
                status_code = 500
                raise e
            finally:
                # 記錄指標
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    status_code=status_code,
                    service=service_name
                ).inc()
                
                REQUEST_DURATION.labels(
                    method=request.method,
                    endpoint=request.url.path,
                    service=service_name
                ).observe(time.time() - start_time)
        
        return wrapper
    return decorator

def monitor_video_processing():
    """影片處理監控裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            stage = func.__name__
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "failed"
                raise e
            finally:
                VIDEO_PROCESSING_DURATION.labels(
                    stage=stage,
                    status=status
                ).observe(time.time() - start_time)
        
        return wrapper
    return decorator

def monitor_ai_calls(provider: str, model: str, call_type: str):
    """AI 調用監控裝飾器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "failed"
                raise e
            finally:
                AI_API_CALLS.labels(
                    provider=provider,
                    model=model,
                    type=call_type,
                    status=status
                ).inc()
        
        return wrapper
    return decorator

# 自定義指標端點
@app.get("/metrics")
async def metrics():
    """Prometheus 指標端點"""
    return Response(generate_latest(), media_type="text/plain")

# 健康檢查指標
class HealthChecker:
    """健康檢查器"""
    
    def __init__(self):
        self.health_metrics = {
            "database": Gauge('database_health', '資料庫健康狀態'),
            "redis": Gauge('redis_health', 'Redis 健康狀態'),
            "ai_services": Gauge('ai_services_health', 'AI 服務健康狀態'),
            "storage": Gauge('storage_health', '存儲服務健康狀態')
        }
    
    async def check_database_health(self) -> bool:
        """檢查資料庫健康狀態"""
        try:
            # 執行簡單查詢
            async with get_db_session() as session:
                result = await session.execute("SELECT 1")
                self.health_metrics["database"].set(1)
                return True
        except Exception as e:
            logging.error(f"Database health check failed: {e}")
            self.health_metrics["database"].set(0)
            return False
    
    async def check_redis_health(self) -> bool:
        """檢查 Redis 健康狀態"""
        try:
            redis_client = get_redis_client()
            await redis_client.ping()
            self.health_metrics["redis"].set(1)
            return True
        except Exception as e:
            logging.error(f"Redis health check failed: {e}")
            self.health_metrics["redis"].set(0)
            return False
    
    async def run_health_checks(self):
        """執行所有健康檢查"""
        tasks = [
            self.check_database_health(),
            self.check_redis_health(),
            # 添加其他檢查...
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        overall_health = all(isinstance(r, bool) and r for r in results)
        
        return {
            "status": "healthy" if overall_health else "unhealthy",
            "checks": {
                "database": results[0] if isinstance(results[0], bool) else False,
                "redis": results[1] if isinstance(results[1], bool) else False,
            },
            "timestamp": datetime.utcnow().isoformat()
        }

# 定期健康檢查
async def periodic_health_check():
    """定期健康檢查任務"""
    health_checker = HealthChecker()
    
    while True:
        try:
            await health_checker.run_health_checks()
            await asyncio.sleep(30)  # 每30秒檢查一次
        except Exception as e:
            logging.error(f"Health check error: {e}")
            await asyncio.sleep(60)  # 錯誤時延長間隔
```

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "\u9032\u884c\u5168\u9762\u67b6\u69cb\u5be9\u67e5\u8207\u4ee3\u78bc\u54c1\u8cea\u8a55\u4f30", "status": "completed", "priority": "high", "id": "architecture_review"}, {"content": "\u8b58\u5225\u9700\u8981\u91cd\u69cb\u7684\u95dc\u9375\u6a21\u7d44", "status": "completed", "priority": "high", "id": "identify_refactor_areas"}, {"content": "\u512a\u5316\u958b\u767c\u8005\u9ad4\u9a57\u8207\u7dad\u8b77\u6027", "status": "completed", "priority": "medium", "id": "improve_developer_experience"}, {"content": "\u5efa\u7acb\u5b8c\u6574\u7684\u958b\u767c\u6587\u6a94\u8207\u6307\u5357", "status": "completed", "priority": "medium", "id": "create_developer_docs"}, {"content": "\u5275\u5efa README.md \u4e3b\u6587\u6a94", "status": "completed", "priority": "high", "id": "create_main_readme"}, {"content": "\u5efa\u7acb\u958b\u767c\u8005\u5165\u9580\u6307\u5357", "status": "completed", "priority": "high", "id": "create_dev_guide"}, {"content": "\u64b0\u5beb API \u6587\u6a94", "status": "completed", "priority": "high", "id": "create_api_docs"}, {"content": "\u5efa\u7acb\u90e8\u7f72\u6307\u5357", "status": "completed", "priority": "medium", "id": "create_deployment_guide"}, {"content": "\u64b0\u5beb\u67b6\u69cb\u6587\u6a94", "status": "completed", "priority": "medium", "id": "create_architecture_docs"}, {"content": "\u5efa\u7acb\u6545\u969c\u6392\u9664\u6307\u5357", "status": "in_progress", "priority": "medium", "id": "create_troubleshooting"}]