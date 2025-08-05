/**
 * K6 負載測試腳本
 * 測試生產環境的性能和穩定性
 */

import http from 'k6/http';
import { check, group, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// 自定義指標
const failureRate = new Rate('failure_rate');
const apiResponseTime = new Trend('api_response_time');
const authenticationErrors = new Counter('authentication_errors');
const fileUploadSuccess = new Counter('file_upload_success');

// 測試配置
export const options = {
  stages: [
    { duration: '2m', target: 10 },   // 預熱：2分鐘內達到10個用戶
    { duration: '5m', target: 10 },   // 穩定：維持10個用戶5分鐘
    { duration: '3m', target: 50 },   // 增壓：3分鐘內增加到50個用戶
    { duration: '10m', target: 50 },  // 高負載：維持50個用戶10分鐘
    { duration: '3m', target: 100 },  // 峰值：3分鐘內增加到100個用戶
    { duration: '5m', target: 100 },  // 峰值維持：維持100個用戶5分鐘
    { duration: '5m', target: 0 },    // 冷卻：5分鐘內減少到0個用戶
  ],
  thresholds: {
    // 95% 的請求響應時間應小於 500ms
    http_req_duration: ['p(95)<500'],
    // 99% 的請求響應時間應小於 1000ms
    'http_req_duration{expected_response:true}': ['p(99)<1000'],
    // 錯誤率應小於 1%
    http_req_failed: ['rate<0.01'],
    // 自定義失敗率應小於 5%
    failure_rate: ['rate<0.05'],
    // API 響應時間 95% 應小於 300ms
    api_response_time: ['p(95)<300'],
  },
};

// 測試配置常數
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const API_BASE_URL = `${BASE_URL}/api/v1`;

// 測試用戶數據
const users = [
  { email: 'user1@test.com', password: 'testpass123' },
  { email: 'user2@test.com', password: 'testpass123' },
  { email: 'user3@test.com', password: 'testpass123' },
  { email: 'user4@test.com', password: 'testpass123' },
  { email: 'user5@test.com', password: 'testpass123' },
];

let authToken = '';

export function setup() {
  // 設置階段：創建測試用戶和取得認證令牌
  console.log('設置測試環境...');
  
  const loginResponse = http.post(`${API_BASE_URL}/auth/login`, {
    email: users[0].email,
    password: users[0].password,
  });

  if (loginResponse.status === 200) {
    const data = JSON.parse(loginResponse.body);
    return { authToken: data.tokens.access_token };
  }
  
  return { authToken: null };
}

export default function(data) {
  const user = users[Math.floor(Math.random() * users.length)];
  
  group('用戶認證流程', () => {
    testUserAuthentication(user);
  });

  sleep(1);

  group('API 端點負載測試', () => {
    testAPIEndpoints(data.authToken);
  });

  sleep(1);

  group('檔案上傳負載測試', () => {
    testFileUpload(data.authToken);
  });

  sleep(2);

  group('影片生成負載測試', () => {
    testVideoGeneration(data.authToken);
  });

  sleep(3);
}

function testUserAuthentication(user) {
  const startTime = Date.now();
  
  const response = http.post(`${API_BASE_URL}/auth/login`, {
    email: user.email,
    password: user.password,
  }, {
    headers: {
      'Content-Type': 'application/json',
    },
  });

  const responseTime = Date.now() - startTime;
  apiResponseTime.add(responseTime);

  const success = check(response, {
    '登入狀態碼為 200': (r) => r.status === 200,
    '登入響應時間 < 1000ms': (r) => responseTime < 1000,
    '返回訪問令牌': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.tokens && body.tokens.access_token;
      } catch (e) {
        return false;
      }
    },
  });

  if (!success) {
    failureRate.add(1);
    authenticationErrors.add(1);
  } else {
    failureRate.add(0);
    const body = JSON.parse(response.body);
    authToken = body.tokens.access_token;
  }
}

function testAPIEndpoints(token) {
  const endpoints = [
    { path: '/health', method: 'GET' },
    { path: '/user/profile', method: 'GET' },
    { path: '/user/projects', method: 'GET' },
    { path: '/user/usage-stats', method: 'GET' },
  ];

  endpoints.forEach(endpoint => {
    const startTime = Date.now();
    const headers = token ? {
      'Authorization': `Bearer ${token}`,
    } : {};

    let response;
    if (endpoint.method === 'GET') {
      response = http.get(`${API_BASE_URL}${endpoint.path}`, { headers });
    }

    const responseTime = Date.now() - startTime;
    apiResponseTime.add(responseTime);

    const success = check(response, {
      [`${endpoint.path} 狀態碼正確`]: (r) => 
        endpoint.path === '/health' ? r.status === 200 : 
        token ? r.status === 200 : r.status === 401,
      [`${endpoint.path} 響應時間 < 500ms`]: (r) => responseTime < 500,
      [`${endpoint.path} 內容類型正確`]: (r) => 
        r.headers['Content-Type'] && r.headers['Content-Type'].includes('application/json'),
    });

    if (!success) {
      failureRate.add(1);
    } else {
      failureRate.add(0);
    }
  });
}

