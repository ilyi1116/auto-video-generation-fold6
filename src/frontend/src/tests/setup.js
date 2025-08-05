/**
 * 測試環境設定檔案
 * 用於配置全域測試環境和工具
 */

import { beforeAll, afterAll, beforeEach, afterEach } from "vitest";
import { vi } from "vitest";
import "@testing-library/jest-dom";

// 模擬瀏覽器 API
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// 模擬 localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock;

// 模擬 fetch API
global.fetch = vi.fn();

// 模擬 IntersectionObserver
global.IntersectionObserver = vi.fn(() => ({
  disconnect: vi.fn(),
  observe: vi.fn(),
  unobserve: vi.fn(),
}));

// 測試前清理
beforeEach(() => {
  // 清理所有 mock
  vi.clearAllMocks();

  // 重置 localStorage
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
  localStorageMock.removeItem.mockClear();
  localStorageMock.clear.mockClear();
});

// 測試後清理
afterEach(() => {
  // 清理 DOM
  document.body.innerHTML = "";
});

// 全域測試工具
export const testUtils = {
  // 模擬 API 回應
  mockApiResponse: (data, status = 200) => {
    if (!global.fetch.mockResolvedValueOnce) {
      global.fetch = vi.fn();
    }
    global.fetch.mockResolvedValueOnce({
      ok: status >= 200 && status < 300,
      status,
      json: async () => data,
      headers: {
        get: (name) => (name === "content-type" ? "application/json" : null),
      },
    });
  },

  // 模擬 API 錯誤
  mockApiError: (status = 500, message = "Internal Server Error") => {
    global.fetch.mockRejectedValueOnce(new Error(message));
  },

  // 等待 DOM 更新
  waitForDOM: async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  },

  // 模擬用戶
  mockUser: {
    id: 1,
    email: "test@example.com",
    name: "Test User",
    avatar: "https://example.com/avatar.jpg",
    subscription: "pro",
    preferences: {
      theme: "light",
      language: "zh-TW",
    },
  },
};
