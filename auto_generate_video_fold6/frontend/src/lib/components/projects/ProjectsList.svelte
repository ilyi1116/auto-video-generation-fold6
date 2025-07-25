<script>
  import { createEventDispatcher } from 'svelte';
  import { Play, Edit, Trash2, Share2, Eye, TrendingUp, Calendar } from 'lucide-svelte';

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
      day: 'numeric',
      year: 'numeric'
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

<div class="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
  <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
    <thead class="bg-gray-50 dark:bg-gray-700">
      <tr>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          <input
            type="checkbox"
            indeterminate={selectedProjects.size > 0 && selectedProjects.size < projects.length}
            checked={selectedProjects.size === projects.length && projects.length > 0}
            on:change={(e) => {
              if (e.target.checked) {
                selectedProjects = new Set(projects.map(p => p.id));
              } else {
                selectedProjects = new Set();
              }
              dispatch('selectionChange', selectedProjects);
            }}
            class="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
          />
        </th>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          Project
        </th>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          Status
        </th>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          Performance
        </th>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          Platforms
        </th>
        <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
          Updated
        </th>
        <th scope="col" class="relative px-6 py-3">
          <span class="sr-only">Actions</span>
        </th>
      </tr>
    </thead>
    <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
      {#each projects as project}
        <tr 
          class="hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer {
            selectedProjects.has(project.id) ? 'bg-primary-50 dark:bg-primary-900/20' : ''
          }"
          on:click={() => handleProjectClick(project)}
        >
          <!-- Selection -->
          <td class="px-6 py-4 whitespace-nowrap">
            <input
              type="checkbox"
              checked={selectedProjects.has(project.id)}
              on:change={(e) => handleSelectProject(project, e)}
              class="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500"
            />
          </td>

          <!-- Project Info -->
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="flex items-center">
              <div class="flex-shrink-0 h-12 w-16">
                <div class="h-12 w-16 bg-gray-200 dark:bg-gray-600 rounded flex items-center justify-center">
                  <Play class="w-4 h-4 text-gray-400" />
                </div>
              </div>
              <div class="ml-4">
                <div class="text-sm font-medium text-gray-900 dark:text-white">
                  {project.title}
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400 max-w-xs truncate">
                  {project.description}
                </div>
              </div>
            </div>
          </td>

          <!-- Status -->
          <td class="px-6 py-4 whitespace-nowrap">
            <span class="px-2 py-1 text-xs font-medium rounded-full {getStatusColor(project.status)}">
              {project.status}
            </span>
            <div class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {formatDuration(project.duration)}
            </div>
          </td>

          <!-- Performance -->
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
            {#if project.status === 'published'}
              <div class="flex items-center space-x-2">
                <div class="flex items-center">
                  <Eye class="w-4 h-4 mr-1 text-gray-400" />
                  {formatNumber(project.views)}
                </div>
                <div class="flex items-center">
                  <TrendingUp class="w-4 h-4 mr-1 text-gray-400" />
                  {project.engagement}%
                </div>
              </div>
            {:else if project.status === 'scheduled'}
              <div class="flex items-center text-yellow-600 dark:text-yellow-400">
                <Calendar class="w-4 h-4 mr-1" />
                {formatDate(project.scheduledFor)}
              </div>
            {:else}
              <span class="text-gray-400">-</span>
            {/if}
          </td>

          <!-- Platforms -->
          <td class="px-6 py-4 whitespace-nowrap">
            <div class="flex items-center space-x-1">
              {#each project.platforms as platform}
                <span class="text-lg" title={platform}>
                  {getPlatformIcon(platform)}
                </span>
              {/each}
            </div>
          </td>

          <!-- Updated -->
          <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
            {formatDate(project.updatedAt)}
          </td>

          <!-- Actions -->
          <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
            <div class="flex items-center space-x-2">
              <button
                type="button"
                class="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300"
                on:click|stopPropagation={() => handleEdit(project)}
              >
                <Edit class="w-4 h-4" />
              </button>
              <button
                type="button"
                class="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                on:click|stopPropagation={() => handleShare(project)}
              >
                <Share2 class="w-4 h-4" />
              </button>
              <button
                type="button"
                class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                on:click|stopPropagation={() => handleDelete(project)}
              >
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>