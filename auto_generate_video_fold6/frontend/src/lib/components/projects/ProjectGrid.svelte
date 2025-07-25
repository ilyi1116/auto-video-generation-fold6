<script>
  import { createEventDispatcher } from 'svelte';
  import { Play, Edit, Trash2, Share2, Eye, TrendingUp, MoreVertical, Calendar } from 'lucide-svelte';

  export let projects = [];
  export let selectedProjects = new Set();

  const dispatch = createEventDispatcher();

  function formatNumber(num) {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  }

  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  }

  function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  function getStatusColor(status) {
    switch (status) {
      case 'published': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'draft': return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
      case 'processing': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'scheduled': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200';
    }
  }

  function getPlatformIcon(platform) {
    switch (platform) {
      case 'youtube': return '📺';
      case 'tiktok': return '🎵';
      case 'instagram': return '📷';
      case 'twitter': return '🐦';
      case 'linkedin': return '💼';
      default: return '📱';
    }
  }

  function handleProjectClick(project) {
    dispatch('view', project);
  }

  function handleEdit(project) {
    dispatch('edit', project);
  }

  function handleDelete(project) {
    dispatch('delete', project);
  }

  function handleShare(project) {
    dispatch('share', project);
  }

  function handleSelectProject(project, event) {
    event.stopPropagation();
    const newSelected = new Set(selectedProjects);
    
    if (newSelected.has(project.id)) {
      newSelected.delete(project.id);
    } else {
      newSelected.add(project.id);
    }
    
    selectedProjects = newSelected;
    dispatch('selectionChange', selectedProjects);
  }
</script>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {#each projects as project}
    <div 
      class="card group cursor-pointer transition-all hover:shadow-lg {
        selectedProjects.has(project.id) ? 'ring-2 ring-primary-500' : ''
      }"
      on:click={() => handleProjectClick(project)}
    >
      <!-- Thumbnail & Status -->
      <div class="relative">
        <div class="aspect-video bg-gray-200 dark:bg-gray-700 rounded-t-lg overflow-hidden">
          <div class="w-full h-full flex items-center justify-center">
            <Play class="w-12 h-12 text-gray-400" />
          </div>
        </div>
        
        <!-- Status Badge -->
        <div class="absolute top-2 left-2">
          <span class="px-2 py-1 text-xs font-medium rounded-full {getStatusColor(project.status)}">
            {project.status}
          </span>
        </div>

        <!-- Duration -->
        <div class="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
          {formatDuration(project.duration)}
        </div>

        <!-- Selection Checkbox -->
        <div class="absolute top-2 right-2">
          <input
            type="checkbox"
            checked={selectedProjects.has(project.id)}
            on:change={(e) => handleSelectProject(project, e)}
            class="w-4 h-4 text-primary-600 bg-white border-gray-300 rounded focus:ring-primary-500"
          />
        </div>
      </div>

      <div class="card-body">
        <!-- Title & Description -->
        <div class="mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
            {project.title}
          </h3>
          <p class="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
            {project.description}
          </p>
        </div>

        <!-- Stats -->
        {#if project.status === 'published'}
          <div class="flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400 mb-4">
            <div class="flex items-center">
              <Eye class="w-4 h-4 mr-1" />
              {formatNumber(project.views)}
            </div>
            <div class="flex items-center">
              <TrendingUp class="w-4 h-4 mr-1" />
              {project.engagement}%
            </div>
          </div>
        {:else if project.status === 'scheduled'}
          <div class="flex items-center text-sm text-gray-500 dark:text-gray-400 mb-4">
            <Calendar class="w-4 h-4 mr-1" />
            Scheduled for {formatDate(project.scheduledFor)}
          </div>
        {/if}

        <!-- Platforms -->
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-1">
            {#each project.platforms as platform}
              <span class="text-lg" title={platform}>
                {getPlatformIcon(platform)}
              </span>
            {/each}
          </div>

          <!-- Actions -->
          <div class="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              type="button"
              class="p-1 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
              on:click|stopPropagation={() => handleEdit(project)}
              title="Edit"
            >
              <Edit class="w-4 h-4" />
            </button>
            <button
              type="button"
              class="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
              on:click|stopPropagation={() => handleShare(project)}
              title="Share"
            >
              <Share2 class="w-4 h-4" />
            </button>
            <button
              type="button"
              class="p-1 text-gray-400 hover:text-red-600 dark:hover:text-red-400"
              on:click|stopPropagation={() => handleDelete(project)}
              title="Delete"
            >
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Tags -->
        {#if project.tags && project.tags.length > 0}
          <div class="mt-3 flex flex-wrap gap-1">
            {#each project.tags.slice(0, 3) as tag}
              <span class="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                {tag}
              </span>
            {/each}
            {#if project.tags.length > 3}
              <span class="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                +{project.tags.length - 3}
              </span>
            {/if}
          </div>
        {/if}

        <!-- Date -->
        <div class="mt-3 text-xs text-gray-500 dark:text-gray-400">
          Updated {formatDate(project.updatedAt)}
        </div>
      </div>
    </div>
  {/each}
</div>