# 🎨 SvelteKit 前端設計系統 v1.0

基於設計 Tokens 的現代化 UI 組件庫，提供一致、可訪問、高性能的用戶界面組件。

## ✨ 特性

- 🎯 **統一設計 Tokens** - 一致的顏色、字體、間距、動畫系統
- 🧩 **模組化組件** - 可復用的標準化 UI 組件
- ⚡ **性能監控** - 內建 Web Vitals 性能追蹤
- 🔧 **開發工具** - 強大的調試和開發體驗工具
- 📱 **響應式設計** - 完整的響應式和無障礙支援
- 🌗 **深色模式** - 內建深色模式支援

## 📁 專案結構

```
src/
├── lib/
│   ├── design/
│   │   └── tokens.js              # 設計 Tokens 定義
│   ├── components/ui/
│   │   ├── Button.svelte          # 按鈕組件
│   │   ├── Input.svelte           # 輸入框組件  
│   │   ├── Card.svelte            # 卡片組件
│   │   ├── LazyImage.svelte       # 懶載入圖片組件
│   │   ├── VirtualGrid.svelte     # 虛擬滾動網格
│   │   ├── GlobalLoading.svelte   # 全域載入組件
│   │   ├── GlobalError.svelte     # 全域錯誤組件
│   │   └── index.js              # 組件庫入口
│   ├── performance/
│   │   └── vitals.js             # Web Vitals 監控
│   └── dev/
│       └── debugTools.js         # 開發調試工具
├── routes/
│   ├── docs/                     # 組件庫文檔 (開發環境)
│   └── +layout.svelte           # 主布局 (整合性能監控)
└── app.css                      # 全域樣式
```

## 🚀 快速開始

### 1. 安裝依賴

確保已安裝所需依賴：

```bash
npm install
```

### 2. 開發環境

啟動開發服務器：

```bash
npm run dev
```

### 3. 訪問組件文檔

開發環境下訪問：`http://localhost:5173/docs`

查看完整的組件庫文檔和示例。

## 🎨 設計 Tokens

### 引入方式

```javascript
import { tokens, getColor, getSpacing } from '$lib/components/ui/index.js';

// 使用顏色
const primaryColor = getColor('primary.500');

// 使用間距
const spacing = getSpacing('4');
```

### 主要 Tokens

```javascript
// 顏色系統
tokens.colors = {
  primary: { 50: '#eff6ff', 500: '#3b82f6', 900: '#1e3a8a' },
  secondary: { /* ... */ },
  semantic: {
    success: { /* ... */ },
    warning: { /* ... */ },
    error: { /* ... */ }
  }
}

// 字體系統
tokens.typography = {
  fontFamily: { sans: ['Inter', ...], mono: [...] },
  fontSize: { xs: '0.75rem', sm: '0.875rem', /* ... */ }
}

// 間距系統
tokens.spacing = { 1: '0.25rem', 2: '0.5rem', /* ... */ }
```

## 🧩 核心組件

### Button 組件

```svelte
<script>
  import { Button } from '$lib/components/ui/index.js';
</script>

<!-- 基礎用法 -->
<Button variant="primary" size="md">
  點擊我
</Button>

<!-- 載入狀態 -->
<Button variant="primary" loading>
  載入中...
</Button>

<!-- 禁用狀態 -->
<Button variant="secondary" disabled>
  禁用按鈕
</Button>

<!-- 全寬度 -->
<Button variant="outline" fullWidth>
  全寬度按鈕
</Button>
```

**Props:**
- `variant`: `'primary' | 'secondary' | 'outline' | 'ghost' | 'destructive'`
- `size`: `'xs' | 'sm' | 'md' | 'lg' | 'xl'`
- `disabled`: `boolean`
- `loading`: `boolean`
- `fullWidth`: `boolean`
- `href`: `string` (渲染為連結)

### Input 組件

