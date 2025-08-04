# 🚀 專案結構改善實施指南

## 📋 總覽

本指南將幫助您按順序執行專案結構改善，包括結構重組、配置統一化和依賴管理現代化。

## ⚠️ 重要提醒

**在開始前，請確保：**
1. 已備份整個專案
2. 在 feature branch 中進行操作
3. 通知團隊成員即將進行的變更
4. 確保有足夠時間完成整個流程（預估 6-8 小時）

## 🎯 實施順序

### 階段 1：專案結構重組 (2-3 小時)

#### 1.1 執行結構遷移
```bash
# 檢查當前狀態
git status
git checkout -b feature/restructure-project

# 執行結構重組
./scripts/migrate-structure.sh
```

**預期結果：**
- `auto_generate_video_fold6` 內容移至新的 `src/` 結構
- 舊版本代碼保存在 `legacy/`
- 基礎設施代碼移至 `infra/`

#### 1.2 驗證新結構
```bash
# 檢查新目錄結構
tree -L 3 src/ infra/ legacy/

# 檢查重要服務是否存在
ls -la src/services/
ls -la src/frontend/
```

#### 1.3 更新路徑引用
```bash
# 搜尋可能需要更新的路徑引用
grep -r "auto_generate_video_fold6" . --exclude=*.md --exclude=*.backup --exclude=*.old
```

**手動修正：**
- 更新 import 路徑
- 修正 Docker 檔案中的路徑
- 更新部署腳本路徑

---

### 階段 2：配置管理統一化 (1-2 小時)

#### 2.1 執行配置清理
```bash
./scripts/cleanup-configs.sh
```

**預期結果：**
- 建立 `config/environments/` 目錄
- 統一的 `.env.example.unified`
- 清理重複的 `.env` 檔案
- Docker 配置統一

#### 2.2 設定環境配置
```bash
# 複製開發環境配置
cp config/environments/development.env .env

# 編輯配置以符合你的環境
nano .env
```

**必須設定的配置：**
```env
# 資料庫連接
DATABASE_URL=postgresql://postgres:password@localhost:5432/autovideo_dev
REDIS_URL=redis://localhost:6379/0

# JWT 密鑰 (請使用強密碼)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production

# API 服務密鑰 (如有)
OPENAI_API_KEY=your-openai-api-key
```

#### 2.3 測試配置載入
```bash
# 測試配置載入器
python config/load_env.py

# 測試 Docker 配置
docker-compose --env-file docker-compose.env config
```

---

### 階段 3：依賴管理現代化 (2-3 小時)

#### 3.1 執行依賴遷移
```bash
./scripts/migrate-dependencies.sh
```

**預期結果：**
- 更新的 `pyproject.toml.new`
- 依賴管理腳本建立
- 舊 requirements.txt 檔案備份

#### 3.2 應用新的依賴配置
```bash
# 備份現有 pyproject.toml
cp pyproject.toml pyproject.toml.original

# 應用新配置
mv pyproject.toml.new pyproject.toml

# 驗證配置語法
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"
```

#### 3.3 安裝依賴
```bash
# 建立新的虛擬環境 (建議)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows

# 安裝開發環境依賴
./scripts/install-deps.sh dev
```

#### 3.4 驗證遷移
```bash
./scripts/validate-migration.py
```

---

### 階段 4：測試與驗證 (1-2 小時)

#### 4.1 功能測試
```bash
# 檢查依賴狀態
./scripts/check-deps.sh

# 測試關鍵服務啟動
cd src/services/api-gateway
python -m uvicorn app.main:app --reload --port 8000 &
curl http://localhost:8000/health
```

#### 4.2 Docker 測試
```bash
# 測試 Docker 構建
docker-compose --env-file docker-compose.env build

# 測試容器啟動
docker-compose --env-file docker-compose.env up -d

# 檢查容器狀態
docker-compose ps
```

#### 4.3 前端測試
```bash
cd src/frontend
npm install
npm run dev
```

---

## 🔧 故障排除

### 常見問題與解決方案

