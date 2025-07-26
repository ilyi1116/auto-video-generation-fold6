# 測試策略實施計劃

## 🎯 測試目標

為重構後的組件庫和頁面建立全面的測試覆蓋，確保代碼品質和穩定性。

## 📊 測試金字塔

### 1. 單元測試 (70%) - Vitest + Testing Library
```javascript
// Button.test.js
import { render, fireEvent } from '@testing-library/svelte';
import Button from '$lib/components/ui/Button.svelte';

describe('Button Component', () => {
  test('renders with correct variant', () => {
    const { getByRole } = render(Button, {
      props: { variant: 'primary' }
    });
    
    const button = getByRole('button');
    expect(button).toHaveClass('bg-primary-600');
  });

  test('handles click events', async () => {
    const mockClick = vi.fn();
    const { getByRole } = render(Button, {
      props: { onClick: mockClick }
    });
    
    await fireEvent.click(getByRole('button'));
    expect(mockClick).toHaveBeenCalledOnce();
  });
});
```

### 2. 整合測試 (20%) - Testing Library
```javascript
// ScriptGenerator.test.js
import { render, fireEvent, waitFor } from '@testing-library/svelte';
import ScriptGenerator from '$lib/components/ai/script/ScriptGenerator.svelte';

describe('ScriptGenerator Integration', () => {
  test('generates script when form is submitted', async () => {
    const { getByLabelText, getByText } = render(ScriptGenerator);
    
    await fireEvent.input(getByLabelText('Video Topic'), {
      target: { value: 'AI productivity tools' }
    });
    
    await fireEvent.click(getByText('Generate Script'));
    
    await waitFor(() => {
      expect(getByText('Generating...')).toBeInTheDocument();
    });
  });
});
```

### 3. 端對端測試 (10%) - Playwright
```javascript
// e2e/video-creation.spec.js
import { test, expect } from '@playwright/test';

test('complete video creation workflow', async ({ page }) => {
  await page.goto('/create');
  
  // Step 1: Project Setup
  await page.fill('[data-testid="project-title"]', 'Test Video');
  await page.click('[data-testid="next-step"]');
  
  // Step 2: Script Generation
  await page.fill('[data-testid="script-topic"]', 'AI tools');
  await page.click('[data-testid="generate-script"]');
  await expect(page.locator('[data-testid="generated-script"]')).toBeVisible();
  
  // Continue workflow...
});
```

## 🛠️ 測試工具配置

### package.json 依賴
```json
{
  "devDependencies": {
    "@testing-library/svelte": "^4.0.0",
    "@testing-library/jest-dom": "^6.0.0",
    "@playwright/test": "^1.40.0",
    "vitest": "^1.0.0",
    "jsdom": "^23.0.0",
    "msw": "^2.0.0"
  },
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

### Vitest 配置
```javascript
// vitest.config.js
import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte({ hot: !process.env.VITEST })],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.js'],
    coverage: {
      reporter: ['text', 'html', 'lcov'],
      threshold: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80
        }
      }
    }
  }
});
```

## 📋 測試實施優先級

### 第一階段: 核心組件測試
1. **UI 組件庫** (12 個組件)
   - Button, Input, Select, Card 等
   - 目標覆蓋率: 90%

2. **Hook 系統**
   - useApi, useForm
   - 目標覆蓋率: 95%

### 第二階段: 業務邏輯測試
1. **API 客戶端**
   - 請求/響應處理
   - 錯誤處理和重試邏輯

2. **表單驗證**
   - 驗證規則測試
   - 錯誤信息顯示

### 第三階段: 頁面整合測試
1. **主要用戶流程**
   - 影片創建流程
   - AI 工具使用流程
   - 專案管理流程

2. **E2E 關鍵路徑**
   - 用戶註冊/登入
   - 完整影片製作流程

## 🎯 品質門檻

- **單元測試覆蓋率**: ≥ 80%
- **整合測試覆蓋率**: ≥ 70%
- **E2E 測試**: 覆蓋 5 個主要用戶流程
- **所有測試**: 在 CI/CD 中必須通過