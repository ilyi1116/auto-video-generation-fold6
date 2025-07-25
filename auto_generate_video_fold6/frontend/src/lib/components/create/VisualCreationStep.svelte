<script>
  import { createEventDispatcher } from 'svelte';
  import { Image, RefreshCw, Eye, Download, Upload } from 'lucide-svelte';

  export let projectData = {};
  export let isGenerating = false;

  const dispatch = createEventDispatcher();

  function handleGenerate() {
    dispatch('generate');
  }

  function handleNext() {
    if (!projectData.images.length) {
      dispatch('error', 'Please generate images first');
      return;
    }
    dispatch('next');
  }

  function handlePrevious() {
    dispatch('previous');
  }

  function handleUpload() {
    // Handle custom image upload
    dispatch('upload');
  }
</script>

<div class="card">
  <div class="card-header">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Visual Creation</h2>
    <p class="text-gray-600 dark:text-gray-400">Generate images and visuals for your video</p>
  </div>
  
  <div class="card-body space-y-6">
    <!-- Generation Controls -->
    <div class="flex items-center justify-between">
      <div>
        <h3 class="text-sm font-medium text-gray-900 dark:text-white">AI-Generated Images</h3>
        <p class="text-xs text-gray-500 dark:text-gray-400">
          Images will be created based on your script content
        </p>
      </div>
      <div class="flex space-x-2">
        <button
          type="button"
          class="btn-secondary flex items-center text-sm"
          on:click={handleUpload}
        >
          <Upload class="w-4 h-4 mr-2" />
          Upload Custom
        </button>
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
            <Image class="w-4 h-4 mr-2" />
            {projectData.images.length ? 'Regenerate' : 'Generate'} Images
          {/if}
        </button>
      </div>
    </div>

    {#if isGenerating}
      <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8">
        <div class="text-center">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            Creating stunning visuals for your video...
          </p>
        </div>
      </div>
    {:else if projectData.images.length}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        {#each projectData.images as image, index}
          <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <div class="aspect-video bg-gray-200 dark:bg-gray-600 rounded-lg mb-3 flex items-center justify-center">
              <Image class="w-8 h-8 text-gray-400" />
            </div>
            <div class="flex items-center justify-between">
              <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-white capitalize">
                  {image.type}
                </h4>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                  {image.prompt}
                </p>
              </div>
              <div class="flex space-x-1">
                <button
                  type="button"
                  class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  title="Preview"
                >
                  <Eye class="w-4 h-4" />
                </button>
                <button
                  type="button"
                  class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  title="Download"
                >
                  <Download class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8">
        <div class="text-center">
          <Image class="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
            Ready to create visuals
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
            AI will generate images that match your script and video style
          </p>
          <button
            type="button"
            class="btn-primary flex items-center mx-auto"
            on:click={handleGenerate}
          >
            <Image class="w-4 h-4 mr-2" />
            Generate Images
          </button>
        </div>
      </div>
    {/if}

    <!-- Image Settings -->
    {#if projectData.images.length}
      <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
        <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-3">Image Settings</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Style
            </label>
            <select class="form-input text-sm">
              <option>Photorealistic</option>
              <option>Artistic</option>
              <option>Minimalist</option>
              <option>Illustration</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Quality
            </label>
            <select class="form-input text-sm">
              <option>Standard</option>
              <option>High</option>
              <option>Ultra</option>
            </select>
          </div>
          <div>
            <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              Aspect Ratio
            </label>
            <select class="form-input text-sm">
              <option>16:9 (YouTube)</option>
              <option>9:16 (Vertical)</option>
              <option>1:1 (Square)</option>
            </select>
          </div>
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
      disabled={!projectData.images.length}
    >
      Continue to Voice
    </button>
  </div>
</div>