<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Navigation from '$lib/components/layout/Navigation.svelte';
  import { Play, Eye, Heart, Clock, Calendar, Search, Filter, Grid, List } from 'lucide-svelte';
  
  let videos = [];
  let filteredVideos = [];
  let searchTerm = '';
  let selectedFilter = 'all';
  let viewMode = 'grid'; // 'grid' or 'list'
  let sortBy = 'newest';
  
  // 模擬影片資料
  const mockVideos = [
    {
      id: '1',
      title: 'AI 影片生成完整教學',
      description: '從腳本生成到最終影片輸出的完整流程',
      thumbnail: 'https://via.placeholder.com/640x360/6366f1/ffffff?text=AI+Tutorial',
      duration: 180,
      views: 15420,
      likes: 892,
      createdAt: '2024-01-15T10:30:00Z',
      status: 'published',
      platforms: ['youtube', 'tiktok'],
      tags: ['教學', 'AI', '影片製作']
    },
    {
      id: '2',
      title: '語音合成技術深度解析',
      description: '探索最新的 AI 語音合成技術和應用',
      thumbnail: 'https://via.placeholder.com/640x360/8b5cf6/ffffff?text=Voice+AI',
      duration: 240,
      views: 8930,
      likes: 456,
      createdAt: '2024-01-12T14:20:00Z',
      status: 'published',
      platforms: ['youtube', 'instagram'],
      tags: ['語音', 'AI', '技術']
    },
    {
      id: '3',
      title: '圖像生成的藝術與科學',
      description: '了解 AI 如何創造令人驚艷的視覺內容',
      thumbnail: 'https://via.placeholder.com/640x360/10b981/ffffff?text=Image+AI',
      duration: 200,
      views: 12350,
      likes: 678,
      createdAt: '2024-01-10T09:15:00Z',
      status: 'published',
      platforms: ['youtube', 'twitter'],
      tags: ['圖像', 'AI', '藝術']
    },
    {
      id: '4',
      title: '自動化內容創作流程',
      description: '建立高效的 AI 驅動內容生產管道',
      thumbnail: 'https://via.placeholder.com/640x360/f59e0b/ffffff?text=Automation',
      duration: 300,
      views: 19800,
      likes: 1234,
      createdAt: '2024-01-08T16:45:00Z',
      status: 'published',
      platforms: ['youtube', 'linkedin'],
      tags: ['自動化', '內容創作', '效率']
    },
    {
      id: '5',
      title: 'TikTok 短影片製作秘訣',
      description: '掌握短影片平台的製作技巧和策略',
      thumbnail: 'https://via.placeholder.com/640x360/ef4444/ffffff?text=TikTok+Tips',
      duration: 120,
      views: 25600,
      likes: 1890,
      createdAt: '2024-01-05T11:30:00Z',
      status: 'published',
      platforms: ['tiktok', 'instagram'],
      tags: ['TikTok', '短影片', '社群媒體']
    },
    {
      id: '6',
      title: '影片 SEO 優化指南',
      description: '提高影片在搜尋引擎中的可見度',
      thumbnail: 'https://via.placeholder.com/640x360/06b6d4/ffffff?text=SEO+Guide',
      duration: 160,
      views: 7420,
      likes: 398,
      createdAt: '2024-01-03T13:20:00Z',
      status: 'published',
      platforms: ['youtube'],
      tags: ['SEO', '優化', '搜尋']
    }
  ];
  
  onMount(() => {
    videos = mockVideos;
    filteredVideos = videos;
  });
  
  // 搜尋和篩選
  $: {
    let filtered = videos;
    
    // 搜尋
    if (searchTerm.trim()) {
      filtered = filtered.filter(video =>
        video.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        video.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        video.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }
    
    // 篩選
    if (selectedFilter !== 'all') {
      filtered = filtered.filter(video => {
        switch (selectedFilter) {
          case 'published':
            return video.status === 'published';
          case 'high-views':
            return video.views > 15000;
          case 'recent':
            return new Date(video.createdAt) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
          default:
            return true;
        }
      });
    }
    
    // 排序
    filtered = filtered.sort((a, b) => {
      switch (sortBy) {
        case 'newest':
          return new Date(b.createdAt) - new Date(a.createdAt);
        case 'oldest':
          return new Date(a.createdAt) - new Date(b.createdAt);
        case 'most-viewed':
          return b.views - a.views;
        case 'most-liked':
          return b.likes - a.likes;
        default:
          return 0;
      }
    });
    
    filteredVideos = filtered;
  }
  
  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }
  
  function formatDuration(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }
  
  function getPlatformIcon(platform) {
    const icons = {
      'youtube': '📺',
      'tiktok': '📱',
      'instagram': '📸',
      'twitter': '🐦',
      'linkedin': '💼'
    };
    return icons[platform] || '📹';
  }
  
  function handleVideoClick(videoId) {
    goto(`/video/${videoId}`);
  }
