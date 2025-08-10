#!/usr/bin/env node

/**
 * 測試DeepSeek優化的語音生成功能
 * Test DeepSeek-enhanced voice generation functionality
 */

const API_BASE = 'http://localhost:8001';

console.log('🎤 測試DeepSeek優化語音生成功能\n');
console.log('='.repeat(70));

async function testDeepSeekVoiceGeneration() {
  let successCount = 0;
  let totalTests = 5;

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

  // 測試案例：不同平台和風格的語音生成
  const voiceTestCases = [
    {
      name: 'YouTube教育風格語音優化',
      data: {
        text: `大家好！歡迎來到今天的Python程式設計入門教學。

這個課程是專為完全零基礎的朋友準備的。不管你是學生還是上班族，只要你想學程式設計，這個影片都能幫到你。

今天我們要學會製作一個簡單的計算機。聽起來很複雜嗎？其實不會的！我會一步一步教你，從最基本的環境安裝開始。

首先，讓我們了解一下Python為什麼這麼受歡迎。Python的語法簡潔，容易理解，就像說話一樣自然。

接下來，我們會學習變數的概念、函數的使用，還有最重要的錯誤調試。

如果你覺得這個影片有幫助，記得點讚和訂閱哦！有問題的話，歡迎在留言區問我。`,
        voice: 'alloy',
        speed: 1.0,
        platform: 'youtube',
        style: 'educational',
        topic: 'Python程式設計入門',
        optimize_with_ai: true
      }
    },
    {
      name: 'TikTok娛樂風格語音優化',
      data: {
        text: `等等！你知道五分鐘早餐也能這麼好吃嗎？

今天教大家三個超簡單的早餐做法！適合所有懶人和上班族！

第一個：吐司加蛋！
把吐司中間挖個洞，打顆蛋進去，平底鍋煎三分鐘就好了！

第二個：燕麥杯！
燕麥、牛奶、香蕉，微波爐兩分鐘搞定！

第三個：雞蛋捲餅！
雞蛋攤成餅，加點蔬菜一捲就完成！

是不是超級簡單？趕快試試看！記得雙擊愛心哦～`,
        voice: 'nova',
        speed: 1.2,
        platform: 'tiktok',
        style: 'entertainment',
        topic: '5分鐘快手早餐製作',
        optimize_with_ai: true
      }
    },
    {
      name: 'B站教程風格語音優化',
      data: {
        text: `大家好，我是你們的健身UP主！今天要跟大家分享居家腹肌訓練！

首先要跟各位說明，這套動作特別適合久坐的上班族。不需要任何器械，在家就能做！

我們先從熱身開始。先做十個開合跳，讓身體熱起來。

接下來是今天的主菜：
第一個動作：平板支撐，30秒
第二個動作：仰臥起坐，15個
第三個動作：俄羅斯轉體，20個

每個動作之間休息30秒。

特別提醒！動作一定要標準，寧可慢也不要錯！

最後是拉伸放鬆，這個很重要，不能忽略！

喜歡的話記得三連支持！我們下期見！`,
        voice: 'fable',
        speed: 1.1,
        platform: 'bilibili',
        style: 'tutorial',
        topic: '居家腹肌訓練',
        optimize_with_ai: true
      }
    },
    {
      name: 'Instagram風格語音優化',
      data: {
        text: `Hi everyone! 今天要跟大家分享咖啡沖泡的小秘密！

你知道嗎？咖啡豆的研磨粗細度，直接影響咖啡的味道。

手沖咖啡的黃金比例是1:15，也就是一克咖啡豆配15毫升水。

水溫控制在90-95度最完美。太熱會焦苦，太涼萃取不足。

先用少量熱水悶蒸30秒，讓咖啡豆釋放香氣。

然後繞圓圈慢慢注水，保持穩定的節奏。

看到美麗的咖啡油脂了嗎？這就是成功的標誌！

每一口都是香醇的享受～

記得tag朋友來試試！`,
        voice: 'shimmer',
        speed: 1.0,
        platform: 'instagram',
        style: 'lifestyle',
        topic: '咖啡沖泡藝術',
        optimize_with_ai: true
      }
    }
  ];

  for (let i = 0; i < voiceTestCases.length; i++) {
    const testCase = voiceTestCases[i];
    console.log(`\n📍 測試步驟 ${i + 2}: ${testCase.name}`);
    console.log(`   平台: ${testCase.data.platform}`);
    console.log(`   風格: ${testCase.data.style}`);
    console.log(`   原始語音: ${testCase.data.voice} @ ${testCase.data.speed}x`);
    console.log(`   文本長度: ${testCase.data.text.length} 字符`);
    
    try {
      const response = await fetch(`${API_BASE}/api/v1/generate/voice`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testCase.data)
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          console.log('✅ 語音生成成功');
          console.log(`   🔊 提供者: ${data.data.provider}`);
          console.log(`   🎵 最終語音: ${data.data.voice} @ ${data.data.speed}x`);
          console.log(`   ⏱️ 預估時長: ${data.data.duration} 秒`);
          console.log(`   📊 品質: ${data.data.quality}`);
          
          // 顯示中文字符統計
          if (data.data.chinese_char_count > 0) {
            console.log(`   🇹🇼 中文字數: ${data.data.chinese_char_count} 字`);
          }
          
          // 顯示AI優化信息
          if (data.data.optimization) {
            const opt = data.data.optimization;
            if (opt.ai_optimized) {
              console.log('   🤖 AI優化詳情:');
              console.log(`      • 原始設定: ${opt.original_voice} @ ${opt.original_speed}x`);
              console.log(`      • 優化設定: ${opt.optimized_voice} @ ${opt.optimized_speed}x`);
              console.log(`      • 情感調性: ${opt.emotion}`);
              console.log(`      • 語調風格: ${opt.tone}`);
              console.log(`      • 優化原因: ${opt.optimization_reason}`);
              
              if (opt.pronunciation_notes && opt.pronunciation_notes.length > 0) {
                console.log('      • 發音建議:');
                opt.pronunciation_notes.forEach(note => {
                  console.log(`        - ${note}`);
                });
              }
            } else {
              console.log(`   ℹ️ 優化狀態: ${opt.note}`);
            }
          }
          
          successCount++;
        } else {
          console.log('❌ 語音生成失敗:', data.error || '未知錯誤');
        }
      } else {
        const errorData = await response.json();
        console.log('❌ API調用失敗:', errorData.detail || response.status);
      }
    } catch (error) {
      console.log('❌ 語音生成錯誤:', error.message);
    }
    
    console.log('\n' + '-'.repeat(50));
    await new Promise(resolve => setTimeout(resolve, 1500));
  }

  console.log('\n' + '='.repeat(70));
  console.log('📊 測試結果總結:');
  console.log(`✅ 通過: ${successCount}/${totalTests}`);
  console.log(`❌ 失敗: ${totalTests - successCount}/${totalTests}`);
  console.log(`📈 成功率: ${Math.round(successCount / totalTests * 100)}%`);

  if (successCount >= totalTests * 0.8) {
    console.log('\n🎉 DeepSeek優化語音生成測試通過！');
    
    console.log('\n📍 新功能特色:');
    console.log('   🤖 DeepSeek AI優化: 智能分析文本並推薦最佳語音參數');
    console.log('   🎭 多平台適配: 針對YouTube、TikTok、B站、Instagram優化');
    console.log('   🎵 智能語音選擇: 根據內容風格自動推薦語音和語速');
    console.log('   🇹🇼 繁體中文支援: 針對中文語音時長精確計算');
    console.log('   🔊 真實語音生成: 支援OpenAI TTS API (需要API密鑰)');
    console.log('   📊 詳細統計分析: 完整的語音生成數據和優化詳情');
    
    console.log('\n🚀 使用方式:');
    console.log('   • 前端界面: http://localhost:5173/create');
    console.log('   • 步驟4: 語音合成 - 生成AI優化語音');
    console.log('   • 查看優化詳情和語音參數建議');
    console.log('   • 支援手動調整語音設置');
    
    console.log('\n💡 技術亮點:');
    console.log('   • DeepSeek文本分析與參數優化');
    console.log('   • 平台和風格智能映射');
    console.log('   • 中英文混合語音時長計算');
    console.log('   • 本地優化邏輯回退機制');
    console.log('   • OpenAI TTS整合支援');
    
    console.log('\n🔧 API配置:');
    console.log('   • DEEPSEEK_API_KEY: DeepSeek AI優化 (可選)');
    console.log('   • OPENAI_API_KEY: 真實語音生成 (可選)');
    console.log('   • 無API密鑰時自動使用本地優化邏輯');
    
  } else {
    console.log('\n⚠️ 部分測試未通過，請檢查相關配置');
    console.log('   • 確認後端服務運行正常');
    console.log('   • 檢查API密鑰配置（可選）');
    console.log('   • 查看控制台日志獲取詳細信息');
  }
}

// 執行測試
testDeepSeekVoiceGeneration().catch(console.error);