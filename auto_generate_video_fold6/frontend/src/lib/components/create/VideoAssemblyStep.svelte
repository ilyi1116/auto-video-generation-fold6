<script>
  import { createEventDispatcher } from 'svelte';
  import { Video, Play, Download, Save, Share2, RefreshCw, Eye, Settings } from 'lucide-svelte';

  export let projectData = {};
  export let isGenerating = false;

  const dispatch = createEventDispatcher();

  let isPlaying = false;

  function handleGenerate() {
    dispatch('generate');
  }

  function handlePrevious() {
    dispatch('previous');
  }

  function handleSave() {
    dispatch('save');
  }

  function handleShare() {
    dispatch('share');
  }

  function handleDownload() {
    dispatch('download');
  }

  function togglePlayback() {
    isPlaying = !isPlaying;
  }
</script>

<div class="card">
  <div class="card-header">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Video Assembly</h2>
    <p class="text-gray-600 dark:text-gray-400">Combine all elements into your final video</p>
  </div>
  
  <div class="card-body space-y-6">
    <!-- Assembly Progress -->
    {#if isGenerating}
      <div class="bg-primary-50 dark:bg-primary-900/20 rounded-lg p-6">
        <div class="flex items-center space-x-4">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          <div>
            <h3 class="text-sm font-medium text-gray-900 dark:text-white">
              Assembling your video...
            </h3>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              This may take a few minutes depending on video length
            </p>
          </div>
        </div>
        
        <!-- Progress Steps -->
        <div class="mt-4 space-y-2">
          <div class="flex items-center text-xs">
            <div class="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
            <span class="text-gray-600 dark:text-gray-400">Processing script and timing</span>
          </div>
          <div class="flex items-center text-xs">
            <div class="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
            <span class="text-gray-600 dark:text-gray-400">Synchronizing audio and visuals</span>
          </div>
          <div class="flex items-center text-xs">
            <div class="w-2 h-2 bg-primary-500 rounded-full mr-2 animate-pulse"></div>
            <span class="text-gray-900 dark:text-white font-medium">Rendering final video</span>
          </div>
          <div class="flex items-center text-xs">
            <div class="w-2 h-2 bg-gray-300 dark:bg-gray-600 rounded-full mr-2"></div>
            <span class="text-gray-400">Optimizing for platform</span>
          </div>
        </div>
      </div>
    {/if}

    <!-- Video Preview -->
    {#if projectData.video}
      <div class="bg-black rounded-lg overflow-hidden">
        <div class="aspect-video flex items-center justify-center">
          <button
            type="button"
            class="flex items-center justify-center w-16 h-16 bg-white bg-opacity-90 rounded-full hover:bg-opacity-100 transition-all"
            on:click={togglePlayback}
          >
            <svelte:component this={isPlaying ? Video : Play} class="w-8 h-8 text-gray-900 {isPlaying ? '' : 'ml-1'}" />
          </button>
        </div>
        
        <!-- Video Controls -->
        <div class="bg-gray-900 p-4">
          <div class="flex items-center justify-between">
            <div class="flex items-center space-x-4">
              <button
                type="button"
                class="text-white hover:text-gray-300"
                on:click={togglePlayback}
              >
                <svelte:component this={isPlaying ? Video : Play} class="w-5 h-5" />  
              </button>
              <span class="text-white text-sm">0:00 / {Math.floor(projectData.video.duration / 60)}:{(projectData.video.duration % 60).toString().padStart(2, '0')}</span>
            </div>
            <div class="flex items-center space-x-2">
              <button
                type="button"
                class="text-white hover:text-gray-300"
                title="Video Settings"
              >
                <Settings class="w-4 h-4" />
              </button>
              <button
                type="button"
                class="text-white hover:text-gray-300"
                title="Fullscreen"
              >
                <Eye class="w-4 h-4" />
              </button>
            </div>
          </div>
          
          <!-- Progress Bar -->
          <div class="mt-3">
            <div class="w-full bg-gray-700 rounded-full h-1">
              <div class="bg-primary-500 h-1 rounded-full" style="width: 0%"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Video Info -->
      <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
        <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-3">Video Information</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span class="text-gray-500 dark:text-gray-400">Duration:</span>
            <p class="font-medium text-gray-900 dark:text-white">
              {Math.floor(projectData.video.duration / 60)}:{(projectData.video.duration % 60).toString().padStart(2, '0')}
            </p>
          </div>
          <div>
            <span class="text-gray-500 dark:text-gray-400">Resolution:</span>
            <p class="font-medium text-gray-900 dark:text-white">{projectData.video.resolution}</p>
          </div>
          <div>
            <span class="text-gray-500 dark:text-gray-400">Size:</span>
            <p class="font-medium text-gray-900 dark:text-white">{projectData.video.fileSize}</p>
          </div>
          <div>
            <span class="text-gray-500 dark:text-gray-400">Format:</span>
            <p class="font-medium text-gray-900 dark:text-white">{projectData.video.format}</p>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex flex-wrap gap-3">
        <button
          type="button"
          class="btn-primary flex items-center"
          on:click={handleSave}
        >
          <Save class="w-4 h-4 mr-2" />
          Save Project
        </button>
        
        <button
          type="button"
          class="btn-secondary flex items-center"
          on:click={handleDownload}
        >
          <Download class="w-4 h-4 mr-2" />
          Download Video
        </button>
        
        <button
          type="button"
          class="btn-secondary flex items-center"
          on:click={handleShare}
        >
          <Share2 class="w-4 h-4 mr-2" />
          Share & Publish
        </button>
        
        <button
          type="button"
          class="btn-outline flex items-center"
          on:click={handleGenerate}
        >
          <RefreshCw class="w-4 h-4 mr-2" />
          Regenerate
        </button>
      </div>
    {:else if !isGenerating}
      <!-- Ready to Assemble -->
      <div class="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8">
        <div class="text-center">
          <Video class="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
            Ready to create your video
          </h3>
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
            All elements are prepared. Click below to assemble your final video.
          </p>
          
          <!-- Assembly Summary -->
          <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-4 text-left">
            <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
              Assembly Summary
            </h4>
            <div class="space-y-1 text-xs text-gray-600 dark:text-gray-400">
              <div class="flex items-center justify-between">
                <span>Script:</span>
                <span class="font-medium">{projectData.script ? 'Ready' : 'Missing'}</span>
              </div>
              <div class="flex items-center justify-between">
                <span>Images:</span>
                <span class="font-medium">{projectData.images?.length || 0} generated</span>
              </div>
              <div class="flex items-center justify-between">
                <span>Audio:</span>
                <span class="font-medium">{projectData.audio ? 'Ready' : 'Missing'}</span>
              </div>
              <div class="flex items-center justify-between">
                <span>Estimated duration:</span>
                <span class="font-medium">
                  {Math.floor((projectData.audio?.duration || 0) / 60)}:{((projectData.audio?.duration || 0) % 60).toString().padStart(2, '0')}
                </span>
              </div>
            </div>
          </div>
          
          <button
            type="button"
            class="btn-primary flex items-center mx-auto"
            on:click={handleGenerate}
            disabled={!projectData.script || !projectData.images?.length || !projectData.audio}
          >
            <Video class="w-4 h-4 mr-2" />
            Assemble Video
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
    
    {#if projectData.video}
      <div class="text-sm text-green-600 dark:text-green-400 flex items-center">
        <Video class="w-4 h-4 mr-1" />
        Video created successfully!
      </div>
    {:else}
      <div class="text-sm text-gray-500 dark:text-gray-400">
        Complete assembly to finish
      </div>
    {/if}
  </div>
</div>