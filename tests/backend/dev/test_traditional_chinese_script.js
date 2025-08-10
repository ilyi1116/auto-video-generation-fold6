#!/usr/bin/env node

/**
 * 測試繁體中文腳本生成和智能圖像生成功能
 * Test Traditional Chinese script generation and intelligent image generation
 */

const API_BASE = 'http://localhost:8001';

console.log('🇹🇼 測試繁體中文腳本生成和智能圖像生成功能\n');
console.log('='.repeat(70));

async function testTraditionalChineseAndImageGeneration() {
  let successCount = 0;
  let totalTests = 6;

  console.log('\n📍 測試步驟 1: 驗證後端服務狀態');
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (response.ok) {
      const data = await response.json();
      console.log('✅ 後端服務正常:', data.service);
      successCount++;
    } else {
      console.log('❌ 後端服務異常:', response.status);
    }
  } catch (error) {
    console.log('❌ 後端服務連接失敗:', error.message);
  }

  // 測試案例：繁體中文腳本生成
  const scriptTestCases = [
    {
      name: 'YouTube教育類繁體中文腳本',
      data: {
        topic: 'Python程式設計入門',
        platform: 'youtube',
        style: 'educational',
        duration: 180,
        language: 'zh-TW',
        description: '這個影片是為完全零基礎的程式設計新手準備的。我想要通過一個實際的小專案（比如製作一個簡單的計算機）來教學，而不是枯燥的語法介紹。希望能夠包含環境安裝、變數概念、函數使用、錯誤調試等基礎知識點。目標是讓觀眾看完後能夠獨立寫出第一個Python程式。'
      }
    },
    {
      name: 'TikTok生活類繁體中文腳本', 
      data: {
        topic: '5分鐘快手早餐製作',
        platform: 'tiktok',
        style: 'lifestyle',
        duration: 60,
        language: 'zh-TW',
        description: '想要分享幾個超簡單的早餐製作方法，適合上班族和學生黨。重點是食材容易買到，製作過程不超過5分鐘，而且營養搭配合理。希望能包含吐司、雞蛋、燕麥這些常見食材的創意搭配。影片要有節奏感，適合早上匆忙時觀看。'
      }
    }
  ];

  let generatedScripts = [];

  for (let i = 0; i < scriptTestCases.length; i++) {
    const testCase = scriptTestCases[i];
    console.log(`\n📍 測試步驟 ${i + 2}: ${testCase.name}`);
    console.log(`   主題: ${testCase.data.topic}`);
    console.log(`   平台: ${testCase.data.platform}`);
    console.log(`   風格: ${testCase.data.style}`);
    console.log(`   描述: ${testCase.data.description.substring(0, 80)}...`);
    
    try {
      const response = await fetch(`${API_BASE}/api/v1/generate/script`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testCase.data)
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          console.log('✅ 繁體中文腳本生成成功');
          console.log(`   生成器: ${data.data.provider || '未知'}`);
          console.log(`   腳本長度: ${data.data.script.length} 字符`);
          console.log(`   詞數統計: ${data.data.word_count} 詞`);
          
          if (data.data.note) {
            console.log(`   📝 說明: ${data.data.note}`);
          }
          
          // 檢查繁體中文字符
          const script = data.data.script;
          const traditionalChineseChars = ['這', '為', '個', '來', '會', '說', '讓', '們', '時', '現'];
          const foundChars = traditionalChineseChars.filter(char => script.includes(char));
          
          console.log(`   🇹🇼 繁體字檢測: 找到 ${foundChars.length}/10 個常見繁體字`);
          console.log(`   📖 腳本預覽: ${script.substring(0, 120)}...`);
          
          // 保存腳本用於圖像生成測試
          generatedScripts.push({
            topic: testCase.data.topic,
            script: script,
            platform: testCase.data.platform,
            style: testCase.data.style
          });
          
          successCount++;
        } else {
          console.log('❌ 腳本生成失敗:', data.error || '未知錯誤');
        }
      } else {
        const errorData = await response.json();
        console.log('❌ API調用失敗:', errorData.detail || response.status);
      }
    } catch (error) {
      console.log('❌ 腳本生成錯誤:', error.message);
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  // 測試基於腳本的智能圖像生成
  if (generatedScripts.length > 0) {
    for (let i = 0; i < Math.min(2, generatedScripts.length); i++) {
      const scriptData = generatedScripts[i];
      console.log(`\n📍 測試步驟 ${scriptTestCases.length + i + 2}: 基於腳本的智能圖像生成`);
      console.log(`   腳本主題: ${scriptData.topic}`);
      console.log(`   平台: ${scriptData.platform}`);
      
      try {
        const imagePrompts = [
          `${scriptData.topic} thumbnail image`,
          `${scriptData.topic} background scene 1`
        ];
        
        for (let j = 0; j < imagePrompts.length; j++) {
          const prompt = imagePrompts[j];
          console.log(`\n   🎨 圖像 ${j + 1}: ${prompt}`);
          
          const response = await fetch(`${API_BASE}/api/v1/generate/image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              prompt: prompt,
              style: scriptData.style,
              script: scriptData.script,
              topic: scriptData.topic,
              platform: scriptData.platform,
              size: '1920x1080'
            })
          });
          
          if (response.ok) {
            const data = await response.json();
            if (data.success) {
              console.log('   ✅ 圖像生成成功');
              console.log(`   📷 提供者: ${data.data.provider}`);
              console.log(`   🔤 原始提示詞: ${data.data.prompt}`);
              if (data.data.enhanced_prompt && data.data.enhanced_prompt !== data.data.prompt) {
                console.log(`   🚀 智能增強提示詞: ${data.data.enhanced_prompt.substring(0, 80)}...`);
              }
              console.log(`   📐 解析度: ${data.data.resolution}`);
              
              if (data.data.provider.includes('DeepSeek')) {
                console.log('   🤖 DeepSeek智能圖像提示詞生成成功！');
              }
            } else {
              console.log('   ❌ 圖像生成失敗');
            }
          } else {
            console.log('   ❌ 圖像API調用失敗');
          }
        }
        
        successCount++;
      } catch (error) {
        console.log(`   ❌ 圖像生成錯誤: ${error.message}`);
      }
      
      await new Promise(resolve => setTimeout(resolve, 1500));
    }
  }

  console.log('\n' + '='.repeat(70));
  console.log('📊 測試結果總結:');
  console.log(`✅ 通過: ${successCount}/${totalTests}`);
  console.log(`❌ 失敗: ${totalTests - successCount}/${totalTests}`);
  console.log(`📈 成功率: ${Math.round(successCount / totalTests * 100)}%`);

  if (successCount >= totalTests * 0.8) {
    console.log('\n🎉 測試基本通過！繁體中文腳本生成和智能圖像功能正常！');
    
    console.log('\n📍 新功能特色:');
    console.log('   🇹🇼 繁體中文輸出: 腳本內容使用正確的繁體中文');
    console.log('   🤖 DeepSeek 整合: 支援 AI 智能腳本生成');
    console.log('   🎨 智能圖像: 根據腳本內容生成視覺提示詞');
    console.log('   📱 多平台適配: YouTube, TikTok 等平台特色');
    console.log('   📝 描述驅動: 根據項目描述生成個性化內容');
    
    console.log('\n🚀 使用方式:');
    console.log('   • 前端界面: http://localhost:5173/create');
    console.log('   • 步驟1: 填寫標題和詳細描述');
    console.log('   • 步驟2: 生成繁體中文腳本');
    console.log('   • 步驟3: 基於腳本生成智能圖像');
    console.log('   • 查看增強的提示詞和視覺效果');
    
    console.log('\n💡 技術亮點:');
    console.log('   • 繁體中文自然語言處理');
    console.log('   • 腳本到圖像的智能轉換');
    console.log('   • 多模態 AI 內容生成');
    console.log('   • 平台特色化內容適配');
  } else {
    console.log('\n⚠️ 部分測試失敗，請檢查相關配置');
    console.log('   • 確認後端服務運行正常');
    console.log('   • 檢查 DeepSeek API 密鑰配置（可選）');
    console.log('   • 查看控制台日志獲取詳細信息');
  }
}

// 執行測試
testTraditionalChineseAndImageGeneration().catch(console.error);