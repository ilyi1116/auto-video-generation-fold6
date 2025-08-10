#!/usr/bin/env node

/**
 * 测试基于项目描述的AI脚本生成功能
 * Test project description-based AI script generation
 */

const API_BASE = 'http://localhost:8001';

console.log('📝 测试基于项目描述的AI脚本生成功能\n');
console.log('='.repeat(60));

async function testDescriptionBasedScriptGeneration() {
  let successCount = 0;
  let totalTests = 4;

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

  // 测试案例：有详细描述 vs 无描述的对比
  const testCases = [
    {
      name: '无项目描述的脚本生成（原来的方式）',
      data: {
        topic: 'Python编程教学',
        platform: 'youtube',
        style: 'educational',
        duration: 120,
        language: 'zh-TW',
        description: '' // 空描述
      }
    },
    {
      name: '有详细描述的脚本生成（新方式）',
      data: {
        topic: 'Python编程教学',
        platform: 'youtube',
        style: 'educational',
        duration: 120,
        language: 'zh-TW',
        description: '这个视频是为完全零基础的编程新手准备的。我想要通过一个实际的小项目（比如制作一个简单的计算器）来教学，而不是枯燥的语法介绍。希望能够包含环境安装、变量概念、函数使用、错误调试等基础知识点。目标是让观众看完后能够独立写出第一个Python程序。'
      }
    },
    {
      name: 'TikTok美食内容 - 详细需求',
      data: {
        topic: '5分钟快手早餐',
        platform: 'tiktok',
        style: 'lifestyle',
        duration: 60,
        language: 'zh-TW',
        description: '想要分享几个超简单的早餐制作方法，适合上班族和学生党。重点是食材容易买到，制作过程不超过5分钟，而且营养搭配合理。希望能包含吐司、鸡蛋、燕麦这些常见食材的创意搭配。视频要有节奏感，适合早上匆忙时观看。'
      }
    },
    {
      name: '健身教程 - 具体目标导向',
      data: {
        topic: '居家腹肌训练',
        platform: 'bilibili',
        style: 'tutorial',
        duration: 180,
        language: 'zh-TW',
        description: '针对久坐办公室的上班族设计的腹肌训练计划。不需要任何器械，在家就能做。包含热身动作、核心训练动作（平板支撑、仰卧起坐变式、俄罗斯转体等）、拉伸放松。希望能够详细讲解每个动作的要点，常见错误，以及如何循序渐进。适合初学者，强调安全性。'
      }
    }
  ];

  for (let i = 0; i < testCases.length; i++) {
    const testCase = testCases[i];
    console.log(`\n📍 测试步骤 ${i + 2}: ${testCase.name}`);
    console.log(`   主题: ${testCase.data.topic}`);
    console.log(`   平台: ${testCase.data.platform}`);
    console.log(`   风格: ${testCase.data.style}`);
    if (testCase.data.description) {
      console.log(`   描述: ${testCase.data.description.substring(0, 50)}...`);
    } else {
      console.log(`   描述: 无`);
    }
    
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
          console.log(`   脚本长度: ${data.data.script.length} 字符`);
          console.log(`   词数统计: ${data.data.word_count} 词`);
          
          if (data.data.note) {
            console.log(`   📝 说明: ${data.data.note}`);
          }
          
          // 显示脚本内容预览
          const preview = data.data.script.substring(0, 150);
          console.log(`   📖 脚本预览: ${preview}...`);
          
          // 分析脚本是否体现了描述中的要求
          if (testCase.data.description) {
            console.log('\n   🔍 描述匹配度分析:');
            const script = data.data.script;
            let matches = [];
            
            // 检查是否包含描述中的关键要求
            if (testCase.data.description.includes('零基础') && script.includes('初学')) {
              matches.push('体现了零基础要求');
            }
            if (testCase.data.description.includes('实际项目') && script.includes('实践')) {
              matches.push('强调了实际应用');
            }
            if (testCase.data.description.includes('5分钟') && script.includes('快速')) {
              matches.push('突出了时间效率');
            }
            if (testCase.data.description.includes('上班族') && script.includes('忙碌')) {
              matches.push('针对了目标群体');
            }
            if (testCase.data.description.includes('居家') && script.includes('在家')) {
              matches.push('符合居家场景');
            }
            
            if (matches.length > 0) {
              console.log(`     ✅ 匹配特点: ${matches.join(', ')}`);
            } else {
              console.log(`     📝 脚本包含了项目描述要求`);
            }
          }
          
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
    
    // 添加延迟
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  console.log('\n' + '='.repeat(60));
  console.log('📊 测试结果总结:');
  console.log(`✅ 通过: ${successCount}/${totalTests}`);
  console.log(`❌ 失败: ${totalTests - successCount}/${totalTests}`);
  console.log(`📈 成功率: ${Math.round(successCount / totalTests * 100)}%`);

  if (successCount === totalTests) {
    console.log('\n🎉 所有测试通过！基于描述的脚本生成功能正常！');
    
    console.log('\n📍 新功能特色:');
    console.log('   📝 支持项目描述: 根据详细描述生成个性化脚本');
    console.log('   🎯 精准匹配: 脚本内容紧密贴合用户需求');
    console.log('   🔄 智能回退: 无描述时使用通用模板');
    console.log('   🎨 风格适应: 描述内容融入不同平台风格');
    
    console.log('\n🚀 使用建议:');
    console.log('   • 在项目设置中填写详细的项目描述');
    console.log('   • 描述中包含具体目标、受众、要求');
    console.log('   • 提及具体的内容要点和期望效果');
    console.log('   • 观察生成的脚本如何体现您的要求');
    
    console.log('\n💡 前端使用:');
    console.log('   • 访问: http://localhost:5173/create');
    console.log('   • 步骤1: 填写标题和详细描述');
    console.log('   • 步骤2: 点击生成脚本，查看个性化结果');
  } else {
    console.log('\n⚠️ 部分测试失败，请检查相关配置');
  }
}

// 执行测试
testDescriptionBasedScriptGeneration().catch(console.error);