```svelte
<script>
  import { Input } from '$lib/components/ui/index.js';
  let value = '';
</script>

<!-- 基礎輸入框 -->
<Input 
  label="用戶名"
  placeholder="請輸入用戶名"
  bind:value
/>

<!-- 錯誤狀態 -->
<Input 
  label="電子郵件"
  type="email"
  error="請輸入有效的電子郵件地址"
/>

<!-- 文本域 -->
<Input 
  type="textarea"
  label="描述"
  rows={4}
  maxlength={200}
/>
```

**Props:**
- `type`: `'text' | 'email' | 'password' | 'textarea' | ...`
- `variant`: `'default' | 'filled' | 'borderless'`
- `size`: `'sm' | 'md' | 'lg'`
- `label`: `string`
- `error`: `string`
- `hint`: `string`
- `disabled`: `boolean`

### Card 組件

```svelte
<script>
  import { Card } from '$lib/components/ui/index.js';
</script>

<!-- 基礎卡片 -->
<Card variant="default">
  <h3>卡片標題</h3>
  <p>卡片內容...</p>
</Card>

<!-- 互動卡片 -->
<Card variant="elevated" interactive clickable on:click={handleClick}>
  <h3>可點擊卡片</h3>
</Card>
```

**Props:**
- `variant`: `'default' | 'elevated' | 'outlined' | 'filled'`
- `size`: `'sm' | 'md' | 'lg' | 'xl' | 'full'`
- `padding`: `'none' | 'sm' | 'default' | 'lg' | 'xl'`
- `interactive`: `boolean`
- `clickable`: `boolean`

## 📊 性能監控

### Web Vitals 監控

系統自動收集以下性能指標：

- **LCP** - Largest Contentful Paint (最大內容繪製)
- **FID** - First Input Delay (首次輸入延遲)  
- **CLS** - Cumulative Layout Shift (累積佈局位移)
- **FCP** - First Contentful Paint (首次內容繪製)
- **TTFB** - Time to First Byte (首位元組時間)
- **INP** - Interaction to Next Paint (交互到下次繪製)

### 開發環境監控

在開發環境下，右下角會顯示實時性能監控小工具。

### 自定義監控

```javascript
import { vitals } from '$lib/performance/vitals.js';

// 記錄自定義指標
vitals.record('user_action', 150, { action: 'button_click' });

// 記錄用戶互動
vitals.interaction('click', buttonElement, 50);

// 記錄頁面導航
vitals.navigation('/home', '/profile', 200);
```

## 🔧 開發工具

### 調試工具

開發環境下自動載入調試工具，提供以下功能：

#### 鍵盤快捷鍵

- `Ctrl/Cmd + Shift + D`: 顯示調試面板
- `Ctrl/Cmd + Shift + G`: 切換網格線
- `Ctrl/Cmd + Shift + C`: 高亮組件邊界

#### 控制台指令

```javascript
// 顯示系統信息
debugTools.showInfo()

// 顯示日誌
debugTools.showLogs()

// 導出日誌
debugTools.exportLogs()

// 切換網格線
debugTools.toggleGrid()

// 高亮組件
debugTools.highlightComponents()
```

### 組件追蹤

```javascript
import debugTools from '$lib/dev/debugTools.js';

// 追蹤組件載入
debugTools.trackComponent('MyComponent', this);

// 性能計時
debugTools.startTimer('data_fetch');
await fetchData();
debugTools.endTimer('data_fetch');
```

## 📱 響應式設計

### 斷點系統

```javascript
// 設計 tokens 中定義的斷點
tokens.breakpoints = {
  xs: '475px',   // 小型手機
  sm: '640px',   // 手機
  md: '768px',   // 平板
  lg: '1024px',  // 小型桌面
  xl: '1280px',  // 桌面
  '2xl': '1536px' // 大型桌面
}
```

### 響應式工具

```javascript
import { themeUtils } from '$lib/components/ui/index.js';

// 響應式類名
const classes = themeUtils.responsive({
  base: 'text-sm',
  md: 'text-base', 
  lg: 'text-lg'
});
// 結果: 'text-sm md:text-base lg:text-lg'
```

## 🌗 深色模式

### 配置

