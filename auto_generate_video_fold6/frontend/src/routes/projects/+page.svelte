<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { toastStore } from '$lib/stores/toast';
  import { Plus, Grid, List } from 'lucide-svelte';

  // Import project components
  import ProjectFilters from '$lib/components/projects/ProjectFilters.svelte';
  import ProjectGrid from '$lib/components/projects/ProjectGrid.svelte';
  import ProjectsList from '$lib/components/projects/ProjectsList.svelte';
  import BulkActions from '$lib/components/projects/BulkActions.svelte';

  let isLoading = true;
  let projects = [];
  let filteredProjects = [];
  let searchQuery = '';
  let selectedFilter = 'all';
  let viewMode = 'grid'; // 'grid' or 'list'
  let selectedProjects = new Set();

  const filters = [
    { value: 'all', label: 'All Projects', count: 0 },
    { value: 'published', label: 'Published', count: 0 },
    { value: 'draft', label: 'Draft', count: 0 },
    { value: 'processing', label: 'Processing', count: 0 },
    { value: 'scheduled', label: 'Scheduled', count: 0 },
  ];

  onMount(async () => {
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
          title: "Remote Work Productivity Hacks",
          description: "Transform your home office setup and boost your productivity by 300%.",
          thumbnail: "/api/placeholder/320/180",
          status: "draft",
          views: 0,
          engagement: 0,
          duration: 72,
          platforms: ["youtube", "linkedin"],
          createdAt: "2024-01-12T14:45:00Z",
          updatedAt: "2024-01-12T14:45:00Z",
          scheduledFor: null,
          tags: ["Productivity", "Remote Work", "Tips"]
        },
        {
          id: 5,
          title: "Crypto Investment Strategy 2024",
          description: "The ultimate guide to building a profitable cryptocurrency portfolio this year.",
          thumbnail: "/api/placeholder/320/180",
          status: "scheduled",
          views: 0,
          engagement: 0,
          duration: 95,
          platforms: ["youtube", "twitter"],
          createdAt: "2024-01-11T11:20:00Z",
          updatedAt: "2024-01-11T11:20:00Z",
          scheduledFor: "2024-01-20T16:00:00Z",
          tags: ["Crypto", "Investment", "Finance"]
        }
      ];

      updateFilters();
      filterProjects();
    } catch (error) {
      console.error('Error loading projects:', error);
      toastStore.error('Failed to load projects');
    } finally {
      isLoading = false;
    }
  }

  function updateFilters() {
    filters.forEach(filter => {
      if (filter.value === 'all') {
        filter.count = projects.length;
      } else {
        filter.count = projects.filter(p => p.status === filter.value).length;
      }
    });
  }

  function filterProjects() {
    let filtered = projects;

    // Filter by status
    if (selectedFilter !== 'all') {
      filtered = filtered.filter(p => p.status === selectedFilter);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(p => 
        p.title.toLowerCase().includes(query) ||
        p.description.toLowerCase().includes(query) ||
        p.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }

    filteredProjects = filtered;
  }

  function handleCreateProject() {
    goto('/create');
  }

  function handleViewProject(project) {
    toastStore.info(`Viewing project: ${project.title}`);
  }

  function handleEditProject(project) {
    toastStore.info(`Editing project: ${project.title}`);
  }

  function handleDeleteProject(project) {
    if (confirm(`Are you sure you want to delete "${project.title}"?`)) {
      projects = projects.filter(p => p.id !== project.id);
      updateFilters();
      filterProjects();
      toastStore.success('Project deleted successfully');
    }
  }

  function handleShareProject(project) {
    toastStore.success(`Sharing options for "${project.title}" opened`);
  }

  function handleSelectionChange(selection) {
    selectedProjects = selection;
  }

  function handleBulkDelete() {
    if (confirm(`Are you sure you want to delete ${selectedProjects.size} project(s)?`)) {
      projects = projects.filter(p => !selectedProjects.has(p.id));
      selectedProjects = new Set();
      updateFilters();
      filterProjects();
      toastStore.success('Projects deleted successfully');
    }
  }

  function handleBulkShare() {
    toastStore.success(`Sharing ${selectedProjects.size} project(s)`);
  }

  function handleBulkDownload() {
    toastStore.success(`Downloading ${selectedProjects.size} project(s)`);
  }

  function handleBulkDuplicate() {
    toastStore.success(`Duplicating ${selectedProjects.size} project(s)`);
  }

  function handleBulkArchive() {
    toastStore.success(`Archiving ${selectedProjects.size} project(s)`);
  }

  function handleClearSelection() {
    selectedProjects = new Set();
  }

  // Reactive filters
  $: if (searchQuery !== undefined || selectedFilter !== undefined) {
    filterProjects();
  }
</script>

<svelte:head>
  <title>Projects - AutoVideo</title>
</svelte:head>

<div class="max-w-7xl mx-auto">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Projects</h1>
      <p class="mt-2 text-gray-600 dark:text-gray-400">
        Manage and organize all your video projects
      </p>
    </div>
    <div class="mt-4 sm:mt-0 flex items-center space-x-3">
      <!-- View Mode Toggle -->
      <div class="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
        <button
          type="button"
          class="p-2 rounded-md transition-colors {
            viewMode === 'grid'
              ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }"
          on:click={() => viewMode = 'grid'}
        >
          <Grid class="w-4 h-4" />
        </button>
        <button
          type="button"
          class="p-2 rounded-md transition-colors {
            viewMode === 'list'
              ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }"
          on:click={() => viewMode = 'list'}
        >
          <List class="w-4 h-4" />
        </button>
      </div>

      <!-- Create Button -->
      <button
        type="button"
        class="btn-primary flex items-center"
        on:click={handleCreateProject}
      >
        <Plus class="w-4 h-4 mr-2" />
        New Project
      </button>
    </div>
  </div>

  <!-- Filters -->
  <ProjectFilters 
    bind:searchQuery
    bind:selectedFilter
    {filters}
  />

  {#if isLoading}
    <div class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>
  {:else if filteredProjects.length === 0}
    <div class="text-center py-12">
      <div class="w-24 h-24 mx-auto mb-4 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center">
        <Plus class="w-12 h-12 text-gray-400" />
      </div>
      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
        {searchQuery || selectedFilter !== 'all' ? 'No projects found' : 'No projects yet'}
      </h3>
      <p class="text-gray-600 dark:text-gray-400 mb-6">
        {searchQuery || selectedFilter !== 'all' 
          ? 'Try adjusting your search or filter criteria'
          : 'Create your first video project to get started'
        }
      </p>
      {#if !searchQuery && selectedFilter === 'all'}
        <button
          type="button"
          class="btn-primary flex items-center mx-auto"
          on:click={handleCreateProject}
        >
          <Plus class="w-4 h-4 mr-2" />
          Create First Project
        </button>
      {/if}
    </div>
  {:else}
    <!-- Projects Content -->
    {#if viewMode === 'grid'}
      <ProjectGrid
        projects={filteredProjects}
        bind:selectedProjects
        on:view={(e) => handleViewProject(e.detail)}
        on:edit={(e) => handleEditProject(e.detail)}
        on:delete={(e) => handleDeleteProject(e.detail)}
        on:share={(e) => handleShareProject(e.detail)}
        on:selectionChange={(e) => handleSelectionChange(e.detail)}
      />
    {:else}
      <ProjectsList
        projects={filteredProjects}
        bind:selectedProjects
        on:view={(e) => handleViewProject(e.detail)}
        on:edit={(e) => handleEditProject(e.detail)}
        on:delete={(e) => handleDeleteProject(e.detail)}
        on:share={(e) => handleShareProject(e.detail)}
        on:selectionChange={(e) => handleSelectionChange(e.detail)}
      />
    {/if}
  {/if}

  <!-- Bulk Actions -->
  <BulkActions
    selectedCount={selectedProjects.size}
    visible={selectedProjects.size > 0}
    on:bulkDelete={handleBulkDelete}
    on:bulkShare={handleBulkShare}
    on:bulkDownload={handleBulkDownload}
    on:bulkDuplicate={handleBulkDuplicate}
    on:bulkArchive={handleBulkArchive}
    on:clearSelection={handleClearSelection}
  />
</div>