/**
 * 完整影片生成流程端對端測試
 * 測試從登入到影片生成完成的完整用戶旅程
 */

import { test, expect } from "@playwright/test";

test.describe("影片生成完整流程", () => {
  test.beforeEach(async ({ page }) => {
    // 設置 API 模擬回應
    await page.route("/api/auth/login", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user: { id: 1, name: "Test User", email: "test@example.com" },
          tokens: { access_token: "test-token" },
        }),
      });
    });

    // 登入用戶
    await page.goto("/login");
    await page.fill('[data-testid="email-input"]', "test@example.com");
    await page.fill('[data-testid="password-input"]', "password123");
    await page.click('[data-testid="login-button"]');
    await page.waitForURL("/dashboard");
  });

  test("應該完成完整的影片生成流程", async ({ page }) => {
    // Step 1: 創建新專案
    await page.click('[data-testid="create-project-button"]');
    await page.fill('[data-testid="project-name-input"]', "測試影片專案");
    await page.fill('[data-testid="project-description-input"]', "這是一個測試專案");
    await page.click('[data-testid="save-project-button"]');

    // 等待專案創建完成
    await expect(page.locator('[data-testid="project-card"]')).toBeVisible();

    // Step 2: 進入專案
    await page.click('[data-testid="project-card"]');
    await expect(page).toHaveURL(/\/projects\/\d+/);

    // Step 3: 上傳聲音檔案
    await page.click('[data-testid="upload-audio-button"]');
    
    // 模擬檔案上傳
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-audio.mp3',
      mimeType: 'audio/mpeg',
      buffer: Buffer.from('fake audio content')
    });

    // 設置檔案上傳 API 模擬
    await page.route("/api/upload/audio", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          file_id: "audio123",
          url: "/uploads/audio123.mp3",
          duration: 120,
        }),
      });
    });

    await expect(page.locator('[data-testid="audio-upload-success"]')).toBeVisible();

    // Step 4: 生成腳本
    await page.click('[data-testid="generate-script-button"]');
    await page.fill('[data-testid="script-prompt-input"]', "生成一個關於科技創新的短影片腳本");

    // 模擬 AI 腳本生成 API
    await page.route("/api/ai/generate-script", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          script: "在這個數位時代，科技創新正在改變我們的生活方式...",
          scenes: [
            { id: 1, text: "科技創新的重要性", duration: 5 },
            { id: 2, text: "人工智慧的應用", duration: 8 },
            { id: 3, text: "未來的發展趨勢", duration: 7 }
          ]
        }),
      });
    });

    await page.click('[data-testid="confirm-generate-script"]');
    await expect(page.locator('[data-testid="script-content"]')).toBeVisible();

    // Step 5: 選擇影片樣式
    await page.click('[data-testid="video-style-modern"]');
    await page.click('[data-testid="color-scheme-blue"]');
    await page.selectOption('[data-testid="resolution-select"]', "1920x1080");

    // Step 6: 開始影片生成
    await page.click('[data-testid="start-video-generation"]');

    // 模擬影片生成 API
    await page.route("/api/video/generate", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          job_id: "video_job_123",
          status: "processing",
          estimated_time: 300,
        }),
      });
    });

    // 驗證生成開始
    await expect(page.locator('[data-testid="generation-progress"]')).toBeVisible();
    await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();

    // 模擬生成進度更新
    await page.route("/api/video/status/video_job_123", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "completed",
          progress: 100,
          result: {
            video_url: "/videos/completed_video_123.mp4",
            thumbnail_url: "/thumbnails/thumb_123.jpg",
            duration: 20,
          }
        }),
      });
    });

    // 等待生成完成
    await expect(page.locator('[data-testid="generation-complete"]')).toBeVisible({
      timeout: 10000
    });

    // Step 7: 預覽和下載影片
    await expect(page.locator('[data-testid="video-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="download-video-button"]')).toBeVisible();

    // 測試影片預覽功能
    await page.click('[data-testid="play-preview-button"]');
    await expect(page.locator('video')).toBeVisible();

    // 測試下載功能
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="download-video-button"]');
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toBe('test-video.mp4');
  });

  test("應該處理影片生成失敗情況", async ({ page }) => {
    // 創建專案並上傳音頻
    await page.click('[data-testid="create-project-button"]');
    await page.fill('[data-testid="project-name-input"]', "失敗測試專案");
    await page.click('[data-testid="save-project-button"]');
    await page.click('[data-testid="project-card"]');

    // 模擬影片生成失敗
    await page.route("/api/video/generate", (route) => {
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          error: "影片生成失敗",
          message: "服務器內部錯誤",
        }),
      });
    });

    // 嘗試生成影片
    await page.click('[data-testid="start-video-generation"]');

    // 驗證錯誤處理
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText("影片生成失敗");
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
  });

  test("應該支援多種音頻格式", async ({ page }) => {
    await page.click('[data-testid="create-project-button"]');
    await page.fill('[data-testid="project-name-input"]', "音頻格式測試");
    await page.click('[data-testid="save-project-button"]');
    await page.click('[data-testid="project-card"]');

    // 測試支援的音頻格式
    const audioFormats = [
      { name: 'test.mp3', mimeType: 'audio/mpeg' },
      { name: 'test.wav', mimeType: 'audio/wav' },
      { name: 'test.m4a', mimeType: 'audio/mp4' },
    ];

    for (const format of audioFormats) {
      await page.click('[data-testid="upload-audio-button"]');
      
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles({
        name: format.name,
        mimeType: format.mimeType,
        buffer: Buffer.from('fake audio content')
      });

      await page.route("/api/upload/audio", (route) => {
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            file_id: `audio_${Date.now()}`,
            url: `/uploads/${format.name}`,
            format: format.mimeType,
          }),
        });
      });

      await expect(page.locator('[data-testid="audio-upload-success"]')).toBeVisible();
      
      // 清除當前音頻以測試下一個格式
      await page.click('[data-testid="remove-audio-button"]');
    }
  });

  test("應該顯示生成進度和預估時間", async ({ page }) => {
    // 設置專案
    await page.click('[data-testid="create-project-button"]');
    await page.fill('[data-testid="project-name-input"]', "進度測試專案");
    await page.click('[data-testid="save-project-button"]');
    await page.click('[data-testid="project-card"]');

    // 模擬逐步進度更新
    let progressStep = 0;
    const progressSteps = [
      { progress: 20, status: "分析音頻中..." },
      { progress: 40, status: "生成腳本中..." },
      { progress: 60, status: "創建場景中..." },
      { progress: 80, status: "渲染影片中..." },
      { progress: 100, status: "完成!" }
    ];

    await page.route("/api/video/status/video_job_123", (route) => {
      const currentStep = progressSteps[progressStep % progressSteps.length];
      progressStep++;
      
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: progressStep >= progressSteps.length ? "completed" : "processing",
          progress: currentStep.progress,
          message: currentStep.status,
          estimated_time_remaining: Math.max(0, (100 - currentStep.progress) * 2),
        }),
      });
    });

    // 開始生成
    await page.click('[data-testid="start-video-generation"]');

    // 驗證進度顯示
    await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();
    await expect(page.locator('[data-testid="progress-text"]')).toBeVisible();
    await expect(page.locator('[data-testid="estimated-time"]')).toBeVisible();

    // 等待完成
    await expect(page.locator('[data-testid="generation-complete"]')).toBeVisible({
      timeout: 15000
    });
  });

  test("應該支援批次處理多個專案", async ({ page }) => {
    // 創建多個專案
    const projects = ["專案1", "專案2", "專案3"];
    
    for (const projectName of projects) {
      await page.click('[data-testid="create-project-button"]');
      await page.fill('[data-testid="project-name-input"]', projectName);
      await page.click('[data-testid="save-project-button"]');
      await expect(page.locator(`[data-testid="project-${projectName}"]`)).toBeVisible();
    }

    // 選擇多個專案進行批次處理
    for (const projectName of projects) {
      await page.check(`[data-testid="checkbox-${projectName}"]`);
    }

    // 開始批次生成
    await page.click('[data-testid="batch-generate-button"]');

    // 模擬批次處理 API
    await page.route("/api/video/batch-generate", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          batch_id: "batch_123",
          jobs: projects.map((name, index) => ({
            project_name: name,
            job_id: `job_${index}`,
            status: "queued"
          }))
        }),
      });
    });

    // 驗證批次處理界面
    await expect(page.locator('[data-testid="batch-progress-panel"]')).toBeVisible();
    await expect(page.locator('[data-testid="batch-job-list"]')).toBeVisible();
    
    // 驗證每個工作項目都顯示
    for (const projectName of projects) {
      await expect(page.locator(`[data-testid="job-${projectName}"]`)).toBeVisible();
    }
  });
});