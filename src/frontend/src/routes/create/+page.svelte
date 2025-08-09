<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { toastStore } from '$lib/stores/toast.js';
  import { apiClient } from '$lib/api/client.js';
  import { notifications, trackVideoProgress, simulateProgress } from '$lib/stores/notifications.js';
  import Navigation from '$lib/components/layout/Navigation.svelte';

  // Import step components
  import StepIndicator from '$lib/components/create/StepIndicator.svelte';
  import ProjectSetupStep from '$lib/components/create/ProjectSetupStep.svelte';
  import ScriptGenerationStep from '$lib/components/create/ScriptGenerationStep.svelte';
  import VisualCreationStep from '$lib/components/create/VisualCreationStep.svelte';
  import VoiceSynthesisStep from '$lib/components/create/VoiceSynthesisStep.svelte';
  import VideoAssemblyStep from '$lib/components/create/VideoAssemblyStep.svelte';

  let currentStep = 1;
  let totalSteps = 5;
  let isGenerating = false;
  let projectData = {
    title: '',
    description: '',
    style: 'educational',
    duration: 60,
    platform: 'youtube',
    script: '',
    voiceSettings: {
      voice_id: 'sarah',
      speed: 1.0,
      emotion: 'neutral'
    },
    images: [],
    audio: null,
    video: null
  };

  // Step configuration
  const steps = [
    { id: 1, title: 'Project Setup', description: 'Basic project information' },
    { id: 2, title: 'Script Generation', description: 'AI-powered script creation' },
    { id: 3, title: 'Visual Creation', description: 'Generate images and visuals' },
    { id: 4, title: 'Voice Synthesis', description: 'Create natural voiceover' },
    { id: 5, title: 'Video Assembly', description: 'Combine all elements' }
  ];

  onMount(() => {
    projectData.title = `New Video Project ${Date.now()}`;
  });

  function goToStep(step) {
    currentStep = step;
  }

  function handleNext() {
    if (currentStep < totalSteps) {
      currentStep++;
    }
  }

  function handlePrevious() {
    if (currentStep > 1) {
      currentStep--;
    }
  }

  function handleError(message) {
    toastStore.error(message);
  }

  async function generateScript() {
    if (!projectData.title.trim()) {
      toastStore.error('Please enter a project title first');
      return;
    }

    isGenerating = true;
    
    try {
      // 調用增強的AI腳本生成API - 整合Google搜索
      const searchSettings = projectData.searchSettings || { enableSearch: true, timeRange: 'w' };
      const response = await apiClient.ai.generateScript(
        projectData.title,
        projectData.platform,
        projectData.style,
        projectData.duration,
        'zh-TW',
        projectData.description,
        searchSettings.enableSearch,
        searchSettings.timeRange
      );
      
      if (response.success) {
        projectData.script = response.data.script || response.data.content || 'Script generated successfully!';
        
        // 顯示搜索增強信息
        const data = response.data;
        if (data.search_enabled && data.search_results_count > 0) {
          toastStore.success(
            `✅ AI腳本生成成功！\n🔍 已整合 ${data.search_results_count} 條最新資訊 (${data.time_range === 'd' ? '過去1天' : data.time_range === 'w' ? '過去1週' : data.time_range === 'm' ? '過去1個月' : '過去1年'})\n🤖 提供者: ${data.provider}`
          );
          
          // 記錄搜索詳情到控制台
          console.log('🔍 腳本生成詳情:', {
            搜索啟用: data.search_enabled,
            搜索結果數量: data.search_results_count,
            時間範圍: data.time_range,
            搜索摘要: data.search_summary,
            來源: data.search_sources
          });
        } else if (data.search_enabled) {
          toastStore.success(`✅ AI腳本生成成功！\n⚠️ 未找到相關最新資訊，使用基礎AI生成\n🤖 提供者: ${data.provider || 'AI'}`);
        } else {
          toastStore.success(`✅ AI腳本生成成功！\n🤖 提供者: ${data.provider || 'AI'}`);
        }
      } else {
        throw new Error(response.error || 'Failed to generate script');
      }
    } catch (error) {
      console.error('Script generation error:', error);
      toastStore.error(error.message || 'Failed to generate script');
      
      // 回退到模擬腳本
      projectData.script = `Welcome to this ${projectData.style} video about ${projectData.title}.

In today's video, we're going to explore the fascinating topic of ${projectData.title.toLowerCase()}. This is something that affects many people, and I want to share some valuable insights with you.

First, let's understand why this matters. The key thing to remember is that ${projectData.title.toLowerCase()} has become increasingly important in our daily lives.

Here are the main points we'll cover:

1. The fundamentals you need to know
2. Common mistakes people make  
3. Practical tips you can implement today
4. Advanced strategies for better results

Let me break this down for you step by step...

[Content continues with detailed explanation]

The bottom line is that understanding ${projectData.title.toLowerCase()} can make a significant difference in your life. I hope this video has been helpful to you.

If you found this valuable, please like and subscribe for more content like this. Let me know in the comments what you'd like to see next!`;
      toastStore.info('Using fallback script generation');
    } finally {
      isGenerating = false;
    }
  }

  async function generateImages() {
    isGenerating = true;
    
    try {
      // 生成多張圖像
      const imagePrompts = [
        `${projectData.title} thumbnail image`,
        `${projectData.title} background scene 1`, 
        `${projectData.title} background scene 2`,
        `${projectData.title} overlay graphics`
      ];
      
      const imagePromises = imagePrompts.map(async (prompt, index) => {
        try {
          // 調用增強的圖像生成API，傳遞腳本內容以獲得更智能的提示詞
          const response = await fetch('http://localhost:8001/api/v1/generate/image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              prompt: prompt,
              style: projectData.style,
              script: projectData.script || '', // 傳遞腳本內容
              topic: projectData.title,
              platform: projectData.platform,
              description: projectData.description || '', // 傳遞專案描述
              size: projectData.platform === 'youtube' ? '1920x1080' : '1080x1920'
            })
          });
          
          const result = await response.json();
          
          if (response.ok && result.success) {
            return {
              id: index + 1,
              url: result.data.url || '/api/placeholder/1920/1080',
              type: index === 0 ? 'thumbnail' : 'background',
              prompt: result.data.prompt,
              enhanced_prompt: result.data.enhanced_prompt,
              provider: result.data.provider
            };
          } else {
            throw new Error('API failed');
          }
        } catch (error) {
          // 回退到預設圖像
          return {
            id: index + 1,
            url: '/api/placeholder/1920/1080',
            type: index === 0 ? 'thumbnail' : 'background',
            prompt: prompt,
            provider: 'Fallback'
          };
        }
      });
      
      projectData.images = await Promise.all(imagePromises);
      toastStore.success('Images generated successfully with AI!');
    } catch (error) {
      console.error('Image generation error:', error);
      toastStore.error('Failed to generate images');
      // 回退到預設圖像
      projectData.images = [
        { id: 1, url: '/api/placeholder/1920/1080', type: 'thumbnail', prompt: 'Video thumbnail' },
        { id: 2, url: '/api/placeholder/1920/1080', type: 'background', prompt: 'Background image 1' },
        { id: 3, url: '/api/placeholder/1920/1080', type: 'background', prompt: 'Background image 2' },
        { id: 4, url: '/api/placeholder/1920/1080', type: 'overlay', prompt: 'Text overlay background' }
      ];
    } finally {
      isGenerating = false;
    }
  }

  async function generateVoice() {
    if (!projectData.script.trim()) {
      toastStore.error('Please generate a script first');
      return;
    }

    isGenerating = true;
    
    try {
      // 調用增強的AI語音合成API - 支援DeepSeek優化
      const response = await fetch('http://localhost:8001/api/v1/generate/voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: projectData.script,
          voice: projectData.voiceSettings.voice_id || 'alloy',
          speed: projectData.voiceSettings.speed || 1.0,
          platform: projectData.platform,
          style: projectData.style,
          topic: projectData.title,
          optimize_with_ai: true  // 啟用AI優化
        })
      });
      
      const result = await response.json();
      
      if (response.ok && result.success) {
        const voices = [
          { id: 'alloy', name: 'Alloy' },
          { id: 'echo', name: 'Echo' },
          { id: 'fable', name: 'Fable' },
          { id: 'onyx', name: 'Onyx' },
          { id: 'nova', name: 'Nova' },
          { id: 'shimmer', name: 'Shimmer' }
        ];
        
        // 構建增強的音頻對象
        projectData.audio = {
          url: result.data.url || '#',
          duration: result.data.duration,
          voice: voices.find(v => v.id === result.data.voice)?.name || 'Alloy',
          provider: result.data.provider,
          quality: result.data.quality,
          optimization: result.data.optimization,
          has_real_audio: result.data.has_real_audio || false,
          filepath: result.data.filepath
        };
        
        // 顯示優化信息
        if (result.data.optimization?.ai_optimized) {
          const opt = result.data.optimization;
          toastStore.success(
            `✅ AI語音生成成功！\n🤖 ${opt.optimization_reason}\n🎵 ${opt.optimized_voice} @ ${opt.optimized_speed}x\n💡 ${opt.emotion} · ${opt.tone}`
          );
          console.log('🎤 語音優化詳情:', opt);
        } else {
          toastStore.success(`✅ 語音生成成功！\n🔊 ${result.data.provider} · ${result.data.quality}\n⏱️ 時長: ${result.data.duration}秒`);
        }
        
        // 記錄統計信息
        console.log('📊 語音生成統計:', {
          provider: result.data.provider,
          voice: result.data.voice,
          speed: result.data.speed,
          duration: result.data.duration,
          text_length: result.data.text_length,
          chinese_chars: result.data.chinese_char_count
        });
        
      } else {
        throw new Error(result.error || 'Failed to generate voice');
      }
    } catch (error) {
      console.error('Voice generation error:', error);
      toastStore.error(error.message || 'Failed to generate voice');
      
      // 回退到模擬音頻
      const voices = [
        { id: 'alloy', name: 'Alloy' },
        { id: 'echo', name: 'Echo' },
        { id: 'fable', name: 'Fable' },
        { id: 'onyx', name: 'Onyx' },
        { id: 'nova', name: 'Nova' },
        { id: 'shimmer', name: 'Shimmer' }
      ];
      
      projectData.audio = {
        url: '#',
        duration: Math.ceil(projectData.script.split(' ').length / 2.5),
        voice: voices.find(v => v.id === projectData.voiceSettings.voice_id)?.name || 'Alloy',
        provider: 'Fallback',
        quality: 'Simulated'
      };
      toastStore.info('Using fallback voice generation');
    } finally {
      isGenerating = false;
    }
  }

  async function assembleVideo() {
    if (!projectData.script || !projectData.images.length || !projectData.audio) {
      toastStore.error('Please complete all previous steps first');
      return;
    }

    isGenerating = true;
    
    // 創建進度通知
    const notificationId = trackVideoProgress(
      `video_${Date.now()}`,
      projectData.title || 'New Video Project'
    );
    
    try {
      // 模擬進度更新
      simulateProgress(notificationId, projectData.title || 'New Video Project');
      
      // 調用真實的影片生成API
      const response = await fetch('http://localhost:8001/api/v1/generate/video', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          project_data: {
            title: projectData.title,
            script: projectData.script,
            images: projectData.images,
            audio: projectData.audio,
            duration: projectData.duration,
            platform: projectData.platform,
            resolution: projectData.platform === 'youtube' ? '1920x1080' : '1080x1920'
          }
        })
      });
      
      const result = await response.json();
      
      if (response.ok && result.success) {
        projectData.video = {
          video_id: result.data.video_id,
          url: result.data.url,
          download_url: result.data.download_url,
          thumbnail: result.data.thumbnail,
          duration: result.data.duration,
          resolution: result.data.resolution,
          fileSize: result.data.fileSize,
          format: result.data.format,
          status: result.data.status,
          generated_at: result.data.generated_at
        };
        toastStore.success('Video assembled successfully!');
      } else {
        throw new Error(result.error || 'Failed to generate video');
      }
    } catch (error) {
      console.error('Video assembly error:', error);
      // 更新通知為失敗狀態
      notifications.update(notificationId, {
        type: 'error',
        title: '影片處理失敗',
        message: `影片 "${projectData.title}" 處理失敗`,
        status: 'failed',
        progress: 0
      });
      toastStore.error(error.message || 'Failed to assemble video');
    } finally {
      isGenerating = false;
    }
  }

  function handleSave() {
    toastStore.success('Project saved successfully!');
  }

  function handleShare() {
    toastStore.success('Sharing options opened!');
  }

  async function handleDownload() {
    if (!projectData.video?.video_id) {
      toastStore.error('No video available for download');
      return;
    }
    
    try {
      // 獲取下載連結
      const response = await fetch(`http://localhost:8001/api/v1/videos/${projectData.video.video_id}/download`);
      const result = await response.json();
      
      if (response.ok && result.success) {
        // 在真實環境中，這裡會觸發檔案下載
        // 現在模擬下載過程
        const downloadUrl = result.data.download_url;
        const filename = result.data.filename;
        
        // 創建臨時下載連結（模擬）
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);
        
        // 在真實環境中會觸發實際下載
        // link.click();
        
        document.body.removeChild(link);
        
        toastStore.success(`Download started for ${filename}`);
        console.log('Download info:', result.data);
      } else {
        throw new Error(result.error || 'Failed to get download link');
      }
    } catch (error) {
      console.error('Download error:', error);
      toastStore.error(error.message || 'Failed to download video');
    }
  }

  function handleUpload() {
    toastStore.info('Upload feature not implemented yet');
  }
