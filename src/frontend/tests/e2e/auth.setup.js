import { test as setup, expect } from "@playwright/test";
import path from "path";

const authFile = path.join(__dirname, ".auth/user.json");

setup("authenticate", async ({ page }) => {
  // 前往登入頁面
  await page.goto("/login");

  // 等待頁面載入完成
  await expect(page.locator("h1")).toContainText("登入");

  // 填寫登入表單
  await page.fill('[data-testid="email-input"]', "test@example.com");
  await page.fill('[data-testid="password-input"]', "password123");

  // 點擊登入按鈕
  await page.click('[data-testid="login-button"]');

  // 等待導向儀表板
  await page.waitForURL("/dashboard");

  // 確認登入成功
  await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();

  // 保存認證狀態
  await page.context().storageState({ path: authFile });
});
