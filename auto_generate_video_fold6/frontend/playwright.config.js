/**
 * Playwright 端對端測試配置
 * 自動影片生成系統 E2E 測試設定
 */

import { defineConfig, devices } from '@playwright/test';

const config = defineConfig({
  testDir: './src/tests/e2e',
  workers: process.env.CI ? 2 : undefined,
  retries: process.env.CI ? 2 : 1,
  timeout: 30 * 1000,
  
  use: {
    baseURL: 'http://localhost:3000',
    actionTimeout: 15 * 1000,
    navigationTimeout: 15 * 1000,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    locale: 'zh-TW',
    timezoneId: 'Asia/Taipei',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],

  outputDir: './test-results/',
  
  reporter: [
    ['html', { outputFolder: './playwright-report' }],
    ['json', { outputFile: './test-results/results.json' }],
  ],

  webServer: {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: !process.env.CI,
  },
});

export default config;