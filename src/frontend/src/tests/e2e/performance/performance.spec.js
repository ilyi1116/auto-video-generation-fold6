/**
 * 性能端對端測試
 * 測試應用程式的性能指標和用戶體驗
 */

import { test, expect } from "@playwright/test";

test.describe("性能測試", () => {
  test("應該滿足核心 Web 指標 (Core Web Vitals)", async ({ page }) => {
    // 開始性能監控
    await page.goto("/");

    // 等待頁面完全載入
    await page.waitForLoadState("networkidle");

    // 測量核心 Web 指標
    const webVitals = await page.evaluate(() => {
      return new Promise((resolve) => {
        const vitals = {};
        
        // Largest Contentful Paint (LCP)
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          vitals.lcp = lastEntry.startTime;
        }).observe({ entryTypes: ['largest-contentful-paint'] });

        // First Input Delay (FID) - 需要用戶互動
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            vitals.fid = entry.processingStart - entry.startTime;
          });
        }).observe({ entryTypes: ['first-input'] });

        // Cumulative Layout Shift (CLS)
        let clsScore = 0;
        new PerformanceObserver((list) => {
          list.getEntries().forEach((entry) => {
            if (!entry.hadRecentInput) {
              clsScore += entry.value;
            }
          });
          vitals.cls = clsScore;
        }).observe({ entryTypes: ['layout-shift'] });

        // Time to First Byte (TTFB)
        const navigation = performance.getEntriesByType('navigation')[0];
        vitals.ttfb = navigation.responseStart - navigation.requestStart;

        // First Contentful Paint (FCP)
        const fcpEntry = performance.getEntriesByType('paint')
          .find(entry => entry.name === 'first-contentful-paint');
        vitals.fcp = fcpEntry ? fcpEntry.startTime : null;

        setTimeout(() => resolve(vitals), 2000);
      });
    });

    // 驗證性能指標
    expect(webVitals.ttfb).toBeLessThan(800); // TTFB < 800ms
    expect(webVitals.fcp).toBeLessThan(1800); // FCP < 1.8s
    expect(webVitals.lcp).toBeLessThan(2500); // LCP < 2.5s
    expect(webVitals.cls).toBeLessThan(0.1); // CLS < 0.1

    console.log("Web Vitals:", webVitals);
  });

  test("應該快速載入和渲染主要頁面", async ({ page }) => {
    const pages = [
      { url: "/", name: "首頁" },
      { url: "/login", name: "登入頁" },
      { url: "/dashboard", name: "儀表板" }
    ];

    for (const testPage of pages) {
      const startTime = Date.now();
      
      await page.goto(testPage.url);
      await page.waitForLoadState("domcontentloaded");
      
      const loadTime = Date.now() - startTime;
      
      // 頁面載入時間應少於 3 秒
      expect(loadTime).toBeLessThan(3000);
      
      // 驗證主要內容元素已載入
      const hasMainContent = await page.locator("main, [role='main'], .main-content").count() > 0;
      expect(hasMainContent).toBe(true);
      
      console.log(`${testPage.name} 載入時間: ${loadTime}ms`);
    }
  });

  test("應該高效處理大量數據渲染", async ({ page }) => {
    // 登入到儀表板
    await page.goto("/login");
    await page.fill('[data-testid="email-input"]', "test@example.com");
    await page.fill('[data-testid="password-input"]', "password123");
    await page.click('[data-testid="login-button"]');
    await page.waitForURL("/dashboard");

    // 模擬大量專案數據
    await page.route("/api/user/projects", (route) => {
      const projects = Array.from({ length: 100 }, (_, i) => ({
        id: i + 1,
        name: `專案 ${i + 1}`,
        description: `這是第 ${i + 1} 個測試專案`,
        status: ["active", "completed", "draft"][i % 3],
        created_at: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString()
      }));

      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          projects,
          total: 100,
          page: 1,
          per_page: 100
        }),
      });
    });

    const renderStart = Date.now();
    
    // 導航到專案列表
    await page.click('[data-testid="projects-tab"]');
    await page.waitForSelector('[data-testid="project-card"]');
    
    const renderTime = Date.now() - renderStart;
    
    // 大量數據渲染時間應少於 2 秒
    expect(renderTime).toBeLessThan(2000);
    
    // 驗證所有項目都已渲染
    const projectCards = await page.locator('[data-testid="project-card"]').count();
    expect(projectCards).toBe(100);
    
    console.log(`渲染 100 個專案耗時: ${renderTime}ms`);
  });

  test("應該有良好的滾動性能", async ({ page }) => {
    await page.goto("/");
    await page.setViewportSize({ width: 1200, height: 800 });

    // 測量滾動性能
    const scrollPerformance = await page.evaluate(() => {
      return new Promise((resolve) => {
        let frameCount = 0;
        let startTime = performance.now();
        
        function measureFrame() {
          frameCount++;
          
          if (frameCount < 60) { // 測量 60 幀
            requestAnimationFrame(measureFrame);
          } else {
            const endTime = performance.now();
            const duration = endTime - startTime;
            const fps = (frameCount / duration) * 1000;
            resolve({ fps, duration, frameCount });
          }
        }

        // 開始滾動
        window.scrollBy(0, 10);
        requestAnimationFrame(measureFrame);
      });
    });

    // FPS 應該保持在 30 以上
    expect(scrollPerformance.fps).toBeGreaterThan(30);
    
    console.log(`滾動性能: ${scrollPerformance.fps.toFixed(2)} FPS`);
  });

  test("應該有效管理記憶體使用", async ({ page }) => {
    await page.goto("/dashboard");

    // 測量初始記憶體使用
    const initialMemory = await page.evaluate(() => {
      return performance.memory ? {
        usedJSHeapSize: performance.memory.usedJSHeapSize,
        totalJSHeapSize: performance.memory.totalJSHeapSize,
        jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
      } : null;
    });

    if (initialMemory) {
      // 執行一些操作來增加記憶體使用
      for (let i = 0; i < 10; i++) {
        await page.click('[data-testid="create-project-button"]');
        await page.fill('[data-testid="project-name-input"]', `記憶體測試專案 ${i}`);
        await page.click('[data-testid="save-project-button"]');
        await page.keyboard.press("Escape"); // 關閉對話框
      }

      // 測量操作後記憶體使用
      const finalMemory = await page.evaluate(() => {
        return {
          usedJSHeapSize: performance.memory.usedJSHeapSize,
          totalJSHeapSize: performance.memory.totalJSHeapSize,
          jsHeapSizeLimit: performance.memory.jsHeapSizeLimit
        };
      });

      const memoryIncrease = finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize;
      const memoryIncreasePercentage = (memoryIncrease / initialMemory.usedJSHeapSize) * 100;

      // 記憶體增長不應超過 50%
      expect(memoryIncreasePercentage).toBeLessThan(50);
      
      // 記憶體使用不應超過限制的 80%
      const memoryUsagePercentage = (finalMemory.usedJSHeapSize / finalMemory.jsHeapSizeLimit) * 100;
      expect(memoryUsagePercentage).toBeLessThan(80);

      console.log(`記憶體增長: ${(memoryIncrease / 1024 / 1024).toFixed(2)} MB (${memoryIncreasePercentage.toFixed(2)}%)`);
    }
  });

  test("應該優化圖片載入性能", async ({ page }) => {
    await page.goto("/");

    // 測量圖片載入性能
    const imagePerformance = await page.evaluate(() => {
      return new Promise((resolve) => {
        const images = Array.from(document.querySelectorAll('img'));
        let loadedCount = 0;
        const startTime = performance.now();
        const imageStats = [];

        if (images.length === 0) {
          resolve({ totalImages: 0, averageLoadTime: 0, imageStats: [] });
          return;
        }

        images.forEach((img, index) => {
          const imageStartTime = performance.now();
          
          const checkLoad = () => {
            if (img.complete && img.naturalHeight !== 0) {
              const loadTime = performance.now() - imageStartTime;
              imageStats.push({
                index,
                src: img.src,
                loadTime,
                naturalWidth: img.naturalWidth,
                naturalHeight: img.naturalHeight
              });
              
              loadedCount++;
              if (loadedCount === images.length) {
                const totalTime = performance.now() - startTime;
                const averageLoadTime = imageStats.reduce((sum, stat) => sum + stat.loadTime, 0) / imageStats.length;
                resolve({
                  totalImages: images.length,
                  totalLoadTime: totalTime,
                  averageLoadTime,
                  imageStats
                });
              }
            } else {
              setTimeout(checkLoad, 100);
            }
          };

          if (img.complete && img.naturalHeight !== 0) {
            checkLoad();
          } else {
            img.onload = checkLoad;
            img.onerror = checkLoad;
          }
        });
      });
    });

    if (imagePerformance.totalImages > 0) {
      // 平均圖片載入時間應少於 1 秒
      expect(imagePerformance.averageLoadTime).toBeLessThan(1000);
      
      // 沒有圖片載入時間超過 3 秒
      const slowImages = imagePerformance.imageStats.filter(stat => stat.loadTime > 3000);
      expect(slowImages.length).toBe(0);

      console.log(`載入 ${imagePerformance.totalImages} 張圖片，平均時間: ${imagePerformance.averageLoadTime.toFixed(2)}ms`);
    }
  });

  test("應該有良好的網路性能", async ({ page }) => {
    // 模擬慢速網路
    await page.route("**/*", (route) => {
      const delay = Math.random() * 100 + 50; // 50-150ms 延遲
      setTimeout(() => route.continue(), delay);
    });

    const startTime = Date.now();
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    const loadTime = Date.now() - startTime;

    // 即使在慢速網路下，載入時間也應該合理
    expect(loadTime).toBeLessThan(5000);

    // 測量網路請求
    const networkStats = await page.evaluate(() => {
      const entries = performance.getEntriesByType('resource');
      return {
        totalRequests: entries.length,
        averageResponseTime: entries.reduce((sum, entry) => 
          sum + (entry.responseEnd - entry.requestStart), 0) / entries.length,
        cachedRequests: entries.filter(entry => entry.transferSize === 0).length
      };
    });

    // 驗證網路效率
    expect(networkStats.averageResponseTime).toBeLessThan(1000);
    
    console.log(`網路統計: ${networkStats.totalRequests} 個請求，平均回應時間: ${networkStats.averageResponseTime.toFixed(2)}ms`);
  });

  test("應該支援離線功能", async ({ page }) => {
    // 先載入頁面
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");

    // 模擬離線狀態
    await page.setOfflineMode(true);

    // 嘗試執行一些操作
    await page.click('[data-testid="projects-tab"]');
    
    // 檢查是否顯示離線提示
    const offlineIndicator = page.locator('[data-testid="offline-indicator"]');
    await expect(offlineIndicator).toBeVisible({ timeout: 5000 });

    // 檢查快取的內容是否仍然可用
    const cachedContent = page.locator('[data-testid="cached-projects"]');
    const isCachedContentVisible = await cachedContent.isVisible();
    
    // 如果有快取內容，應該顯示
    if (isCachedContentVisible) {
      expect(await cachedContent.count()).toBeGreaterThan(0);
    }

    // 恢復線上狀態
    await page.setOfflineMode(false);
    
    // 等待重新連線
    await expect(offlineIndicator).toBeHidden({ timeout: 10000 });
  });

  test("應該有良好的響應式性能", async ({ page }) => {
    const viewports = [
      { width: 375, height: 667, name: "手機" },
      { width: 768, height: 1024, name: "平板" },
      { width: 1920, height: 1080, name: "桌面" }
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      
      const startTime = Date.now();
      await page.goto("/dashboard");
      await page.waitForLoadState("domcontentloaded");
      const loadTime = Date.now() - startTime;

      // 各種視窗大小下載入時間都應該合理
      expect(loadTime).toBeLessThan(3000);

      // 檢查響應式佈局
      const mainContent = page.locator("main");
      const boundingBox = await mainContent.boundingBox();
      
      expect(boundingBox.width).toBeLessThanOrEqual(viewport.width);
      expect(boundingBox.width).toBeGreaterThan(viewport.width * 0.8); // 至少使用 80% 寬度

      console.log(`${viewport.name} (${viewport.width}x${viewport.height}) 載入時間: ${loadTime}ms`);
    }
  });
});