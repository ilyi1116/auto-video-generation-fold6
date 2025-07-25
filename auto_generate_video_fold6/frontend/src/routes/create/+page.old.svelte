<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { apiClient } from '$lib/api/client';
  import { toastStore } from '$lib/stores/toast';
  import { 
    Plus,
    Video,
    Wand2,
    Image,
    Mic,
    FileText,
    Settings,
    Play,
    Download,
    Upload,
    ChevronRight,
    ChevronLeft,
    Check,
    Clock,
    Eye,
    Edit3,
    RefreshCw,
    Save,
    Share2
  } from 'lucide-svelte';

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

  const videoStyles = [
    { value: 'educational', label: 'Educational', description: 'Informative and structured', icon: '📚' },
    { value: 'entertaining', label: 'Entertaining', description: 'Fun and engaging', icon: '🎭' },
    { value: 'promotional', label: 'Promotional', description: 'Marketing and sales focused', icon: '📢' },
    { value: 'tutorial', label: 'Tutorial', description: 'Step-by-step guidance', icon: '🛠️' },
    { value: 'storytelling', label: 'Storytelling', description: 'Narrative-driven content', icon: '📖' },
    { value: 'news', label: 'News & Updates', description: 'Current events and announcements', icon: '📰' }
  ];

  const platforms = [
    { value: 'youtube', label: 'YouTube', icon: '📺', recommended: '16:9' },
    { value: 'tiktok', label: 'TikTok', icon: '🎵', recommended: '9:16' },
    { value: 'instagram', label: 'Instagram Reels', icon: '📷', recommended: '9:16' },
    { value: 'twitter', label: 'Twitter', icon: '🐦', recommended: '16:9' },
    { value: 'linkedin', label: 'LinkedIn', icon: '💼', recommended: '16:9' }
  ];

  const voices = [
    { id: 'sarah', name: 'Sarah', gender: 'Female', accent: 'American', description: 'Professional and clear' },
    { id: 'james', name: 'James', gender: 'Male', accent: 'British', description: 'Authoritative and warm' },
    { id: 'maria', name: 'Maria', gender: 'Female', accent: 'Spanish', description: 'Energetic and friendly' },
    { id: 'alex', name: 'Alex', gender: 'Neutral', accent: 'Canadian', description: 'Versatile and natural' }
  ];

  onMount(() => {
    // Initialize project with defaults
    projectData.title = `New Video Project ${Date.now()}`;
  });

  function nextStep() {
    if (currentStep < totalSteps) {
      currentStep++;
    }
  }

  function prevStep() {
    if (currentStep > 1) {
      currentStep--;
    }
  }

  function goToStep(step) {
    currentStep = step;
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
        resolution: '1920x1080',
        format: 'mp4'
      };

      toastStore.success('Video assembled successfully!');
    } catch (error) {
      toastStore.error('Failed to assemble video');
    } finally {
      isGenerating = false;
    }
  }

  async function saveProject() {
    try {
      // In a real app, this would save to the database
      await new Promise(resolve => setTimeout(resolve, 1000));
      toastStore.success('Project saved successfully!');
    } catch (error) {
      toastStore.error('Failed to save project');
    }
  }

  function publishVideo() {
    goto('/projects');
    toastStore.success('Video published successfully!');
  }

  function getStepStatus(step) {
    if (step < currentStep) return 'completed';
    if (step === currentStep) return 'current';
    return 'upcoming';
  }

  function isStepCompleted(step) {
    switch (step) {
      case 1:
        return projectData.title && projectData.style && projectData.platform;
      case 2:
        return projectData.script;
      case 3:
        return projectData.images.length > 0;
      case 4:
        return projectData.audio;
      case 5:
        return projectData.video;
      default:
        return false;
    }
  }

  function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
</script>

<svelte:head>
  <title>Create Video - AutoVideo</title>
</svelte:head>

