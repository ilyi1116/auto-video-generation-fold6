<script>
  import { onMount } from 'svelte';
  import { authStore } from '$lib/stores/auth.js';
  import { apiClient } from '$lib/api/client.js';
  import Navigation from '$lib/components/layout/Navigation.svelte';
  import { 
    Play, 
    Plus, 
    TrendingUp, 
    BarChart3, 
    Users, 
    Clock,
    Eye,
    Heart,
    Share
  } from 'lucide-svelte';

  let stats = {
    totalVideos: 0,
    totalViews: 0,
    totalLikes: 0,
    totalShares: 0
  };

  let recentVideos = [];
  let isLoading = true;

  onMount(async () => {
    // Redirect if not authenticated
    if (!$authStore.isAuthenticated) {
      window.location.href = '/login';
      return;
    }

    try {
      // Fetch dashboard data using API client
      const [statsData, videosData] = await Promise.all([
        apiClient.analytics.getDashboard('7d').catch(() => ({ totalVideos: 0, totalViews: 0, totalLikes: 0, totalShares: 0 })),
        apiClient.videos.list({ limit: 5 }).catch(() => ({ videos: [] }))
      ]);

      stats = statsData;
      recentVideos = videosData.videos || [];
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      isLoading = false;
    }
  });

  function createNewVideo() {
    window.location.href = '/create';
  }

  function viewAllVideos() {
    window.location.href = '/projects';
  }

</script>

<svelte:head>
  <title>Dashboard - AutoVideo</title>
  <meta name="description" content="Manage your AI-generated videos and track performance" />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <!-- Navigation -->
  <Navigation />
  
  <!-- Header -->
  <header class="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center py-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            Welcome back, {$authStore.user?.name || $authStore.user?.email || 'Creator'}!
          </h1>
          <p class="text-gray-600 dark:text-gray-400">
            Ready to create your next viral video?
          </p>
        </div>
        
        <div class="flex items-center space-x-4">
          <button
            on:click={createNewVideo}
            class="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 flex items-center"
          >
            <Plus class="w-5 h-5 mr-2" />
            Create New Video
          </button>
        </div>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    {#if isLoading}
      <!-- Loading State -->
      <div class="flex items-center justify-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    {:else}
      <!-- Stats Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center">
            <div class="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Play class="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Videos</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">{stats.totalVideos || 0}</p>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center">
            <div class="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <Eye class="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Views</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">{(stats.totalViews || 0).toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center">
            <div class="p-2 bg-red-100 dark:bg-red-900 rounded-lg">
              <Heart class="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Likes</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">{(stats.totalLikes || 0).toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center">
            <div class="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <Share class="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div class="ml-4">
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Shares</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">{(stats.totalShares || 0).toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Videos -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
        <div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div class="flex justify-between items-center">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Recent Videos</h2>
            <button
              on:click={viewAllVideos}
              class="text-primary-600 hover:text-primary-500 dark:text-primary-400 text-sm font-medium"
            >
              View all
            </button>
          </div>
        </div>

        <div class="p-6">
          {#if recentVideos.length === 0}
            <div class="text-center py-12">
              <Play class="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">No videos yet</h3>
              <p class="text-gray-600 dark:text-gray-400 mb-6">Create your first AI-generated video to get started!</p>
              <button
                on:click={createNewVideo}
                class="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 flex items-center mx-auto"
              >
                <Plus class="w-5 h-5 mr-2" />
                Create Your First Video
              </button>
            </div>
          {:else}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {#each recentVideos as video}
                <div class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden hover:shadow-lg transition-shadow">
                  <div class="aspect-video bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                    {#if video.thumbnail}
                      <img src={video.thumbnail} alt={video.title} class="w-full h-full object-cover" />
                    {:else}
                      <Play class="w-12 h-12 text-gray-400" />
                    {/if}
                  </div>
                  
                  <div class="p-4">
                    <h3 class="font-medium text-gray-900 dark:text-white truncate mb-2">
                      {video.title || 'Untitled Video'}
                    </h3>
                    
                    <div class="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
                      <div class="flex items-center space-x-4">
                        <span class="flex items-center">
                          <Eye class="w-4 h-4 mr-1" />
                          {video.views || 0}
                        </span>
                        <span class="flex items-center">
                          <Heart class="w-4 h-4 mr-1" />
                          {video.likes || 0}
                        </span>
                      </div>
                      <span class="flex items-center">
                        <Clock class="w-4 h-4 mr-1" />
                        {video.duration || '0:30'}
                      </span>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center mb-4">
            <TrendingUp class="w-8 h-8 text-primary-600 dark:text-primary-400 mr-3" />
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Trending Topics</h3>
          </div>
          <p class="text-gray-600 dark:text-gray-400 mb-4">
            Discover what's trending and create content that resonates with your audience.
          </p>
          <button class="text-primary-600 hover:text-primary-500 dark:text-primary-400 font-medium">
            Explore Trends →
          </button>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center mb-4">
            <BarChart3 class="w-8 h-8 text-green-600 dark:text-green-400 mr-3" />
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Analytics</h3>
          </div>
          <p class="text-gray-600 dark:text-gray-400 mb-4">
            Track your video performance and understand your audience better.
          </p>
          <button class="text-green-600 hover:text-green-500 dark:text-green-400 font-medium">
            View Analytics →
          </button>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
          <div class="flex items-center mb-4">
            <Users class="w-8 h-8 text-purple-600 dark:text-purple-400 mr-3" />
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Community</h3>
          </div>
          <p class="text-gray-600 dark:text-gray-400 mb-4">
            Connect with other creators and share tips and best practices.
          </p>
          <button class="text-purple-600 hover:text-purple-500 dark:text-purple-400 font-medium">
            Join Community →
          </button>
        </div>
      </div>
    {/if}
  </main>
</div>