<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { toastStore } from '$lib/stores/toast';

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
      await new Promise(resolve => setTimeout(resolve, 3000));
      
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

      toastStore.success('Script generated successfully!');
    } catch (error) {
      toastStore.error('Failed to generate script');
    } finally {
      isGenerating = false;
    }
  }

  async function generateImages() {
    isGenerating = true;
    
    try {
      await new Promise(resolve => setTimeout(resolve, 4000));
      
      projectData.images = [
        { id: 1, url: '/api/placeholder/1920/1080', type: 'thumbnail', prompt: 'Video thumbnail' },
        { id: 2, url: '/api/placeholder/1920/1080', type: 'background', prompt: 'Background image 1' },
        { id: 3, url: '/api/placeholder/1920/1080', type: 'background', prompt: 'Background image 2' },
        { id: 4, url: '/api/placeholder/1920/1080', type: 'overlay', prompt: 'Text overlay background' }
      ];

      toastStore.success('Images generated successfully!');
    } catch (error) {
      toastStore.error('Failed to generate images');
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
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      const voices = [
        { id: 'sarah', name: 'Sarah' },
        { id: 'james', name: 'James' },
        { id: 'maria', name: 'Maria' },
        { id: 'alex', name: 'Alex' }
      ];
      
      projectData.audio = {
        url: '#',
        duration: Math.ceil(projectData.script.split(' ').length / 2.5),
        voice: voices.find(v => v.id === projectData.voiceSettings.voice_id)?.name || 'Sarah'
      };

      toastStore.success('Voice generated successfully!');
    } catch (error) {
      toastStore.error('Failed to generate voice');
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
    
    try {
      await new Promise(resolve => setTimeout(resolve, 8000));
      
      projectData.video = {
        url: '#',
        duration: projectData.audio.duration,
        resolution: projectData.platform === 'youtube' ? '1920x1080' : '1080x1920',
        fileSize: '125 MB',
        format: 'MP4'
      };

      toastStore.success('Video assembled successfully!');
    } catch (error) {
      toastStore.error('Failed to assemble video');
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

  function handleDownload() {
    toastStore.success('Download started!');
  }

  function handleUpload() {
    toastStore.info('Upload feature not implemented yet');
  }
</script>

<svelte:head>
  <title>Create Video - AutoVideo</title>
</svelte:head>

<div class="max-w-4xl mx-auto">
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