<div class="max-w-7xl mx-auto space-y-8">
  <!-- Header -->
  <div class="text-center">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-4">
      Create New Video
    </h1>
    <p class="text-lg text-gray-600 dark:text-gray-300">
      Follow our guided workflow to create professional videos with AI
    </p>
  </div>

  <!-- Progress Steps -->
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <div class="flex items-center justify-between">
      {#each steps as step, index}
        <div class="flex items-center {index < steps.length - 1 ? 'flex-1' : ''}">
          <!-- Step Circle -->
          <button
            type="button"
            class="flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors {
              getStepStatus(step.id) === 'completed' 
                ? 'bg-green-500 border-green-500 text-white' 
                : getStepStatus(step.id) === 'current'
                ? 'bg-primary-600 border-primary-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400'
            }"
            on:click={() => goToStep(step.id)}
          >
            {#if getStepStatus(step.id) === 'completed'}
              <Check class="w-5 h-5" />
            {:else}
              <span class="text-sm font-medium">{step.id}</span>
            {/if}
          </button>
          
          <!-- Step Info -->
          <div class="ml-3 hidden sm:block">
            <div class="text-sm font-medium text-gray-900 dark:text-white">
              {step.title}
            </div>
            <div class="text-xs text-gray-500 dark:text-gray-400">
              {step.description}
            </div>
          </div>
          
          <!-- Connector Line -->
          {#if index < steps.length - 1}
            <div class="flex-1 mx-4 h-0.5 bg-gray-200 dark:bg-gray-600"></div>
          {/if}
        </div>
      {/each}
    </div>
  </div>

  <!-- Step Content -->
  <div class="grid lg:grid-cols-4 gap-8">
    <!-- Main Content -->
    <div class="lg:col-span-3">
      {#if currentStep === 1}
        <!-- Step 1: Project Setup -->
        <div class="card">
          <div class="card-header">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Project Setup</h2>
          </div>
          <div class="card-body space-y-6">
            <!-- Project Title -->
            <div>
              <label for="title" class="form-label">Project Title *</label>
              <input
                id="title"
                type="text"
                bind:value={projectData.title}
                placeholder="e.g., 10 AI Tools That Will Change Everything"
                class="form-input"
              />
            </div>

            <!-- Description -->
            <div>
              <label for="description" class="form-label">Description (Optional)</label>
              <textarea
                id="description"
                bind:value={projectData.description}
                placeholder="Brief description of your video content..."
                rows="3"
                class="form-input resize-none"
              ></textarea>
            </div>

            <!-- Video Style -->
            <div>
              <label class="form-label">Video Style</label>
              <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                {#each videoStyles as style}
                  <button
                    type="button"
                    class="p-4 border-2 rounded-lg text-center transition-colors {projectData.style === style.value
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}"
                    on:click={() => projectData.style = style.value}
                  >
                    <div class="text-2xl mb-2">{style.icon}</div>
                    <div class="text-sm font-medium text-gray-900 dark:text-white">{style.label}</div>
                    <div class="text-xs text-gray-600 dark:text-gray-400 mt-1">{style.description}</div>
                  </button>
                {/each}
              </div>
            </div>

            <!-- Target Platform -->
            <div>
              <label class="form-label">Target Platform</label>
              <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                {#each platforms as platform}
                  <button
                    type="button"
                    class="p-4 border-2 rounded-lg text-center transition-colors {projectData.platform === platform.value
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}"
                    on:click={() => projectData.platform = platform.value}
                  >
                    <div class="text-2xl mb-2">{platform.icon}</div>
                    <div class="text-sm font-medium text-gray-900 dark:text-white">{platform.label}</div>
                    <div class="text-xs text-gray-600 dark:text-gray-400 mt-1">{platform.recommended}</div>
                  </button>
                {/each}
              </div>
            </div>

            <!-- Duration -->
            <div>
              <label for="duration" class="form-label">Target Duration</label>
              <div class="flex items-center space-x-4">
                <input
                  id="duration"
                  type="range"
                  bind:value={projectData.duration}
                  min="15"
                  max="300"
                  class="flex-1"
                />
                <span class="text-sm font-medium text-gray-700 dark:text-gray-300 w-16">
                  {formatDuration(projectData.duration)}
                </span>
              </div>
            </div>
          </div>
        </div>

      {:else if currentStep === 2}
        <!-- Step 2: Script Generation -->
        <div class="card">
          <div class="card-header">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Script Generation</h2>
              <button
                type="button"
                class="btn-primary flex items-center"
                on:click={generateScript}
                disabled={isGenerating || !projectData.title}
              >
                {#if isGenerating}
                  <RefreshCw class="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                {:else}
                  <Wand2 class="w-4 h-4 mr-2" />
                  Generate Script
                {/if}
              </button>
            </div>
          </div>
          <div class="card-body">
            {#if projectData.script}
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                    <span>{projectData.script.split(' ').length} words</span>
                    <span>~{Math.ceil(projectData.script.split(' ').length / 2.5)}s duration</span>
                    <span class="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-full text-xs">
                      AI Generated
                    </span>
                  </div>
                  <div class="flex space-x-2">
                    <button type="button" class="btn-secondary text-sm">
                      <Edit3 class="w-4 h-4 mr-1" />
                      Edit
                    </button>
                    <button type="button" class="btn-secondary text-sm" on:click={generateScript}>
                      <RefreshCw class="w-4 h-4 mr-1" />
                      Regenerate
                    </button>
                  </div>
                </div>
                
                <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <pre class="whitespace-pre-wrap text-sm text-gray-900 dark:text-white font-mono">{projectData.script}</pre>
                </div>
              </div>
            {:else}
              <div class="text-center py-12">
                <FileText class="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  No Script Generated Yet
                </h3>
                <p class="text-gray-600 dark:text-gray-400 mb-6">
                  Click "Generate Script" to create an AI-powered script based on your project settings
                </p>
              </div>
            {/if}
          </div>
        </div>

      {:else if currentStep === 3}
        <!-- Step 3: Visual Creation -->
        <div class="card">
          <div class="card-header">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Visual Creation</h2>
              <button
                type="button"
                class="btn-primary flex items-center"
                on:click={generateImages}
                disabled={isGenerating}
              >
                {#if isGenerating}
                  <RefreshCw class="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                {:else}
                  <Image class="w-4 h-4 mr-2" />
                  Generate Images
                {/if}
              </button>
            </div>
          </div>
          <div class="card-body">
            {#if projectData.images.length > 0}
              <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                {#each projectData.images as image}
                  <div class="relative bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden aspect-video">
                    <div class="absolute inset-0 flex items-center justify-center">
                      <Image class="w-8 h-8 text-gray-400" />
                    </div>
                    <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-2">
                      <p class="text-white text-xs">{image.type}</p>
                    </div>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="text-center py-12">
                <Image class="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  No Images Generated Yet
                </h3>
                <p class="text-gray-600 dark:text-gray-400 mb-6">
                  Generate AI-powered visuals that match your video content and style
                </p>
              </div>
            {/if}
          </div>
        </div>

      {:else if currentStep === 4}
        <!-- Step 4: Voice Synthesis -->
        <div class="card">
          <div class="card-header">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Voice Synthesis</h2>
              <button
                type="button"
                class="btn-primary flex items-center"
                on:click={generateVoice}
                disabled={isGenerating || !projectData.script}
              >
                {#if isGenerating}
                  <RefreshCw class="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                {:else}
                  <Mic class="w-4 h-4 mr-2" />
                  Generate Voice
                {/if}
              </button>
            </div>
          </div>
          <div class="card-body space-y-6">
            <!-- Voice Selection -->
            <div>
              <label class="form-label">Select Voice</label>
              <div class="grid grid-cols-2 gap-4">
                {#each voices as voice}
                  <button
                    type="button"
                    class="p-4 border-2 rounded-lg text-left transition-colors {projectData.voiceSettings.voice_id === voice.id
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}"
                    on:click={() => projectData.voiceSettings.voice_id = voice.id}
                  >
                    <div class="font-medium text-gray-900 dark:text-white">{voice.name}</div>
                    <div class="text-sm text-gray-600 dark:text-gray-400">{voice.gender} • {voice.accent}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-500 mt-1">{voice.description}</div>
                  </button>
                {/each}
              </div>
            </div>

            <!-- Voice Settings -->
            <div class="grid md:grid-cols-3 gap-6">
              <div>
                <label for="speed" class="form-label">Speed</label>
                <input
                  id="speed"
                  type="range"
                  bind:value={projectData.voiceSettings.speed}
                  min="0.5"
                  max="2.0"
                  step="0.1"
                  class="w-full"
                />
                <div class="text-sm text-gray-600 dark:text-gray-400 text-center mt-1">
                  {projectData.voiceSettings.speed}x
                </div>
              </div>
              
              <div>
                <label for="emotion" class="form-label">Emotion</label>
                <select id="emotion" bind:value={projectData.voiceSettings.emotion} class="form-input">
                  <option value="neutral">Neutral</option>
                  <option value="happy">Happy</option>
                  <option value="excited">Excited</option>
                  <option value="calm">Calm</option>
                  <option value="serious">Serious</option>
                </select>
              </div>
            </div>

            <!-- Generated Audio Preview -->
            {#if projectData.audio}
              <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <div class="flex items-center justify-between mb-4">
                  <div>
                    <h3 class="font-medium text-gray-900 dark:text-white">Generated Audio</h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400">
                      {projectData.audio.voice} • {formatDuration(projectData.audio.duration)}
                    </p>
                  </div>
                  <button type="button" class="btn-secondary flex items-center">
                    <Play class="w-4 h-4 mr-2" />
                    Preview
                  </button>
                </div>
                <div class="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                  <div class="bg-primary-600 h-2 rounded-full w-0"></div>
                </div>
              </div>
            {:else}
              <div class="text-center py-8">
                <Mic class="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Audio will appear here after generation
                </p>
              </div>
            {/if}
          </div>
        </div>

      {:else if currentStep === 5}
        <!-- Step 5: Video Assembly -->
        <div class="card">
          <div class="card-header">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Video Assembly</h2>
              <button
                type="button"
                class="btn-primary flex items-center"
                on:click={assembleVideo}
                disabled={isGenerating || !projectData.script || !projectData.images.length || !projectData.audio}
              >
                {#if isGenerating}
                  <RefreshCw class="w-4 h-4 mr-2 animate-spin" />
                  Assembling...
                {:else}
                  <Video class="w-4 h-4 mr-2" />
                  Assemble Video
                {/if}
              </button>
            </div>
          </div>
          <div class="card-body">
            {#if projectData.video}
              <!-- Video Preview -->
              <div class="bg-gray-100 dark:bg-gray-700 rounded-lg aspect-video flex items-center justify-center mb-6">
                <div class="text-center">
                  <Video class="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p class="text-lg font-medium text-gray-900 dark:text-white">Video Ready!</p>
                  <p class="text-sm text-gray-600 dark:text-gray-400">
                    {projectData.video.resolution} • {formatDuration(projectData.video.duration)} • {projectData.video.format.toUpperCase()}
                  </p>
                </div>
              </div>

              <!-- Action Buttons -->
              <div class="flex flex-col sm:flex-row gap-4">
                <button type="button" class="btn-secondary flex items-center justify-center">
                  <Eye class="w-4 h-4 mr-2" />
                  Preview Video
                </button>
                <button type="button" class="btn-secondary flex items-center justify-center">
                  <Download class="w-4 h-4 mr-2" />
                  Download
                </button>
                <button type="button" class="btn-secondary flex items-center justify-center" on:click={saveProject}>
                  <Save class="w-4 h-4 mr-2" />
                  Save Project
                </button>
                <button type="button" class="btn-primary flex items-center justify-center" on:click={publishVideo}>
                  <Share2 class="w-4 h-4 mr-2" />
                  Publish
                </button>
              </div>
            {:else}
              <div class="text-center py-12">
                <Video class="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  Ready to Assemble
                </h3>
                <p class="text-gray-600 dark:text-gray-400 mb-6">
                  Combine your script, images, and voice into a professional video
                </p>
                
                <!-- Assembly Checklist -->
                <div class="text-left max-w-md mx-auto space-y-2">
                  <div class="flex items-center space-x-2">
                    <div class="w-4 h-4 rounded-full {projectData.script ? 'bg-green-500' : 'bg-gray-300'}"></div>
                    <span class="text-sm text-gray-700 dark:text-gray-300">Script Generated</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <div class="w-4 h-4 rounded-full {projectData.images.length > 0 ? 'bg-green-500' : 'bg-gray-300'}"></div>
                    <span class="text-sm text-gray-700 dark:text-gray-300">Images Created</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <div class="w-4 h-4 rounded-full {projectData.audio ? 'bg-green-500' : 'bg-gray-300'}"></div>
                    <span class="text-sm text-gray-700 dark:text-gray-300">Voice Synthesized</span>
                  </div>
                </div>
              </div>
            {/if}
          </div>
        </div>
      {/if}
    </div>

    <!-- Sidebar -->
    <div class="space-y-6">
      <!-- Project Overview -->
      <div class="card">
        <div class="card-header">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Project Overview</h3>
        </div>
        <div class="card-body space-y-4">
          <div>
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">Title</label>
            <p class="text-sm text-gray-900 dark:text-white">{projectData.title || 'Untitled Project'}</p>
          </div>
          
          <div>
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">Style</label>
            <p class="text-sm text-gray-900 dark:text-white capitalize">{projectData.style}</p>
          </div>
          
          <div>
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">Platform</label>
            <p class="text-sm text-gray-900 dark:text-white capitalize">{projectData.platform}</p>
          </div>
          
          <div>
            <label class="text-sm font-medium text-gray-700 dark:text-gray-300">Duration</label>
            <p class="text-sm text-gray-900 dark:text-white">{formatDuration(projectData.duration)}</p>
          </div>
        </div>
      </div>

      <!-- Progress Checklist -->
      <div class="card">
        <div class="card-header">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Progress</h3>
        </div>
        <div class="card-body space-y-3">
          {#each steps as step}
            <div class="flex items-center space-x-3">
              <div class="w-6 h-6 rounded-full flex items-center justify-center {
                isStepCompleted(step.id) 
                  ? 'bg-green-500 text-white' 
                  : 'bg-gray-200 dark:bg-gray-600 text-gray-500 dark:text-gray-400'
              }">
                {#if isStepCompleted(step.id)}
                  <Check class="w-4 h-4" />
                {:else}
                  <span class="text-xs">{step.id}</span>
                {/if}
              </div>
              <span class="text-sm text-gray-900 dark:text-white">{step.title}</span>
            </div>
          {/each}
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="card">
        <div class="card-header">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Quick Actions</h3>
        </div>
        <div class="card-body space-y-2">
          <button type="button" class="w-full btn-secondary text-sm" on:click={saveProject}>
            <Save class="w-4 h-4 mr-2" />
            Save Progress
          </button>
          <button type="button" class="w-full btn-secondary text-sm">
            <Upload class="w-4 h-4 mr-2" />
            Upload Assets
          </button>
          <button type="button" class="w-full btn-secondary text-sm">
            <Settings class="w-4 h-4 mr-2" />
            Project Settings
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Navigation -->
  <div class="flex items-center justify-between">
    <button
      type="button"
      class="btn-secondary flex items-center"
      on:click={prevStep}
      disabled={currentStep === 1}
    >
      <ChevronLeft class="w-4 h-4 mr-2" />
      Previous
    </button>
    
    <div class="text-sm text-gray-500 dark:text-gray-400">
      Step {currentStep} of {totalSteps}
    </div>
    
    <button
      type="button"
      class="btn-primary flex items-center"
      on:click={nextStep}
      disabled={currentStep === totalSteps || !isStepCompleted(currentStep)}
    >
      Next
      <ChevronRight class="w-4 h-4 ml-2" />
    </button>
  </div>
</div>