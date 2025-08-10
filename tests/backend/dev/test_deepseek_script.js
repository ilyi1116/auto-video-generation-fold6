#!/usr/bin/env node

/**
 * 测试DeepSeek AI脚本生成功能
 * Test DeepSeek AI script generation functionality
 */

const API_BASE = 'http://localhost:8001';

console.log('🤖 测试DeepSeek AI脚本生成功能\n');
console.log('='.repeat(60));

async function testScriptGeneration() {
  let successCount = 0;
  let totalTests = 6;

  console.log('\n📍 测试步骤 1: 验证后端服务状态');
  try {
    const response = await fetch(`${API_BASE}/health`);
    if (response.ok) {
      const data = await response.json();
      console.log('✅ 后端服务正常:', data.service);
      successCount++;
    } else {
      console.log('❌ 后端服务异常:', response.status);
    }
  } catch (error) {
    console.log('❌ 后端服务连接失败:', error.message);
  }

  // 不同风格和平台的测试案例
  const testCases = [
    {
      name: 'YouTube教育类脚本',
      data: {
        topic: 'Python编程入门',
        platform: 'youtube',
        style: 'educational',
        duration: 120,
        language: 'zh-TW'
      }
    },
    {
      name: 'TikTok娱乐类脚本',
      data: {
        topic: '健身小技巧',
        platform: 'tiktok', 
        style: 'entertainment',
        duration: 30,
        language: 'zh-TW'
      }
    },
    {
      name: 'B站教程类脚本',
      data: {
        topic: '摄影构图技巧',
        platform: 'bilibili',
        style: 'tutorial',
        duration: 90,
        language: 'zh-TW'
      }
    },
    {
      name: 'Instagram生活类脚本',
      data: {
        topic: '咖啡冲泡艺术',
        platform: 'instagram',
        style: 'lifestyle',
        duration: 60,
        language: 'zh-TW'
      }
    },
    {
      name: 'YouTube评测类脚本',
      data: {
        topic: '最新智能手机对比',
        platform: 'youtube',
        style: 'review',
        duration: 180,
        language: 'zh-TW'
      }
    }
  ];

  for (let i = 0; i < testCases.length; i++) {
    const testCase = testCases[i];
    console.log(`\n📍 测试步骤 ${i + 2}: ${testCase.name}`);
    
    try {
      const response = await fetch(`${API_BASE}/api/v1/generate/script`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testCase.data)
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          console.log('✅ 脚本生成成功');
          console.log(`   生成器: ${data.data.provider || '未知'}`);
          console.log(`   模型: ${data.data.model || '未知'}`);
          console.log(`   脚本长度: ${data.data.script.length} 字符`);
          console.log(`   词数统计: ${data.data.word_count} 词`);
          console.log(`   预估时长: ${data.data.estimated_duration}`);
          console.log(`   生成时间: ${data.data.generated_at}`);
          
          if (data.data.note) {
            console.log(`   📝 说明: ${data.data.note}`);
          }
          
          // 显示脚本开头预览
          const preview = data.data.script.substring(0, 100);
          console.log(`   📖 脚本预览: ${preview}...`);
          
          // 检查脚本质量
          const script = data.data.script;
          let qualityScore = 0;
          let qualityNotes = [];
          
          // 检查开头是否吸引人
          if (script.includes('？') || script.includes('！') || script.includes('等等') || script.includes('你知道')) {
            qualityScore += 20;
            qualityNotes.push('开头有吸引力');
          }
          
          // 检查是否有结构化内容
          if (script.includes('第一') || script.includes('首先') || script.includes('步骤')) {
            qualityScore += 20;
            qualityNotes.push('内容结构化');
          }
          
          // 检查是否有行动呼吁
          if (script.includes('订阅') || script.includes('点赞') || script.includes('关注') || script.includes('评论')) {
            qualityScore += 20;
            qualityNotes.push('包含行动呼吁');
          }
          
          // 检查语言生动性
          if (script.includes('超') || script.includes('绝对') || script.includes('震惊') || script.includes('有趣')) {
            qualityScore += 20;
            qualityNotes.push('语言生动有趣');
          }
          
          // 检查平台适配
          const platformKeywords = {
            'youtube': ['订阅', '评论区'],
            'tiktok': ['小爱心', '双击'],
            'bilibili': ['UP主', '一键三连'],
            'instagram': ['保存', '分享']
          };
          
          const keywords = platformKeywords[testCase.data.platform] || [];
          if (keywords.some(keyword => script.includes(keyword))) {
            qualityScore += 20;
            qualityNotes.push('平台特色明显');
          }
          
          console.log(`   🏆 质量得分: ${qualityScore}/100`);
          console.log(`   📊 质量特点: ${qualityNotes.join(', ')}`);
          
          successCount++;
        } else {
          console.log('❌ 脚本生成失败:', data.error || '未知错误');
        }
      } else {
        const errorData = await response.json();
        console.log('❌ API调用失败:', errorData.detail || response.status);
      }
    } catch (error) {
      console.log('❌ 脚本生成错误:', error.message);
    }
    
    // 添加延迟避免API限制
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  console.log('\n' + '='.repeat(60));
  console.log('📊 测试结果总结:');
  console.log(`✅ 通过: ${successCount}/${totalTests}`);
  console.log(`❌ 失败: ${totalTests - successCount}/${totalTests}`);
  console.log(`📈 成功率: ${Math.round(successCount / totalTests * 100)}%`);

  if (successCount === totalTests) {
    console.log('\n🎉 所有测试通过！AI脚本生成功能完全正常！');
    console.log('\n📍 功能特色:');
    console.log('   🤖 DeepSeek AI模型: 生成更有创意的脚本');
    console.log('   🔄 智能回退机制: API失败时使用增强版本地生成');
    console.log('   🎯 平台适配: 针对不同平台优化脚本风格');
    console.log('   🎨 多样风格: 支持教育、娱乐、教程、评测等风格');
    console.log('   📊 质量评估: 自动评估脚本质量和特色');
    
    console.log('\n🚀 现在可以在前端体验:');
    console.log('   • 访问: http://localhost:5173/create');
    console.log('   • 进入步骤2：脚本生成');
    console.log('   • 尝试不同的主题、平台和风格组合');
    console.log('   • 观察AI生成的脚本质量提升');
  } else if (successCount > 0) {
    console.log('\n⚠️ 部分测试通过，系统基本功能正常');
    console.log('💡 可能的问题:');
    console.log('   • DeepSeek API密钥未配置 (将使用增强版回退)');
    console.log('   • 网络连接问题');
    console.log('   • API配额限制');
  } else {
    console.log('\n❌ 所有测试失败，请检查系统配置');
  }
}

// 执行测试
testScriptGeneration().catch(console.error);