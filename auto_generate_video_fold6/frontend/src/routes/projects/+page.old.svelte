<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/stores/auth';
  import { apiClient } from '$lib/api/client';
  import { toastStore } from '$lib/stores/toast';
  import { 
    Plus, 
    Search, 
    Filter, 
    Grid, 
    List, 
    Play,
    Edit,
    Trash2,
    Share2,
    Calendar,
    Eye,
    TrendingUp,
    MoreVertical,
    Copy,
    Download
  } from 'lucide-svelte';

  let mounted = false;
  let isLoading = true;
  let projects = [];
  let filteredProjects = [];
  let searchQuery = '';
  let selectedFilter = 'all';
  let viewMode = 'grid'; // 'grid' or 'list'
  let selectedProjects = new Set();
  let showBulkActions = false;
  let dropdownOpen = {};

  const filters = [
    { value: 'all', label: 'All Projects', count: 0 },
    { value: 'published', label: 'Published', count: 0 },
    { value: 'draft', label: 'Draft', count: 0 },
    { value: 'processing', label: 'Processing', count: 0 },
    { value: 'scheduled', label: 'Scheduled', count: 0 },
  ];

  onMount(async () => {
    mounted = true;
    await loadProjects();
  });

  async function loadProjects() {
    try {
      isLoading = true;
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      projects = [
        {
          id: 1,
          title: "10 AI Tools That Will Change Everything",
          description: "Discover the most powerful AI tools that are revolutionizing productivity and creativity in 2024.",
          thumbnail: "/api/placeholder/320/180",
          status: "published",
          views: 15400,
          engagement: 9.2,
          duration: 62,
          platforms: ["youtube", "tiktok", "instagram"],
          createdAt: "2024-01-15T10:30:00Z",
          updatedAt: "2024-01-15T10:30:00Z",
          scheduledFor: null,
          tags: ["AI", "Technology", "Productivity"]
        },
        {
          id: 2,
          title: "Secret TikTok Algorithm Hack",
          description: "Learn the insider secrets to make your TikTok videos go viral every time.",
          thumbnail: "/api/placeholder/320/180",
          status: "published",
          views: 8900,
          engagement: 12.1,
          duration: 45,
          platforms: ["tiktok", "instagram"],
          createdAt: "2024-01-14T15:20:00Z",
          updatedAt: "2024-01-14T15:20:00Z",
          scheduledFor: null,
          tags: ["TikTok", "Social Media", "Growth"]
        },
        {
          id: 3,
          title: "Why Everyone Is Switching to AI",
          description: "The complete guide to understanding the AI revolution and how it affects you.",
          thumbnail: "/api/placeholder/320/180",
          status: "processing",
          views: 0,
          engagement: 0,
          duration: 58,
          platforms: ["youtube"],
          createdAt: "2024-01-13T09:15:00Z",
          updatedAt: "2024-01-13T09:15:00Z",
          scheduledFor: null,
          tags: ["AI", "Future", "Technology"]
        },
        {
          id: 4,
          title: "Morning Motivation Tips",
          description: "Start your day right with these proven motivation techniques.",
          thumbnail: "/api/placeholder/320/180",
          status: "scheduled",
          views: 0,
          engagement: 0,
          duration: 40,
          platforms: ["all"],
          createdAt: "2024-01-12T14:45:00Z",
          updatedAt: "2024-01-12T14:45:00Z",
          scheduledFor: "2024-01-16T08:00:00Z",
          tags: ["Motivation", "Lifestyle", "Self-Help"]
        },
        {
          id: 5,
          title: "Complete Guide to Remote Work",
          description: "Everything you need to know about working from home effectively.",
          thumbnail: "/api/placeholder/320/180",
          status: "draft",
          views: 0,
          engagement: 0,
          duration: 0,
          platforms: [],
          createdAt: "2024-01-11T11:30:00Z",
          updatedAt: "2024-01-11T11:30:00Z",
          scheduledFor: null,
          tags: ["Remote Work", "Productivity", "Career"]
        }
      ];
      
      updateFilterCounts();
      applyFilters();
      
    } catch (error) {
      console.error('Error loading projects:', error);
      toastStore.error('Failed to load projects');
    } finally {
      isLoading = false;
    }
  }

  function updateFilterCounts() {
    filters.forEach(filter => {
      if (filter.value === 'all') {
        filter.count = projects.length;
      } else {
        filter.count = projects.filter(p => p.status === filter.value).length;
      }
    });
  }

  function applyFilters() {
    let filtered = projects;
    
    // Apply status filter
    if (selectedFilter !== 'all') {
      filtered = filtered.filter(project => project.status === selectedFilter);
    }
    
    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(project => 
        project.title.toLowerCase().includes(query) ||
        project.description.toLowerCase().includes(query) ||
        project.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }
    
    filteredProjects = filtered;
  }

  function formatNumber(num) {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  }

  function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  }

  function getStatusColor(status) {
    switch (status) {
      case 'published': return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-300';
      case 'processing': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-300';
      case 'draft': return 'text-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-gray-300';
      case 'scheduled': return 'text-blue-600 bg-blue-100 dark:bg-blue-900 dark:text-blue-300';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-gray-300';
    }
  }

  function getPlatformIcons(platforms) {
    const icons = {
      'youtube': '📺',
      'tiktok': '🎵',
      'instagram': '📷',
      'twitter': '🐦',
      'facebook': '👥',
      'all': '🌐'
    };
    
    if (platforms.includes('all')) return [icons.all];
    return platforms.map(platform => icons[platform] || '🌐');
  }

  function toggleProjectSelection(projectId) {
    if (selectedProjects.has(projectId)) {
      selectedProjects.delete(projectId);
    } else {
      selectedProjects.add(projectId);
    }
    selectedProjects = selectedProjects;
    showBulkActions = selectedProjects.size > 0;
  }

  function selectAllProjects() {
    selectedProjects = new Set(filteredProjects.map(p => p.id));
    showBulkActions = true;
  }

  function clearSelection() {
    selectedProjects = new Set();
    showBulkActions = false;
  }

  function toggleDropdown(projectId) {
    dropdownOpen = { [projectId]: !dropdownOpen[projectId] };
  }

  async function deleteProject(projectId) {
    if (confirm('Are you sure you want to delete this project?')) {
      try {
        projects = projects.filter(p => p.id !== projectId);
        selectedProjects.delete(projectId);
        selectedProjects = selectedProjects;
        updateFilterCounts();
        applyFilters();
        toastStore.success('Project deleted successfully');
      } catch (error) {
        toastStore.error('Failed to delete project');
      }
    }
  }

  async function duplicateProject(projectId) {
    try {
      const original = projects.find(p => p.id === projectId);
      const duplicate = {
        ...original,
        id: Math.max(...projects.map(p => p.id)) + 1,
        title: original.title + ' (Copy)',
        status: 'draft',
        views: 0,
        engagement: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
      
      projects = [duplicate, ...projects];
      updateFilterCounts();
      applyFilters();
      toastStore.success('Project duplicated successfully');
    } catch (error) {
      toastStore.error('Failed to duplicate project');
    }
  }

  // Reactive statements
  $: applyFilters();
</script>

<svelte:head>
  <title>Projects - AutoVideo</title>
</svelte:head>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Projects</h1>
      <p class="mt-2 text-gray-600 dark:text-gray-400">
        Manage your video projects and track their performance
      </p>
    </div>
    <div class="mt-4 sm:mt-0">
      <a href="/create" class="btn-primary inline-flex items-center">
        <Plus class="w-4 h-4 mr-2" />
        New Project
      </a>
    </div>
  </div>

  <!-- Filters and Search -->
  <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
    <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
      <!-- Search -->
      <div class="flex-1 max-w-lg">
        <div class="relative">
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search class="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            bind:value={searchQuery}
            placeholder="Search projects..."
            class="form-input pl-10"
          />
        </div>
      </div>

      <!-- Filters and View Toggle -->
      <div class="flex items-center space-x-4">
        <!-- Status Filter -->
        <div class="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          {#each filters as filter}
            <button
              type="button"
              class="px-3 py-1.5 text-sm font-medium rounded-md transition-colors {selectedFilter === filter.value 
                ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm' 
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}"
              on:click={() => selectedFilter = filter.value}
            >
              {filter.label}
              {#if filter.count > 0}
                <span class="ml-1 text-xs">({filter.count})</span>
              {/if}
            </button>
          {/each}
        </div>

        <!-- View Toggle -->
        <div class="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          <button
            type="button"
            class="p-2 rounded-md transition-colors {viewMode === 'grid' 
              ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm' 
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}"
            on:click={() => viewMode = 'grid'}
          >
            <Grid class="w-4 h-4" />
          </button>
          <button
            type="button"
            class="p-2 rounded-md transition-colors {viewMode === 'list' 
              ? 'bg-white dark:bg-gray-600 text-gray-900 dark:text-white shadow-sm' 
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}"
            on:click={() => viewMode = 'list'}
          >
            <List class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Bulk Actions -->
  {#if showBulkActions}
    <div class="bg-primary-50 dark:bg-primary-900/20 rounded-lg p-4 border border-primary-200 dark:border-primary-800">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <span class="text-sm font-medium text-primary-800 dark:text-primary-200">
            {selectedProjects.size} project{selectedProjects.size > 1 ? 's' : ''} selected
          </span>
          <button
            type="button"
            class="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
            on:click={selectAllProjects}
          >
            Select all
          </button>
          <button
            type="button"
            class="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
            on:click={clearSelection}
          >
            Clear selection
          </button>
        </div>
        <div class="flex items-center space-x-2">
          <button class="btn-secondary">
            <Share2 class="w-4 h-4 mr-2" />
            Publish
          </button>
          <button class="btn-secondary">
            <Trash2 class="w-4 h-4 mr-2" />
            Delete
          </button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Projects Grid/List -->
  {#if isLoading}
    <div class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>
  {:else if filteredProjects.length === 0}
    <div class="text-center py-12">
      <div class="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mx-auto mb-4">
        <Play class="w-8 h-8 text-gray-400" />
      </div>
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
        {searchQuery ? 'No projects found' : 'No projects yet'}
      </h3>
      <p class="text-gray-600 dark:text-gray-400 mb-6">
        {searchQuery 
          ? `No projects match "${searchQuery}". Try a different search term.`
          : 'Get started by creating your first AI-powered video project.'
        }
      </p>
      {#if !searchQuery}
        <a href="/create" class="btn-primary inline-flex items-center">
          <Plus class="w-4 h-4 mr-2" />
          Create Your First Project
        </a>
      {/if}
    </div>
  {:else if viewMode === 'grid'}
    <!-- Grid View -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {#each filteredProjects as project}
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-md transition-shadow">
          <!-- Thumbnail -->
          <div class="relative aspect-video bg-gray-100 dark:bg-gray-700">
            <div class="absolute inset-0 flex items-center justify-center">
              <Play class="w-12 h-12 text-gray-400" />
            </div>
            
            <!-- Selection checkbox -->
            <div class="absolute top-2 left-2">
              <input
                type="checkbox"
                checked={selectedProjects.has(project.id)}
                on:change={() => toggleProjectSelection(project.id)}
                class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </div>
            
            <!-- Status badge -->
            <div class="absolute top-2 right-2">
              <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium {getStatusColor(project.status)}">
                {project.status}
              </span>
            </div>
            
            <!-- Duration -->
            {#if project.duration > 0}
              <div class="absolute bottom-2 right-2 bg-black/70 text-white px-2 py-1 rounded text-xs">
                {formatDuration(project.duration)}
              </div>
            {/if}
          </div>
          
          <!-- Content -->
          <div class="p-4">
            <div class="flex items-start justify-between mb-2">
              <h3 class="text-sm font-medium text-gray-900 dark:text-white line-clamp-2 flex-1">
                {project.title}
              </h3>
              <div class="relative ml-2">
                <button
                  type="button"
                  class="p-1 rounded-md text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  on:click={() => toggleDropdown(project.id)}
                >
                  <MoreVertical class="w-4 h-4" />
                </button>
                
                {#if dropdownOpen[project.id]}
                  <div class="absolute right-0 mt-1 w-48 bg-white dark:bg-gray-700 rounded-lg shadow-lg border border-gray-200 dark:border-gray-600 z-10">
                    <div class="py-1">
                      <a href="/projects/{project.id}/edit" class="flex items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600">
                        <Edit class="w-4 h-4 mr-2" />
                        Edit
                      </a>
                      <button
                        type="button"
                        class="flex items-center w-full px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600"
                        on:click={() => duplicateProject(project.id)}
                      >
                        <Copy class="w-4 h-4 mr-2" />
                        Duplicate
                      </button>
                      <button
                        type="button"
                        class="flex items-center w-full px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600"
                      >
                        <Download class="w-4 h-4 mr-2" />
                        Download
                      </button>
                      <div class="border-t border-gray-200 dark:border-gray-600 my-1"></div>
                      <button
                        type="button"
                        class="flex items-center w-full px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-gray-100 dark:hover:bg-gray-600"
                        on:click={() => deleteProject(project.id)}
                      >
                        <Trash2 class="w-4 h-4 mr-2" />
                        Delete
                      </button>
                    </div>
                  </div>
                {/if}
              </div>
            </div>
            
            <p class="text-xs text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
              {project.description}
            </p>
            
            <!-- Stats -->
            {#if project.status === 'published'}
              <div class="flex items-center space-x-4 mb-3 text-xs text-gray-500 dark:text-gray-400">
                <div class="flex items-center">
                  <Eye class="w-3 h-3 mr-1" />
                  {formatNumber(project.views)}
                </div>
                <div class="flex items-center">
                  <TrendingUp class="w-3 h-3 mr-1" />
                  {project.engagement}%
                </div>
              </div>
            {/if}
            
            <!-- Platforms and Date -->
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-1">
                {#each getPlatformIcons(project.platforms) as icon}
                  <span class="text-sm">{icon}</span>
                {/each}
              </div>
              <span class="text-xs text-gray-500 dark:text-gray-400">
                {formatDate(project.createdAt)}
              </span>
            </div>
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <!-- List View -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead class="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                <input
                  type="checkbox"
                  checked={selectedProjects.size === filteredProjects.length && filteredProjects.length > 0}
                  on:change={(e) => e.target.checked ? selectAllProjects() : clearSelection()}
                  class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Project
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Views
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Engagement
              </th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Created
              </th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {#each filteredProjects as project}
              <tr class="hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="px-6 py-4 whitespace-nowrap">
                  <input
                    type="checkbox"
                    checked={selectedProjects.has(project.id)}
                    on:change={() => toggleProjectSelection(project.id)}
                    class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                </td>
                <td class="px-6 py-4">
                  <div class="flex items-center">
                    <div class="flex-shrink-0 h-10 w-16">
                      <div class="h-10 w-16 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center">
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
                <td class="px-6 py-4 whitespace-nowrap">
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {getStatusColor(project.status)}">
                    {project.status}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                  {formatNumber(project.views)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                  {project.engagement}%
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {formatDate(project.createdAt)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div class="flex items-center justify-end space-x-2">
                    <a href="/projects/{project.id}/edit" class="text-primary-600 hover:text-primary-900 dark:text-primary-400">
                      <Edit class="w-4 h-4" />
                    </a>
                    <button
                      type="button"
                      class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                      on:click={() => duplicateProject(project.id)}
                    >
                      <Copy class="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      class="text-red-400 hover:text-red-600"
                      on:click={() => deleteProject(project.id)}
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
    </div>
  {/if}
</div>

<style>
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>