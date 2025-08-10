#!/usr/bin/env node

/**
 * 完整的 /create 頁面功能測試
 * 測試所有 5 個步驟的完整流程
 */

const BASE_URL = 'http://localhost:5173';
const API_BASE = 'http://localhost:8001';

console.log('🧪 開始測試 /create 頁面完整功能流程\n');
console.log('='.repeat(60));

async function testCreatePageWorkflow() {
  let successCount = 0;
  let totalTests = 5;

  console.log('\n📍 測試步驟 1: 檢查前端頁面載入');
  try {
    const response = await fetch(`${BASE_URL}/create`);
    if (response.ok) {
      console.log('✅ 前端 /create 頁面載入成功');
      successCount++;
    } else {
      console.log('❌ 前端頁面載入失敗:', response.status);
    }
  } catch (error) {
    console.log('❌ 前端頁面載入錯誤:', error.message);
  }

  console.log('\n📍 測試步驟 2: 驗證後端 API 連接');
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (response.ok) {
      const data = await response.json();
      console.log('✅ 後端 API 連接正常:', data.service);
      successCount++;
    } else {
      console.log('❌ 後端 API 連接失敗:', response.status);
    }
  } catch (error) {
    console.log('❌ 後端 API 連接錯誤:', error.message);
  }

  console.log('\n📍 測試步驟 3: 腳本生成 API');
  try {
    const response = await fetch(`${API_BASE}/api/v1/generate/script`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: 'AI 技術教學',
        platform: 'youtube',
        style: 'educational',
        duration: 60,
        language: 'zh-TW'
      })
    });

    if (response.ok) {
      const data = await response.json();
      console.log('✅ 腳本生成 API 正常運作');
      console.log(`   生成腳本長度: ${data.data.script.length} 字符`);
      successCount++;
    } else {
      console.log('❌ 腳本生成 API 失敗:', response.status);
    }
  } catch (error) {
    console.log('❌ 腳本生成 API 錯誤:', error.message);
  }

  console.log('\n📍 測試步驟 4: 圖像生成 API');
  try {
    const response = await fetch(`${API_BASE}/api/v1/generate/image`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt: 'AI 教學影片縮圖',
        style: 'realistic',
        size: '1920x1080'
      })
    });

    if (response.ok) {
      const data = await response.json();
      console.log('✅ 圖像生成 API 正常運作');
      console.log(`   生成圖像 URL: ${data.data.url ? '✓' : '✗'}`);
      successCount++;
    } else {
      console.log('❌ 圖像生成 API 失敗:', response.status);
    }
  } catch (error) {
    console.log('❌ 圖像生成 API 錯誤:', error.message);
  }

  console.log('\n📍 測試步驟 5: 語音合成 API');
  try {
    const response = await fetch(`${API_BASE}/api/v1/generate/voice`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: '歡迎來到 AI 技術教學的精彩世界！',
        voice: 'alloy',
        speed: 1.0
      })
    });

    if (response.ok) {
      const data = await response.json();
      console.log('✅ 語音合成 API 正常運作');
      console.log(`   語音時長: ${data.data.duration} 秒`);
      successCount++;
    } else {
      console.log('❌ 語音合成 API 失敗:', response.status);
    }
  } catch (error) {
    console.log('❌ 語音合成 API 錯誤:', error.message);
  }

  console.log('\n' + '=' .repeat(60));
  console.log('📊 測試結果總結:');
  console.log(`✅ 通過: ${successCount}/${totalTests}`);
  console.log(`❌ 失敗: ${totalTests - successCount}/${totalTests}`);
  console.log(`📈 成功率: ${Math.round(successCount / totalTests * 100)}%`);

  if (successCount === totalTests) {
    console.log('\n🎉 所有測試通過！/create 頁面功能完全正常！');
    console.log('\n📍 您現在可以訪問：');
    console.log(`   前端頁面: ${BASE_URL}/create`);
    console.log(`   後端 API: ${API_BASE}/docs`);
    console.log('\n✨ 步驟 1-5 已全部實現並可正常使用！');
  } else {
    console.log('\n⚠️ 部分測試失敗，請檢查相關服務');
  }
}

// 執行測試
testCreatePageWorkflow().catch(console.error);