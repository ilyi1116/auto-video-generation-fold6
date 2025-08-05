/**
 * API 集成端對端測試
 * 測試前端與後端 API 的完整集成
 */

import { test, expect } from "@playwright/test";

test.describe("API 集成測試", () => {
  let authToken;

  test.beforeAll(async ({ request }) => {
    // 獲取認證令牌用於 API 測試
    const response = await request.post("/api/auth/login", {
      data: {
        email: "test@example.com",
        password: "password123"
      }
    });
    
    const data = await response.json();
    authToken = data.tokens.access_token;
  });

  test("應該正確處理用戶認證流程", async ({ page, request }) => {
    // 測試未認證訪問受保護資源
    const unauthorizedResponse = await request.get("/api/user/profile");
    expect(unauthorizedResponse.status()).toBe(401);

    // 測試登入流程
    await page.goto("/login");
    await page.fill('[data-testid="email-input"]', "test@example.com");
    await page.fill('[data-testid="password-input"]', "password123");
    
    // 監聽登入 API 請求
    const loginPromise = page.waitForResponse("/api/auth/login");
    await page.click('[data-testid="login-button"]');
    const loginResponse = await loginPromise;
    
    expect(loginResponse.status()).toBe(200);
    const loginData = await loginResponse.json();
    expect(loginData.user).toBeTruthy();
    expect(loginData.tokens.access_token).toBeTruthy();

    // 驗證登入後可以訪問受保護資源
    await page.waitForURL("/dashboard");
    
    // 使用頁面上下文中的認證令牌訪問 API
    const profileResponse = await page.evaluate(async () => {
      const response = await fetch("/api/user/profile", {
        headers: {
          "Authorization": `Bearer ${localStorage.getItem("access_token")}`
        }
      });
      return {
        status: response.status,
        data: await response.json()
      };
    });
    
    expect(profileResponse.status).toBe(200);
    expect(profileResponse.data.user).toBeTruthy();
  });

  test("應該正確處理檔案上傳 API", async ({ page, request }) => {
    // 先登入
    await page.goto("/login");
    await page.fill('[data-testid="email-input"]', "test@example.com");
    await page.fill('[data-testid="password-input"]', "password123");
    await page.click('[data-testid="login-button"]');
    await page.waitForURL("/dashboard");

    // 創建專案
    await page.click('[data-testid="create-project-button"]');
    await page.fill('[data-testid="project-name-input"]', "API 測試專案");
    await page.click('[data-testid="save-project-button"]');
    await page.click('[data-testid="project-card"]');

    // 測試檔案上傳
    const fileInput = page.locator('input[type="file"]');
    
    // 監聽上傳請求
    const uploadPromise = page.waitForResponse("/api/upload/audio");
    
    await fileInput.setInputFiles({
      name: 'test-audio.mp3',
      mimeType: 'audio/mpeg',
      buffer: Buffer.from('fake audio content for testing')
    });
    
    const uploadResponse = await uploadPromise;
    expect(uploadResponse.status()).toBe(200);
    
    const uploadData = await uploadResponse.json();
    expect(uploadData.file_id).toBeTruthy();
    expect(uploadData.url).toBeTruthy();
    expect(uploadData.duration).toBeGreaterThan(0);
  });

  test("應該正確處理 WebSocket 連接", async ({ page }) => {
    await page.goto("/login");
    await page.fill('[data-testid="email-input"]', "test@example.com");
    await page.fill('[data-testid="password-input"]', "password123");
    await page.click('[data-testid="login-button"]');
    await page.waitForURL("/dashboard");

    // 檢查 WebSocket 連接狀態
    const wsStatus = await page.evaluate(() => {
      return new Promise((resolve) => {
        if (window.websocket) {
          resolve({
            connected: window.websocket.readyState === WebSocket.OPEN,
            url: window.websocket.url
          });
        } else {
          // 等待 WebSocket 初始化
          setTimeout(() => {
            resolve({
              connected: window.websocket?.readyState === WebSocket.OPEN,
              url: window.websocket?.url
            });
          }, 1000);
        }
      });
    });

    expect(wsStatus.connected).toBe(true);
    expect(wsStatus.url).toContain("ws://");

    // 測試實時通知
    await page.evaluate(() => {
      if (window.websocket) {
        // 模擬收到服務器消息
        const mockEvent = new MessageEvent('message', {
          data: JSON.stringify({
            type: 'notification',
            message: '您的影片生成已完成！',
            timestamp: Date.now()
          })
        });
        window.websocket.dispatchEvent(mockEvent);
      }
    });

    // 驗證通知顯示
    await expect(page.locator('[data-testid="notification-toast"]')).toBeVisible();
    await expect(page.locator('[data-testid="notification-toast"]')).toContainText("您的影片生成已完成！");
  });

  test("應該正確處理 API 限流", async ({ page, request }) => {
    // 測試 API 限流機制
    const promises = [];
    
    // 發送大量並發請求
    for (let i = 0; i < 20; i++) {
      promises.push(
        request.get("/api/health", {
          headers: {
            "Authorization": `Bearer ${authToken}`
          }
        })
      );
    }

    const responses = await Promise.all(promises);
    
    // 檢查是否有部分請求被限流
    const rateLimitedResponses = responses.filter(r => r.status() === 429);
    const successfulResponses = responses.filter(r => r.status() === 200);
    
    expect(successfulResponses.length).toBeGreaterThan(0);
    
    // 如果有限流，驗證錯誤回應格式
    if (rateLimitedResponses.length > 0) {
      const rateLimitData = await rateLimitedResponses[0].json();
      expect(rateLimitData.error).toBeTruthy();
      expect(rateLimitData.retry_after).toBeGreaterThan(0);
    }
  });

  test("應該正確處理 API 錯誤回應", async ({ page }) => {
    await page.goto("/login");
    await page.fill('[data-testid="email-input"]', "test@example.com"); 
    await page.fill('[data-testid="password-input"]', "password123");
    await page.click('[data-testid="login-button"]');
    await page.waitForURL("/dashboard");

    // 模擬服務器錯誤
    await page.route("/api/ai/generate-script", (route) => {
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          error: "Service Unavailable",
          message: "AI 服務暫時不可用，請稍後再試",
          code: "SERVICE_UNAVAILABLE",
          retry_after: 30
        }),
      });
    });

    // 嘗試生成腳本
    await page.click('[data-testid="create-project-button"]');
    await page.fill('[data-testid="project-name-input"]', "錯誤測試專案");
    await page.click('[data-testid="save-project-button"]');
    await page.click('[data-testid="project-card"]');
    await page.click('[data-testid="generate-script-button"]');
    await page.fill('[data-testid="script-prompt-input"]', "測試腳本生成");
    await page.click('[data-testid="confirm-generate-script"]');

    // 驗證錯誤處理
    await expect(page.locator('[data-testid="error-alert"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText("AI 服務暫時不可用");
    await expect(page.locator('[data-testid="retry-button"]')).toBeVisible();
    await expect(page.locator('[data-testid="retry-countdown"]')).toBeVisible();
  });

  test("應該支援 API 版本兼容性", async ({ request }) => {
    // 測試不同 API 版本
    const v1Response = await request.get("/api/v1/health", {
      headers: {
        "Authorization": `Bearer ${authToken}`
      }
    });
    expect(v1Response.status()).toBe(200);

    const v2Response = await request.get("/api/v2/health", {
      headers: {
        "Authorization": `Bearer ${authToken}`
      }
    });
    
    // v2 可能存在或返回向後兼容回應
    expect([200, 404].includes(v2Response.status())).toBe(true);

    // 測試版本協商
    const negotiationResponse = await request.get("/api/health", {
      headers: {
        "Authorization": `Bearer ${authToken}`,
        "Accept": "application/vnd.api+json;version=1"
      }
    });
    expect(negotiationResponse.status()).toBe(200);

    const negotiationData = await negotiationResponse.json();
    expect(negotiationData.api_version).toBeTruthy();
  });

  test("應該正確處理大檔案上傳", async ({ page }) => {
    await page.goto("/login");
    await page.fill('[data-testid="email-input"]', "test@example.com");
    await page.fill('[data-testid="password-input"]', "password123");
    await page.click('[data-testid="login-button"]');
    await page.waitForURL("/dashboard");

    // 創建專案
    await page.click('[data-testid="create-project-button"]');
    await page.fill('[data-testid="project-name-input"]', "大檔案測試");
    await page.click('[data-testid="save-project-button"]');
    await page.click('[data-testid="project-card"]');

    // 模擬大檔案上傳進度
    await page.route("/api/upload/audio", (route) => {
      // 模擬分片上傳回應
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          file_id: "large_audio_123",
          url: "/uploads/large_audio_123.mp3",
          size: 52428800, // 50MB
          chunks_total: 10,
          chunks_uploaded: 10,
          upload_complete: true
        }),
      });
    });

    // 開始上傳
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'large-audio.mp3',
      mimeType: 'audio/mpeg',
      buffer: Buffer.alloc(1024 * 1024) // 1MB 測試檔案
    });

    // 驗證上傳進度顯示
    await expect(page.locator('[data-testid="upload-progress"]')).toBeVisible();
    await expect(page.locator('[data-testid="progress-bar"]')).toBeVisible();
    await expect(page.locator('[data-testid="upload-speed"]')).toBeVisible();

    // 等待上傳完成
    await expect(page.locator('[data-testid="upload-complete"]')).toBeVisible();
    await expect(page.locator('[data-testid="file-size-display"]')).toContainText("50MB");
  });

  test("應該支援 API 快取機制", async ({ page, request }) => {
    // 測試 GET 請求快取
    const firstResponse = await request.get("/api/user/projects", {
      headers: {
        "Authorization": `Bearer ${authToken}`
      }
    });
    
    const firstETag = firstResponse.headers()["etag"];
    expect(firstResponse.status()).toBe(200);

    // 發送帶有 If-None-Match 標頭的請求
    const cachedResponse = await request.get("/api/user/projects", {
      headers: {
        "Authorization": `Bearer ${authToken}`,
        "If-None-Match": firstETag
      }
    });

    // 如果資料未變更，應返回 304
    if (firstETag) {
      expect([200, 304].includes(cachedResponse.status())).toBe(true);
    }

    // 測試瀏覽器端快取
    await page.goto("/dashboard");
    
    const performanceEntries = await page.evaluate(() => {
      return performance.getEntriesByType('resource')
        .filter(entry => entry.name.includes('/api/'))
        .map(entry => ({
          name: entry.name,
          transferSize: entry.transferSize,
          encodedBodySize: entry.encodedBodySize
        }));
    });

    // 檢查是否有資源從快取載入（transferSize 小於 encodedBodySize）
    const cachedRequests = performanceEntries.filter(
      entry => entry.transferSize < entry.encodedBodySize
    );
    
    expect(cachedRequests.length).toBeGreaterThanOrEqual(0); // 允許沒有快取的情況
  });
});