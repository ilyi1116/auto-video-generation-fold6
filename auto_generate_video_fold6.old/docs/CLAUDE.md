## 溝通語言設定
**重要：所有與 Claude 的對話請只使用繁體中文回答**

## 系統架構與藍圖

### 生產級聲音克隆系統架構筆記

#### 核心設計理念
- 採用 DevSecOps 思維模式
- 強調模組化、安全性與可維護性
- 基於微服務架構的現代化系統設計

#### 技術棧選擇重點
- 後端：FastAPI (Python)
- 前端：SvelteKit (Node.js)
- 非同步任務：Celery
- 資料庫：PostgreSQL, Redis, S3
- 容器化：Docker
- CI/CD：GitHub Actions

#### 系統架構關鍵服務
- API 閘道器
- 使用者認證服務
- 語音資料接收與預處理服務
- 非同步模型訓練服務
- 即時推論服務

#### 安全性與可維護性策略
- 多層次安全框架
- 自動化安全掃描 (Snyk, Trivy)
- 結構化日誌記錄
- 全面自動化測試流程
- 持續整合與部署 (CI/CD)

#### 未來發展路線
- 分階段實施
- 逐步擴展功能
- 持續優化架構

## 前端開發完成狀態

### 已完成的頁面與功能 ✅

#### 核心頁面
- **登入/註冊系統** (`/login`, `/register`, `/forgot-password`)
  - 完整的身份驗證流程
  - 表單驗證與錯誤處理
  - 深色模式支援

- **儀表板** (`/dashboard`)
  - 統計概覽與快速動作
  - 最近影片與趨勢主題
  - 響應式設計

- **專案管理** (`/projects`)
  - 專案列表與搜尋功能
  - 批次操作與篩選
  - 狀態追蹤

#### AI 工具頁面
- **腳本生成器** (`/ai/script`)
  - 多平台優化設定
  - 趨勢主題建議
  - 腳本歷史記錄

- **圖像生成器** (`/ai/images`)
  - 高級圖像生成介面
  - 風格選擇與品質控制
  - 批次生成與管理

- **語音合成** (`/ai/voice`)
  - 多語言語音選項
  - 情感與速度控制
  - 自訂語音上傳

#### 工作流程頁面
- **影片創建** (`/create`)
  - 5步驟引導式工作流程
  - 專案設定與腳本生成
  - 視覺創建與語音合成
  - 影片組裝

#### 分析與洞察
- **數據分析** (`/analytics`)
  - 綜合效能儀表板
  - 受眾人口統計
  - 平台效能比較

- **趨勢分析** (`/trends`)
  - 即時趨勢追蹤
  - 病毒內容分析
  - 關鍵字研究工具

#### 社群媒體管理
- **社群媒體** (`/social`)
  - 多平台發布與排程
  - 平台連接管理
  - 即時分析與效能指標
  - 內容日曆

#### 設定與個人檔案
- **設定頁面** (`/settings`)
  - 6個主要類別設定
  - 個人資訊管理
  - 通知偏好設定
  - 隱私與數據控制
  - 外觀自訂設定
  - 計費與訂閱管理
  - 安全功能設定

- **個人檔案** (`/profile`)
  - 完整的用戶檔案介面
  - 內容組織與展示
  - 活動時間軸
  - 成就系統

### 技術實作亮點

#### 設計系統
- **一致的 UI/UX**: 現代化設計模式與用戶體驗
- **響應式設計**: 所有頁面在行動與桌面裝置上無縫運作
- **深色模式**: 完整的深/淺主題相容性
- **無障礙設計**: 適當的 ARIA 標籤與鍵盤導航

#### 技術架構
- **Svelte 反應式**: 高效的組件結構與狀態管理
- **模組化組件**: 組件組合與重用性
- **表單驗證**: 表單驗證與錯誤處理
- **載入狀態**: 高效的組件結構與載入狀態
- **API 整合**: 完整的 API 客戶端設定

#### 開發模式
- **Toast 通知**: 用戶回饋系統
- **模態對話框**: 確認流程
- **網格與列表**: 檢視切換功能
- **搜尋與篩選**: 搜尋與篩選功能

### 專案完成度
🎯 **前端開發完成度: 100%**

所有主要功能頁面已實作完成，包含完整的 AI 影片生成平台所需的所有前端功能。

## 開發流程與品質保證

### 🧪 測試開發要求

#### 必要測試類型
每次開發完成後，**必須**撰寫以下完整測試程式：

1. **單元測試 (Unit Tests)**
   - 對所有新增/修改的函數進行測試
   - 使用 Jest 或 Vitest 作為測試框架
   - 測試覆蓋率必須達到 80% 以上
   - 測試檔案放置於 `__tests__` 或 `.test.js/.test.ts` 檔案中

