# 🚀 MacBook Pro M4 ARM64 架構優化指南

## 📖 概覽

本指南專門為 MacBook Pro M4 (ARM64) 架構提供優化建議，幫助開發者充分利用 M4 晶片的性能優勢。

## 🏗️ M4 架構特色

### 統一記憶體架構 (Unified Memory Architecture)
- CPU、GPU 和 Neural Engine 共享記憶體
- 更高的記憶體帶寬和更低的延遲
- 需要調整傳統的記憶體配置策略

### 高效能核心設計
- 4個性能核心 + 6個效率核心
- 單核心性能極強
- 多核心並行處理能力出色

### AI 和機器學習優化
- 內建 Neural Engine
- Metal Performance Shaders 支援
- Core ML 原生加速

## 🐳 Docker 優化配置

### 使用 M4 專用配置文件
```bash
# 使用針對 M4 優化的 Docker Compose 配置
docker-compose -f docker/docker-compose.m4.yml up --build
```

### 平台設定
確保所有服務使用 ARM64 平台：
```yaml
services:
  your-service:
    platform: linux/arm64
    build:
      platform: linux/arm64
```

### 基礎映像選擇
優先使用官方 ARM64 映像：
```dockerfile
# Python 服務
FROM python:3.11-slim

# Node.js 服務  
FROM node:18-alpine

# PostgreSQL
FROM postgres:15-alpine

# Redis
FROM redis:7-alpine
```

## ⚡ 性能優化設定

### PostgreSQL M4 優化
```sql
-- 針對 M4 統一記憶體架構優化
shared_buffers = 512MB              -- 利用高記憶體帶寬
effective_cache_size = 2GB          -- M4 記憶體優勢
max_worker_processes = 8            -- 利用多核心
max_parallel_workers = 8            -- 並行查詢優化
max_parallel_workers_per_gather = 4
work_mem = 8MB                      -- 平衡記憶體使用
random_page_cost = 1.1              -- SSD 優化
effective_io_concurrency = 200      -- 高 I/O 並發
```

### Redis M4 設定
```redis
# 記憶體優化
maxmemory 768mb
maxmemory-policy allkeys-lru

# 持久化優化
appendonly yes
appendfsync everysec
save 60 1000

# 網路優化
tcp-keepalive 300
timeout 300
maxclients 1000
```

### Node.js 前端優化
```bash
# 環境變數設定
NODE_OPTIONS="--max-old-space-size=4096"
UV_THREADPOOL_SIZE=8  # 利用 M4 多核心
```

### Python 後端優化
```bash
# Python 執行時優化
PYTHONOPTIMIZE=2
OMP_NUM_THREADS=8
MKL_NUM_THREADS=8
OPENBLAS_NUM_THREADS=8
```

## 🔧 開發環境設定

### Docker Desktop 配置
```json
{
  "experimental-features": true,
  "builder": {
    "gc": {
      "enabled": true,
      "defaultKeepStorage": "20GB"
    }
  },
  "features": {
    "buildkit": true
  },
  "default-platform": "linux/arm64"
}
```

### 環境變數設定
在 `.zshrc` 或 `.bash_profile` 中添加：
```bash
# Docker M4 優化
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_DEFAULT_PLATFORM=linux/arm64

# 開發工具路徑
export PATH="/opt/homebrew/bin:$PATH"

# Python/Node.js 性能優化
export PYTHONOPTIMIZE=2
export NODE_OPTIONS="--max-old-space-size=4096"
```

### Homebrew 依賴安裝
```bash
# 安裝 M4 原生工具
brew install --formula \
  postgresql@15 \
  redis \
  node@18 \
  python@3.11 \
  ffmpeg \
  imagemagick

# 確認 ARM64 版本
file $(which python3)  # 應顯示 arm64
file $(which node)     # 應顯示 arm64
```

## 🧪 AI/ML 優化

### PyTorch M4 支援
```python
# requirements.txt
torch>=2.0.0
torchvision>=0.15.0
torchaudio>=2.0.0

# 檢查 MPS (Metal Performance Shaders) 支援
import torch
print(f"MPS available: {torch.backends.mps.is_available()}")
print(f"MPS built: {torch.backends.mps.is_built()}")

# 使用 MPS 裝置
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
```

