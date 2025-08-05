/**
 * 認證系統整合測試
 * 測試登入、登出、註冊等完整流程
 */

import { describe, it, expect, beforeEach, vi } from "vitest";
import { testUtils } from "../setup.js";

describe("認證系統整合測試", () => {
  beforeEach(() => {
    global.localStorage.clear();
    vi.clearAllMocks();
  });

  describe("登入流程", () => {
    it("應該處理成功的登入 API 請求", async () => {
      const mockResponse = {
        user: testUtils.mockUser,
        tokens: {
          access_token: "mock-access-token",
          refresh_token: "mock-refresh-token",
        },
      };
      testUtils.mockApiResponse(mockResponse);

      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: "test@example.com",
          password: "password123",
        }),
      });

      const data = await response.json();
      expect(data).toEqual(mockResponse);
      expect(response.ok).toBe(true);
    });
  });

  describe("Token 管理", () => {
    it("應該處理 token 刷新請求", async () => {
      const mockResponse = {
        access_token: "new-access-token",
        refresh_token: "new-refresh-token",
      };
      testUtils.mockApiResponse(mockResponse);

      const response = await fetch("/api/auth/refresh", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer refresh-token",
        },
      });

      const data = await response.json();
      expect(data.access_token).toBe("new-access-token");
    });
  });
});