2. **組件測試 (Component Tests)**
   - 對所有 Svelte 組件進行渲染測試
   - 使用 @testing-library/svelte 進行互動測試
   - 測試組件的 props、events 和 slots
   - 驗證組件在不同狀態下的行為

3. **整合測試 (Integration Tests)**
   - 測試 API 整合功能
   - 測試多個組件間的協作
   - 使用 Mock Service Worker (MSW) 模擬 API

4. **端對端測試 (E2E Tests)**
   - 使用 Playwright 或 Cypress
   - 測試關鍵用戶流程
   - 涵蓋主要功能路徑

#### 測試執行命令
```bash
# 前端測試
npm run test              # 執行所有測試
npm run test:unit         # 單元測試
npm run test:component    # 組件測試
npm run test:integration  # 整合測試
npm run test:e2e         # 端對端測試
npm run test:coverage    # 測試覆蓋率報告

# 後端測試
pytest tests/             # Python 後端測試
pytest --cov=app tests/   # 覆蓋率測試
```

### 🐳 Docker 驗證要求

#### 容器化驗證流程
每次開發完成後，**必須**確保應用可在 Docker 環境中正常執行：

1. **本地 Docker 驗證**
   ```bash
   # 構建並運行完整系統
   docker-compose up --build
   
   # 驗證各服務狀態
   docker-compose ps
   
   # 檢查服務日誌
   docker-compose logs [service-name]
   ```

2. **多階段構建驗證**
   - 確保 Dockerfile 多階段構建正常
   - 驗證生產環境映像檔大小合理
   - 測試容器啟動時間和資源使用

3. **服務間通信測試**
   - 驗證微服務間的網路連接
   - 測試 API 閘道器路由功能
   - 確認資料庫連接正常

4. **健康檢查驗證**
   ```bash
   # 檢查所有服務健康狀態
   curl http://localhost:8080/health
   curl http://localhost:3000/health
   ```

