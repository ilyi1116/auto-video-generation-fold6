<script>
  import { createEventDispatcher } from 'svelte';
  import { Wand2, RefreshCw, Edit3 } from 'lucide-svelte';

  export let projectData = {};
  export let isGenerating = false;

  const dispatch = createEventDispatcher();

  function handleGenerate() {
    dispatch('generate');
  }

  function handleNext() {
    if (!projectData.script.trim()) {
      dispatch('error', 'Please generate a script first');
      return;
    }
    dispatch('next');
  }

  function handlePrevious() {
    dispatch('previous');
  }
</script>

<div class="card">
  <div class="card-header">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Script Generation</h2>
    <p class="text-gray-600 dark:text-gray-400">AI will create an engaging script based on your project settings</p>
  </div>
  
  <div class="card-body space-y-6">
    <!-- Project Summary -->
    <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
      <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-2">Project Summary</h3>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <span class="text-gray-500 dark:text-gray-400">Title:</span>
          <p class="font-medium text-gray-900 dark:text-white">{projectData.title}</p>
        </div>
        <div>
          <span class="text-gray-500 dark:text-gray-400">Style:</span>
          <p class="font-medium text-gray-900 dark:text-white capitalize">{projectData.style}</p>
        </div>
        <div>
          <span class="text-gray-500 dark:text-gray-400">Platform:</span>
          <p class="font-medium text-gray-900 dark:text-white capitalize">{projectData.platform}</p>
        </div>
        <div>
          <span class="text-gray-500 dark:text-gray-400">Duration:</span>
          <p class="font-medium text-gray-900 dark:text-white">
            {Math.floor(projectData.duration / 60)}:{(projectData.duration % 60).toString().padStart(2, '0')}
          </p>
        </div>
      </div>
    </div>

    <!-- Script Generation -->
    <div>
      <div class="flex items-center justify-between mb-4">
        <label class="text-sm font-medium text-gray-700 dark:text-gray-300">
          Generated Script
        </label>
        <button
          type="button"
          class="btn-secondary flex items-center text-sm"
          on:click={handleGenerate}
          disabled={isGenerating}
        >
          {#if isGenerating}
            <RefreshCw class="w-4 h-4 mr-2 animate-spin" />
            Generating...
          {:else}
            <Wand2 class="w-4 h-4 mr-2" />
            {projectData.script ? 'Regenerate' : 'Generate'} Script
          {/if}
        </button>
      </div>

      {#if isGenerating}
        <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8">
          <div class="text-center">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-4"></div>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              AI is crafting your script...
            </p>
          </div>
        </div>
      {:else if projectData.script}
        <div class="space-y-4">
          <textarea
            bind:value={projectData.script}
            rows="12"
            class="form-input w-full font-mono text-sm"
            placeholder="Your generated script will appear here..."
          ></textarea>
          
          <div class="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
            <div class="flex items-center space-x-4">
              <span>Words: {projectData.script.split(' ').length}</span>
              <span>Est. duration: {Math.ceil(projectData.script.split(' ').length / 2.5)}s</span>
            </div>
            <button
              type="button"
              class="flex items-center text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300"
            >
              <Edit3 class="w-4 h-4 mr-1" />
              Edit manually
            </button>
          </div>
        </div>
      {:else}
        <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8">
          <div class="text-center">
            <Wand2 class="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
              Ready to generate your script
            </h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
              Click "Generate Script" to create AI-powered content based on your project settings
            </p>
            <button
              type="button"
              class="btn-primary flex items-center mx-auto"
              on:click={handleGenerate}
            >
              <Wand2 class="w-4 h-4 mr-2" />
              Generate Script
            </button>
          </div>
        </div>
      {/if}
    </div>
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
      disabled={!projectData.script}
    >
      Continue to Visuals
    </button>
  </div>
</div>