<script>
  import { createEventDispatcher } from 'svelte';
  import { Mic, Play, Pause, RefreshCw, Upload } from 'lucide-svelte';

  export let projectData = {};
  export let isGenerating = false;

  const dispatch = createEventDispatcher();

  const voices = [
    { id: 'sarah', name: 'Sarah', gender: 'Female', accent: 'American', description: 'Professional and clear' },
    { id: 'james', name: 'James', gender: 'Male', accent: 'British', description: 'Authoritative and warm' },
    { id: 'maria', name: 'Maria', gender: 'Female', accent: 'Spanish', description: 'Energetic and friendly' },
    { id: 'alex', name: 'Alex', gender: 'Neutral', accent: 'Canadian', description: 'Versatile and natural' }
  ];

  let isPlaying = false;

  function handleGenerate() {
    dispatch('generate');
  }

  function handleNext() {
    if (!projectData.audio) {
      dispatch('error', 'Please generate voice first');
      return;
    }
    dispatch('next');
  }

  function handlePrevious() {
    dispatch('previous');
  }

  function togglePlayback() {
    isPlaying = !isPlaying;
    // In a real app, this would control audio playback
  }

  function handleUpload() {
    dispatch('upload');
  }
</script>

<div class="card">
  <div class="card-header">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Voice Synthesis</h2>
    <p class="text-gray-600 dark:text-gray-400">Create natural voiceover from your script</p>
  </div>
  
  <div class="card-body space-y-6">
    <!-- Voice Selection -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
        Select Voice
      </label>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        {#each voices as voice}
          <button
            type="button"
            class="p-4 text-left border rounded-lg transition-colors {
              projectData.voiceSettings.voice_id === voice.id
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }"
            on:click={() => projectData.voiceSettings.voice_id = voice.id}
          >
            <div class="flex items-center justify-between mb-2">
              <h3 class="text-sm font-medium text-gray-900 dark:text-white">
                {voice.name}
              </h3>
              <span class="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-600 rounded text-gray-600 dark:text-gray-400">
                {voice.gender}
              </span>
            </div>
            <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">
              {voice.accent} • {voice.description}
            </p>
            <button
              type="button"
              class="text-xs text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
              on:click|stopPropagation={() => {}}
            >
              Preview voice
            </button>
          </button>
        {/each}
      </div>
    </div>

    <!-- Voice Settings -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Speed: {projectData.voiceSettings.speed}x
        </label>
        <input
          type="range"
          bind:value={projectData.voiceSettings.speed}
          min="0.5"
          max="2.0"
          step="0.1"
          class="w-full"
        />
        <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
          <span>0.5x</span>
          <span>2.0x</span>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Emotion
        </label>
        <select bind:value={projectData.voiceSettings.emotion} class="form-input w-full">
          <option value="neutral">Neutral</option>
          <option value="happy">Happy</option>
          <option value="excited">Excited</option>
          <option value="calm">Calm</option>
          <option value="professional">Professional</option>
        </select>
      </div>
    </div>

    <!-- Generation Controls -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-sm font-medium text-gray-900 dark:text-white">Generated Audio</h3>
        <p class="text-xs text-gray-500 dark:text-gray-400">
          {#if projectData.script}
            Script length: {projectData.script.split(' ').length} words
          {:else}
            No script available
          {/if}
        </p>
      </div>
      <div class="flex space-x-2">
        <button
          type="button"
          class="btn-secondary flex items-center text-sm"
          on:click={handleUpload}
        >
          <Upload class="w-4 h-4 mr-2" />
          Upload Audio
        </button>
        <button
          type="button"
          class="btn-secondary flex items-center text-sm"
          on:click={handleGenerate}
          disabled={isGenerating || !projectData.script}
        >
          {#if isGenerating}
            <RefreshCw class="w-4 h-4 mr-2 animate-spin" />
            Synthesizing...
          {:else}
            <Mic class="w-4 h-4 mr-2" />
            {projectData.audio ? 'Regenerate' : 'Generate'} Voice
          {/if}
        </button>
      </div>
    </div>

    {#if isGenerating}
      <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8">
        <div class="text-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Synthesizing natural voice from your script...
          </p>
        </div>
      </div>
    {:else if projectData.audio}
      <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
        <div class="flex items-center justify-between mb-4">
          <div>
            <h4 class="text-sm font-medium text-gray-900 dark:text-white">
              Generated Audio
            </h4>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              Voice: {projectData.audio.voice} • Duration: {projectData.audio.duration}s
            </p>
          </div>
          <button
            type="button"
            class="flex items-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            on:click={togglePlayback}
          >
            <svelte:component this={isPlaying ? Pause : Play} class="w-4 h-4" />
            <span class="text-sm">{isPlaying ? 'Pause' : 'Play'}</span>
          </button>
        </div>
        
        <!-- Audio Waveform Placeholder -->
        <div class="h-16 bg-gray-200 dark:bg-gray-600 rounded flex items-center justify-center">
          <div class="flex items-end space-x-1">
            {#each Array(20) as _, i}
              <div class="w-1 bg-primary-400 rounded-t" style="height: {Math.random() * 40 + 10}px"></div>
            {/each}
          </div>
        </div>
      </div>
    {:else}
      <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8">
        <div class="text-center">
          <Mic class="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
            Ready to synthesize voice
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
            {#if projectData.script}
              Generate natural-sounding voiceover from your script
            {:else}
              Please complete the script generation step first
            {/if}
          </p>
          <button
            type="button"
            class="btn-primary flex items-center mx-auto"
            on:click={handleGenerate}
            disabled={!projectData.script}
          >
            <Mic class="w-4 h-4 mr-2" />
            Generate Voice
          </button>
        </div>
      </div>
    {/if}
  </div>

  <div class="card-footer flex justify-between">
    <button
      type="button"
      class="btn-secondary"
      on:click={handlePrevious}
    >
      Previous Step
    </button>
    
    <button
      type="button"
      class="btn-primary"
      on:click={handleNext}
      disabled={!projectData.audio}
    >
      Continue to Assembly
    </button>
  </div>
</div>