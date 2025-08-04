/**
 * 專案創建功能端對端測試
 * 測試完整的影片專案創建流程
 */

import { test, expect } from '@playwright/test';

test.describe('專案創建功能', () => {
  test.beforeEach(async ({ page }) => {
    // 模擬已登入用戶
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('/dashboard');
  });

  test('應該能完成完整的專案創建流程', async ({ page }) => {
    // 前往專案創建頁面
    await page.click('[data-testid="create-project-button"]');
    await page.waitForURL('/create');
    
    // 步驟 1: 專案設定
    await expect(page.locator('[data-testid="step-indicator"]')).toContainText('1 / 5');
    
    await page.fill('[data-testid="project-title"]', '測試影片專案');
    await page.fill('[data-testid="project-description"]', '這是一個測試用的影片專案描述');
    await page.selectOption('[data-testid="target-platform"]', 'youtube');
    await page.selectOption('[data-testid="video-format"]', '16:9');
    
    await page.click('[data-testid="next-button"]');
    
    // 步驟 2: 腳本生成
    await expect(page.locator('[data-testid="step-indicator"]')).toContainText('2 / 5');
    
    await page.fill('[data-testid="script-topic"]', 'AI 技術趨勢');
    await page.selectOption('[data-testid="script-tone"]', 'professional');
    await page.selectOption('[data-testid="script-length"]', 'medium');
    
    // 模擬 AI 腳本生成
    await page.route('/api/ai/script/generate', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          script: '歡迎來到 AI 技術趨勢的介紹。今天我們將探討最新的人工智慧發展...',
          scenes: [
            { id: 1, text: '歡迎來到 AI 技術趨勢的介紹', duration: 3 },
            { id: 2, text: '今天我們將探討最新的人工智慧發展', duration: 5 }
          ]
        })
      });
    });
    
    await page.click('[data-testid="generate-script-button"]');
    await expect(page.locator('[data-testid="generated-script"]')).toBeVisible();
    await page.click('[data-testid="next-button"]');
    
    // 步驟 3: 視覺創建
    await expect(page.locator('[data-testid="step-indicator"]')).toContainText('3 / 5');
    
    await page.selectOption('[data-testid="visual-style"]', 'modern');
    await page.selectOption('[data-testid="color-scheme"]', 'blue');
    
    // 模擬圖像生成
    await page.route('/api/ai/images/generate', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          images: [
            { id: 1, url: '/mock-image-1.jpg', scene_id: 1 },
            { id: 2, url: '/mock-image-2.jpg', scene_id: 2 }
          ]
        })
      });
    });
    
    await page.click('[data-testid="generate-images-button"]');
    await expect(page.locator('[data-testid="generated-images"]')).toBeVisible();
    await page.click('[data-testid="next-button"]');
    
    // 步驟 4: 語音合成
    await expect(page.locator('[data-testid="step-indicator"]')).toContainText('4 / 5');
    
    await page.selectOption('[data-testid="voice-selection"]', 'female-professional');
    await page.selectOption('[data-testid="voice-speed"]', 'normal');
    
    // 模擬語音合成
    await page.route('/api/ai/voice/synthesis', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          audio_files: [
            { id: 1, url: '/mock-audio-1.mp3', scene_id: 1 },
            { id: 2, url: '/mock-audio-2.mp3', scene_id: 2 }
          ]
        })
      });
    });
    
    await page.click('[data-testid="generate-voice-button"]');
    await expect(page.locator('[data-testid="audio-preview"]')).toBeVisible();
    await page.click('[data-testid="next-button"]');
    
    // 步驟 5: 影片組裝
    await expect(page.locator('[data-testid="step-indicator"]')).toContainText('5 / 5');
    
    await page.selectOption('[data-testid="transition-style"]', 'fade');
    await page.selectOption('[data-testid="background-music"]', 'corporate');
    
    // 模擬影片生成
    await page.route('/api/ai/video/assembly', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          video_url: '/mock-video.mp4',
          thumbnail_url: '/mock-thumbnail.jpg',
          duration: 45,
          status: 'completed'
        })
      });
    });
    
    await page.click('[data-testid="create-video-button"]');
    
    // 等待影片生成完成
    await expect(page.locator('[data-testid="video-preview"]')).toBeVisible({ timeout: 30000 });
    
    // 驗證專案創建成功
    await expect(page.locator('[data-testid="success-message"]')).toContainText('專案創建成功');
    
    // 前往專案列表驗證
    await page.click('[data-testid="view-project-button"]');
    await page.waitForURL('/projects/*');
    
    await expect(page.locator('[data-testid="project-title"]')).toContainText('測試影片專案');
  });

  test('應該能保存草稿並稍後繼續', async ({ page }) => {
    // 前往專案創建頁面
    await page.click('[data-testid="create-project-button"]');
    await page.waitForURL('/create');
    
    // 填寫部分資訊
    await page.fill('[data-testid="project-title"]', '草稿專案');
    await page.fill('[data-testid="project-description"]', '這是一個草稿專案');
    
    // 保存草稿
    await page.click('[data-testid="save-draft-button"]');
    
    // 驗證草稿保存成功
    await expect(page.locator('[data-testid="draft-saved-message"]')).toBeVisible();
    
    // 離開頁面
    await page.goto('/dashboard');
    
    // 驗證草稿顯示在儀表板
    await expect(page.locator('[data-testid="draft-projects"] >> text=草稿專案')).toBeVisible();
    
    // 繼續編輯草稿
    await page.click('[data-testid="draft-projects"] >> text=草稿專案');
    await page.waitForURL('/create');
    
    // 驗證資料已保存
    await expect(page.locator('[data-testid="project-title"]')).toHaveValue('草稿專案');
    await expect(page.locator('[data-testid="project-description"]')).toHaveValue('這是一個草稿專案');
  });

  test('應該處理 AI 服務錯誤', async ({ page }) => {
    await page.click('[data-testid="create-project-button"]');
    await page.waitForURL('/create');
    
    // 填寫專案資訊並繼續到腳本生成
    await page.fill('[data-testid="project-title"]', '錯誤測試專案');
    await page.click('[data-testid="next-button"]');
    
    // 模擬 AI 服務錯誤
    await page.route('/api/ai/script/generate', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'AI 服務暫時不可用',
          code: 'AI_SERVICE_ERROR'
        })
      });
    });
    
    await page.fill('[data-testid="script-topic"]', 'AI 技術');
    await page.click('[data-testid="generate-script-button"]');
    
    // 驗證錯誤處理
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('AI 服務暫時不可用');
    
    // 驗證重試按鈕
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test('應該支援步驟間的導航', async ({ page }) => {
    await page.click('[data-testid="create-project-button"]');
    await page.waitForURL('/create');
    
    // 填寫第一步並前進
    await page.fill('[data-testid="project-title"]', '導航測試專案');
    await page.click('[data-testid="next-button"]');
    
    // 驗證在第二步
    await expect(page.locator('[data-testid="step-indicator"]')).toContainText('2 / 5');
    
    // 返回第一步
    await page.click('[data-testid="previous-button"]');
    await expect(page.locator('[data-testid="step-indicator"]')).toContainText('1 / 5');
    
    // 驗證資料保留
    await expect(page.locator('[data-testid="project-title"]')).toHaveValue('導航測試專案');
    
    // 使用步驟指示器直接跳轉
    await page.click('[data-testid="step-2-indicator"]');
    await expect(page.locator('[data-testid="step-indicator"]')).toContainText('2 / 5');
  });

  test('應該在載入時顯示進度指示器', async ({ page }) => {
    await page.click('[data-testid="create-project-button"]');
    await page.waitForURL('/create');
    
    // 填寫資訊並前進到腳本生成
    await page.fill('[data-testid="project-title"]', '載入測試專案');
    await page.click('[data-testid="next-button"]');
    
    // 模擬慢速 AI 回應
    let resolveResponse;
    const responsePromise = new Promise(resolve => {
      resolveResponse = resolve;
    });
    
    await page.route('/api/ai/script/generate', async route => {
      await responsePromise;
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          script: '生成的腳本內容...'
        })
      });
    });
    
    await page.fill('[data-testid="script-topic"]', 'AI 技術');
    await page.click('[data-testid="generate-script-button"]');
    
    // 驗證載入狀態
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible();
    await expect(page.locator('[data-testid="generate-script-button"]')).toBeDisabled();
    
    // 完成請求
    resolveResponse();
    
    // 驗證載入完成
    await expect(page.locator('[data-testid="loading-spinner"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="generated-script"]')).toBeVisible();
  });

  test('應該支援手機版面的專案創建', async ({ page }) => {
    // 設置手機視窗
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.click('[data-testid="create-project-button"]');
    await page.waitForURL('/create');
    
    // 驗證手機版面元素可見且可操作
    await expect(page.locator('[data-testid="project-title"]')).toBeVisible();
    await expect(page.locator('[data-testid="step-indicator"]')).toBeVisible();
    
    // 驗證步驟導航在手機版面正常工作
    await page.fill('[data-testid="project-title"]', '手機測試專案');
    await page.click('[data-testid="next-button"]');
    
    await expect(page.locator('[data-testid="step-indicator"]')).toContainText('2 / 5');
    
    // 驗證表單元素大小適合觸控
    const titleInput = await page.locator('[data-testid="project-title"]').boundingBox();
    expect(titleInput.height).toBeGreaterThanOrEqual(44);
  });
});