#### 1. 路徑引用錯誤
```bash
# 搜尋並修正路徑引用
find . -name "*.py" -exec grep -l "auto_generate_video_fold6" {} \;
find . -name "*.js" -exec grep -l "auto_generate_video_fold6" {} \;
```

#### 2. 依賴安裝失敗
```bash
# 檢查 Python 版本
python --version  # 需要 >= 3.9

# 清理 pip 快取
pip cache purge

# 重新安裝
pip install -e .[dev] --force-reinstall
```

#### 3. Docker 構建失敗
```bash
# 清理 Docker 快取
docker system prune -a

# 重新構建
docker-compose build --no-cache
```

#### 4. 配置載入錯誤
```bash
# 檢查環境變數
env | grep -E "(DATABASE|REDIS|JWT)"

# 測試配置檔案語法
python -c "
from dotenv import dotenv_values
print(dotenv_values('.env'))
"
```

---

## 📋 驗證檢核表

### ✅ 結構重組驗證
- [ ] `src/services/` 包含所有微服務
- [ ] `src/frontend/` 包含前端應用
- [ ] `infra/` 包含基礎設施配置
- [ ] `legacy/` 保存舊版本代碼
- [ ] 所有服務可正常啟動

### ✅ 配置管理驗證
- [ ] `config/environments/` 目錄存在
- [ ] 環境特定配置檔案建立
- [ ] `.env` 檔案設定正確
- [ ] Docker 配置檔案正常
- [ ] 配置載入器運作正常

### ✅ 依賴管理驗證
- [ ] `pyproject.toml` 語法正確
- [ ] 所有依賴可正常安裝
- [ ] 依賴管理腳本可執行
- [ ] 版本衝突已解決
- [ ] 安全漏洞已修復

### ✅ 功能驗證
- [ ] 所有微服務正常啟動
- [ ] API 閘道器正常回應
- [ ] 前端應用正常載入
- [ ] 資料庫連接正常
- [ ] Redis 快取正常

### ✅ Docker 驗證
- [ ] 所有容器成功構建
- [ ] 容器可正常啟動
- [ ] 服務間網路通信正常
- [ ] 健康檢查通過
- [ ] 資料持久化正常

---

## 📊 效能監控

### 監控指標
```bash
# 檢查應用啟動時間
time docker-compose up -d

# 檢查記憶體使用
docker stats

# 檢查磁碟使用
du -sh src/ infra/ legacy/
```

### 效能基準
- **容器啟動時間**: < 30 秒
- **API 回應時間**: < 500ms
- **前端載入時間**: < 3 秒
- **記憶體使用**: < 2GB (開發環境)

---

## 🚀 部署準備

### CI/CD 更新
1. **更新 GitHub Actions**
   ```yaml
   - name: Install dependencies
     run: pip install -e .[dev]
   
   - name: Build Docker images
     run: docker-compose build
   ```

2. **更新部署腳本**
   ```bash
   # 更新部署路徑
   sed -i 's|auto_generate_video_fold6|src|g' deploy/*.sh
   ```

### 文檔更新
```bash
# 更新 README.md 中的路徑
# 更新 API 文檔
# 更新部署指南
```

---

## 📞 支援與回滾

### 如需協助
1. 檢查各階段的報告檔案
2. 查看 `.backup_path` 和 `.requirements_backup_path` 中的備份
3. 查閱故障排除章節

### 緊急回滾
```bash
# 回滾到原始狀態
git checkout main
git branch -D feature/restructure-project

# 恢復備份 (如需要)
backup_path=$(cat .backup_path)
cp -r "$backup_path"/* .
```

---

## 🎉 完成後的下一步

1. **團隊通知**
   - 發送更新通知給團隊
   - 安排程式碼審查會議
   - 更新開發環境設定文檔

2. **持續改善**
   - 建立定期依賴更新流程
   - 設定自動化安全掃描
   - 監控系統效能指標

3. **知識分享**
   - 記錄改善經驗
   - 建立最佳實踐文檔
   - 培訓新團隊成員

---

**🎯 目標達成指標：**
- 專案結構清晰一致
- 配置管理統一化
- 依賴版本無衝突
- 所有服務正常運行
- 開發體驗顯著改善

祝您實施順利！ 🚀