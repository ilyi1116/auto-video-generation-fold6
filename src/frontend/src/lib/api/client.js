/**
 * API 客戶端
 * 統一管理所有後端API調用
 */

import { browser } from '$app/environment';

const API_BASE_URL = browser 
  ? (import.meta.env.VITE_API_URL || 'http://localhost:8001')
  : 'http://localhost:8001';

// HTTP 客戶端基類
class HttpClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  // 獲取認證 token
  getAuthToken() {
    if (!browser) return null;
    return localStorage.getItem('auth_token');
  }

  // 通用請求方法
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.getAuthToken();
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` })
      }
    };

    const requestOptions = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers
      }
    };

    try {
      const response = await fetch(url, requestOptions);
      
      // 處理 HTTP 錯誤
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Request failed' }));
        throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }
      
      // 嘗試解析 JSON，如果失敗則返回空對象
      return await response.json().catch(() => ({}));
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // GET 請求
  get(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    return this.request(url, { method: 'GET' });
  }

  // POST 請求
  post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  // PUT 請求
  put(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  // DELETE 請求
  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // 文件上傳
  async upload(endpoint, file, additionalData = {}) {
    const formData = new FormData();
    formData.append('file', file);
    
    // 添加額外數據
    Object.keys(additionalData).forEach(key => {
      formData.append(key, additionalData[key]);
    });

    const token = this.getAuthToken();
    
    return this.request(endpoint, {
      method: 'POST',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` })
        // 注意：不設置 Content-Type，讓瀏覽器自動設置 multipart/form-data
      },
      body: formData
    });
  }
}

// 創建 HTTP 客戶端實例
const httpClient = new HttpClient(API_BASE_URL);

// API 模組
export const apiClient = {
  // 認證相關 API
  auth: {
    login: (email, password) => 
      httpClient.post('/api/v1/auth/login', { email, password }),
    
    register: (userData) => 
      httpClient.post('/api/v1/auth/register', userData),
    
    logout: () => 
      httpClient.post('/api/v1/auth/logout'),
    
    verifyToken: (token) => 
      httpClient.get('/api/v1/auth/verify'),
    
    refreshToken: () => 
      httpClient.post('/api/v1/auth/refresh'),
    
    forgotPassword: (email) => 
      httpClient.post('/api/v1/auth/forgot-password', { email }),
    
    resetPassword: (token, password) => 
      httpClient.post('/api/v1/auth/reset-password', { token, password })
  },

  // 用戶相關 API
  user: {
    getProfile: () => 
      httpClient.get('/api/v1/user/profile'),
    
    updateProfile: (userData) => 
      httpClient.put('/api/v1/user/profile', userData),
    
    changePassword: (currentPassword, newPassword) => 
      httpClient.post('/api/v1/user/change-password', { 
        current_password: currentPassword, 
        new_password: newPassword 
      })
  },

  // 專案相關 API
  projects: {
    list: (params = {}) => 
      httpClient.get('/api/v1/projects', params),
    
    create: (projectData) => 
      httpClient.post('/api/v1/projects', projectData),
    
    get: (projectId) => 
      httpClient.get(`/api/v1/projects/${projectId}`),
    
    update: (projectId, projectData) => 
      httpClient.put(`/api/v1/projects/${projectId}`, projectData),
    
    delete: (projectId) => 
      httpClient.delete(`/api/v1/projects/${projectId}`)
  },

  // AI 服務相關 API
  ai: {
    // 腳本生成
    generateScript: (topic, platform = 'youtube', style = 'educational', duration = 60, language = 'zh-TW') => 
      httpClient.post('/api/v1/generate/script', { topic, platform, style, duration, language }),
    
    // 圖像生成
    generateImage: (prompt, style = 'realistic', size = '1024x1024') => 
      httpClient.post('/api/v1/generate/image', { prompt, style, size }),
    
    // 音樂生成
    generateMusic: (prompt, style = 'ambient', duration = 60) => 
      httpClient.post('/api/v1/generate/music', { prompt, style, duration }),
    
    // 語音合成
    synthesizeVoice: (text, voice = 'alloy', speed = 1.0) => 
      httpClient.post('/api/v1/generate/voice', { text, voice, speed })
  },

  // 影片相關 API
  videos: {
    list: (params = {}) => 
      httpClient.get('/api/v1/videos', params),
    
    create: (videoData) => 
      httpClient.post('/api/v1/videos', videoData),
    
    get: (videoId) => 
      httpClient.get(`/api/v1/videos/${videoId}`),
    
    update: (videoId, videoData) => 
      httpClient.put(`/api/v1/videos/${videoId}`, videoData),
    
    delete: (videoId) => 
      httpClient.delete(`/api/v1/videos/${videoId}`),
    
    render: (videoId, options = {}) => 
      httpClient.post(`/api/v1/videos/${videoId}/render`, options),
    
    getStatus: (videoId) => 
      httpClient.get(`/api/v1/videos/${videoId}/status`)
  },

  // 檔案上傳相關 API
  upload: {
    audio: (file, options = {}) => 
      httpClient.upload('/api/v1/upload/audio', file, options),
    
    image: (file, options = {}) => 
      httpClient.upload('/api/v1/upload/image', file, options),
    
    video: (file, options = {}) => 
      httpClient.upload('/api/v1/upload/video', file, options)
  },

  // 社交媒體相關 API
  social: {
    getPlatforms: () => 
      httpClient.get('/api/v1/social/platforms'),
    
    connectPlatform: (platform, credentials) => 
      httpClient.post(`/api/v1/social/connect/${platform}`, credentials),
    
    publish: (videoId, platforms, options = {}) => 
      httpClient.post('/api/v1/social/publish', { video_id: videoId, platforms, ...options }),
    
    getPublishStatus: (publishId) => 
      httpClient.get(`/api/v1/social/publish/${publishId}/status`)
  },

  // 趨勢分析相關 API
  trends: {
    getTopics: (platform = 'all', limit = 10) => 
      httpClient.get('/api/v1/trends/topics', { platform, limit }),
    
    analyzeContent: (content) => 
      httpClient.post('/api/v1/trends/analyze', { content }),
    
    getSuggestions: (topic, options = {}) => 
      httpClient.post('/api/v1/trends/suggestions', { topic, ...options })
  },

  // 分析相關 API
  analytics: {
    getDashboard: (timeRange = '7d') => 
      httpClient.get('/api/v1/analytics/dashboard', { time_range: timeRange }),
    
    getVideoMetrics: (videoId) => 
      httpClient.get(`/api/v1/analytics/videos/${videoId}`),
    
    getPerformanceReport: (params = {}) => 
      httpClient.get('/api/v1/analytics/performance', params)
  },

  // 系統健康檢查
  health: {
    check: () => 
      httpClient.get('/health'),
    
    ping: () => 
      httpClient.get('/ping')
  }
};

export default apiClient;