/**
 * 認證狀態管理
 * 處理用戶登入、登出、JWT token 管理
 */

import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { apiClient } from '../api/client.js';

// 認證狀態
const createAuthStore = () => {
  const { subscribe, set, update } = writable({
    isAuthenticated: false,
    user: null,
    token: null,
    loading: true,
    error: null
  });

  return {
    subscribe,
    
    // 初始化認證狀態
    init: async () => {
      if (!browser) return;
      
      try {
        const token = localStorage.getItem('auth_token');
        if (token) {
          // 驗證 token 有效性
          const user = await apiClient.auth.verifyToken(token);
          set({
            isAuthenticated: true,
            user,
            token,
            loading: false,
            error: null
          });
        } else {
          set({
            isAuthenticated: false,
            user: null,
            token: null,
            loading: false,
            error: null
          });
        }
      } catch (error) {
        console.error('Auth initialization failed:', error);
        // Token 無效，清除本地存儲
        if (browser) {
          localStorage.removeItem('auth_token');
        }
        set({
          isAuthenticated: false,
          user: null,
          token: null,
          loading: false,
          error: error.message
        });
      }
    },

    // 登入
    login: async (email, password) => {
      update(state => ({ ...state, loading: true, error: null }));
      
      try {
        const { user, token } = await apiClient.auth.login(email, password);
        
        if (browser) {
          localStorage.setItem('auth_token', token);
        }
        
        set({
          isAuthenticated: true,
          user,
          token,
          loading: false,
          error: null
        });
        
        return { success: true };
      } catch (error) {
        set({
          isAuthenticated: false,
          user: null,
          token: null,
          loading: false,
          error: error.message
        });
        return { success: false, error: error.message };
      }
    },

    // 註冊
    register: async (userData) => {
      update(state => ({ ...state, loading: true, error: null }));
      
      try {
        const { user, token } = await apiClient.auth.register(userData);
        
        if (browser) {
          localStorage.setItem('auth_token', token);
        }
        
        set({
          isAuthenticated: true,
          user,
          token,
          loading: false,
          error: null
        });
        
        return { success: true };
      } catch (error) {
        set({
          isAuthenticated: false,
          user: null,
          token: null,
          loading: false,
          error: error.message
        });
        return { success: false, error: error.message };
      }
    },

    // 登出
    logout: () => {
      if (browser) {
        localStorage.removeItem('auth_token');
      }
      
      set({
        isAuthenticated: false,
        user: null,
        token: null,
        loading: false,
        error: null
      });
    },

    // 更新用戶資料
    updateUser: (userData) => {
      update(state => ({
        ...state,
        user: { ...state.user, ...userData }
      }));
    },

    // 清除錯誤
    clearError: () => {
      update(state => ({ ...state, error: null }));
    }
  };
};

export const authStore = createAuthStore();

// 在瀏覽器中自動初始化
if (browser) {
  authStore.init();
}