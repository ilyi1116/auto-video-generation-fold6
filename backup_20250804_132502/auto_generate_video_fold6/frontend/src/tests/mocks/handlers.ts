import { http, HttpResponse } from 'msw';

export const handlers = [
  // 模擬 API 回應
  http.get('/api/health', () => {
    return HttpResponse.json({ status: 'ok' });
  }),
  
  http.get('/api/v1/status', () => {
    return HttpResponse.json({ status: 'operational' });
  }),
  
  http.post('/api/v1/auth/login', () => {
    return HttpResponse.json(
      { token: 'mock-jwt-token', user: { id: 1, username: 'testuser' } },
      { status: 200 }
    );
  }),
  
  http.get('/api/v1/videos', () => {
    return HttpResponse.json([
      { id: 1, title: 'Test Video', status: 'published' }
    ]);
  }),
  
  http.get('/api/v1/ai/models', () => {
    return HttpResponse.json([
      { id: 'gpt-4', name: 'GPT-4', type: 'text-generation' }
    ]);
  })
];