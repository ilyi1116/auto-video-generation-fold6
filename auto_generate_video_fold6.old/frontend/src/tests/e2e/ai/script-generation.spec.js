/**
 * AI 腳本生成功能端對端測試
 * 測試 AI 腳本生成的完整用戶流程
 */

import { test, expect } from '@playwright/test';

test.describe('AI 腳本生成功能', () => {
  test.beforeEach(async ({ page }) => {
    // 模擬已登入用戶
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'test@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('/dashboard');
    
    // 前往 AI 腳本生成頁面
    await page.click('[data-testid="ai-tools-menu"]');
    await page.click('[data-testid="script-generator-link"]');
    await page.waitForURL('/ai/script');
  });

  test('應該能生成基本腳本', async ({ page }) => {
    // 模擬 AI API 回應
    await page.route('/api/ai/script/generate', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          script: {
            title: '科技趨勢分析',
            content: '歡迎來到今天的科技趨勢分析。在這個快速發展的數位時代，我們看到了許多令人興奮的技術突破...',
            scenes: [
              {
                id: 1,
                text: '歡迎來到今天的科技趨勢分析',
                duration: 3,
                type: 'intro'
              },
              {
                id: 2,
                text: '在這個快速發展的數位時代，我們看到了許多令人興奮的技術突破',
                duration: 8,
                type: 'content'
              },
              {
                id: 3,
                text: '感謝您的觀看，我們下次見',
                duration: 3,
                type: 'outro'
              }
            ],
            metadata: {
              duration: 14,
              word_count: 156,
              reading_time: '1分14秒'
            }
          }
        })
      });
    });

    // 填寫腳本生成表單
    await page.fill('[data-testid="topic-input"]', '科技趨勢分析');
    await page.selectOption('[data-testid="platform-select"]', 'youtube');
    await page.selectOption('[data-testid="duration-select"]', 'short');
    await page.selectOption('[data-testid="tone-select"]', 'professional');
    
    // 點擊生成按鈕
    await page.click('[data-testid="generate-button"]');
    
    // 驗證載入狀態
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible();
    await expect(page.locator('[data-testid="generate-button"]')).toBeDisabled();
    
    // 驗證腳本生成結果
    await expect(page.locator('[data-testid="generated-script"]')).toBeVisible();
    await expect(page.locator('[data-testid="script-title"]')).toContainText('科技趨勢分析');
    await expect(page.locator('[data-testid="script-content"]')).toContainText('歡迎來到今天的科技趨勢分析');
    
    // 驗證場景顯示
    await expect(page.locator('[data-testid="scene-1"]')).toBeVisible();
    await expect(page.locator('[data-testid="scene-2"]')).toBeVisible();
    await expect(page.locator('[data-testid="scene-3"]')).toBeVisible();
    
    // 驗證元數據顯示
    await expect(page.locator('[data-testid="script-duration"]')).toContainText('14');
    await expect(page.locator('[data-testid="word-count"]')).toContainText('156');
    await expect(page.locator('[data-testid="reading-time"]')).toContainText('1分14秒');
  });

  test('應該能編輯生成的腳本', async ({ page }) => {
    // 先生成腳本
    await page.route('/api/ai/script/generate', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          script: {
            title: '測試腳本',
            content: '這是原始腳本內容',
            scenes: [
              { id: 1, text: '原始場景內容', duration: 5, type: 'content' }
            ]
          }
        })
      });
    });

    await page.fill('[data-testid="topic-input"]', '測試主題');
    await page.click('[data-testid="generate-button"]');
    await expect(page.locator('[data-testid="generated-script"]')).toBeVisible();
    
    // 切換到編輯模式
    await page.click('[data-testid="edit-script-button"]');
    
    // 編輯腳本標題
    await page.fill('[data-testid="editable-title"]', '編輯後的腳本標題');
    
    // 編輯場景內容
    await page.click('[data-testid="edit-scene-1"]');
    await page.fill('[data-testid="scene-text-editor"]', '編輯後的場景內容');
    await page.click('[data-testid="save-scene-button"]');
    
    // 保存腳本
    await page.click('[data-testid="save-script-button"]');
    
    // 驗證編輯結果
    await expect(page.locator('[data-testid="script-title"]')).toContainText('編輯後的腳本標題');
    await expect(page.locator('[data-testid="scene-1"]')).toContainText('編輯後的場景內容');
    
    // 驗證保存成功訊息
    await expect(page.locator('[data-testid="save-success-message"]')).toBeVisible();
  });

  test('應該能添加和刪除場景', async ({ page }) => {
    // 先生成基本腳本
    await page.route('/api/ai/script/generate', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          script: {
            title: '場景測試腳本',
            scenes: [
              { id: 1, text: '第一個場景', duration: 5, type: 'intro' }
            ]
          }
        })
      });
    });

    await page.fill('[data-testid="topic-input"]', '場景測試');
    await page.click('[data-testid="generate-button"]');
    await expect(page.locator('[data-testid="generated-script"]')).toBeVisible();
    
    // 進入編輯模式
    await page.click('[data-testid="edit-script-button"]');
    
    // 添加新場景
    await page.click('[data-testid="add-scene-button"]');
    await page.fill('[data-testid="new-scene-text"]', '新添加的場景');
    await page.selectOption('[data-testid="new-scene-type"]', 'content');
    await page.click('[data-testid="confirm-add-scene"]');
    
    // 驗證新場景已添加
    await expect(page.locator('[data-testid="scene-2"]')).toBeVisible();
    await expect(page.locator('[data-testid="scene-2"]')).toContainText('新添加的場景');
    
    // 刪除第一個場景
    await page.click('[data-testid="delete-scene-1"]');
    await page.click('[data-testid="confirm-delete"]');
    
    // 驗證場景已刪除
    await expect(page.locator('[data-testid="scene-1"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="scene-2"]')).toBeVisible();
  });

  test('應該能使用趨勢主題建議', async ({ page }) => {
    // 模擬趨勢主題 API
    await page.route('/api/trends/topics', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          trending_topics: [
            {
              id: 1,
              topic: 'ChatGPT 最新功能',
              category: 'technology',
              growth: 245,
              difficulty: 'medium'
            },
            {
              id: 2,
              topic: '2024 網路安全趨勢',
              category: 'technology',
              growth: 189,
              difficulty: 'hard'
            },
            {
              id: 3,
              topic: '居家辦公生產力技巧',
              category: 'lifestyle',
              growth: 156,
              difficulty: 'easy'
            }
          ]
        })
      });
    });

    // 點擊趨勢主題按鈕
    await page.click('[data-testid="trending-topics-button"]');
    
    // 驗證趨勢主題顯示
    await expect(page.locator('[data-testid="trending-topics-modal"]')).toBeVisible();
    await expect(page.locator('[data-testid="topic-1"]')).toContainText('ChatGPT 最新功能');
    await expect(page.locator('[data-testid="topic-2"]')).toContainText('2024 網路安全趨勢');
    await expect(page.locator('[data-testid="topic-3"]')).toContainText('居家辦公生產力技巧');
    
    // 選擇一個趨勢主題
    await page.click('[data-testid="select-topic-1"]');
    
    // 驗證主題已填入表單
    await expect(page.locator('[data-testid="topic-input"]')).toHaveValue('ChatGPT 最新功能');
    
    // 驗證模態框關閉
    await expect(page.locator('[data-testid="trending-topics-modal"]')).not.toBeVisible();
  });

  test('應該能保存腳本到專案', async ({ page }) => {
    // 生成腳本
    await page.route('/api/ai/script/generate', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          script: {
            title: '保存測試腳本',
            content: '這是要保存的腳本內容',
            scenes: [
              { id: 1, text: '測試場景', duration: 5, type: 'content' }
            ]
          }
        })
      });
    });

    await page.fill('[data-testid="topic-input"]', '保存測試');
    await page.click('[data-testid="generate-button"]');
    await expect(page.locator('[data-testid="generated-script"]')).toBeVisible();
    
    // 模擬保存到專案 API
    await page.route('/api/projects', route => {
      route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          project: {
            id: 123,
            title: '保存測試腳本',
            status: 'draft'
          }
        })
      });
    });

    // 保存到新專案
    await page.click('[data-testid="save-to-project-button"]');
    await page.click('[data-testid="create-new-project-option"]');
    
    // 填寫專案資訊
    await page.fill('[data-testid="project-name-input"]', '保存測試腳本');
    await page.click('[data-testid="confirm-save-button"]');
    
    // 驗證保存成功
    await expect(page.locator('[data-testid="save-success-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="save-success-message"]')).toContainText('腳本已保存到專案');
    
    // 驗證前往專案的連結
    await expect(page.locator('[data-testid="view-project-link"]')).toBeVisible();
  });

  test('應該處理 AI 服務錯誤', async ({ page }) => {
    // 模擬 AI 服務錯誤
    await page.route('/api/ai/script/generate', route => {
      route.fulfill({
        status: 503,
        contentType: 'application/json',
        body: JSON.stringify({
          message: 'AI 服務暫時不可用，請稍後再試',
          code: 'AI_SERVICE_UNAVAILABLE'
        })
      });
    });

    // 嘗試生成腳本
    await page.fill('[data-testid="topic-input"]', '錯誤測試');
    await page.click('[data-testid="generate-button"]');
    
    // 驗證錯誤訊息
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText('AI 服務暫時不可用');
    
    // 驗證重試按鈕
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
    
    // 驗證表單保持可用狀態
    await expect(page.locator('[data-testid="generate-button"]')).not.toBeDisabled();
  });

  test('應該支援腳本模板', async ({ page }) => {
    // 點擊模板按鈕
    await page.click('[data-testid="script-templates-button"]');
    
    // 驗證模板選項顯示
    await expect(page.locator('[data-testid="templates-modal"]')).toBeVisible();
    await expect(page.locator('[data-testid="template-educational"]')).toBeVisible();
    await expect(page.locator('[data-testid="template-entertainment"]')).toBeVisible();
    await expect(page.locator('[data-testid="template-promotional"]')).toBeVisible();
    
    // 選擇教育模板
    await page.click('[data-testid="select-template-educational"]');
    
    // 驗證模板已套用到表單
    await expect(page.locator('[data-testid="tone-select"]')).toHaveValue('educational');
    await expect(page.locator('[data-testid="platform-select"]')).toHaveValue('youtube');
    
    // 驗證模板提示文字
    await expect(page.locator('[data-testid="template-hint"]')).toContainText('教育內容建議');
  });

  test('應該在手機版面正常工作', async ({ page }) => {
    // 設置手機視窗
    await page.setViewportSize({ width: 375, height: 667 });
    
    // 驗證響應式佈局
    await expect(page.locator('[data-testid="topic-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="generate-button"]')).toBeVisible();
    
    // 驗證觸控友好的元素大小
    const generateButton = await page.locator('[data-testid="generate-button"]').boundingBox();
    expect(generateButton.height).toBeGreaterThanOrEqual(44);
    
    // 測試手機版面的腳本生成
    await page.route('/api/ai/script/generate', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          script: {
            title: '手機測試腳本',
            content: '手機版面腳本內容',
            scenes: [{ id: 1, text: '手機測試場景', duration: 5 }]
          }
        })
      });
    });

    await page.fill('[data-testid="topic-input"]', '手機測試');
    await page.click('[data-testid="generate-button"]');
    
    // 驗證結果在手機版面正確顯示
    await expect(page.locator('[data-testid="generated-script"]')).toBeVisible();
    await expect(page.locator('[data-testid="script-title"]')).toContainText('手機測試腳本');
  });
});