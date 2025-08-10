#!/usr/bin/env node

/**
 * 測試真實語音生成功能
 * Test real voice generation with TTS libraries
 */

const API_BASE = 'http://localhost:8001';

console.log('🎤 測試真實語音生成功能\n');
console.log('='.repeat(60));

async function testRealVoiceGeneration() {
  console.log('\n📍 測試步驟 1: 驗證後端服務狀態');
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (response.ok) {
      const data = await response.json();
      console.log('✅ 後端服務正常:', data.service);
    } else {
      console.log('❌ 後端服務異常:', response.status);
      return;
    }
  } catch (error) {
    console.log('❌ 後端服務連接失敗:', error.message);
    return;
  }

  // 測試簡短的繁體中文語音生成
  const testText = "大家好！這是一個測試語音。今天天氣真好！";

  console.log('\n📍 測試步驟 2: 生成真實語音文件');
  console.log(`   測試文本: ${testText}`);
  console.log(`   文本長度: ${testText.length} 字符`);

  try {
    const response = await fetch(`${API_BASE}/api/v1/generate/voice`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: testText,
        voice: 'alloy',
        speed: 1.0,
        platform: 'youtube',
        style: 'educational',
        topic: '測試語音',
        optimize_with_ai: true
      })
    });

    if (response.ok) {
      const data = await response.json();
      if (data.success) {
        console.log('✅ 語音API調用成功');
        console.log(`   🔊 提供者: ${data.data.provider}`);
        console.log(`   🎵 語音: ${data.data.voice} @ ${data.data.speed}x`);
        console.log(`   ⏱️ 時長: ${data.data.duration} 秒`);
        console.log(`   📊 品質: ${data.data.quality}`);
        console.log(`   🔗 URL: ${data.data.url}`);
        console.log(`   📁 本地文件: ${data.data.has_real_audio ? '有' : '無'}`);

        if (data.data.has_real_audio) {
          console.log(`   📂 文件路徑: ${data.data.filepath}`);
          
          // 嘗試訪問音頻文件
          console.log('\n📍 測試步驟 3: 驗證音頻文件訪問');
          try {
            const audioResponse = await fetch(data.data.url);
            if (audioResponse.ok) {
              console.log('✅ 音頻文件可以正常訪問');
              console.log(`   📏 文件大小: ${audioResponse.headers.get('content-length') || '未知'} 字節`);
              console.log(`   📋 內容類型: ${audioResponse.headers.get('content-type') || '未知'}`);
            } else {
              console.log('❌ 音頻文件訪問失敗:', audioResponse.status);
            }
          } catch (error) {
            console.log('❌ 音頻文件訪問異常:', error.message);
          }
        } else {
          console.log('⚠️ 沒有生成真實的音頻文件，這是模擬模式');
        }

        // 顯示AI優化信息
        if (data.data.optimization?.ai_optimized) {
          const opt = data.data.optimization;
          console.log('\n🤖 AI優化詳情:');
          console.log(`   • 原始設定: ${opt.original_voice} @ ${opt.original_speed}x`);
          console.log(`   • 優化設定: ${opt.optimized_voice} @ ${opt.optimized_speed}x`);
          console.log(`   • 情感調性: ${opt.emotion}`);
          console.log(`   • 語調風格: ${opt.tone}`);
          console.log(`   • 優化原因: ${opt.optimization_reason}`);
        }

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

  console.log('\n' + '='.repeat(60));
  console.log('🔍 故障排除建議:');
  console.log('');
  console.log('如果沒有生成真實音頻文件，可能的原因：');
  console.log('1. 缺少API密鑰:');
  console.log('   - OPENAI_API_KEY (OpenAI TTS, 最佳品質)');
  console.log('   - 或使用免費的 Edge TTS / gTTS');
  console.log('');
  console.log('2. 免費TTS庫未安裝:');
  console.log('   - pip install edge-tts gtts');
  console.log('');
  console.log('3. 網路連接問題:');
  console.log('   - 檢查網路連接');
  console.log('   - 檢查防火牆設置');
  console.log('');
  console.log('✨ 推薦解決方案:');
  console.log('   1. 使用 Edge TTS (免費，支援繁體中文)');
  console.log('   2. 或配置 OpenAI API 密鑰獲得最佳效果');
}

// 執行測試
testRealVoiceGeneration().catch(console.error);