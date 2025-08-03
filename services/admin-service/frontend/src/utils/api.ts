import axios from 'axios';
import type { AxiosInstance, AxiosRequestConfig } from 'axios';
import { authStore, authActions } from '$stores/auth';
import { get } from 'svelte/store';

// API 基礎 URL
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

// 創建 axios 實例
const api: AxiosInstance = axios.create({
	baseURL: BASE_URL,
	timeout: 30000,
	headers: {
		'Content-Type': 'application/json'
	}
});

// 請求攔截器 - 添加認證 token
api.interceptors.request.use((config) => {
	const auth = get(authStore);
	if (auth.token) {
		config.headers.Authorization = `Bearer ${auth.token}`;
	}
	return config;
});

// 響應攔截器 - 處理認證錯誤
api.interceptors.response.use(
	(response) => response,
	(error) => {
		if (error.response?.status === 401) {
			authActions.logout();
			if (typeof window !== 'undefined') {
				window.location.href = '/login';
			}
		}
		return Promise.reject(error);
	}
);

// API 接口定義
export const apiClient = {
	// 認證相關
	auth: {
		login: (username: string, password: string) =>
			api.post('/admin/auth/login', { username, password }),
		
		me: () =>
			api.get('/admin/auth/me'),
		
		logout: () =>
			api.post('/admin/auth/logout')
	},

	// AI Provider 管理
	aiProviders: {
		list: (params?: any) =>
			api.get('/admin/ai-providers', { params }),
		
		get: (id: number) =>
			api.get(`/admin/ai-providers/${id}`),
		
		create: (data: any) =>
			api.post('/admin/ai-providers', data),
		
		update: (id: number, data: any) =>
			api.put(`/admin/ai-providers/${id}`, data),
		
		delete: (id: number) =>
			api.delete(`/admin/ai-providers/${id}`),
		
		test: (id: number) =>
			api.post(`/admin/ai-providers/${id}/test`)
	},

	// 爬蟲配置管理
	crawlers: {
		list: (params?: any) =>
			api.get('/admin/crawler-configs', { params }),
		
		get: (id: number) =>
			api.get(`/admin/crawler-configs/${id}`),
		
		create: (data: any) =>
			api.post('/admin/crawler-configs', data),
		
		update: (id: number, data: any) =>
			api.put(`/admin/crawler-configs/${id}`, data),
		
		delete: (id: number) =>
			api.delete(`/admin/crawler-configs/${id}`),
		
		run: (id: number) =>
			api.post(`/admin/crawler-configs/${id}/run`),
		
		getResults: (id: number, params?: any) =>
			api.get(`/admin/crawler-configs/${id}/results`, { params }),
			
		exportResults: (id: number, params?: any) =>
			api.get(`/admin/crawler-configs/${id}/export`, { params, responseType: 'blob' })
	},

	// 社交媒體趨勢
	socialTrends: {
		configs: {
			list: (params?: any) =>
				api.get('/admin/social-trend-configs', { params }),
			
			create: (data: any) =>
				api.post('/admin/social-trend-configs', data),
			
			update: (id: number, data: any) =>
				api.put(`/admin/social-trend-configs/${id}`, data),
			
			delete: (id: number) =>
				api.delete(`/admin/social-trend-configs/${id}`)
		},
		
		keywords: (params?: any) =>
			api.get('/admin/trending-keywords', { params }),
		
		topKeywords: (params?: any) =>
			api.get('/admin/trending-keywords/top', { params }),
		
		stats: (params?: any) =>
			api.get('/admin/trending-keywords/stats', { params }),
		
		collect: (platform?: string) =>
			api.post('/admin/social-trends/collect', { platform })
	},

	// 關鍵字趨勢 (新版本 API)
	keywordTrends: {
		// 獲取關鍵字趨勢列表
		list: (params?: any) =>
			api.get('/admin/keyword-trends', { params }),
		
		// 獲取各平台熱門關鍵字排行榜
		platforms: (params?: any) =>
			api.get('/admin/keyword-trends/platforms', { params }),
		
		// 獲取趨勢統計數據
		statistics: (params?: any) =>
			api.get('/admin/keyword-trends/statistics', { params }),
		
		// 搜尋關鍵字趨勢
		search: (query: string, params?: any) =>
			api.get('/admin/keyword-trends/search', { params: { q: query, ...params } }),
		
		// 手動觸發趨勢數據收集
		collect: (data?: any) =>
			api.post('/admin/keyword-trends/collect', data),
		
		// 根據日期範圍獲取趨勢數據
		dateRange: (params: any) =>
			api.get('/admin/keyword-trends/date-range', { params })
	},

	// 系統日誌
	logs: {
		list: (params?: any) =>
			api.get('/admin/logs', { params }),
		
		stats: (params?: any) =>
			api.get('/admin/logs/stats', { params }),
		
		export: (params?: any) =>
			api.post('/admin/logs/export', params),
		
		cleanup: (days: number) =>
			api.delete(`/admin/logs/cleanup?days=${days}`)
	},

	// 用戶管理
	users: {
		list: (params?: any) =>
			api.get('/admin/users', { params }),
		
		get: (id: number) =>
			api.get(`/admin/users/${id}`),
		
		create: (data: any) =>
			api.post('/admin/users', data),
		
		update: (id: number, data: any) =>
			api.put(`/admin/users/${id}`, data),
		
		delete: (id: number) =>
			api.delete(`/admin/users/${id}`)
	},

	// 儀表板統計
	dashboard: {
		stats: () =>
			api.get('/admin/dashboard/stats'),
		
		overview: () =>
			api.get('/admin/dashboard/overview')
	},

	// 系統健康檢查
	health: () =>
		api.get('/admin/health')
};

export default api;