function testFileUpload(token) {
  if (!token) return;

  const startTime = Date.now();
  
  // 模擬音頻檔案上傳
  const audioData = new Uint8Array(1024 * 100); // 100KB 假音頻數據
  const formData = {
    file: http.file(audioData, 'test-audio.mp3', 'audio/mpeg'),
    project_id: '1',
  };

  const response = http.post(`${API_BASE_URL}/upload/audio`, formData, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  const responseTime = Date.now() - startTime;
  apiResponseTime.add(responseTime);

  const success = check(response, {
    '檔案上傳狀態碼為 200': (r) => r.status === 200,
    '檔案上傳響應時間 < 5000ms': (r) => responseTime < 5000,
    '返回檔案資訊': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.file_id && body.url;
      } catch (e) {
        return false;
      }
    },
  });

  if (success) {
    fileUploadSuccess.add(1);
    failureRate.add(0);
  } else {
    failureRate.add(1);
  }
}

function testVideoGeneration(token) {
  if (!token) return;

  // 測試影片生成請求
  const startTime = Date.now();
  
  const generationRequest = {
    project_id: 1,
    script: '這是一個測試腳本',
    style: 'modern',
    resolution: '1920x1080',
  };

  const response = http.post(`${API_BASE_URL}/video/generate`, 
    JSON.stringify(generationRequest), {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  const responseTime = Date.now() - startTime;
  apiResponseTime.add(responseTime);

  const success = check(response, {
    '影片生成請求狀態碼正確': (r) => r.status === 200 || r.status === 202,
    '影片生成響應時間 < 2000ms': (r) => responseTime < 2000,
    '返回工作 ID': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.job_id;
      } catch (e) {
        return false;
      }
    },
  });

  if (success) {
    const body = JSON.parse(response.body);
    if (body.job_id) {
      // 測試狀態查詢
      testJobStatus(token, body.job_id);
    }
    failureRate.add(0);
  } else {
    failureRate.add(1);
  }
}

function testJobStatus(token, jobId) {
  const startTime = Date.now();
  
  const response = http.get(`${API_BASE_URL}/video/status/${jobId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  const responseTime = Date.now() - startTime;
  apiResponseTime.add(responseTime);

  check(response, {
    '工作狀態查詢成功': (r) => r.status === 200,
    '狀態查詢響應時間 < 300ms': (r) => responseTime < 300,
    '返回狀態資訊': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.status && ['pending', 'processing', 'completed', 'failed'].includes(body.status);
      } catch (e) {
        return false;
      }
    },
  });
}

export function teardown(data) {
  // 清理階段
  console.log('清理測試環境...');
  
  // 可以在這裡清理測試數據
  if (data.authToken) {
    http.post(`${API_BASE_URL}/auth/logout`, {}, {
      headers: {
        'Authorization': `Bearer ${data.authToken}`,
      },
    });
  }
}

export function handleSummary(data) {
  // 自定義測試結果報告
  const summary = {
    testStart: data.state.testRunDurationMs,
    totalRequests: data.metrics.http_reqs.values.count,
    failedRequests: data.metrics.http_req_failed.values.rate * data.metrics.http_reqs.values.count,
    averageResponseTime: data.metrics.http_req_duration.values.avg,
    p95ResponseTime: data.metrics.http_req_duration.values['p(95)'],
    p99ResponseTime: data.metrics.http_req_duration.values['p(99)'],
    maxResponseTime: data.metrics.http_req_duration.values.max,
    rps: data.metrics.http_reqs.values.rate,
    failureRate: data.metrics.failure_rate ? data.metrics.failure_rate.values.rate : 0,
    authErrors: data.metrics.authentication_errors ? data.metrics.authentication_errors.values.count : 0,
    fileUploads: data.metrics.file_upload_success ? data.metrics.file_upload_success.values.count : 0,
  };

  return {
    'load-test-summary.json': JSON.stringify(summary, null, 2),
    stdout: generateTextSummary(summary),
  };
}

function generateTextSummary(summary) {
  return `
╔══════════════════════════════════════════════════════════════╗
║                    負載測試結果摘要                          ║
╠══════════════════════════════════════════════════════════════╣
║ 總請求數: ${summary.totalRequests.toFixed(0).padStart(10)} 個                           ║
║ 失敗請求: ${summary.failedRequests.toFixed(0).padStart(10)} 個                           ║
║ 失敗率:   ${(summary.failureRate * 100).toFixed(2).padStart(8)}%                           ║
║ 平均回應: ${summary.averageResponseTime.toFixed(2).padStart(8)}ms                         ║
║ P95 回應: ${summary.p95ResponseTime.toFixed(2).padStart(8)}ms                         ║
║ P99 回應: ${summary.p99ResponseTime.toFixed(2).padStart(8)}ms                         ║
║ 最大回應: ${summary.maxResponseTime.toFixed(2).padStart(8)}ms                         ║
║ 請求速率: ${summary.rps.toFixed(2).padStart(8)} req/s                       ║
║ 認證錯誤: ${summary.authErrors.toFixed(0).padStart(10)} 個                           ║
║ 檔案上傳: ${summary.fileUploads.toFixed(0).padStart(10)} 個                           ║
╚══════════════════════════════════════════════════════════════╝
  `;
}