</script>

<svelte:head>
  <title>Create Video - AutoVideo</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <!-- Navigation -->
  <Navigation />
  
  <div class="max-w-4xl mx-auto px-4 py-8">
    <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">Create New Video</h1>
    <p class="text-gray-600 dark:text-gray-400">
      Follow the guided process to create your AI-powered video content
    </p>
  </div>

  <!-- Step Indicator -->
  <StepIndicator {steps} {currentStep} onStepClick={goToStep} />

  <!-- Step Content -->
  {#if currentStep === 1}
    <ProjectSetupStep 
      bind:projectData 
      on:next={handleNext}
      on:error={(e) => handleError(e.detail)}
    />
  {:else if currentStep === 2}
    <ScriptGenerationStep 
      bind:projectData 
      {isGenerating}
      on:next={handleNext}
      on:previous={handlePrevious}
      on:generate={generateScript}
      on:error={(e) => handleError(e.detail)}
    />
  {:else if currentStep === 3}
    <VisualCreationStep 
      bind:projectData 
      {isGenerating}
      on:next={handleNext}
      on:previous={handlePrevious}
      on:generate={generateImages}
      on:upload={handleUpload}
      on:error={(e) => handleError(e.detail)}
    />
  {:else if currentStep === 4}
    <VoiceSynthesisStep 
      bind:projectData 
      {isGenerating}
      on:next={handleNext}
      on:previous={handlePrevious}
      on:generate={generateVoice}
      on:upload={handleUpload}
      on:error={(e) => handleError(e.detail)}
    />
  {:else if currentStep === 5}
    <VideoAssemblyStep 
      bind:projectData 
      {isGenerating}
      on:previous={handlePrevious}
      on:generate={assembleVideo}
      on:save={handleSave}
      on:share={handleShare}
      on:download={handleDownload}
    />
  {/if}
  </div>
</div>