### Core ML 整合
```python
# 使用 Core ML 進行推論加速
import coremltools as ct

# 轉換模型到 Core ML 格式
mlmodel = ct.convert(
    pytorch_model,
    inputs=[ct.TensorType(shape=(1, 3, 224, 224))]
)
mlmodel.save("model.mlmodel")
```

### TensorFlow M4 優化
```python
import tensorflow as tf

# 啟用 Metal GPU 支援
physical_devices = tf.config.experimental.list_physical_devices('GPU')
if len(physical_devices) > 0:
    tf.config.experimental.set_memory_growth(physical_devices[0], True)
```

## 🎥 影片處理優化

### FFmpeg ARM64 配置
```bash
# 使用硬體加速 (如果支援)
ffmpeg -hwaccel videotoolbox -i input.mp4 -c:v h264_videotoolbox output.mp4

# 利用多核心並行處理
ffmpeg -threads 8 -i input.mp4 -c:v libx264 -preset medium output.mp4
```

### 容器內 FFmpeg 優化
```dockerfile
# 在 Dockerfile 中
ENV FFMPEG_THREADS=8
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*
```

## 📊 監控和性能分析

### M4 特定監控指標
```bash
# CPU 使用情況
htop  # 觀察 P 核心和 E 核心使用情況

# 記憶體壓力
memory_pressure

# GPU 活動
sudo powermetrics -s gpu_power -n 1

# 溫度監控
sudo powermetrics -s thermal -n 1
```

### 容器資源監控
```bash
# 監控容器資源使用
docker stats

# 檢查 ARM64 平台
docker image inspect your-image:tag | grep Architecture
```

## 🚀 部署最佳實踐

### 多階段建構優化
```dockerfile
# 利用 BuildKit 快取
# syntax=docker/dockerfile:1
FROM --platform=$BUILDPLATFORM node:18-alpine AS deps
ARG TARGETPLATFORM
ARG BUILDPLATFORM
RUN echo "Building on $BUILDPLATFORM, targeting $TARGETPLATFORM"

# 依賴安裝階段
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# 建構階段
FROM deps AS build
RUN npm ci
COPY . .
RUN npm run build

# 生產階段
FROM node:18-alpine AS runtime
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
```

### CI/CD ARM64 支援
```yaml
# GitHub Actions 範例
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v2

- name: Build and push
  uses: docker/build-push-action@v4
  with:
    platforms: linux/arm64,linux/amd64
    push: true
    tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ env.VERSION }}
```

## ⚠️ 已知限制和解決方案

### 相容性問題
```bash
# 某些 x86_64 映像可能無法運行
# 解決方案：使用 ARM64 原生映像或多架構映像

# 檢查映像架構
docker manifest inspect python:3.11-slim
```

### 性能調優
```bash
# 如果遇到記憶體問題，調整容器限制
docker-compose -f docker-compose.m4.yml up --scale worker=2
```

### 開發工具兼容性
```bash
# 確保使用 ARM64 版本的開發工具
brew install --formula your-tool
# 而不是
brew install --cask your-tool  # 可能是 x86_64 版本
```

## 🔄 遷移檢查清單

### 從 Intel Mac 遷移
- [ ] 重新安裝 Homebrew 和依賴項
- [ ] 重建所有 Docker 映像
- [ ] 更新 CI/CD 配置支援 ARM64
- [ ] 測試所有服務在 ARM64 上的功能
- [ ] 調整資源配置檔案

### 驗證 M4 最佳化
```bash
# 運行完整系統測試
docker-compose -f docker/docker-compose.m4.yml up --build
curl http://localhost:3000/health
curl http://localhost:8000/health

# 性能基準測試
npm run benchmark  # 前端
pytest tests/performance/  # 後端
```

## 📈 預期性能提升

### 典型性能改善
- **建構時間**: 減少 30-50%
- **啟動時間**: 減少 40-60% 
- **記憶體效率**: 提升 20-30%
- **AI/ML 推論**: 提升 2-5x (使用 Neural Engine)
- **影片處理**: 提升 1.5-3x (使用硬體加速)

### 監控關鍵指標
- 容器啟動時間
- API 響應時間
- 記憶體使用效率
- CPU 使用分布 (P-core vs E-core)
- 熱節流頻率

透過這些優化設定，您的自動影片生成系統將能夠充分發揮 MacBook Pro M4 的性能潛力！