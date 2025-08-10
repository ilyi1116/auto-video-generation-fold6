#!/usr/bin/env node

/**
 * 测试影片生成和下载完整流程
 * Test complete video generation and download workflow
 */

const API_BASE = 'http://localhost:8001';

console.log('🎬 测试影片生成和下载功能\n');
console.log('='.repeat(60));

async function testVideoGenerationAndDownload() {
  let successCount = 0;
  let totalTests = 4;
  let videoId = null;

  console.log('\n📍 测试步骤 1: 验证后端API健康状态');
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

  console.log('\n📍 测试步骤 2: 测试影片生成API');
  try {
    const projectData = {
      title: 'AI技术教学影片',
      script: '欢迎来到AI技术教学的精彩世界！在今天的内容中，我们将探索AI技术的各个面向。',
      images: [
        { id: 1, url: 'https://picsum.photos/800/600?random=1', type: 'thumbnail' },
        { id: 2, url: 'https://picsum.photos/800/600?random=2', type: 'background' }
      ],
      audio: {
        url: 'https://example.com/audio.mp3',
        duration: 45,
        voice: 'Alloy'
      },
      duration: 60,
      platform: 'youtube',
      resolution: '1920x1080'
    };

    const response = await fetch(`${API_BASE}/api/v1/generate/video`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_data: projectData })
    });

    if (response.ok) {
      const data = await response.json();
      if (data.success && data.data.video_id) {
        videoId = data.data.video_id;
        console.log('✅ 影片生成成功');
        console.log(`   影片ID: ${videoId}`);
        console.log(`   影片标题: ${data.data.title}`);
        console.log(`   档案大小: ${data.data.fileSize}`);
        console.log(`   解析度: ${data.data.resolution}`);
        successCount++;
      } else {
        console.log('❌ 影片生成响应格式错误');
      }
    } else {
      const errorData = await response.json();
      console.log('❌ 影片生成失败:', errorData.detail || response.status);
    }
  } catch (error) {
    console.log('❌ 影片生成API错误:', error.message);
  }

  console.log('\n📍 测试步骤 3: 测试影片详情获取');
  if (videoId) {
    try {
      const response = await fetch(`${API_BASE}/api/v1/videos/${videoId}`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          console.log('✅ 影片详情获取成功');
          console.log(`   影片URL: ${data.data.url}`);
          console.log(`   下载URL: ${data.data.download_url}`);
          console.log(`   状态: ${data.data.status}`);
          successCount++;
        }
      } else {
        console.log('❌ 影片详情获取失败:', response.status);
      }
    } catch (error) {
      console.log('❌ 影片详情获取错误:', error.message);
    }
  } else {
    console.log('⏭️ 跳过影片详情测试（没有影片ID）');
  }

  console.log('\n📍 测试步骤 4: 测试影片下载API');
  if (videoId) {
    try {
      const response = await fetch(`${API_BASE}/api/v1/videos/${videoId}/download`);
      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          console.log('✅ 影片下载API正常');
          console.log(`   下载文件名: ${data.data.filename}`);
          console.log(`   文件大小: ${data.data.size}`);
          console.log(`   下载URL: ${data.data.download_url}`);
          console.log(`   过期时间: ${data.data.expires_at}`);
          successCount++;
        }
      } else {
        console.log('❌ 影片下载API失败:', response.status);
      }
    } catch (error) {
      console.log('❌ 影片下载API错误:', error.message);
    }
  } else {
    console.log('⏭️ 跳过影片下载测试（没有影片ID）');
  }

  console.log('\n' + '='.repeat(60));
  console.log('📊 测试结果总结:');
  console.log(`✅ 通过: ${successCount}/${totalTests}`);
  console.log(`❌ 失败: ${totalTests - successCount}/${totalTests}`);
  console.log(`📈 成功率: ${Math.round(successCount / totalTests * 100)}%`);

  if (successCount === totalTests) {
    console.log('\n🎉 所有测试通过！影片生成和下载功能完全正常！');
    console.log('\n📍 完整工作流程验证:');
    console.log('   1. ✅ 后端服务健康检查');
    console.log('   2. ✅ 影片生成API（包含所有必要元素验证）');
    console.log('   3. ✅ 影片详情获取API');
    console.log('   4. ✅ 影片下载API（生成下载链接）');
    console.log('\n🎬 现在您可以在前端 http://localhost:5173/create 完成整个流程：');
    console.log('   • 完成步骤1-4的所有设置');
    console.log('   • 在步骤5点击"开始组装影片"');
    console.log('   • 影片完成后点击"下载影片"按钮');
  } else {
    console.log('\n⚠️ 部分测试失败，请检查相关服务和配置');
  }
}

// 执行测试
testVideoGenerationAndDownload().catch(console.error);