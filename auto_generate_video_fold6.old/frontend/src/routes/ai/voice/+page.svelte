<script>
  import { onMount } from 'svelte';
  import { toastStore } from '$lib/stores/toast';

  // Import voice components
  import VoiceSynthesizer from '$lib/components/ai/voice/VoiceSynthesizer.svelte';

  let isGenerating = false;
  let generatedAudio = null;
  let showAdvanced = false;
  
  // Form data
  let formData = {
    text: '',
    voice_id: 'sarah',
    language: 'en',
    speed: 1.0,
    pitch: 0,
    volume: 80,
    emphasis: 'none',
    sentence_pause: 300,
    paragraph_pause: 500,
    enable_ssml: false
  };

  async function generateVoice() {
    if (!formData.text.trim()) {
      toastStore.error('Please enter text to synthesize');
      return;
    }

    isGenerating = true;
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      generatedAudio = {
        id: Date.now(),
        text: formData.text,
        voice_id: formData.voice_id,
        duration: Math.ceil(formData.text.length / 10), // Rough estimate
        createdAt: new Date().toISOString(),
        url: '/api/placeholder/audio.mp3' // Mock URL
      };
      
      toastStore.success('Voice generated successfully!');
    } catch (error) {
      console.error('Error generating voice:', error);
      toastStore.error('Failed to generate voice. Please try again.');
    } finally {
      isGenerating = false;
    }
  }

  function handleGenerate() {
    generateVoice();
  }

  function handlePreview(event) {
    const voiceId = event.detail;
    toastStore.info(`Playing preview for voice: ${voiceId}`);
  }
</script>

<svelte:head>
  <title>AI Voice Synthesizer - AutoVideo</title>
</svelte:head>

<div class="max-w-4xl mx-auto">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
      AI Voice Synthesizer
    </h1>
    <p class="text-gray-600 dark:text-gray-400">
      Convert text to natural-sounding speech with customizable voice options
    </p>
  </div>

  <div class="space-y-6">
    <!-- Voice Synthesizer -->
    <VoiceSynthesizer
      bind:formData
      bind:isGenerating
      bind:showAdvanced
      on:generate={handleGenerate}
      on:preview={handlePreview}
    />

    <!-- Generated Audio -->
    {#if generatedAudio}
      <div class="card">
        <div class="card-header">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Generated Audio
          </h3>
        </div>
        
        <div class="card-body">
          <div class="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-4">
            <div class="flex items-center justify-between mb-3">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-white">
                  Audio Preview
                </h4>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  Duration: {generatedAudio.duration}s • Voice: {generatedAudio.voice_id}
                </p>
              </div>
              <div class="flex items-center space-x-2">
                <button
                  type="button"
                  class="btn-ghost text-sm"
                  on:click={() => toastStore.success('Audio downloaded')}
                >
                  Download
                </button>
                <button
                  type="button"
                  class="btn-primary text-sm"
                  on:click={() => toastStore.success('Added to project')}
                >
                  Use in Project
                </button>
              </div>
            </div>
            
            <!-- Mock Audio Player -->
            <div class="bg-white dark:bg-gray-700 rounded p-3 border">
              <div class="flex items-center space-x-3">
                <button class="w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center hover:bg-primary-700">
                  ▶
                </button>
                <div class="flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                  <div class="bg-primary-600 h-2 rounded-full" style="width: 0%"></div>
                </div>
                <span class="text-xs text-gray-500 dark:text-gray-400">00:00 / 00:{generatedAudio.duration.toString().padStart(2, '0')}</span>
              </div>
            </div>
          </div>
          
          <div class="text-xs text-gray-600 dark:text-gray-300 p-3 bg-gray-100 dark:bg-gray-700 rounded">
            <strong>Original Text:</strong><br>
            {generatedAudio.text}
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>