深色模式通過 Tailwind CSS 的 `class` 策略實現：

```javascript
// tailwind.config.js
export default {
  darkMode: 'class',
  // ...
}
```

### 使用方式

```svelte
<!-- 自動響應深色模式的組件 -->
<div class="bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100">
  內容會自動適應深色模式
</div>
```

## 🧪 測試

### 運行測試

```bash
# 單元測試
npm run test:unit

# 組件測試  
npm run test:component

# E2E 測試
npm run test:e2e

# 測試覆蓋率
npm run test:coverage
```

### 測試組件

```javascript
import { render, screen } from '@testing-library/svelte';
import { Button } from '$lib/components/ui/index.js';

test('Button renders correctly', () => {
  render(Button, { props: { variant: 'primary' } });
  expect(screen.getByRole('button')).toBeInTheDocument();
});
```

## 📦 建置與部署

### 建置應用

```bash
# 生產建置
npm run build

# 預覽建置結果
npm run preview

# 分析 bundle 大小
npm run build:analyze
```

### 性能優化

- ✅ **Tree Shaking** - 自動移除未使用的程式碼
- ✅ **Code Splitting** - 按需載入組件
- ✅ **Image Optimization** - LazyImage 組件自動優化
- ✅ **Virtual Scrolling** - VirtualGrid 處理大型列表
- ✅ **Bundle Analysis** - 內建 bundle 分析

## 🔄 遷移指南

### 從舊組件遷移

```javascript
// 舊方式
import Button from '$lib/components/Button.svelte';

// 新方式  
import { Button } from '$lib/components/ui/index.js';
```

### Tailwind 類名更新

系統現在使用統一的設計 tokens：

```css
/* 舊方式 */
.bg-blue-500 { }

/* 新方式 - 使用設計 tokens */  
.bg-primary-500 { }
```

## 📚 最佳實踐

### 組件設計

1. **一致性** - 始終使用設計系統中的組件和 tokens
2. **可訪問性** - 確保所有互動元素都有適當的 ARIA 屬性
3. **性能** - 使用 LazyImage 和 VirtualGrid 處理大量內容
4. **響應式** - 考慮所有設備和屏幕尺寸

### 開發流程

1. **組件優先** - 優先使用現有組件，避免重複造輪子
2. **測試驅動** - 為自定義組件編寫測試
3. **性能監控** - 利用內建的性能工具持續優化
4. **文檔更新** - 新組件需要在 `/docs` 中添加示例

### 性能優化

1. **懶載入** - 使用 LazyImage 組件處理圖片
2. **虛擬化** - 大型列表使用 VirtualGrid
3. **監控** - 持續關注 Web Vitals 指標
4. **分析** - 定期使用 bundle 分析工具

## 🤝 貢獻指南

### 添加新組件

1. 在 `src/lib/components/ui/` 中創建組件
2. 使用設計 tokens 定義樣式
3. 在 `index.js` 中導出
4. 在 `/docs` 中添加文檔和示例
5. 編寫測試

### 更新設計 Tokens

1. 修改 `src/lib/design/tokens.js`
2. 更新 Tailwind 配置
3. 更新組件文檔
4. 驗證所有組件仍正常工作

## ❓ 常見問題

### Q: 如何自定義主題顏色？

A: 修改 `tokens.js` 中的顏色定義，系統會自動更新所有組件。

### Q: 性能監控數據如何使用？

A: 開發環境下可以在控制台查看，生產環境會發送到配置的分析端點。

### Q: 如何禁用調試工具？

A: 調試工具只在開發環境（`dev = true`）下載入，生產環境自動禁用。

### Q: 組件不響應深色模式怎麼辦？

A: 確保使用了 `dark:` 前綴的 Tailwind 類名，或使用組件庫中的標準化組件。

## 📄 授權

MIT License - 查看 LICENSE 文件了解更多詳情。

---

🎉 **恭喜！** 您現在擁有一個完整的、生產就緒的設計系統。

如需更多幫助，請查看 `/docs` 頁面的實時示例或聯繫開發團隊。