# 專案結構重組計劃

## 🎯 重組目標

解決當前專案中的結構混亂問題：
- 統一專案邊界和責任分工
- 整合重複的配置和依賴管理
- 建立清晰的開發和部署流程

## 📊 現狀分析

### 問題識別
1. **雙重專案結構**
   - 根目錄：基本版本 (backend/, services/, docs/)
   - auto_generate_video_fold6/：完整生產級系統
   - 造成開發者困惑和維護困難

2. **配置檔案重複**
   - 12 個 .env* 檔案散布在不同目錄
   - 配置管理策略不一致

3. **依賴管理混亂**
   - pyproject.toml (根目錄) vs 40+ requirements.txt
   - 版本衝突和管理複雜度高

## 🚀 重組方案：提升 auto_generate_video_fold6

### 階段 1：結構重組 (2-3 天)

#### 1.1 目錄結構調整
```bash
# 新的專案結構
myProject/
├── src/                              # 主要應用程式碼
│   ├── services/                     # 微服務 (從 auto_generate_video_fold6/services)
│   ├── frontend/                     # 前端應用 (從 auto_generate_video_fold6/frontend)
│   ├── shared/                       # 共享組件
│   └── config/                       # 配置管理
├── infra/                            # 基礎設施代碼
│   ├── docker/                       # Docker 配置
│   ├── k8s/                         # Kubernetes 配置
│   ├── monitoring/                   # 監控系統
│   └── security/                     # 安全配置
├── scripts/                          # 部署和管理腳本
├── tests/                            # 整合測試
├── docs/                             # 統一文檔
├── legacy/                           # 舊版本代碼 (暫時保留)
│   ├── backend/                      # 原根目錄的 backend/
│   └── services/                     # 原根目錄的 services/
├── pyproject.toml                    # 統一依賴管理
├── docker-compose.yml               # 主要 compose 文件
├── .env.example                     # 統一配置模板
└── alembic.ini                      # 資料庫遷移配置
```

#### 1.2 遷移檢核表
- [ ] 建立新的目錄結構
- [ ] 移動 auto_generate_video_fold6/ 內容到新結構
- [ ] 保留原 backend/ 和 services/ 到 legacy/
- [ ] 更新所有路徑引用
- [ ] 測試新結構的功能完整性

### 階段 2：配置統一化 (1-2 天)

#### 2.1 環境配置清理
```bash
# 保留的配置檔案
.env.example                          # 統一配置模板
config/environments/
├── development.env                   # 開發環境配置
├── staging.env                      # 測試環境配置
└── production.env                   # 生產環境配置
```

#### 2.2 配置管理策略
1. **單一配置模板**：只保留 `.env.example`
2. **環境分離**：使用 `config/environments/` 管理不同環境
3. **Docker 整合**：在 docker-compose 中使用環境特定配置
4. **安全管理**：敏感配置通過環境變數注入

#### 2.3 配置清理檢核表
- [ ] 合併重複的 .env 檔案
- [ ] 建立統一的配置模板
- [ ] 更新 Docker 配置以使用新的環境設定
- [ ] 更新部署腳本的配置路徑
- [ ] 文檔化配置管理流程

### 階段 3：依賴管理現代化 (2-3 天)

#### 3.1 pyproject.toml 擴展
```toml
[project.optional-dependencies]
# 服務特定依賴組
api-gateway = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "python-jose[cryptography]>=3.3.4"
]

auth-service = [
    "python-jose[cryptography]>=3.3.4",
    "passlib[bcrypt]>=1.7.4",
    "sqlalchemy>=2.0.0"
]

ai-service = [
    "torch>=2.2.0",
    "transformers>=4.40.0",
    "openai>=1.0.0"
]

video-service = [
    "opencv-python-headless>=4.8.0",
    "pillow>=10.3.0",
    "ffmpeg-python>=0.2.0"
]

data-service = [
    "boto3>=1.29.0",
    "sqlalchemy>=2.0.0",
    "alembic>=1.12.0"
]

# 環境特定依賴
monitoring = [
    "prometheus-client>=0.19.0",
    "opentelemetry-api>=1.21.0",
    "structlog>=23.2.0"
]

frontend = [
    # 前端相關 Python 工具 (如需要)
]
```

#### 3.2 依賴遷移檢核表
- [ ] 分析所有 requirements.txt 檔案
- [ ] 將依賴分組到 pyproject.toml
- [ ] 解決版本衝突
- [ ] 更新 Docker 構建腳本
- [ ] 更新 CI/CD 流程
- [ ] 測試所有服務的依賴解析

