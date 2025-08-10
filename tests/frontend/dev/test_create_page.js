#!/usr/bin/env node

/**
 * Create Page 功能測試腳本
 * 測試所有 AI 生成端點
 */

const BASE_URL = 'http://localhost:8001';

// 測試數據
const testData = {
  script: {
    topic: "人工智慧技術教學",
    platform: "youtube",
    style: "educational", 
    duration: 60,
    language: "zh-TW"
  },
  image: {
    prompt: "AI 教學影片縮圖",
    style: "realistic",
    size: "1920x1080"
  },
  voice: {
    text: "歡迎來到人工智慧技術教學的精彩世界！今天我們要探索AI的各個面向。",
    voice: "alloy",
    speed: 1.0
  },
  music: {
    prompt: "educational background music",
    style: "ambient",
    duration: 60
  }
};

async function testEndpoint(endpoint, data, description) {
  try {
    console.log(`\n🧪 測試 ${description}...`);
    console.log(`📡 POST ${BASE_URL}${endpoint}`);
    
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    
    if (result.success) {
      console.log(`✅ ${description} 成功`);
      console.log(`📊 回應數據:`, JSON.stringify(result.data, null, 2));
      return true;
    } else {
      console.log(`❌ ${description} 失敗:`, result.error);
      return false;
    }
  } catch (error) {
    console.log(`❌ ${description} 錯誤:`, error.message);
    return false;
  }
}

async function runTests() {
  console.log("🚀 開始測試 /create 頁面 AI 生成功能\n");
  console.log("=".repeat(50));

  const tests = [
    {
      endpoint: '/api/v1/generate/script',
      data: testData.script,
      description: 'AI腳本生成'
    },
    {
      endpoint: '/api/v1/generate/image', 
      data: testData.image,
      description: 'AI圖像生成'
    },
    {
      endpoint: '/api/v1/generate/voice',
      data: testData.voice,
      description: 'AI語音合成'
    },
    {
      endpoint: '/api/v1/generate/music',
      data: testData.music,
      description: 'AI音樂生成'
    }
  ];

  let passedTests = 0;
  let totalTests = tests.length;

  for (const test of tests) {
    const passed = await testEndpoint(test.endpoint, test.data, test.description);
    if (passed) passedTests++;
  }

  console.log("\n" + "=".repeat(50));
  console.log("📊 測試結果總結:");
  console.log(`✅ 通過: ${passedTests}/${totalTests}`);
  console.log(`❌ 失敗: ${totalTests - passedTests}/${totalTests}`);
  console.log(`📈 成功率: ${Math.round(passedTests / totalTests * 100)}%`);

  if (passedTests === totalTests) {
    console.log("\n🎉 所有測試通過！/create 頁面功能完全正常！");
  } else {
    console.log("\n⚠️  有部分測試失敗，請檢查相關端點");
  }

  console.log("\n📍 前端頁面: http://localhost:5173/create");
  console.log("📍 API 文檔: http://localhost:8001/docs");
}

// 執行測試
runTests().catch(console.error);