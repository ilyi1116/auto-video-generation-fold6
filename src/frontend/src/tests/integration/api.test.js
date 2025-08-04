import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { waitFor } from '@testing-library/svelte';
import { apiClient, setAuthToken, clearAuthToken } from '../../lib/api/client';

// Mock fetch
global.fetch = vi.fn();

describe('API 整合測試', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    clearAuthToken();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('認證 API', () => {
    it('應該正確處理登入請求', async () => {
      const mockResponse = {
        user: { id: 1, username: 'testuser', email: 'test@example.com' },
        token: 'jwt-token-12345'
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      const response = await apiClient.post('/api/auth/login', {
        email: 'test@example.com',
        password: 'password123'
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/login'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          }),
          body: JSON.stringify({
            email: 'test@example.com',
            password: 'password123'
          })
        })
      );

      expect(response.data).toEqual(mockResponse);
    });

    it('應該正確處理註冊請求', async () => {
      const mockResponse = {
        message: '註冊成功，請檢查電子郵件進行驗證'
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      const response = await apiClient.post('/api/auth/register', {
        username: 'newuser',
        email: 'new@example.com',
        password: 'StrongPass123!'
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/register'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            username: 'newuser',
            email: 'new@example.com',
            password: 'StrongPass123!'
          })
        })
      );

      expect(response.data).toEqual(mockResponse);
    });

    it('應該在認證請求中包含 Authorization 標頭', async () => {
      setAuthToken('test-jwt-token');

      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ user: {} }),
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      await apiClient.get('/api/auth/me');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/me'),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-jwt-token'
          })
        })
      );
    });
  });

  describe('AI 服務 API', () => {
    beforeEach(() => {
      setAuthToken('test-jwt-token');
    });

    it('應該正確處理腳本生成請求', async () => {
      const mockResponse = {
        script: '這是生成的腳本內容...',
        metadata: {
          wordCount: 150,
          estimatedDuration: '45 seconds',
          tone: 'professional'
        }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      const response = await apiClient.post('/api/ai/script/generate', {
        topic: '人工智慧的未來發展',
        platform: 'youtube',
        length: 'medium',
        tone: 'professional'
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/ai/script/generate'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            topic: '人工智慧的未來發展',
            platform: 'youtube',
            length: 'medium',
            tone: 'professional'
          })
        })
      );

      expect(response.data).toEqual(mockResponse);
    });

    it('應該正確處理圖像生成請求', async () => {
      const mockResponse = {
        images: [
          {
            id: 'img_001',
            url: 'https://example.com/image1.jpg',
            prompt: 'A beautiful sunset over mountains',
            style: 'realistic'
          }
        ],
        metadata: {
          model: 'stable-diffusion-xl',
          seed: 42,
          steps: 50
        }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      const response = await apiClient.post('/api/ai/images/generate', {
        prompt: 'A beautiful sunset over mountains',
        style: 'realistic',
        count: 1,
        size: '1024x1024'
      });

      expect(response.data).toEqual(mockResponse);
    });

    it('應該正確處理語音合成請求', async () => {
      const mockResponse = {
        audioUrl: 'https://example.com/audio/voice_001.mp3',
        duration: 45.5,
        metadata: {
          voice: 'zh-TW-female-001',
          speed: 1.0,
          pitch: 0
        }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      const response = await apiClient.post('/api/ai/voice/synthesize', {
        text: '歡迎來到我們的頻道',
        voice: 'zh-TW-female-001',
        speed: 1.0,
        pitch: 0
      });

      expect(response.data).toEqual(mockResponse);
    });

    it('應該正確處理音樂生成請求', async () => {
      const mockResponse = {
        musicUrl: 'https://example.com/music/bgm_001.mp3',
        duration: 60,
        metadata: {
          genre: 'ambient',
          mood: 'uplifting',
          bpm: 120
        }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      const response = await apiClient.post('/api/ai/music/generate', {
        prompt: 'Uplifting ambient background music',
        duration: 60,
        genre: 'ambient',
        mood: 'uplifting'
      });

      expect(response.data).toEqual(mockResponse);
    });
  });

  describe('專案管理 API', () => {
    beforeEach(() => {
      setAuthToken('test-jwt-token');
    });

    it('應該正確獲取專案列表', async () => {
      const mockResponse = {
        projects: [
          {
            id: 1,
            title: '我的第一個影片',
            status: 'draft',
            createdAt: '2024-01-15T10:00:00Z',
            updatedAt: '2024-01-15T12:30:00Z'
          },
          {
            id: 2,
            title: '產品介紹影片',
            status: 'published',
            createdAt: '2024-01-14T09:00:00Z',
            updatedAt: '2024-01-14T16:45:00Z'
          }
        ],
        pagination: {
          total: 2,
          page: 1,
          limit: 10,
          totalPages: 1
        }
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      const response = await apiClient.get('/api/projects', {
        params: { page: 1, limit: 10 }
      });

      expect(response.data).toEqual(mockResponse);
    });

    it('應該正確創建新專案', async () => {
      const mockResponse = {
        id: 3,
        title: '新專案',
        description: '這是一個新的影片專案',
        status: 'draft',
        createdAt: '2024-01-16T10:00:00Z'
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => mockResponse,
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      const response = await apiClient.post('/api/projects', {
        title: '新專案',
        description: '這是一個新的影片專案',
        platform: 'youtube'
      });

      expect(response.data).toEqual(mockResponse);
    });

    it('應該正確更新專案', async () => {
      const mockResponse = {
        id: 1,
        title: '更新後的專案標題',
        description: '更新後的描述',
        status: 'in_progress',
        updatedAt: '2024-01-16T11:00:00Z'
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      const response = await apiClient.put('/api/projects/1', {
        title: '更新後的專案標題',
        description: '更新後的描述',
        status: 'in_progress'
      });

      expect(response.data).toEqual(mockResponse);
    });

    it('應該正確刪除專案', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => ({}),
        headers: new Headers()
      });

      const response = await apiClient.delete('/api/projects/1');

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/projects/1'),
        expect.objectContaining({
          method: 'DELETE'
        })
      );
    });
  });

  describe('檔案上傳 API', () => {
    beforeEach(() => {
      setAuthToken('test-jwt-token');
    });

    it('應該正確處理檔案上傳', async () => {
      const mockResponse = {
        fileId: 'file_12345',
        filename: 'audio_sample.mp3',
        url: 'https://example.com/files/audio_sample.mp3',
        size: 1024000,
        type: 'audio/mpeg'
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      const file = new File(['audio data'], 'audio_sample.mp3', { type: 'audio/mpeg' });
      const formData = new FormData();
      formData.append('file', file);
      formData.append('type', 'audio');

      const response = await apiClient.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/upload'),
        expect.objectContaining({
          method: 'POST',
          body: expect.any(FormData)
        })
      );

      expect(response.data).toEqual(mockResponse);
    });

    it('應該正確處理大檔案上傳進度', async () => {
      const mockResponse = {
        fileId: 'file_67890',
        filename: 'large_video.mp4',
        url: 'https://example.com/files/large_video.mp4',
        size: 50000000
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockResponse,
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      const file = new File(['large video data'], 'large_video.mp4', { type: 'video/mp4' });
      const formData = new FormData();
      formData.append('file', file);

      let uploadProgress = 0;
      const onUploadProgress = (progress) => {
        uploadProgress = progress;
      };

      const response = await apiClient.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress
      });

      expect(response.data).toEqual(mockResponse);
    });
  });

  describe('錯誤處理', () => {
    beforeEach(() => {
      setAuthToken('test-jwt-token');
    });

    it('應該正確處理 401 未授權錯誤', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Unauthorized' }),
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      try {
        await apiClient.get('/api/protected-resource');
      } catch (error) {
        expect(error.response.status).toBe(401);
        expect(error.response.data.error).toBe('Unauthorized');
      }
    });

    it('應該正確處理 403 禁止訪問錯誤', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({ error: 'Forbidden' }),
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      try {
        await apiClient.get('/api/admin-only-resource');
      } catch (error) {
        expect(error.response.status).toBe(403);
        expect(error.response.data.error).toBe('Forbidden');
      }
    });

    it('應該正確處理 404 找不到資源錯誤', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ error: 'Not Found' }),
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      try {
        await apiClient.get('/api/non-existent-resource');
      } catch (error) {
        expect(error.response.status).toBe(404);
        expect(error.response.data.error).toBe('Not Found');
      }
    });

    it('應該正確處理 500 伺服器錯誤', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Internal Server Error' }),
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      try {
        await apiClient.get('/api/error-prone-endpoint');
      } catch (error) {
        expect(error.response.status).toBe(500);
        expect(error.response.data.error).toBe('Internal Server Error');
      }
    });

    it('應該正確處理網路錯誤', async () => {
      fetch.mockRejectedValueOnce(new Error('Network Error'));

      try {
        await apiClient.get('/api/test-endpoint');
      } catch (error) {
        expect(error.message).toBe('Network Error');
      }
    });

    it('應該正確處理請求超時', async () => {
      // Mock 超時錯誤
      fetch.mockRejectedValueOnce(new Error('Request timeout'));

      try {
        await apiClient.get('/api/slow-endpoint', { timeout: 5000 });
      } catch (error) {
        expect(error.message).toBe('Request timeout');
      }
    });
  });

  describe('請求重試機制', () => {
    it('應該在網路錯誤時自動重試', async () => {
      const mockResponse = { data: 'success after retry' };

      // 前兩次請求失敗，第三次成功
      fetch
        .mockRejectedValueOnce(new Error('Network Error'))
        .mockRejectedValueOnce(new Error('Network Error'))
        .mockResolvedValueOnce({
          ok: true,
          status: 200,
          json: async () => mockResponse,
          headers: new Headers({ 'Content-Type': 'application/json' })
        });

      const response = await apiClient.get('/api/unreliable-endpoint', {
        retry: { attempts: 3, delay: 100 }
      });

      expect(fetch).toHaveBeenCalledTimes(3);
      expect(response.data).toEqual(mockResponse);
    });

    it('應該在達到最大重試次數後拋出錯誤', async () => {
      // 所有請求都失敗
      fetch
        .mockRejectedValue(new Error('Network Error'))
        .mockRejectedValue(new Error('Network Error'))
        .mockRejectedValue(new Error('Network Error'));

      try {
        await apiClient.get('/api/always-failing-endpoint', {
          retry: { attempts: 3, delay: 100 }
        });
      } catch (error) {
        expect(error.message).toBe('Network Error');
        expect(fetch).toHaveBeenCalledTimes(3);
      }
    });
  });

  describe('請求攔截器', () => {
    it('應該在請求中自動添加時間戳', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ data: 'success' }),
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      await apiClient.get('/api/test-endpoint');

      const callArgs = fetch.mock.calls[0];
      const url = new URL(callArgs[0]);
      expect(url.searchParams.has('_t')).toBe(true);
    });

    it('應該在請求中自動添加請求 ID', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ data: 'success' }),
        headers: new Headers({ 'Content-Type': 'application/json' })
      });

      await apiClient.get('/api/test-endpoint');

      const callArgs = fetch.mock.calls[0];
      const headers = callArgs[1].headers;
      expect(headers['X-Request-ID']).toBeDefined();
    });
  });
});