### 階段 4：CI/CD 和文檔更新 (1 天)

#### 4.1 更新構建流程
- [ ] 更新 Dockerfile 以使用 pyproject.toml
- [ ] 修改 docker-compose 檔案路徑
- [ ] 更新部署腳本
- [ ] 調整 GitHub Actions 工作流程

#### 4.2 文檔整合
- [ ] 合併重複的文檔
- [ ] 更新 README.md
- [ ] 修正所有文檔中的路徑引用
- [ ] 建立遷移指南

## 🔧 實施工具和腳本

### 自動化遷移腳本
```bash
#!/bin/bash
# migrate-structure.sh - 自動化結構遷移腳本

echo "開始專案結構重組..."

# 1. 建立新目錄結構
mkdir -p src/{services,frontend,shared,config}
mkdir -p infra/{docker,k8s,monitoring,security}
mkdir -p legacy/{backend,services}

# 2. 移動 auto_generate_video_fold6 內容
mv auto_generate_video_fold6/services/* src/services/
mv auto_generate_video_fold6/frontend/* src/frontend/
mv auto_generate_video_fold6/shared/* src/shared/

# 3. 移動基礎設施代碼
mv auto_generate_video_fold6/docker/* infra/docker/
mv auto_generate_video_fold6/k8s/* infra/k8s/
mv auto_generate_video_fold6/monitoring/* infra/monitoring/

# 4. 保留舊版本代碼
mv backend/* legacy/backend/
mv services/* legacy/services/

echo "結構重組完成，請檢查並測試新結構。"
```

### 配置清理腳本
```bash
#!/bin/bash
# cleanup-configs.sh - 配置檔案清理腳本

echo "清理重複的配置檔案..."

# 1. 建立統一配置目錄
mkdir -p config/environments

# 2. 合併環境配置
cat .env.development > config/environments/development.env
cat auto_generate_video_fold6/.env.development >> config/environments/development.env

# 3. 移除重複檔案
rm -f .env .env.development .env.production .env.test .env.testing
rm -f auto_generate_video_fold6/.env*

echo "配置清理完成。"
```

## ✅ 驗證檢核表

### 功能驗證
- [ ] 所有微服務正常啟動
- [ ] 前端可正常訪問
- [ ] API 閘道器路由正常
- [ ] 資料庫連接正常
- [ ] Redis 快取功能正常
- [ ] 檔案上傳下載功能正常

### 開發流程驗證
- [ ] 本地開發環境設定正常
- [ ] Docker 容器構建成功
- [ ] 測試套件執行正常
- [ ] CI/CD 流程無錯誤
- [ ] 文檔引用路徑正確

### 效能驗證
- [ ] 應用啟動時間無明顯增加
- [ ] API 回應時間維持正常
- [ ] 前端頁面載入速度正常
- [ ] 資源使用量合理

## 📅 實施時程

| 階段 | 工作項目 | 預估時間 | 負責人 |
|------|----------|----------|--------|
| 階段 1 | 結構重組 | 2-3 天 | 開發團隊 |
| 階段 2 | 配置統一 | 1-2 天 | DevOps |
| 階段 3 | 依賴管理 | 2-3 天 | 後端團隊 |
| 階段 4 | CI/CD 更新 | 1 天 | DevOps |
| **總計** | | **6-9 天** | |

## 🚨 風險管控

### 潛在風險
1. **服務中斷**：重組過程可能影響開發環境
2. **路徑錯誤**：大量路徑變更可能導致引用錯誤
3. **依賴衝突**：依賴整合可能產生版本衝突
4. **測試失敗**：結構變更可能影響測試執行

### 風險緩解措施
1. **分支保護**：在 feature branch 中進行重組
2. **備份策略**：重組前建立完整備份
3. **階段性驗證**：每個階段完成後進行完整測試
4. **回滾計劃**：準備快速回滾到原始狀態的方案

## 🎯 預期效益

### 短期效益 (1 個月內)
- 專案結構清晰易懂
- 配置管理統一化
- 依賴版本衝突解決
- 開發體驗改善

### 長期效益 (3-6 個月)
- 維護成本降低
- 新成員上手時間縮短
- 部署流程簡化
- 技術債務減少

---

**執行建議**：建議按階段逐步實施，每個階段完成後進行充分測試，確保系統穩定性後再進行下一階段。