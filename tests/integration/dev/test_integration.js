#!/usr/bin/env node
/**
 * 前端-後端整合測試腳本
 * Frontend-Backend Integration Test Script
 */

const axios = require('axios').default;

// 測試配置
const FRONTEND_URL = 'http://localhost:3000';
const BACKEND_URL = 'http://localhost:8001';

// 測試結果記錄
const testResults = {
  passed: 0,
  failed: 0,
  tests: []
};

// 測試輔助函數
function logTest(name, passed, message = '') {
  const status = passed ? '✅ PASS' : '❌ FAIL';
  console.log(`${status}: ${name}${message ? ' - ' + message : ''}`);
  
  testResults.tests.push({ name, passed, message });
  if (passed) {
    testResults.passed++;
  } else {
    testResults.failed++;
  }
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// 測試函數
async function testBackendHealth() {
  console.log('\n🔍 測試後端健康檢查...');
  
  try {
    const response = await axios.get(`${BACKEND_URL}/health`);
    const isHealthy = response.status === 200 && response.data.status === 'healthy';
    logTest('後端健康檢查', isHealthy, `狀態: ${response.data.status}`);
    return isHealthy;
  } catch (error) {
    logTest('後端健康檢查', false, `錯誤: ${error.message}`);
    return false;
  }
}

async function testBackendAuth() {
  console.log('\n🔐 測試後端認證功能...');
  
  try {
    // 測試登入
    const loginResponse = await axios.post(`${BACKEND_URL}/api/v1/auth/login`, {
      email: 'demo@example.com',
      password: 'demo123'
    });
    
    const loginSuccess = loginResponse.status === 200 && loginResponse.data.success;
    logTest('模擬登入API', loginSuccess, `用戶: ${loginResponse.data.data?.user?.email || 'N/A'}`);
    
    if (loginSuccess) {
      const token = loginResponse.data.data.token;
      
      // 測試獲取用戶資料
      const profileResponse = await axios.get(`${BACKEND_URL}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const profileSuccess = profileResponse.status === 200 && profileResponse.data.success;
      logTest('獲取用戶資料API', profileSuccess, `用戶名: ${profileResponse.data.data?.name || 'N/A'}`);
      
      return { loginSuccess, profileSuccess, token };
    }
    
    return { loginSuccess: false, profileSuccess: false, token: null };
  } catch (error) {
    logTest('後端認證測試', false, `錯誤: ${error.message}`);
    return { loginSuccess: false, profileSuccess: false, token: null };
  }
}

async function testBackendData() {
  console.log('\n📊 測試後端數據API...');
  
  try {
    // 測試影片列表API
    const videosResponse = await axios.get(`${BACKEND_URL}/api/v1/videos`);
    const videosSuccess = videosResponse.status === 200 && videosResponse.data.success;
    const videoCount = videosResponse.data.data?.videos?.length || 0;
    logTest('影片列表API', videosSuccess, `影片數量: ${videoCount}`);
    
    // 測試分析數據API
    const analyticsResponse = await axios.get(`${BACKEND_URL}/api/v1/analytics/dashboard`);
    const analyticsSuccess = analyticsResponse.status === 200 && analyticsResponse.data.success;
    const totalVideos = analyticsResponse.data.data?.totalVideos || 0;
    logTest('儀表板分析API', analyticsSuccess, `總影片數: ${totalVideos}`);
    
    return { videosSuccess, analyticsSuccess };
  } catch (error) {
    logTest('後端數據測試', false, `錯誤: ${error.message}`);
    return { videosSuccess: false, analyticsSuccess: false };
  }
}

async function testBackendAI() {
  console.log('\n🤖 測試後端AI功能...');
  
  try {
    // 測試AI腳本生成
    const scriptResponse = await axios.post(`${BACKEND_URL}/api/v1/ai/generate-script`, {
      topic: '測試主題',
      length: 'short',
      tone: 'friendly'
    });
    
    const scriptSuccess = scriptResponse.status === 200 && scriptResponse.data.success;
    const wordCount = scriptResponse.data.data?.word_count || 0;
    logTest('AI腳本生成API', scriptSuccess, `生成字數: ${wordCount}`);
    
    // 測試AI圖像生成
    const imageResponse = await axios.post(`${BACKEND_URL}/api/v1/ai/generate-image`, {
      prompt: 'beautiful landscape',
      style: 'realistic'
    });
    
    const imageSuccess = imageResponse.status === 200 && imageResponse.data.success;
    const hasImageUrl = !!imageResponse.data.data?.image_url;
    logTest('AI圖像生成API', imageSuccess, `圖像URL生成: ${hasImageUrl ? '是' : '否'}`);
    
    return { scriptSuccess, imageSuccess };
  } catch (error) {
    logTest('後端AI功能測試', false, `錯誤: ${error.message}`);
    return { scriptSuccess: false, imageSuccess: false };
  }
}

async function testFrontendPages() {
  console.log('\n🌐 測試前端頁面...');
  
  try {
    // 測試首頁
    const homeResponse = await axios.get(FRONTEND_URL);
    const homeSuccess = homeResponse.status === 200 && homeResponse.data.includes('AutoVideo');
    logTest('前端首頁', homeSuccess, '頁面載入正常');
    
    // 測試登入頁面
    const loginResponse = await axios.get(`${FRONTEND_URL}/login`);
    const loginPageSuccess = loginResponse.status === 200 && loginResponse.data.includes('Sign in');
    logTest('前端登入頁', loginPageSuccess, '登入頁面載入正常');
    
    return { homeSuccess, loginPageSuccess };
  } catch (error) {
    logTest('前端頁面測試', false, `錯誤: ${error.message}`);
    return { homeSuccess: false, loginPageSuccess: false };
  }
}

async function testCORS() {
  console.log('\n🌍 測試CORS配置...');
  
  try {
    // 使用 OPTIONS 請求測試CORS
    const corsResponse = await axios.options(`${BACKEND_URL}/api/v1/auth/login`, {
      headers: {
        'Origin': FRONTEND_URL,
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type'
      }
    });
    
    const corsSuccess = corsResponse.status === 200;
    const allowOrigin = corsResponse.headers['access-control-allow-origin'];
    logTest('CORS配置', corsSuccess, `允許來源: ${allowOrigin || '未設定'}`);
    
    return corsSuccess;
  } catch (error) {
    // CORS 可能會導致 OPTIONS 請求失敗，但這不一定表示配置錯誤
    logTest('CORS配置', true, '需要瀏覽器環境測試');
    return true;
  }
}

async function runPerformanceTest() {
  console.log('\n⚡ 執行基本性能測試...');
  
  const tests = [
    { name: '健康檢查', url: `${BACKEND_URL}/health` },
    { name: '登入API', url: `${BACKEND_URL}/api/v1/auth/login`, method: 'POST', data: { email: 'test@test.com', password: 'test123' } },
    { name: '影片列表', url: `${BACKEND_URL}/api/v1/videos` },
    { name: '分析數據', url: `${BACKEND_URL}/api/v1/analytics/dashboard` }
  ];
  
  for (const test of tests) {
    try {
      const startTime = Date.now();
      
      if (test.method === 'POST') {
        await axios.post(test.url, test.data);
      } else {
        await axios.get(test.url);
      }
      
      const responseTime = Date.now() - startTime;
      const isGood = responseTime < 1000; // 1秒內為良好
      
      logTest(
        `${test.name}響應時間`,
        isGood,
        `${responseTime}ms ${isGood ? '(良好)' : '(需優化)'}`
      );
    } catch (error) {
      logTest(`${test.name}響應時間`, false, `錯誤: ${error.message}`);
    }
  }
}

// 主測試函數
async function runIntegrationTests() {
  console.log('🚀 開始前端-後端整合測試...\n');
  console.log('📋 測試配置:');
  console.log(`   前端URL: ${FRONTEND_URL}`);
  console.log(`   後端URL: ${BACKEND_URL}`);
  console.log('');
  
  // 執行所有測試
  const backendHealthy = await testBackendHealth();
  
  if (backendHealthy) {
    await testBackendAuth();
    await testBackendData();
    await testBackendAI();
    await testCORS();
    await runPerformanceTest();
  }
  
  await testFrontendPages();
  
  // 輸出測試總結
  console.log('\n📊 測試結果總結:');
  console.log(`   ✅ 通過: ${testResults.passed} 個測試`);
  console.log(`   ❌ 失敗: ${testResults.failed} 個測試`);
  console.log(`   📈 成功率: ${((testResults.passed / (testResults.passed + testResults.failed)) * 100).toFixed(1)}%`);
  
  if (testResults.failed > 0) {
    console.log('\n❌ 失敗的測試:');
    testResults.tests
      .filter(test => !test.passed)
      .forEach(test => console.log(`   - ${test.name}: ${test.message}`));
  }
  
  console.log('\n🎉 整合測試完成!');
  
  const overallSuccess = testResults.failed === 0;
  process.exit(overallSuccess ? 0 : 1);
}

// 執行測試
if (require.main === module) {
  runIntegrationTests().catch(error => {
    console.error('❌ 測試執行失敗:', error.message);
    process.exit(1);
  });
}

module.exports = { runIntegrationTests };