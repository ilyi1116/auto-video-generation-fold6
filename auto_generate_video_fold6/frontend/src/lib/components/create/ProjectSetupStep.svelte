<script>
  import { createEventDispatcher } from 'svelte';

  export let projectData = {};

  const dispatch = createEventDispatcher();

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

  function handleNext() {
    if (!projectData.title.trim()) {
      dispatch('error', 'Please enter a project title');
      return;
    }
    dispatch('next');
  }
</script>

<div class="card">
  <div class="card-header">
    <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Project Setup</h2>
    <p class="text-gray-600 dark:text-gray-400">Configure the basic settings for your video project</p>
  </div>
  
  <div class="card-body space-y-6">
    <!-- Project Title -->
    <div>
      <label for="title" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Project Title *
      </label>
      <input
        id="title"
        type="text"
        bind:value={projectData.title}
        placeholder="Enter your video title..."
        class="form-input w-full"
        required
      />
    </div>

    <!-- Project Description -->
    <div>
      <label for="description" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Description
      </label>
      <textarea
        id="description"
        bind:value={projectData.description}
        placeholder="Describe what your video will be about..."
        rows="3"
        class="form-input w-full"
      ></textarea>
    </div>

    <!-- Video Style -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
        Video Style
      </label>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {#each videoStyles as style}
          <button
            type="button"
            class="p-4 text-left border rounded-lg transition-colors {
              projectData.style === style.value
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }"
            on:click={() => projectData.style = style.value}
          >
            <div class="flex items-center space-x-3">
              <span class="text-2xl">{style.icon}</span>
              <div>
                <h3 class="text-sm font-medium text-gray-900 dark:text-white">{style.label}</h3>
                <p class="text-xs text-gray-500 dark:text-gray-400">{style.description}</p>
              </div>
            </div>
          </button>
        {/each}
      </div>
    </div>

    <!-- Target Platform -->
    <div>
      <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
        Target Platform
      </label>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {#each platforms as platform}
          <button
            type="button"
            class="p-4 text-left border rounded-lg transition-colors {
              projectData.platform === platform.value
                ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
            }"
            on:click={() => projectData.platform = platform.value}
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-3">
                <span class="text-xl">{platform.icon}</span>
                <span class="text-sm font-medium text-gray-900 dark:text-white">{platform.label}</span>
              </div>
              <span class="text-xs text-gray-500 dark:text-gray-400">{platform.recommended}</span>
            </div>
          </button>
        {/each}
      </div>
    </div>

    <!-- Duration -->
    <div>
      <label for="duration" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Target Duration (seconds)
      </label>
      <div class="flex items-center space-x-4">
        <input
          id="duration"
          type="range"
          bind:value={projectData.duration}
          min="15"
          max="600"
          step="15"
          class="flex-1"
        />
        <span class="text-sm font-medium text-gray-900 dark:text-white w-16">
          {Math.floor(projectData.duration / 60)}:{(projectData.duration % 60).toString().padStart(2, '0')}
        </span>
      </div>
      <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
        <span>15s</span>
        <span>10m</span>
      </div>
    </div>
  </div>

  <div class="card-footer">
    <button
      type="button"
      class="btn-primary"
      on:click={handleNext}
    >
      Continue to Script Generation
    </button>
  </div>
</div>