import { test, expect } from "@playwright/test";

test.describe("用戶完整流程", () => {
  test.beforeEach(async ({ page }) => {
    // 每個測試前都導向首頁
    await page.goto("/");
  });

  test("完整影片創建流程", async ({ page }) => {
    // 1. 導向影片創建頁面
    await page.click('[data-testid="create-video-button"]');
    await expect(page).toHaveURL("/create");

    // 2. 步驟1：專案設定
    await expect(page.locator('[data-testid="step-indicator-1"]')).toHaveClass(
      /active/,
    );

    await page.fill('[data-testid="project-title"]', "我的測試影片");
    await page.fill(
      '[data-testid="project-description"]',
      "這是一個測試影片的描述",
    );
    await page.selectOption('[data-testid="platform-select"]', "youtube");
    await page.selectOption('[data-testid="video-length"]', "medium");

    await page.click('[data-testid="next-step-button"]');

    // 3. 步驟2：腳本生成
    await expect(page.locator('[data-testid="step-indicator-2"]')).toHaveClass(
      /active/,
    );

    await page.fill('[data-testid="script-topic"]', "人工智慧的未來發展");
    await page.selectOption('[data-testid="script-tone"]', "professional");
    await page.selectOption('[data-testid="script-style"]', "educational");

    await page.click('[data-testid="generate-script-button"]');

    // 等待腳本生成完成
    await expect(page.locator('[data-testid="generated-script"]')).toBeVisible({
      timeout: 30000,
    });
    await expect(
      page.locator('[data-testid="script-content"]'),
    ).not.toBeEmpty();

    await page.click('[data-testid="next-step-button"]');

    // 4. 步驟3：視覺創建
    await expect(page.locator('[data-testid="step-indicator-3"]')).toHaveClass(
      /active/,
    );

    await page.fill('[data-testid="image-prompt"]', "現代科技辦公室環境");
    await page.selectOption('[data-testid="image-style"]', "realistic");
    await page.selectOption('[data-testid="image-count"]', "3");

    await page.click('[data-testid="generate-images-button"]');

    // 等待圖像生成完成
    await expect(page.locator('[data-testid="generated-images"]')).toBeVisible({
      timeout: 60000,
    });
    await expect(page.locator('[data-testid="image-item"]')).toHaveCount(3);

    // 選擇第一張圖片
    await page.click(
      '[data-testid="image-item"]:first-child [data-testid="select-image"]',
    );

    await page.click('[data-testid="next-step-button"]');

    // 5. 步驟4：語音合成
    await expect(page.locator('[data-testid="step-indicator-4"]')).toHaveClass(
      /active/,
    );

    await page.selectOption('[data-testid="voice-select"]', "zh-TW-female-001");
    await page.fill('[data-testid="voice-speed"]', "1.0");
    await page.fill('[data-testid="voice-pitch"]', "0");

    await page.click('[data-testid="synthesize-voice-button"]');

    // 等待語音合成完成
    await expect(page.locator('[data-testid="audio-player"]')).toBeVisible({
      timeout: 45000,
    });

    // 播放語音預覽
    await page.click('[data-testid="play-audio-button"]');
    await expect(page.locator('[data-testid="audio-playing"]')).toBeVisible();

    await page.click('[data-testid="next-step-button"]');

    // 6. 步驟5：影片組裝
    await expect(page.locator('[data-testid="step-indicator-5"]')).toHaveClass(
      /active/,
    );

    // 檢查所有元素都已載入
    await expect(page.locator('[data-testid="script-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="image-preview"]')).toBeVisible();
    await expect(page.locator('[data-testid="audio-preview"]')).toBeVisible();

    // 選擇背景音樂
    await page.selectOption('[data-testid="background-music"]', "ambient");

    // 調整音量
    await page.fill('[data-testid="music-volume"]', "30");

    // 開始影片組裝
    await page.click('[data-testid="assemble-video-button"]');

    // 等待影片組裝完成
    await expect(
      page.locator('[data-testid="video-processing"]'),
    ).toBeVisible();
    await expect(page.locator('[data-testid="video-preview"]')).toBeVisible({
      timeout: 120000,
    });

    // 7. 確認影片創建成功
    await expect(page.locator('[data-testid="success-message"]')).toContainText(
      "影片創建成功",
    );
    await expect(page.locator('[data-testid="video-player"]')).toBeVisible();

    // 8. 保存專案
    await page.click('[data-testid="save-project-button"]');
    await expect(page.locator('[data-testid="save-success"]')).toBeVisible();

    // 9. 導向專案列表確認
    await page.click('[data-testid="view-projects-button"]');
    await expect(page).toHaveURL("/projects");
    await expect(
      page.locator('[data-testid="project-item"]').first(),
    ).toContainText("我的測試影片");
  });

  test("AI 腳本生成功能", async ({ page }) => {
    await page.goto("/ai/script");

    // 填寫腳本生成表單
    await page.fill('[data-testid="script-topic"]', "健康飲食的重要性");
    await page.selectOption('[data-testid="platform-target"]', "tiktok");
    await page.selectOption('[data-testid="video-length"]', "short");
    await page.selectOption('[data-testid="content-tone"]', "friendly");
    await page.selectOption('[data-testid="target-audience"]', "young-adults");

    // 添加關鍵字
    await page.fill('[data-testid="keywords-input"]', "營養, 健康, 生活方式");

    // 選擇趨勢主題
    await page.click('[data-testid="trending-topic"]').first();

    // 生成腳本
    await page.click('[data-testid="generate-script-button"]');

    // 等待生成完成
    await expect(
      page.locator('[data-testid="loading-indicator"]'),
    ).toBeVisible();
    await expect(page.locator('[data-testid="generated-script"]')).toBeVisible({
      timeout: 30000,
    });

    // 檢查腳本內容
    const scriptContent = await page
      .locator('[data-testid="script-content"]')
      .textContent();
    expect(scriptContent.length).toBeGreaterThan(50);

    // 檢查腳本統計
    await expect(page.locator('[data-testid="word-count"]')).toContainText(
      /\d+ 字/,
    );
    await expect(
      page.locator('[data-testid="estimated-duration"]'),
    ).toContainText(/\d+ 秒/);

    // 測試腳本編輯
    await page.click('[data-testid="edit-script-button"]');
    await page.fill(
      '[data-testid="script-editor"]',
      scriptContent + "\n\n這是額外添加的內容。",
    );
    await page.click('[data-testid="save-script-button"]');

    // 保存腳本
    await page.click('[data-testid="save-to-library-button"]');
    await page.fill('[data-testid="script-title"]', "健康飲食腳本");
    await page.click('[data-testid="confirm-save-button"]');

    await expect(
      page.locator('[data-testid="save-success-message"]'),
    ).toContainText("腳本已保存到資料庫");

    // 檢查腳本歷史
    await page.click('[data-testid="script-history-tab"]');
    await expect(
      page.locator('[data-testid="history-item"]').first(),
    ).toContainText("健康飲食腳本");
  });

  test("圖像生成和管理", async ({ page }) => {
    await page.goto("/ai/images");

    // 測試圖像生成
    await page.fill('[data-testid="image-prompt"]', "美麗的日落風景配山脈背景");
    await page.selectOption('[data-testid="image-style"]', "photorealistic");
    await page.selectOption('[data-testid="image-size"]', "1024x1024");
    await page.selectOption('[data-testid="image-count"]', "4");

    // 高級設定
    await page.click('[data-testid="advanced-settings-toggle"]');
    await page.fill('[data-testid="cfg-scale"]', "7.5");
    await page.fill('[data-testid="steps"]', "50");
    await page.fill('[data-testid="seed"]', "42");

    // 生成圖像
    await page.click('[data-testid="generate-images-button"]');

    // 等待生成完成
    await expect(
      page.locator('[data-testid="generation-progress"]'),
    ).toBeVisible();
    await expect(page.locator('[data-testid="generated-images"]')).toBeVisible({
      timeout: 90000,
    });

    // 檢查生成的圖像數量
    await expect(page.locator('[data-testid="image-item"]')).toHaveCount(4);

    // 測試圖像操作
    const firstImage = page.locator('[data-testid="image-item"]').first();

    // 放大檢視
    await firstImage.locator('[data-testid="zoom-image"]').click();
    await expect(page.locator('[data-testid="image-modal"]')).toBeVisible();
    await page.click('[data-testid="close-modal"]');

    // 下載圖像
    await firstImage.locator('[data-testid="download-image"]').click();

    // 添加到收藏
    await firstImage.locator('[data-testid="favorite-image"]').click();
    await expect(
      firstImage.locator('[data-testid="favorite-icon"]'),
    ).toHaveClass(/active/);

    // 使用圖像作為基礎生成變體
    await firstImage.locator('[data-testid="create-variant"]').click();
    await page.fill('[data-testid="variant-prompt"]', "相同場景但是在黃昏時分");
    await page.click('[data-testid="generate-variant-button"]');

    await expect(page.locator('[data-testid="variant-images"]')).toBeVisible({
      timeout: 60000,
    });

    // 檢查圖像庫
    await page.click('[data-testid="image-library-tab"]');
    await expect(
      page.locator('[data-testid="library-image"]'),
    ).toHaveCountGreaterThan(0);

    // 篩選收藏的圖像
    await page.click('[data-testid="filter-favorites"]');
    await expect(
      page.locator('[data-testid="library-image"]'),
    ).toHaveCountGreaterThan(0);
  });

  test("社群媒體發布流程", async ({ page }) => {
    await page.goto("/social");

    // 檢查平台連接狀態
    await expect(
      page.locator('[data-testid="platform-connections"]'),
    ).toBeVisible();

    // 模擬連接 YouTube
    await page.click('[data-testid="connect-youtube"]');
    await expect(
      page.locator('[data-testid="youtube-connected"]'),
    ).toBeVisible();

    // 創建新貼文
    await page.click('[data-testid="create-post-button"]');

    // 選擇影片
    await page.click('[data-testid="select-video-button"]');
    await page.click('[data-testid="video-item"]').first();
    await page.click('[data-testid="confirm-video-selection"]');

    // 填寫貼文內容
    await page.fill('[data-testid="post-title"]', "我的精彩影片分享");
    await page.fill(
      '[data-testid="post-description"]',
      "這是一個關於人工智慧的教育影片，希望大家喜歡！",
    );
    await page.fill('[data-testid="post-tags"]', "#AI #教育 #科技 #未來");

    // 選擇發布平台
    await page.check('[data-testid="platform-youtube"]');
    await page.check('[data-testid="platform-tiktok"]');

    // 設定發布時間
    await page.click('[data-testid="schedule-toggle"]');
    await page.fill('[data-testid="schedule-date"]', "2024-02-01");
    await page.fill('[data-testid="schedule-time"]', "10:00");

    // 預覽貼文
    await page.click('[data-testid="preview-post-button"]');
    await expect(page.locator('[data-testid="post-preview"]')).toBeVisible();

    // 確認發布
    await page.click('[data-testid="publish-post-button"]');
    await expect(page.locator('[data-testid="publish-success"]')).toContainText(
      "貼文已排程發布",
    );

    // 檢查排程列表
    await page.click('[data-testid="scheduled-posts-tab"]');
    await expect(
      page.locator('[data-testid="scheduled-item"]').first(),
    ).toContainText("我的精彩影片分享");

    // 檢查分析數據
    await page.click('[data-testid="analytics-tab"]');
    await expect(
      page.locator('[data-testid="analytics-overview"]'),
    ).toBeVisible();
    await expect(
      page.locator('[data-testid="engagement-chart"]'),
    ).toBeVisible();
    await expect(page.locator('[data-testid="reach-metrics"]')).toBeVisible();
  });

  test("用戶設定和個人檔案管理", async ({ page }) => {
    await page.goto("/settings");

    // 個人資訊設定
    await page.click('[data-testid="profile-settings-tab"]');

    await page.fill('[data-testid="display-name"]', "測試用戶");
    await page.fill('[data-testid="bio"]', "我是一個熱愛創作的內容創作者");
    await page.selectOption('[data-testid="language"]', "zh-TW");
    await page.selectOption('[data-testid="timezone"]', "Asia/Taipei");

    // 上傳頭像
    await page.setInputFiles(
      '[data-testid="avatar-upload"]',
      "tests/fixtures/avatar.jpg",
    );
    await expect(page.locator('[data-testid="avatar-preview"]')).toBeVisible();

    await page.click('[data-testid="save-profile-button"]');
    await expect(page.locator('[data-testid="save-success"]')).toContainText(
      "個人資訊已更新",
    );

    // 通知設定
    await page.click('[data-testid="notification-settings-tab"]');

    await page.check('[data-testid="email-notifications"]');
    await page.check('[data-testid="video-completion-notifications"]');
    await page.check('[data-testid="social-media-notifications"]');
    await page.uncheck('[data-testid="marketing-notifications"]');

    await page.click('[data-testid="save-notifications-button"]');
    await expect(
      page.locator('[data-testid="notifications-saved"]'),
    ).toBeVisible();

    // 隱私設定
    await page.click('[data-testid="privacy-settings-tab"]');

    await page.selectOption('[data-testid="profile-visibility"]', "public");
    await page.check('[data-testid="allow-analytics"]');
    await page.check('[data-testid="improve-experience"]');

    await page.click('[data-testid="save-privacy-button"]');

    // 安全設定
    await page.click('[data-testid="security-settings-tab"]');

    // 更改密碼
    await page.fill('[data-testid="current-password"]', "password123");
    await page.fill('[data-testid="new-password"]', "newPassword456!");
    await page.fill('[data-testid="confirm-password"]', "newPassword456!");
    await page.click('[data-testid="change-password-button"]');

    await expect(
      page.locator('[data-testid="password-changed"]'),
    ).toContainText("密碼已成功更新");

    // 檢查個人檔案頁面
    await page.goto("/profile");
    await expect(
      page.locator('[data-testid="user-display-name"]'),
    ).toContainText("測試用戶");
    await expect(page.locator('[data-testid="user-bio"]')).toContainText(
      "我是一個熱愛創作的內容創作者",
    );
    await expect(page.locator('[data-testid="user-avatar"]')).toBeVisible();
  });

  test("響應式設計測試", async ({ page }) => {
    // 測試桌面視窗
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto("/dashboard");

    await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();
    await expect(page.locator('[data-testid="main-content"]')).toHaveCSS(
      "margin-left",
      /\d+px/,
    );

    // 測試平板視窗
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.reload();

    await expect(
      page.locator('[data-testid="mobile-menu-button"]'),
    ).toBeVisible();
    await page.click('[data-testid="mobile-menu-button"]');
    await expect(page.locator('[data-testid="mobile-sidebar"]')).toBeVisible();

    // 測試手機視窗
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload();

    await expect(page.locator('[data-testid="mobile-header"]')).toBeVisible();
    await expect(page.locator('[data-testid="stats-grid"]')).toHaveCSS(
      "grid-template-columns",
      /1fr/,
    );

    // 測試手機導航
    await page.click('[data-testid="mobile-menu-button"]');
    await expect(page.locator('[data-testid="mobile-nav"]')).toBeVisible();

    await page.click('[data-testid="mobile-nav-projects"]');
    await expect(page).toHaveURL("/projects");

    // 確保手機版本功能正常
    await page.click('[data-testid="create-video-button"]');
    await expect(page).toHaveURL("/create");
    await expect(
      page.locator('[data-testid="mobile-step-indicator"]'),
    ).toBeVisible();
  });
});