</script>

<svelte:head>
  <title>影片庫 - AI Video Creator</title>
  <meta name="description" content="瀏覽所有 AI 生成的影片內容" />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <!-- Navigation -->
  <Navigation />
  
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Page Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        影片庫
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        探索所有 AI 生成的影片內容，共 {videos.length} 個影片
      </p>
    </div>
    
    <!-- Search and Filters -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6 mb-8">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <!-- Search -->
        <div class="relative flex-1 max-w-md">
          <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            bind:value={searchTerm}
            placeholder="搜尋影片..."
            class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                   focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          />
        </div>
        
        <!-- Filters and Controls -->
        <div class="flex items-center space-x-4">
          <!-- Filter -->
          <select
            bind:value={selectedFilter}
            class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                   focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="all">所有影片</option>
            <option value="published">已發布</option>
            <option value="high-views">高觀看數</option>
            <option value="recent">最近一週</option>
          </select>
          
          <!-- Sort -->
          <select
            bind:value={sortBy}
            class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg
                   focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
          >
            <option value="newest">最新</option>
            <option value="oldest">最舊</option>
            <option value="most-viewed">最多觀看</option>
            <option value="most-liked">最多讚數</option>
          </select>
          
          <!-- View Mode -->
          <div class="flex rounded-lg border border-gray-300 dark:border-gray-600">
            <button
              type="button"
              on:click={() => viewMode = 'grid'}
              class="px-3 py-2 text-sm rounded-l-lg transition-colors
                     {viewMode === 'grid' 
                       ? 'bg-blue-600 text-white' 
                       : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}"
            >
              <Grid class="w-4 h-4" />
            </button>
            <button
              type="button"
              on:click={() => viewMode = 'list'}
              class="px-3 py-2 text-sm rounded-r-lg border-l border-gray-300 dark:border-gray-600 transition-colors
                     {viewMode === 'list' 
                       ? 'bg-blue-600 text-white' 
                       : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'}"
            >
              <List class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
      
      <!-- Results Count -->
      {#if searchTerm || selectedFilter !== 'all'}
        <div class="mt-4 text-sm text-gray-600 dark:text-gray-400">
          顯示 {filteredVideos.length} 個符合條件的影片
        </div>
      {/if}
    </div>
    
    <!-- Videos Grid/List -->
    {#if filteredVideos.length > 0}
      {#if viewMode === 'grid'}
        <!-- Grid View -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {#each filteredVideos as video (video.id)}
            <div
              class="group bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 
                     hover:shadow-lg hover:border-gray-300 dark:hover:border-gray-600 transition-all duration-200 cursor-pointer"
              on:click={() => handleVideoClick(video.id)}
              role="button"
              tabindex="0"
              on:keydown={(e) => e.key === 'Enter' && handleVideoClick(video.id)}
            >
              <!-- Thumbnail -->
              <div class="aspect-video bg-gray-100 dark:bg-gray-700 rounded-t-lg overflow-hidden relative">
                <img
                  src={video.thumbnail}
                  alt={video.title}
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                  loading="lazy"
                />
                
                <!-- Play Overlay -->
                <div class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-all">
                  <Play class="w-16 h-16 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
                
                <!-- Duration Badge -->
                <div class="absolute bottom-2 right-2">
                  <span class="inline-flex items-center px-2 py-1 rounded bg-black bg-opacity-75 text-white text-xs font-medium">
                    {formatDuration(video.duration)}
                  </span>
                </div>
              </div>
              
              <!-- Content -->
              <div class="p-4">
                <!-- Title -->
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2 line-clamp-2">
                  {video.title}
                </h3>
                
                <!-- Description -->
                <p class="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                  {video.description}
                </p>
                
                <!-- Stats -->
                <div class="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-3">
                  <div class="flex items-center space-x-4">
                    <span class="flex items-center">
                      <Eye class="w-4 h-4 mr-1" />
                      {video.views.toLocaleString()}
                    </span>
                    <span class="flex items-center">
                      <Heart class="w-4 h-4 mr-1" />
                      {video.likes.toLocaleString()}
                    </span>
                  </div>
                  <span class="flex items-center">
                    <Calendar class="w-4 h-4 mr-1" />
                    {formatDate(video.createdAt)}
                  </span>
                </div>
                
                <!-- Platforms -->
                <div class="flex items-center space-x-1">
                  {#each video.platforms as platform}
                    <span class="text-sm" title={platform}>
                      {getPlatformIcon(platform)}
                    </span>
                  {/each}
                </div>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <!-- List View -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="divide-y divide-gray-200 dark:divide-gray-700">
            {#each filteredVideos as video (video.id)}
              <div
                class="p-6 hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                on:click={() => handleVideoClick(video.id)}
                role="button"
                tabindex="0"
                on:keydown={(e) => e.key === 'Enter' && handleVideoClick(video.id)}
              >
                <div class="flex items-start space-x-4">
                  <!-- Thumbnail -->
                  <div class="flex-shrink-0 w-32 h-20 bg-gray-100 dark:bg-gray-700 rounded overflow-hidden relative">
                    <img
                      src={video.thumbnail}
                      alt={video.title}
                      class="w-full h-full object-cover"
                      loading="lazy"
                    />
                    <div class="absolute bottom-1 right-1">
                      <span class="inline-flex items-center px-1 py-0.5 rounded bg-black bg-opacity-75 text-white text-xs font-medium">
                        {formatDuration(video.duration)}
                      </span>
                    </div>
                  </div>
                  
                  <!-- Content -->
                  <div class="flex-1 min-w-0">
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      {video.title}
                    </h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                      {video.description}
                    </p>
                    
                    <div class="flex items-center justify-between">
                      <!-- Stats -->
                      <div class="flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-400">
                        <span class="flex items-center">
                          <Eye class="w-4 h-4 mr-1" />
                          {video.views.toLocaleString()}
                        </span>
                        <span class="flex items-center">
                          <Heart class="w-4 h-4 mr-1" />
                          {video.likes.toLocaleString()}
                        </span>
                        <span class="flex items-center">
                          <Calendar class="w-4 h-4 mr-1" />
                          {formatDate(video.createdAt)}
                        </span>
                      </div>
                      
                      <!-- Platforms -->
                      <div class="flex items-center space-x-1">
                        {#each video.platforms as platform}
                          <span class="text-sm" title={platform}>
                            {getPlatformIcon(platform)}
                          </span>
                        {/each}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    {:else}
      <!-- Empty State -->
      <div class="text-center py-12">
        <Play class="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          找不到符合條件的影片
        </h3>
        <p class="text-gray-600 dark:text-gray-400 mb-6">
          嘗試調整搜尋關鍵詞或篩選條件
        </p>
        <button
          type="button"
          on:click={() => { searchTerm = ''; selectedFilter = 'all'; }}
          class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          清除篩選
        </button>
      </div>
    {/if}
  </div>
</div>

<style>
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>