import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import userEvent from '@testing-library/user-event';
import { get } from 'svelte/store';

// 導入頁面組件和相關依賴
import LoginPage from '../../routes/login/+page.svelte';
import RegisterPage from '../../routes/register/+page.svelte';
import DashboardPage from '../../routes/dashboard/+page.svelte';
import { authStore } from '../../lib/stores/auth.js';

// Mock fetch API
global.fetch = vi.fn();

// Mock 路由導航
const mockGoto = vi.fn();
vi.mock('$app/navigation', () => ({
  goto: mockGoto
}));

// Mock toast 通知
const mockToast = {
  success: vi.fn(),
  error: vi.fn(),
  info: vi.fn()
};
vi.mock('svelte-french-toast', () => ({
  toast: mockToast
}));

describe('認證整合測試', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // 重置認證狀態
    authStore.set({
      user: null,
      isAuthenticated: false,
      loading: false,
      error: null
    });

    // 清理 localStorage
    global.localStorage = {
      getItem: vi.fn(),
      setItem: vi.fn(),
      removeItem: vi.fn(),
      clear: vi.fn()
    };
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('用戶登入流程', () => {
    it('應該完成完整的登入流程', async () => {
      const user = userEvent.setup();

      // Mock 成功的登入 API 回應
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          user: { 
            id: 1, 
            username: 'testuser', 
            email: 'test@example.com' 
          },
          token: 'mock-jwt-token'
        })
      });

      render(LoginPage);

      // 填寫登入表單
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // 等待 API 請求完成
      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'password123'
          })
        });
      });

      // 驗證認證狀態已更新
      const authState = get(authStore);
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.user.email).toBe('test@example.com');

      // 驗證 token 已保存到 localStorage
      expect(localStorage.setItem).toHaveBeenCalledWith('token', 'mock-jwt-token');

      // 驗證成功訊息已顯示
      expect(mockToast.success).toHaveBeenCalledWith('登入成功！');

      // 驗證重導向到儀表板
      expect(mockGoto).toHaveBeenCalledWith('/dashboard');
    });

    it('應該處理登入失敗情況', async () => {
      const user = userEvent.setup();

      // Mock 失敗的登入 API 回應
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({
          error: '帳號或密碼錯誤'
        })
      });

      render(LoginPage);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'wrong@example.com');
      await user.type(passwordInput, 'wrongpassword');
      await user.click(submitButton);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });

      // 驗證錯誤訊息已顯示
      expect(mockToast.error).toHaveBeenCalledWith('帳號或密碼錯誤');

      // 驗證認證狀態未更改
      const authState = get(authStore);
      expect(authState.isAuthenticated).toBe(false);
      expect(authState.user).toBe(null);

      // 驗證沒有重導向
      expect(mockGoto).not.toHaveBeenCalled();
    });

    it('應該顯示載入狀態', async () => {
      const user = userEvent.setup();

      // Mock 延遲的 API 回應
      let resolvePromise;
      const delayedPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });
      fetch.mockReturnValueOnce(delayedPromise);

      render(LoginPage);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      // 驗證載入狀態
      await waitFor(() => {
        expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
        expect(submitButton).toBeDisabled();
      });

      // 解決 Promise 並驗證載入狀態消失
      resolvePromise({
        ok: true,
        json: async () => ({ user: {}, token: 'token' })
      });

      await waitFor(() => {
        expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
      });
    });
  });

  describe('用戶註冊流程', () => {
    it('應該完成完整的註冊流程', async () => {
      const user = userEvent.setup();

      // Mock 成功的註冊 API 回應
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          message: '註冊成功，請檢查您的電子郵件進行驗證'
        })
      });

      render(RegisterPage);

      // 填寫註冊表單
      const usernameInput = screen.getByLabelText(/username/i);
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const submitButton = screen.getByRole('button', { name: /sign up/i });

      await user.type(usernameInput, 'newuser');
      await user.type(emailInput, 'new@example.com');
      await user.type(passwordInput, 'StrongPass123!');
      await user.type(confirmPasswordInput, 'StrongPass123!');
      await user.click(submitButton);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/auth/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: 'newuser',
            email: 'new@example.com',
            password: 'StrongPass123!'
          })
        });
      });

      // 驗證成功訊息
      expect(mockToast.success).toHaveBeenCalledWith('註冊成功，請檢查您的電子郵件進行驗證');

      // 驗證重導向到登入頁面
      expect(mockGoto).toHaveBeenCalledWith('/login');
    });

    it('應該驗證密碼確認', async () => {
      const user = userEvent.setup();

      render(RegisterPage);

      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const submitButton = screen.getByRole('button', { name: /sign up/i });

      await user.type(passwordInput, 'password123');
      await user.type(confirmPasswordInput, 'differentpassword');
      await user.click(submitButton);

      // 驗證錯誤訊息顯示
      expect(screen.getByText('密碼確認不符')).toBeInTheDocument();

      // 驗證 API 沒有被調用
      expect(fetch).not.toHaveBeenCalled();
    });

    it('應該處理註冊錯誤', async () => {
      const user = userEvent.setup();

      // Mock 失敗的註冊 API 回應
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          error: '電子郵件已被使用'
        })
      });

      render(RegisterPage);

      const usernameInput = screen.getByLabelText(/username/i);
      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/^password/i);
      const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
      const submitButton = screen.getByRole('button', { name: /sign up/i });

      await user.type(usernameInput, 'existinguser');
      await user.type(emailInput, 'existing@example.com');
      await user.type(passwordInput, 'StrongPass123!');
      await user.type(confirmPasswordInput, 'StrongPass123!');
      await user.click(submitButton);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });

      expect(mockToast.error).toHaveBeenCalledWith('電子郵件已被使用');
    });
  });

  describe('認證狀態管理', () => {
    it('應該從 localStorage 恢復認證狀態', async () => {
      // Mock localStorage 中的 token
      localStorage.getItem.mockReturnValue('existing-token');

      // Mock 用戶資料 API 回應
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          user: { 
            id: 1, 
            username: 'existinguser', 
            email: 'existing@example.com' 
          }
        })
      });

      // 模擬應用啟動時的認證檢查
      render(DashboardPage);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalledWith('/api/auth/me', {
          headers: { 
            'Authorization': 'Bearer existing-token',
            'Content-Type': 'application/json'
          }
        });
      });

      const authState = get(authStore);
      expect(authState.isAuthenticated).toBe(true);
      expect(authState.user.username).toBe('existinguser');
    });

    it('應該處理無效的 token', async () => {
      localStorage.getItem.mockReturnValue('invalid-token');

      // Mock 無效 token 的 API 回應
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Invalid token' })
      });

      render(DashboardPage);

      await waitFor(() => {
        expect(fetch).toHaveBeenCalled();
      });

      // 驗證 token 被移除
      expect(localStorage.removeItem).toHaveBeenCalledWith('token');

      // 驗證重導向到登入頁面
      expect(mockGoto).toHaveBeenCalledWith('/login');

      const authState = get(authStore);
      expect(authState.isAuthenticated).toBe(false);
    });

    it('應該正確處理登出', async () => {
      // 設置已登入狀態
      authStore.set({
        user: { id: 1, username: 'testuser' },
        isAuthenticated: true,
        loading: false,
        error: null
      });

      render(DashboardPage);

      const logoutButton = screen.getByRole('button', { name: /logout/i });
      await fireEvent.click(logoutButton);

      // 驗證 localStorage 被清理
      expect(localStorage.removeItem).toHaveBeenCalledWith('token');

      // 驗證認證狀態被重置
      const authState = get(authStore);
      expect(authState.isAuthenticated).toBe(false);
      expect(authState.user).toBe(null);

      // 驗證重導向到首頁
      expect(mockGoto).toHaveBeenCalledWith('/');
    });
  });

  describe('路由保護', () => {
    it('未認證用戶應該被重導向到登入頁面', () => {
      // 設置未認證狀態
      authStore.set({
        user: null,
        isAuthenticated: false,
        loading: false,
        error: null
      });

      render(DashboardPage);

      // 驗證重導向到登入頁面
      expect(mockGoto).toHaveBeenCalledWith('/login');
    });

    it('已認證用戶應該能正常訪問受保護的頁面', () => {
      // 設置已認證狀態
      authStore.set({
        user: { id: 1, username: 'testuser' },
        isAuthenticated: true,
        loading: false,
        error: null
      });

      render(DashboardPage);

      // 驗證頁面正常渲染，沒有重導向
      expect(mockGoto).not.toHaveBeenCalled();
      expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
    });
  });

  describe('錯誤處理', () => {
    it('應該處理網路錯誤', async () => {
      const user = userEvent.setup();

      // Mock 網路錯誤
      fetch.mockRejectedValueOnce(new Error('Network Error'));

      render(LoginPage);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('網路錯誤，請稍後再試');
      });
    });

    it('應該處理伺服器錯誤', async () => {
      const user = userEvent.setup();

      // Mock 伺服器錯誤
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Internal Server Error' })
      });

      render(LoginPage);

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);
      const submitButton = screen.getByRole('button', { name: /sign in/i });

      await user.type(emailInput, 'test@example.com');
      await user.type(passwordInput, 'password123');
      await user.click(submitButton);

      await waitFor(() => {
        expect(mockToast.error).toHaveBeenCalledWith('伺服器錯誤，請聯繫技術支援');
      });
    });
  });
});