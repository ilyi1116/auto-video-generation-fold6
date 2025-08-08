#!/usr/bin/env node
/**
 * 測試前端 API 連接
 */

const fetch = require('node-fetch');

const API_BASE_URL = 'http://localhost:8000';

async function testRegister() {
  console.log('🔄 測試用戶註冊 API...');
  
  const userData = {
    first_name: 'Test',
    last_name: 'User',
    email: 'frontend.test@example.com',
    password: 'testPassword123!',
    subscribe_newsletter: true
  };

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(userData)
    });

    console.log('📊 回應狀態:', response.status);
    console.log('📊 回應標頭:', Object.fromEntries(response.headers.entries()));
    
    const data = await response.json();
    console.log('📊 回應內容:', JSON.stringify(data, null, 2));

    if (response.ok) {
      console.log('✅ 註冊成功!');
      return true;
    } else {
      console.log('❌ 註冊失敗!');
      return false;
    }
  } catch (error) {
    console.log('❌ 請求錯誤:', error.message);
    return false;
  }
}

async function testHealth() {
  console.log('🔄 測試健康檢查 API...');
  
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    const data = await response.json();
    
    console.log('✅ 健康檢查:', data);
    return true;
  } catch (error) {
    console.log('❌ 健康檢查失敗:', error.message);
    return false;
  }
}

async function testCORS() {
  console.log('🔄 測試 CORS...');
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/register`, {
      method: 'OPTIONS',
      headers: {
        'Origin': 'http://localhost:5174',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type'
      }
    });
    
    console.log('📊 CORS 預檢狀態:', response.status);
    console.log('📊 CORS 標頭:', Object.fromEntries(response.headers.entries()));
    
    return response.ok;
  } catch (error) {
    console.log('❌ CORS 測試失敗:', error.message);
    return false;
  }
}

async function main() {
  console.log('🧪 開始 API 連接測試...\n');
  
  const healthOK = await testHealth();
  console.log('');
  
  const corsOK = await testCORS();
  console.log('');
  
  const registerOK = await testRegister();
  console.log('');
  
  console.log('📋 測試結果總結:');
  console.log(`   健康檢查: ${healthOK ? '✅' : '❌'}`);
  console.log(`   CORS 設定: ${corsOK ? '✅' : '❌'}`);
  console.log(`   註冊 API: ${registerOK ? '✅' : '❌'}`);
  
  if (healthOK && corsOK && registerOK) {
    console.log('\n🎉 所有測試通過! API 連接正常。');
  } else {
    console.log('\n⚠️ 部分測試失敗，請檢查設定。');
  }
}

main().catch(console.error);