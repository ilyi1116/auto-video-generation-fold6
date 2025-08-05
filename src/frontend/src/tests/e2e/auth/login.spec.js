/**
 * 登入功能端對端測試
 * 測試完整的用戶登入流程
 */

import { test, expect } from "@playwright/test";

test.describe("用戶登入功能", () => {
  test.beforeEach(async ({ page }) => {
    // 每個測試前導航到登入頁面
    await page.goto("/login");
  });

  test("應該成功登入並重定向到儀表板", async ({ page }) => {
    // 填寫登入表單
    await page.fill('[data-testid="email-input"]', "test@example.com");
    await page.fill('[data-testid="password-input"]', "password123");

    // 點擊登入按鈕
    await page.click('[data-testid="login-button"]');

    // 等待重定向到儀表板
    await page.waitForURL("/dashboard");

    // 驗證頁面標題
    await expect(page).toHaveTitle(/儀表板/);

    // 驗證用戶已登入
    await expect(page.locator('[data-testid="user-avatar"]')).toBeVisible();

    // 驗證導航選單顯示
    await expect(page.locator('[data-testid="main-navigation"]')).toBeVisible();
  });

  test("應該顯示錯誤訊息當登入失敗時", async ({ page }) => {
    // 填寫錯誤的登入資訊
    await page.fill('[data-testid="email-input"]', "wrong@example.com");
    await page.fill('[data-testid="password-input"]', "wrongpassword");

    // 模擬 API 錯誤回應
    await page.route("/api/auth/login", (route) => {
      route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({
          message: "電子郵件或密碼錯誤",
          code: "INVALID_CREDENTIALS",
        }),
      });
    });

    // 點擊登入按鈕
    await page.click('[data-testid="login-button"]');

    // 驗證錯誤訊息顯示
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText(
      "電子郵件或密碼錯誤",
    );

    // 驗證仍在登入頁面
    await expect(page).toHaveURL("/login");
  });

  test("應該驗證必填欄位", async ({ page }) => {
    // 嘗試提交空表單
    await page.click('[data-testid="login-button"]');

    // 驗證電子郵件欄位錯誤
    await expect(page.locator('[data-testid="email-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-error"]')).toContainText(
      "請輸入電子郵件",
    );

    // 驗證密碼欄位錯誤
    await expect(page.locator('[data-testid="password-error"]')).toBeVisible();
    await expect(page.locator('[data-testid="password-error"]')).toContainText(
      "請輸入密碼",
    );

    // 驗證 API 未被調用
    let apiCalled = false;
    await page.route("/api/auth/login", (route) => {
      apiCalled = true;
      route.continue();
    });

    expect(apiCalled).toBe(false);
  });

  test("應該顯示載入狀態", async ({ page }) => {
    // 模擬慢速 API 回應
    await page.route("/api/auth/login", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 2000));
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user: { id: 1, name: "Test User", email: "test@example.com" },
          tokens: { access_token: "test-token" },
        }),
      });
    });

    // 填寫表單
    await page.fill('[data-testid="email-input"]', "test@example.com");
    await page.fill('[data-testid="password-input"]', "password123");

    // 點擊登入按鈕
    await page.click('[data-testid="login-button"]');

    // 驗證載入狀態
    await expect(page.locator('[data-testid="login-button"]')).toBeDisabled();
    await expect(page.locator('[data-testid="loading-spinner"]')).toBeVisible();

    // 等待登入完成
    await page.waitForURL("/dashboard", { timeout: 5000 });
  });

  test("應該支援記住我功能", async ({ page, context }) => {
    // 勾選記住我選項
    await page.check('[data-testid="remember-me-checkbox"]');

    // 填寫並提交表單
    await page.fill('[data-testid="email-input"]', "test@example.com");
    await page.fill('[data-testid="password-input"]', "password123");
    await page.click('[data-testid="login-button"]');

    // 等待登入完成
    await page.waitForURL("/dashboard");

    // 關閉所有頁面並創建新頁面（模擬瀏覽器重啟）
    await page.close();
    const newPage = await context.newPage();

    // 訪問受保護頁面
    await newPage.goto("/dashboard");

    // 驗證用戶仍然已登入（沒有重定向到登入頁面）
    await expect(newPage).toHaveURL("/dashboard");
  });

  test("應該支援鍵盤導航", async ({ page }) => {
    // 使用 Tab 鍵導航
    await page.keyboard.press("Tab"); // 電子郵件欄位
    await expect(page.locator('[data-testid="email-input"]')).toBeFocused();

    await page.keyboard.press("Tab"); // 密碼欄位
    await expect(page.locator('[data-testid="password-input"]')).toBeFocused();

    await page.keyboard.press("Tab"); // 記住我選項
    await expect(
      page.locator('[data-testid="remember-me-checkbox"]'),
    ).toBeFocused();

    await page.keyboard.press("Tab"); // 登入按鈕
    await expect(page.locator('[data-testid="login-button"]')).toBeFocused();

    // 使用 Enter 鍵提交表單
    await page.keyboard.press("Enter");

    // 驗證表單驗證觸發
    await expect(page.locator('[data-testid="email-error"]')).toBeVisible();
  });

  test("應該在手機版面正確顯示", async ({ page }) => {
    // 設置手機視窗大小
    await page.setViewportSize({ width: 375, height: 667 });

    // 驗證響應式設計
    await expect(page.locator('[data-testid="login-form"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="password-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-button"]')).toBeVisible();

    // 驗證元素大小適合觸控操作
    const buttonBoundingBox = await page
      .locator('[data-testid="login-button"]')
      .boundingBox();
    expect(buttonBoundingBox.height).toBeGreaterThanOrEqual(44); // 最小觸控目標大小
  });

  test("應該處理網路錯誤", async ({ page }) => {
    // 模擬網路錯誤
    await page.route("/api/auth/login", (route) => {
      route.abort("failed");
    });

    // 填寫並提交表單
    await page.fill('[data-testid="email-input"]', "test@example.com");
    await page.fill('[data-testid="password-input"]', "password123");
    await page.click('[data-testid="login-button"]');

    // 驗證網路錯誤訊息
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText(
      "網路連接失敗",
    );
  });

  test("應該支援深色模式", async ({ page }) => {
    // 切換到深色模式
    await page.evaluate(() => {
      document.documentElement.classList.add("dark");
    });

    // 驗證深色模式樣式
    const loginForm = page.locator('[data-testid="login-form"]');
    await expect(loginForm).toHaveClass(/dark/);

    // 驗證表單元素在深色模式下可見
    await expect(page.locator('[data-testid="email-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="password-input"]')).toBeVisible();
    await expect(page.locator('[data-testid="login-button"]')).toBeVisible();
  });
});
