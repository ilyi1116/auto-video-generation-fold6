# 後台管理系統前端

基於 SvelteKit 的現代化管理後台介面。

## 🚀 快速開始

### 開發環境

```bash
# 安裝依賴
npm install

# 配置環境變數
cp .env.example .env

# 啟動開發服務器
npm run dev
```

訪問 http://localhost:3000

### 生產環境

```bash
# 建構生產版本
npm run build

# 預覽生產版本
npm run preview
```

## 🏗️ 項目結構

```
src/
├── app.css                 # 全局樣式
├── app.html               # HTML 模板
├── lib/
│   └── components/        # 可復用組件
│       ├── Header.svelte  # 頂部導航
│       └── Sidebar.svelte # 側邊欄
├── routes/                # 頁面路由
│   ├── +layout.svelte     # 全局佈局
│   ├── +page.svelte       # 首頁 (儀表板)
│   ├── login/             # 登錄頁面
│   ├── ai-providers/      # AI Provider 管理
│   ├── crawlers/          # 爬蟲管理
│   ├── trends/            # 社交趨勢
│   ├── logs/              # 系統日誌
│   └── users/             # 用戶管理
├── stores/                # 狀態管理
│   └── auth.ts            # 認證狀態
└── utils/                 # 工具函數
    ├── api.ts             # API 客戶端
    └── helpers.ts         # 輔助函數
```

## 🎨 設計系統

### 顏色主題

- **主色**: `#3B82F6` (Blue 500)
- **成功**: `#10B981` (Green 500)
- **警告**: `#F59E0B` (Yellow 500)
- **錯誤**: `#EF4444` (Red 500)
- **灰階**: Gray 50-900

### 組件庫

- **按鈕**: `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-outline`, `.btn-danger`
- **表單**: `.form-input`, `.form-select`, `.form-textarea`
- **卡片**: `.card`
- **徽章**: `.badge`, `.badge-success`, `.badge-warning`, `.badge-error`

### 圖標

使用 [Lucide Svelte](https://lucide.dev/guide/packages/lucide-svelte) 圖標庫。

## 📱 響應式設計

- **手機**: < 640px
- **平板**: 640px - 1024px
- **桌面**: > 1024px

側邊欄在手機版會自動收起，提供良好的移動端體驗。

## 🔐 認證機制

- 使用 JWT Token 進行身份驗證
- Token 存儲在 localStorage
- 自動重定向到登錄頁面
- 請求攔截器自動添加 Authorization 頭

## 🌐 API 集成

API 客戶端位於 `src/utils/api.ts`，提供：

- 自動 Token 認證
- 錯誤處理
- 請求/響應攔截
- 統一的接口定義

## 🧪 開發指南

### 添加新頁面

1. 在 `src/routes/` 下創建新目錄
2. 添加 `+page.svelte` 文件
3. 更新 `Sidebar.svelte` 導航菜單

### 創建新組件

1. 在 `src/lib/components/` 下創建 `.svelte` 文件
2. 遵循現有的命名和樣式約定
3. 添加 TypeScript 類型定義

### 狀態管理

使用 Svelte 的內建 stores：

```typescript
import { writable } from 'svelte/store';

export const myStore = writable(initialValue);
```

### 樣式規範

- 使用 Tailwind CSS 原子化樣式
- 遵循 BEM 命名約定的自定義類
- 保持樣式一致性

## 📦 依賴說明

### 核心依賴

- **SvelteKit**: 全棧框架
- **Tailwind CSS**: 原子化 CSS
- **Axios**: HTTP 客戶端
- **Lucide Svelte**: 圖標庫
- **svelte-french-toast**: 通知組件

### 開發依賴

- **TypeScript**: 類型安全
- **Vite**: 建構工具
- **ESLint**: 代碼檢查
- **Prettier**: 代碼格式化

## 🔧 配置文件

- `svelte.config.js`: SvelteKit 配置
- `vite.config.js`: Vite 配置和代理設置
- `tailwind.config.js`: Tailwind CSS 配置
- `tsconfig.json`: TypeScript 配置

## 🚢 部署

### Docker 部署

```bash
# 建構 Docker 映像
docker build -t admin-frontend .

# 運行容器
docker run -p 3000:80 admin-frontend
```

### 靜態部署

建構後的檔案位於 `build/` 目錄，可部署到任何靜態文件服務器。

## 🐛 故障排除

### 常見問題

1. **API 連接失敗**
   - 檢查 `.env` 中的 `VITE_API_URL`
   - 確認後端服務運行正常

2. **路由不工作**
   - 檢查伺服器是否支援 SPA 路由
   - 確認 nginx 配置正確

3. **樣式問題**
   - 清除瀏覽器快取
   - 檢查 Tailwind CSS 是否正確載入

### 調試工具

- 瀏覽器開發者工具
- SvelteKit 開發模式日誌
- Network 標籤查看 API 請求

## 📚 參考資源

- [SvelteKit 文檔](https://kit.svelte.dev/docs)
- [Tailwind CSS 文檔](https://tailwindcss.com/docs)
- [Lucide 圖標](https://lucide.dev/)
- [MDN Web 文檔](https://developer.mozilla.org/)

---

**開發愉快！** 🎉