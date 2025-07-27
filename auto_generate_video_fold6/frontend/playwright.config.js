import { defineConfig, devices } from '@playwright/test';

/**
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',
  
  /* 並行執行測試 */
  fullyParallel: true,
  
  /* 如果在 CI 環境中測試失敗則退出 */
  forbidOnly: !!process.env.CI,
  
  /* 在 CI 環境中重試失敗的測試 */
  retries: process.env.CI ? 2 : 0,
  
  /* 並行工作進程數 */
  workers: process.env.CI ? 1 : undefined,
  
  /* 全局測試設定 */
  timeout: 30 * 1000,
  
  /* 設定期望超時 */
  expect: {
    timeout: 5000,
  },
  
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }]
  ],
  
  /* 共享設定給所有專案 */
  use: {
    /* 基礎 URL，相對於測試檔案 */
    baseURL: 'http://localhost:3000',
    
    /* 測試時收集追蹤資訊 */
    trace: 'on-first-retry',
    
    /* 截圖設定 */
    screenshot: 'only-on-failure',
    
    /* 錄影設定 */
    video: 'retain-on-failure',
    
    /* 瀏覽器設定 */
    ignoreHTTPSErrors: true,
    
    /* 導航超時 */
    navigationTimeout: 30000,
    
    /* 操作超時 */
    actionTimeout: 10000,
  },

  /* 設定不同瀏覽器的測試專案 */
  projects: [
    {
      name: 'setup',
      testMatch: /.*\.setup\.js/,
    },
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // 使用 setup 專案建立的狀態
        storageState: 'tests/e2e/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'firefox',
      use: { 
        ...devices['Desktop Firefox'],
        storageState: 'tests/e2e/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'webkit',
      use: { 
        ...devices['Desktop Safari'],
        storageState: 'tests/e2e/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    
    /* 手機瀏覽器測試 */
    {
      name: 'Mobile Chrome',
      use: { 
        ...devices['Pixel 5'],
        storageState: 'tests/e2e/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'Mobile Safari',
      use: { 
        ...devices['iPhone 12'],
        storageState: 'tests/e2e/.auth/user.json',
      },
      dependencies: ['setup'],
    },
    
    /* 平板測試 */
    {
      name: 'Tablet',
      use: { 
        ...devices['iPad Pro'],
        storageState: 'tests/e2e/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],

  /* 在測試前啟動本地開發伺服器 */
  webServer: {
    command: 'npm run build && npm run preview',
    port: 3000,
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
  
  /* 全域設定 */
  globalSetup: require.resolve('./tests/e2e/global-setup.js'),
  globalTeardown: require.resolve('./tests/e2e/global-teardown.js'),
});