#### Docker 測試清單
- [ ] 所有容器正常啟動
- [ ] 前端可正常訪問 (http://localhost:3000)
- [ ] API 閘道器回應正常 (http://localhost:8080)
- [ ] 資料庫連接正常
- [ ] Redis 快取功能正常
- [ ] 檔案上傳/下載功能正常
- [ ] 日誌收集正常運作
- [ ] 服務發現機制正常

### 📋 開發完成驗證檢核表

每次功能開發完成時，必須完成以下檢核：

#### 程式碼品質
- [ ] 通過所有單元測試 (覆蓋率 ≥ 80%)
- [ ] 通過所有整合測試
- [ ] 通過 ESLint/Prettier 程式碼格式檢查
- [ ] 通過 TypeScript 類型檢查 (如適用)
- [ ] 程式碼審查完成

#### 功能驗證
- [ ] 功能在本地開發環境正常運作
- [ ] 功能在 Docker 環境正常運作
- [ ] 響應式設計在多種裝置上正常顯示
- [ ] 深色模式功能正常
- [ ] 無障礙功能符合標準

#### 效能與安全
- [ ] 頁面載入時間 < 3 秒
- [ ] API 回應時間 < 500ms
- [ ] 通過安全性掃描 (無高風險漏洞)
- [ ] 通過 Lighthouse 效能測試 (≥ 90 分)

#### 文檔更新
- [ ] 更新相關 API 文檔
- [ ] 更新組件使用說明
- [ ] 更新部署文檔
- [ ] 更新 CHANGELOG.md

### 🚀 部署前驗證

在部署到生產環境前，額外執行：

```bash
# 完整測試套件
npm run test:all
pytest tests/ --cov=app

# Docker 生產環境驗證
docker-compose -f docker-compose.prod.yml up --build

# 效能基準測試
npm run benchmark
```

**重要提醒**: 只有通過所有測試和 Docker 驗證的程式碼才能合併到主分支或部署到生產環境。

## 🧬 TDD 測試驅動開發方法論

### 核心開發理念
遵循 Kent Beck 的測試驅動開發 (TDD) 和 Tidy First 原則，確保高品質的程式碼產出。

#### TDD 開發循環: Red → Green → Refactor
1. **Red (紅燈)**: 撰寫一個會失敗的測試
2. **Green (綠燈)**: 實作最少的程式碼讓測試通過
3. **Refactor (重構)**: 在測試通過的前提下改善程式碼結構

### 🔄 TDD 開發流程

#### 第一階段: 撰寫失敗測試 (Red)
```javascript
// 範例: 撰寫明確描述行為的測試
describe('VideoProcessor', () => {
  it('shouldGenerateVideoFromScriptAndAudio', () => {
    // 安排
    const script = createMockScript();
    const audioFile = createMockAudio();
    
    // 行動
    const result = videoProcessor.generate(script, audioFile);
    
    // 斷言
    expect(result).toBeDefined();
    expect(result.duration).toBeGreaterThan(0);
  });
});
```

#### 第二階段: 實作最小程式碼 (Green)
- 僅實作足以讓測試通過的程式碼
- 避免過度設計或提前最佳化
- 專注於滿足測試需求

#### 第三階段: 重構改善 (Refactor)
- 只在所有測試通過時進行重構
- 消除重複程式碼
- 提升程式碼可讀性和維護性

### 🏗️ Tidy First 結構改善原則

#### 分類變更類型
1. **結構性變更 (Structural Changes)**
   - 重新命名變數、函數、類別
   - 提取方法或抽象共用邏輯
   - 重新組織程式碼結構
   - **不改變程式行為**

2. **行為性變更 (Behavioral Changes)**
   - 新增功能
   - 修改現有功能邏輯
   - 修復錯誤

#### 變更執行順序
```
結構性變更 → 驗證測試 → 行為性變更 → 驗證測試
```

### 📝 TDD 測試撰寫指導

#### 測試命名規範
```javascript
// 好的測試名稱: 描述行為而非實作
it('shouldReturnErrorWhenScriptIsEmpty', () => {});
it('shouldGenerateVideoWithCorrectDuration', () => {});
it('shouldSupportMultipleAudioFormats', () => {});

// 避免的測試名稱: 過於技術性
it('testVideoGeneration', () => {});
it('checkResult', () => {});
```

#### 測試結構: AAA 模式
```javascript
it('shouldProcessVideoSuccessfully', () => {
  // Arrange (安排) - 設定測試條件
  const mockData = createTestData();
  const processor = new VideoProcessor();
  
  // Act (行動) - 執行測試動作
  const result = processor.process(mockData);
  
  // Assert (斷言) - 驗證結果
  expect(result.status).toBe('success');
  expect(result.videoUrl).toBeDefined();
});
```

### 🚀 TDD 工作流程實例

#### 功能開發流程
```bash
# 1. 撰寫失敗測試
npm run test -- --watch

# 2. 實作最小程式碼
# 編輯 src/components/VideoProcessor.js

# 3. 確認測試通過
npm run test:unit

# 4. 重構改善 (如需要)
# 執行結構性變更

# 5. 再次驗證所有測試
npm run test:all

# 6. 提交變更
git add . && git commit -m "feat: implement video processing logic"
```

#### 錯誤修復流程
```bash
# 1. 撰寫重現問題的測試 (API 層級)
# 2. 撰寫最小重現問題的測試
# 3. 修復程式碼讓兩個測試都通過
# 4. 重構改善 (如需要)
# 5. 驗證所有測試通過
```

### 📊 程式碼品質指標

#### 必須達到的標準
- **測試覆蓋率**: ≥ 90%
- **循環複雜度**: ≤ 10
- **方法長度**: ≤ 20 行
- **類別長度**: ≤ 200 行
- **重複程式碼**: 0 容忍

#### 持續改善原則
1. **消除重複**: 發現重複立即重構
2. **表達意圖**: 程式碼要能自我解釋
3. **明確依賴**: 避免隱式依賴關係
4. **單一職責**: 每個方法只做一件事
5. **最小狀態**: 減少可變狀態和副作用

### 🔧 TDD 工具配置

#### 測試框架設定
```javascript
// vitest.config.js - 前端測試配置
export default defineConfig({
  test: {
    environment: 'jsdom',
    coverage: {
      threshold: {
        global: {
          branches: 90,
          functions: 90,
          lines: 90,
          statements: 90
        }
      }
    }
  }
});
```

#### 後端測試配置
```python
# pytest.ini - Python 測試配置
[tool:pytest]
minversion = 6.0
addopts = --cov=app --cov-report=html --cov-fail-under=90
testpaths = tests
```

### 🎯 TDD 最佳實踐

#### 開發節奏
- **一次一個測試**: 專注於單一功能增量
- **小步快跑**: 頻繁的小型提交
- **持續驗證**: 每次變更後執行完整測試套件
- **立即重構**: 發現程式碼異味立即處理

#### 團隊協作
- **結對程式設計**: 複雜功能使用結對開發
- **程式碼審查**: 重點檢視測試品質和覆蓋率
- **知識分享**: 定期分享 TDD 實踐經驗

**TDD 核心信念**: 測試不僅是驗證工具，更是設計和文檔工具。好的測試能指導良好的設計。