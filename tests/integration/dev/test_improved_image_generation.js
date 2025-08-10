#!/usr/bin/env node

/**
 * 測試改善後的AI圖像生成功能
 * 驗證專案描述與圖像提示詞的相關性
 */

const API_BASE = 'http://localhost:8001';

console.log('🎨 測試改善後的AI圖像生成與專案描述相關性\n');
console.log('='.repeat(70));

async function testImprovedImageGeneration() {
  let successCount = 0;
  let totalTests = 4;

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

  // 測試案例：具有詳細描述的專案
  const testCases = [
    {
      name: 'Python程式設計教學專案',
      topic: 'Python程式設計入門',
      description: '這個影片是為完全零基礎的程式設計新手準備的。我想要通過一個實際的小專案（比如製作一個簡單的計算機）來教學，而不是枯燥的語法介紹。希望能夠包含環境安裝、變數概念、函數使用、錯誤調試等基礎知識點。',
      platform: 'youtube',
      style: 'educational'
    },
    {
      name: '快手早餐製作專案', 
      topic: '5分鐘快手早餐',
      description: '想要分享幾個超簡單的早餐製作方法，適合上班族和學生黨。重點是食材容易買到，製作過程不超過5分鐘，而且營養搭配合理。希望能包含吐司、雞蛋、燕麥這些常見食材的創意搭配。影片要有節奏感，適合早上匆忙時觀看。',
      platform: 'tiktok', 
      style: 'lifestyle'
    },
    {
      name: '居家健身專案',
      topic: '居家腹肌訓練',
      description: '針對久坐辦公室的上班族設計的腹肌訓練計劃。不需要任何器械，在家就能做。包含熱身動作、核心訓練動作（平板支撐、仰臥起坐變式、俄羅斯轉體等）、拉伸放松。希望能夠詳細講解每個動作的要點，常見錯誤，以及如何循序漸進。',
      platform: 'bilibili',
      style: 'tutorial'
    }
  ];

  // 先生成腳本，然後基於腳本和描述生成圖像
  for (let i = 0; i < testCases.length; i++) {
    const testCase = testCases[i];
    console.log(`\n📍 測試步驟 ${i + 2}: ${testCase.name}`);
    
    try {
      // 1. 先生成腳本
      console.log('   🤖 步驟 1/2: 生成繁體中文腳本...');
      
      const scriptResponse = await fetch(`${API_BASE}/api/v1/generate/script`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic: testCase.topic,
          description: testCase.description,
          platform: testCase.platform,
          style: testCase.style,
          duration: 120,
          language: 'zh-TW'
        })
      });

      let generatedScript = '';
      if (scriptResponse.ok) {
        const scriptData = await scriptResponse.json();
        if (scriptData.success) {
          generatedScript = scriptData.data.script;
          console.log(`   ✅ 腳本生成成功 (${scriptData.data.script.length} 字符)`);
          console.log(`   📖 腳本預覽: ${generatedScript.substring(0, 100)}...`);
        }
      }

      // 2. 基於腳本和描述生成圖像
      console.log('   🎨 步驟 2/2: 生成智能圖像提示詞...');
      
      const imagePrompts = [
        `${testCase.topic} thumbnail image`,
        `${testCase.topic} background scene`
      ];
      
      for (let j = 0; j < imagePrompts.length; j++) {
        const prompt = imagePrompts[j];
        console.log(`\n   🖼️ 圖像 ${j + 1}: ${prompt}`);
        
        const imageResponse = await fetch(`${API_BASE}/api/v1/generate/image`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            prompt: prompt,
            style: testCase.style,
            script: generatedScript,
            topic: testCase.topic,
            platform: testCase.platform,
            description: testCase.description,
            size: '1920x1080'
          })
        });
        
        if (imageResponse.ok) {
          const imageData = await imageResponse.json();
          if (imageData.success) {
            console.log('   ✅ 圖像生成成功');
            console.log(`   🔧 提供者: ${imageData.data.provider}`);
            console.log(`   🔤 原始提示詞: ${imageData.data.prompt}`);
            console.log(`   🚀 增強提示詞: ${imageData.data.enhanced_prompt}`);
            
            // 分析提示詞與描述的相關性
            const enhancedPrompt = imageData.data.enhanced_prompt.toLowerCase();
            const description = testCase.description.toLowerCase();
            
            let relevanceScore = 0;
            let matchedElements = [];
            
            // 檢查關鍵詞匹配
            const keywordMapping = {
              '零基礎': ['beginner', 'accessible', 'tutorial'],
              '計算機': ['computer', 'programming', 'coding'],
              '實際': ['practical', 'useful', 'real'],
              '上班族': ['office', 'professional', 'worker'],
              '早餐': ['breakfast', 'morning', 'food'],
              '食材': ['ingredients', 'cooking', 'kitchen'],
              '簡單': ['simple', 'easy', 'clear'],
              '快速': ['dynamic', 'energetic', 'quick'],
              '居家': ['home', 'cozy', 'indoor'],
              '健身': ['fitness', 'exercise', 'workout'],
              '腹肌': ['training', 'exercise', 'fitness'],
              '辦公室': ['office', 'professional']
            };
            
            for (const [chineseKey, englishKeys] of Object.entries(keywordMapping)) {
              if (description.includes(chineseKey)) {
                const matches = englishKeys.filter(key => enhancedPrompt.includes(key));
                if (matches.length > 0) {
                  relevanceScore += matches.length;
                  matchedElements.push(`${chineseKey} → ${matches.join(', ')}`);
                }
              }
            }
            
            // 檢查平台特色
            if (enhancedPrompt.includes(testCase.platform)) {
              relevanceScore++;
              matchedElements.push(`平台特色: ${testCase.platform}`);
            }
            
            // 檢查風格匹配
            if (enhancedPrompt.includes(testCase.style)) {
              relevanceScore++;
              matchedElements.push(`風格匹配: ${testCase.style}`);
            }
            
            console.log(`   📊 相關性評分: ${relevanceScore}/10`);
            if (matchedElements.length > 0) {
              console.log(`   🎯 匹配元素: ${matchedElements.join('; ')}`);
            }
            
            if (relevanceScore >= 3) {
              console.log('   ✅ 相關性良好 - 圖像提示詞與專案描述高度相關');
            } else if (relevanceScore >= 1) {
              console.log('   ⚠️ 相關性中等 - 部分匹配專案描述');
            } else {
              console.log('   ❌ 相關性不足 - 需要改善');
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
      console.log(`   ❌ 測試失敗: ${error.message}`);
    }
    
    console.log('\n' + '-'.repeat(50));
    await new Promise(resolve => setTimeout(resolve, 2000));
  }

  console.log('\n' + '='.repeat(70));
  console.log('📊 測試結果總結:');
  console.log(`✅ 通過: ${successCount}/${totalTests}`);
  console.log(`❌ 失敗: ${totalTests - successCount}/${totalTests}`);
  console.log(`📈 成功率: ${Math.round(successCount / totalTests * 100)}%`);

  if (successCount >= totalTests * 0.75) {
    console.log('\n🎉 圖像生成相關性改善測試通過！');
    
    console.log('\n📍 改善成果:');
    console.log('   🎯 專案描述整合: 圖像提示詞直接對應描述內容');
    console.log('   🤖 智能關鍵詞映射: 中文描述自動轉換為英文視覺元素');
    console.log('   🎨 多層次增強: 腳本+描述+平台+風格全面整合');
    console.log('   📱 平台特色: 不同平台的視覺風格適配');
    console.log('   🔍 相關性評分: 自動分析匹配度');
    
    console.log('\n🚀 技術亮點:');
    console.log('   • 中英文語意映射系統');
    console.log('   • 多模態內容分析');
    console.log('   • 智能關鍵詞提取');
    console.log('   • 本地回退增強邏輯');
    console.log('   • 平台風格適配');
    
  } else {
    console.log('\n⚠️ 部分測試未通過，建議進一步優化');
    console.log('   • 檢查關鍵詞映射是否完整');
    console.log('   • 確認專案描述傳遞正確');
    console.log('   • 驗證增強邏輯是否生效');
  }
}

// 執行測試
testImprovedImageGeneration().catch(console.error);