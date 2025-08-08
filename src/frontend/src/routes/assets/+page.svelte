<script>
  import { onMount } from 'svelte';
  import { toastStore } from '$lib/stores/toast.js';
  import { apiClient } from '$lib/api/client.js';
  import Navigation from '$lib/components/layout/Navigation.svelte';
  import { 
    Image as ImageIcon, 
    Music, 
    Video, 
    Download, 
    Trash2, 
    Search, 
    Filter, 
    Grid3X3, 
    List,
    Upload,
    RefreshCw,
    Eye,
    Calendar,
    User,
    Tag,
    Star,
    Copy,
    Share2,
    MoreVertical
  } from 'lucide-svelte';
  
  let activeTab = 'images';
  let viewMode = 'grid'; // grid or list
  let isLoading = false;
  let isUploading = false;
  let searchQuery = '';
  let selectedFilter = 'all'; // all, favorites, recent, unused
  let selectedAssets = new Set();
  let showPreview = null;
  
  // Asset data
  let assets = {
    images: [],
    videos: [],
    audio: [],
    music: []
  };
  
  // Upload data
  let dragOver = false;
  let fileInput = null;
  
  // Filters
  const filters = [
    { value: 'all', label: '全部素材', icon: null },
    { value: 'favorites', label: '我的最愛', icon: Star },
    { value: 'recent', label: '最近使用', icon: Calendar },
    { value: 'unused', label: '未使用', icon: Tag }
  ];
  
  // Asset categories
  const categories = [
    { id: 'images', label: '圖片', icon: ImageIcon, count: 0 },
    { id: 'videos', label: '影片', icon: Video, count: 0 },
    { id: 'audio', label: '語音', icon: Music, count: 0 },
    { id: 'music', label: '背景音樂', icon: Music, count: 0 }
  ];
  
  onMount(() => {
    loadAssets();
  });
  
  async function loadAssets() {
    isLoading = true;
    try {
      const response = await apiClient.get('/api/v1/assets', {
        params: {
          category: activeTab,
          search: searchQuery,
          filter: selectedFilter
        }
      });
      
      if (response.success) {
        assets[activeTab] = response.data.assets || [];
        updateCategoryCounts();
      } else {
        // Fallback to mock data
        assets[activeTab] = generateMockAssets(activeTab);
      }
    } catch (error) {
      console.error('Failed to load assets:', error);
      assets[activeTab] = generateMockAssets(activeTab);
    } finally {
      isLoading = false;
    }
  }
  
  function generateMockAssets(category) {
    const mockAssets = [];
    const count = Math.floor(Math.random() * 20) + 10;
    
    for (let i = 1; i <= count; i++) {
      const asset = {
        id: `${category}_${i}`,
        name: `${category === 'images' ? '圖片' : category === 'videos' ? '影片' : category === 'audio' ? '語音' : '音樂'} ${i}`,
        url: category === 'images' ? '/api/placeholder/400/300' : 
             category === 'videos' ? '/api/placeholder/video.mp4' :
             category === 'audio' ? '/api/placeholder/audio.mp3' :
             '/api/placeholder/music.mp3',
        thumbnail: category === 'images' ? '/api/placeholder/400/300' : '/api/placeholder/200/150',
        size: Math.floor(Math.random() * 5000000) + 100000,
        duration: category !== 'images' ? Math.floor(Math.random() * 300) + 10 : null,
        format: category === 'images' ? 'JPG' : 
                category === 'videos' ? 'MP4' :
                category === 'audio' ? 'MP3' :
                'MP3',
        createdAt: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
        usedCount: Math.floor(Math.random() * 10),
        isFavorite: Math.random() > 0.7,
        tags: ['AI生成', '自動創建', category === 'images' ? '風景' : category === 'videos' ? '動畫' : '語音合成'].slice(0, Math.floor(Math.random() * 3) + 1),
        metadata: {
          width: category === 'images' ? 1920 : null,
          height: category === 'images' ? 1080 : null,
          bitrate: category !== 'images' ? '128kbps' : null
        }
      };
      mockAssets.push(asset);
    }
    
    return mockAssets;
  }
  
  function updateCategoryCounts() {
    categories.forEach(cat => {
      cat.count = assets[cat.id]?.length || 0;
    });
  }
  
  function handleTabChange(tab) {
    activeTab = tab;
    selectedAssets.clear();
    selectedAssets = selectedAssets; // Trigger reactivity
    loadAssets();
  }
  
  function handleSearch() {
    loadAssets();
  }
  
  function handleFilterChange() {
    loadAssets();
  }
  
  function formatFileSize(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
  }
  
  function formatDuration(seconds) {
    if (!seconds) return '';
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }
  
  function handleAssetSelect(assetId, event) {
    if (event.ctrlKey || event.metaKey) {
      // Multi-select with Ctrl/Cmd
      if (selectedAssets.has(assetId)) {
        selectedAssets.delete(assetId);
      } else {
        selectedAssets.add(assetId);
      }
      selectedAssets = selectedAssets; // Trigger reactivity
    } else {
      // Single select
      selectedAssets.clear();
      selectedAssets.add(assetId);
      selectedAssets = selectedAssets;
    }
  }
  
  function selectAllAssets() {
    const currentAssets = assets[activeTab] || [];
    if (selectedAssets.size === currentAssets.length) {
      selectedAssets.clear();
    } else {
      selectedAssets.clear();
      currentAssets.forEach(asset => selectedAssets.add(asset.id));
    }
    selectedAssets = selectedAssets;
  }
  
  async function downloadAsset(asset) {
    try {
      const response = await apiClient.get(`/api/v1/assets/${asset.id}/download`);
      if (response.success && response.data.downloadUrl) {
        const link = document.createElement('a');
        link.href = response.data.downloadUrl;
        link.download = asset.name;
        link.click();
        toastStore.success(`${asset.name} 下載開始`);
      } else {
        toastStore.info('下載功能開發中...');
      }
    } catch (error) {
      toastStore.error('下載失敗');
    }
  }
  
  async function deleteAsset(assetId) {
    if (!confirm('確定要刪除此素材嗎？此操作無法復原。')) {
      return;
    }
    
    try {
      const response = await apiClient.delete(`/api/v1/assets/${assetId}`);
      if (response.success) {
        assets[activeTab] = assets[activeTab].filter(asset => asset.id !== assetId);
        selectedAssets.delete(assetId);
        selectedAssets = selectedAssets;
        toastStore.success('素材已刪除');
        updateCategoryCounts();
      } else {
        toastStore.error('刪除失敗');
      }
    } catch (error) {
      toastStore.error('刪除素材時發生錯誤');
    }
  }
  
  async function toggleFavorite(assetId) {
    const asset = assets[activeTab].find(a => a.id === assetId);
    if (!asset) return;
    
    try {
      const response = await apiClient.put(`/api/v1/assets/${assetId}/favorite`, {
        favorite: !asset.isFavorite
      });
      
      if (response.success) {
        asset.isFavorite = !asset.isFavorite;
        assets[activeTab] = [...assets[activeTab]]; // Trigger reactivity
        toastStore.success(asset.isFavorite ? '已加入我的最愛' : '已從我的最愛移除');
      } else {
        // Simulate toggle for mock data
        asset.isFavorite = !asset.isFavorite;
        assets[activeTab] = [...assets[activeTab]];
        toastStore.success(asset.isFavorite ? '已加入我的最愛' : '已從我的最愛移除');
      }
    } catch (error) {
      // Simulate toggle for mock data
      asset.isFavorite = !asset.isFavorite;
      assets[activeTab] = [...assets[activeTab]];
      toastStore.success(asset.isFavorite ? '已加入我的最愛' : '已從我的最愛移除');
    }
  }
  
  function copyAssetUrl(asset) {
    navigator.clipboard.writeText(asset.url).then(() => {
      toastStore.success('連結已複製到剪貼簿');
    }).catch(() => {
      toastStore.error('複製失敗');
    });
  }
  
  function handleDragOver(event) {
    event.preventDefault();
    dragOver = true;
  }
  
  function handleDragLeave() {
    dragOver = false;
  }
  
  function handleDrop(event) {
    event.preventDefault();
    dragOver = false;
    const files = Array.from(event.dataTransfer.files);
    handleFileUpload(files);
  }
  
  function handleFileSelect(event) {
    const files = Array.from(event.target.files);
    handleFileUpload(files);
    event.target.value = ''; // Reset input
  }
  
  async function handleFileUpload(files) {
    if (files.length === 0) return;
    
    const validTypes = {
      images: ['image/jpeg', 'image/png', 'image/webp', 'image/gif'],
      videos: ['video/mp4', 'video/webm', 'video/mov'],
      audio: ['audio/mp3', 'audio/wav', 'audio/ogg'],
      music: ['audio/mp3', 'audio/wav', 'audio/ogg']
    };
    
    const validFiles = files.filter(file => 
      validTypes[activeTab]?.includes(file.type)
    );
    
    if (validFiles.length !== files.length) {
      toastStore.error(`只能上傳 ${activeTab} 類型的檔案`);
    }
    
    if (validFiles.length === 0) return;
    
    isUploading = true;
    const uploadPromises = validFiles.map(async (file) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', activeTab);
      
      try {
        const response = await apiClient.post('/api/v1/assets/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        
        if (response.success) {
          return response.data;
        } else {
          // Mock upload for development
          return {
            id: `uploaded_${Date.now()}_${Math.random()}`,
            name: file.name,
            url: URL.createObjectURL(file),
            thumbnail: activeTab === 'images' ? URL.createObjectURL(file) : '/api/placeholder/200/150',
            size: file.size,
            format: file.type.split('/')[1].toUpperCase(),
            createdAt: new Date().toISOString(),
            usedCount: 0,
            isFavorite: false,
            tags: ['用戶上傳'],
            metadata: {}
          };
        }
      } catch (error) {
        throw new Error(`${file.name} 上傳失敗`);
      }
    });
    
    try {
      const uploadedAssets = await Promise.all(uploadPromises);
      assets[activeTab] = [...assets[activeTab], ...uploadedAssets];
      updateCategoryCounts();
      toastStore.success(`成功上傳 ${uploadedAssets.length} 個檔案`);
    } catch (error) {
      toastStore.error(error.message);
    } finally {
      isUploading = false;
    }
  }
  
  // Computed values
  $: currentAssets = assets[activeTab] || [];
  $: filteredAssets = currentAssets.filter(asset => {
    const matchesSearch = !searchQuery || 
      asset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      asset.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    const matchesFilter = selectedFilter === 'all' ||
      (selectedFilter === 'favorites' && asset.isFavorite) ||
      (selectedFilter === 'recent' && new Date() - new Date(asset.createdAt) < 7 * 24 * 60 * 60 * 1000) ||
      (selectedFilter === 'unused' && asset.usedCount === 0);
    
    return matchesSearch && matchesFilter;
  });
</script>

<svelte:head>
  <title>素材庫 - AI Video Creator</title>
  <meta name="description" content="管理您的圖片、影片、語音和音樂素材" />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <!-- Navigation -->
  <Navigation />
  
  <div class="max-w-7xl mx-auto px-4 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        素材庫
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        管理您的圖片、影片、語音和音樂素材
      </p>
    </div>
    
    <!-- Tab Navigation -->
    <div class="mb-6">
      <!-- Mobile Tab Navigation -->
      <div class="sm:hidden mb-4">
        <label for="category-select" class="sr-only">選擇素材類別</label>
        <select 
          id="category-select"
          class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          bind:value={activeTab}
        >
          {#each categories as category}
            <option value={category.id}>{category.name} ({categoryCounts[category.id]})</option>
          {/each}
        </select>
      </div>
      
      <!-- Desktop Tab Navigation -->
      <div class="hidden sm:block border-b border-gray-200 dark:border-gray-700">
        <nav class="flex space-x-4 overflow-x-auto" role="tablist" aria-label="素材類別">
          {#each categories as category}
            <button
              class="flex items-center py-2 px-3 border-b-2 font-medium text-sm transition-colors whitespace-nowrap focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-50
                     {activeTab === category.id
                       ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                       : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'}"
              on:click={() => handleTabChange(category.id)}
              role="tab"
              aria-selected={activeTab === category.id}
              aria-controls="assets-panel"
              tabindex={activeTab === category.id ? 0 : -1}
              aria-label="{category.name} ({category.count} 個素材)"
            >
              <svelte:component this={category.icon} class="w-4 h-4 mr-2" aria-hidden="true" />
              {category.label}
              <span class="ml-2 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 py-0.5 px-2 rounded-full text-xs">
                {category.count}
              </span>
            </button>
          {/each}
        </nav>
      </div>
    </div>
    
    <!-- Toolbar -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
        <div class="flex flex-col sm:flex-row sm:items-center gap-4">
          <!-- Search -->
          <div class="relative flex-1 sm:flex-none">
            <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" aria-hidden="true" />
            <label for="search-assets" class="sr-only">搜尋素材</label>
            <input
              id="search-assets"
              type="text"
              placeholder="搜尋素材..."
              bind:value={searchQuery}
              on:input={handleSearch}
              class="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white w-full sm:w-64"
              aria-describedby="search-help"
            />
            <div id="search-help" class="sr-only">搜尋素材名稱或標籤</div>
          </div>
          
          <!-- Filter -->
          <div class="flex-shrink-0">
            <label for="filter-select" class="sr-only">篩選素材</label>
            <select
              id="filter-select"
              bind:value={selectedFilter}
              on:change={handleFilterChange}
              class="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white w-full sm:w-auto"
            >
              {#each filters as filter}
                <option value={filter.value}>{filter.label}</option>
              {/each}
            </select>
          </div>
        </div>
        
        <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
          <!-- View Mode Toggle -->
          <div class="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1" role="group" aria-label="檢視模式">
            <button
              class="p-2 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-gray-100 dark:focus:ring-offset-gray-700 {viewMode === 'grid' ? 'bg-white dark:bg-gray-600 shadow-sm' : ''}"
              on:click={() => viewMode = 'grid'}
              aria-pressed={viewMode === 'grid'}
              aria-label="網格檢視"
              title="網格檢視"
            >
              <Grid3X3 class="w-4 h-4" aria-hidden="true" />
            </button>
            <button
              class="p-2 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-gray-100 dark:focus:ring-offset-gray-700 {viewMode === 'list' ? 'bg-white dark:bg-gray-600 shadow-sm' : ''}"
              on:click={() => viewMode = 'list'}
              aria-pressed={viewMode === 'list'}
              aria-label="清單檢視"
              title="清單檢視"
            >
              <List class="w-4 h-4" aria-hidden="true" />
            </button>
          </div>
          
          <!-- Upload Button -->
          <button
            on:click={() => fileInput?.click()}
            disabled={isUploading}
            class="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white rounded-lg transition-colors flex items-center"
          >
            {#if isUploading}
              <RefreshCw class="w-4 h-4 mr-2 animate-spin" />
            {:else}
              <Upload class="w-4 h-4 mr-2" />
            {/if}
            上傳素材
          </button>
          
          <!-- Hidden file input -->
          <input
            type="file"
            bind:this={fileInput}
            on:change={handleFileSelect}
            multiple
            accept={activeTab === 'images' ? 'image/*' : 
                   activeTab === 'videos' ? 'video/*' :
                   activeTab === 'audio' || activeTab === 'music' ? 'audio/*' : '*'}
            class="hidden"
          />
          
          <!-- Bulk Actions -->
          {#if selectedAssets.size > 0}
            <button
              on:click={selectAllAssets}
              class="px-3 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              {selectedAssets.size === filteredAssets.length ? '取消全選' : '全選'}
            </button>
          {/if}
        </div>
      </div>
    </div>
    
    <!-- Upload Drop Zone -->
    {#if dragOver}
      <div
        class="fixed inset-0 bg-primary-600/20 backdrop-blur-sm z-50 flex items-center justify-center"
        on:dragover={handleDragOver}
        on:dragleave={handleDragLeave}
        on:drop={handleDrop}
        role="button"
        tabindex="-1"
      >
        <div class="bg-white dark:bg-gray-800 rounded-lg p-8 shadow-xl border-2 border-dashed border-primary-500">
          <Upload class="w-16 h-16 text-primary-500 mx-auto mb-4" />
          <p class="text-xl font-semibold text-gray-900 dark:text-white text-center">
            拖放檔案到這裡上傳
          </p>
          <p class="text-gray-500 dark:text-gray-400 text-center mt-2">
            支援 {activeTab} 格式檔案
          </p>
        </div>
      </div>
    {/if}
    
    <!-- Loading State -->
    {#if isLoading}
      <div class="flex items-center justify-center py-16">
        <RefreshCw class="w-8 h-8 animate-spin text-primary-600" />
        <span class="ml-3 text-gray-600 dark:text-gray-400">載入素材中...</span>
      </div>
    
    <!-- Empty State -->
    {:else if filteredAssets.length === 0}
      <div class="text-center py-16">
        <svelte:component 
          this={categories.find(c => c.id === activeTab)?.icon || ImageIcon} 
          class="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" 
        />
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
          {searchQuery ? '找不到符合條件的素材' : `尚未有任何${categories.find(c => c.id === activeTab)?.label}素材`}
        </h3>
        <p class="text-gray-500 dark:text-gray-400 mb-6">
          {searchQuery ? '嘗試調整搜尋條件或篩選器' : '開始上傳您的第一個素材，或使用 AI 功能自動生成'}
        </p>
        {#if !searchQuery}
          <button
            on:click={() => fileInput?.click()}
            class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors inline-flex items-center"
          >
            <Upload class="w-4 h-4 mr-2" />
            上傳素材
          </button>
        {/if}
      </div>
    
    <!-- Assets Grid/List -->
    {:else}
      <!-- Selected Items Info -->
      {#if selectedAssets.size > 0}
        <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-6">
          <div class="flex items-center justify-between">
            <p class="text-blue-800 dark:text-blue-300">
              已選擇 {selectedAssets.size} 個項目
            </p>
            <div class="flex items-center space-x-2">
              <button
                on:click={() => {
                  selectedAssets.forEach(id => {
                    const asset = filteredAssets.find(a => a.id === id);
                    if (asset) downloadAsset(asset);
                  });
                }}
                class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
              >
                批量下載
              </button>
              <button
                on:click={() => {
                  if (confirm(`確定要刪除所選的 ${selectedAssets.size} 個素材嗎？`)) {
                    selectedAssets.forEach(id => deleteAsset(id));
                  }
                }}
                class="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white text-sm rounded transition-colors"
              >
                批量刪除
              </button>
            </div>
          </div>
        </div>
      {/if}
      
      <!-- Grid View -->
      {#if viewMode === 'grid'}
        <div id="assets-panel" role="tabpanel" aria-labelledby="tab-{activeTab}" class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
          {#each filteredAssets as asset, index (asset.id)}
            <div 
              class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-all duration-200 group relative focus-within:ring-2 focus-within:ring-primary-500 focus-within:ring-offset-2 focus-within:ring-offset-white dark:focus-within:ring-offset-gray-50
                     {selectedAssets.has(asset.id) ? 'ring-2 ring-primary-500 bg-primary-50 dark:bg-primary-900/10' : ''}"
              on:click={(e) => handleAssetSelect(asset.id, e)}
              on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), handleAssetSelect(asset.id, e))}
              role="option"
              aria-selected={selectedAssets.has(asset.id)}
              aria-label="{asset.name} - {activeTab} 素材"
              aria-describedby="asset-info-{asset.id}"
              tabindex="0"
            >
              <!-- Asset Preview -->
              <div class="aspect-square relative rounded-t-lg overflow-hidden">
                {#if activeTab === 'images'}
                  <img
                    src={asset.thumbnail || asset.url}
                    alt={asset.name}
                    class="w-full h-full object-cover"
                  />
                {:else if activeTab === 'videos'}
                  <div class="w-full h-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                    <Video class="w-12 h-12 text-gray-400" />
                  </div>
                  {#if asset.duration}
                    <div class="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                      {formatDuration(asset.duration)}
                    </div>
                  {/if}
                {:else}
                  <div class="w-full h-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                    <Music class="w-12 h-12 text-gray-400" />
                  </div>
                  {#if asset.duration}
                    <div class="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                      {formatDuration(asset.duration)}
                    </div>
                  {/if}
                {/if}
                
                <!-- Selection Indicator -->
                {#if selectedAssets.has(asset.id)}
                  <div class="absolute top-2 left-2 w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center">
                    <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
                    </svg>
                  </div>
                {/if}
                
                <!-- Favorite Badge -->
                {#if asset.isFavorite}
                  <div class="absolute top-2 right-2">
                    <Star class="w-4 h-4 text-yellow-400 fill-current" />
                  </div>
                {/if}
                
                <!-- Hover Actions -->
                <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-2">
                  <button
                    on:click|stopPropagation={() => showPreview = asset}
                    class="p-2 bg-white/90 text-gray-700 rounded-full hover:bg-white transition-colors"
                    title="預覽"
                  >
                    <Eye class="w-4 h-4" />
                  </button>
                  <button
                    on:click|stopPropagation={() => downloadAsset(asset)}
                    class="p-2 bg-white/90 text-gray-700 rounded-full hover:bg-white transition-colors"
                    title="下載"
                  >
                    <Download class="w-4 h-4" />
                  </button>
                  <button
                    on:click|stopPropagation={() => toggleFavorite(asset.id)}
                    class="p-2 bg-white/90 text-gray-700 rounded-full hover:bg-white transition-colors"
                    title="收藏"
                  >
                    <Star class="w-4 h-4 {asset.isFavorite ? 'text-yellow-500 fill-current' : ''}" />
                  </button>
                </div>
              </div>
              
              <!-- Asset Info -->
              <div class="p-3">
                <h3 class="text-sm font-medium text-gray-900 dark:text-white truncate mb-1">
                  {asset.name}
                </h3>
                <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                  <span>{asset.format}</span>
                  <span>{formatFileSize(asset.size)}</span>
                </div>
                {#if asset.usedCount > 0}
                  <div class="text-xs text-green-600 dark:text-green-400 mt-1">
                    已使用 {asset.usedCount} 次
                  </div>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      
      <!-- List View -->
      {:else}
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table class="w-full">
            <thead class="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th class="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedAssets.size === filteredAssets.length && filteredAssets.length > 0}
                    on:change={selectAllAssets}
                    class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  名稱
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  格式
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  大小
                </th>
                {#if activeTab !== 'images'}
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    時長
                  </th>
                {/if}
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  使用次數
                </th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  建立時間
                </th>
                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                  操作
                </th>
              </tr>
            </thead>
            <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
              {#each filteredAssets as asset (asset.id)}
                <tr 
                  class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors
                         {selectedAssets.has(asset.id) ? 'bg-primary-50 dark:bg-primary-900/20' : ''}"
                  on:click={(e) => handleAssetSelect(asset.id, e)}
                  role="button"
                  tabindex="0"
                >
                  <td class="px-6 py-4">
                    <input
                      type="checkbox"
                      checked={selectedAssets.has(asset.id)}
                      on:change={() => handleAssetSelect(asset.id, { ctrlKey: true })}
                      class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                  </td>
                  <td class="px-6 py-4">
                    <div class="flex items-center">
                      <div class="h-10 w-10 flex-shrink-0 mr-3">
                        {#if activeTab === 'images'}
                          <img 
                            src={asset.thumbnail || asset.url} 
                            alt={asset.name}
                            class="h-10 w-10 rounded object-cover"
                          />
                        {:else}
                          <div class="h-10 w-10 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center">
                            <svelte:component 
                              this={activeTab === 'videos' ? Video : Music} 
                              class="w-5 h-5 text-gray-400" 
                            />
                          </div>
                        {/if}
                      </div>
                      <div>
                        <div class="text-sm font-medium text-gray-900 dark:text-white flex items-center">
                          {asset.name}
                          {#if asset.isFavorite}
                            <Star class="w-4 h-4 ml-2 text-yellow-400 fill-current" />
                          {/if}
                        </div>
                        {#if asset.tags?.length > 0}
                          <div class="text-xs text-gray-500 dark:text-gray-400">
                            {asset.tags.join(', ')}
                          </div>
                        {/if}
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                    {asset.format}
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                    {formatFileSize(asset.size)}
                  </td>
                  {#if activeTab !== 'images'}
                    <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                      {asset.duration ? formatDuration(asset.duration) : '-'}
                    </td>
                  {/if}
                  <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                                 {asset.usedCount > 0 ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300' : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}">
                      {asset.usedCount} 次
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                    {new Date(asset.createdAt).toLocaleDateString('zh-TW')}
                  </td>
                  <td class="px-6 py-4 text-right text-sm font-medium">
                    <div class="flex items-center justify-end space-x-2">
                      <button
                        on:click|stopPropagation={() => copyAssetUrl(asset)}
                        class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        title="複製連結"
                      >
                        <Copy class="w-4 h-4" />
                      </button>
                      <button
                        on:click|stopPropagation={() => downloadAsset(asset)}
                        class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        title="下載"
                      >
                        <Download class="w-4 h-4" />
                      </button>
                      <button
                        on:click|stopPropagation={() => toggleFavorite(asset.id)}
                        class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                        title="收藏"
                      >
                        <Star class="w-4 h-4 {asset.isFavorite ? 'text-yellow-500 fill-current' : ''}" />
                      </button>
                      <button
                        on:click|stopPropagation={() => deleteAsset(asset.id)}
                        class="text-red-400 hover:text-red-600"
                        title="刪除"
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
      {/if}
    {/if}
  </div>
  
  <!-- Drop zone event listeners -->
  <div
    class="fixed inset-0 pointer-events-none"
    on:dragover={handleDragOver}
    on:dragleave={handleDragLeave}
    on:drop={handleDrop}
  ></div>
</div>

<!-- Preview Modal -->
{#if showPreview}
  <div 
    class="fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-4"
    on:click={() => showPreview = null}
    role="dialog"
    tabindex="-1"
  >
    <div class="bg-white dark:bg-gray-800 rounded-lg max-w-4xl max-h-[90vh] overflow-auto">
      <div class="p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            {showPreview.name}
          </h3>
          <button
            on:click={() => showPreview = null}
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="mb-4">
          {#if activeTab === 'images'}
            <img 
              src={showPreview.url} 
              alt={showPreview.name}
              class="max-w-full max-h-96 object-contain mx-auto"
            />
          {:else if activeTab === 'videos'}
            <video 
              src={showPreview.url} 
              controls
              class="max-w-full max-h-96 mx-auto"
            >
              您的瀏覽器不支援影片播放
            </video>
          {:else}
            <audio 
              src={showPreview.url} 
              controls
              class="w-full"
            >
              您的瀏覽器不支援音頻播放
            </audio>
          {/if}
        </div>
        
        <div class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span class="font-medium text-gray-700 dark:text-gray-300">格式:</span>
            <span class="text-gray-600 dark:text-gray-400 ml-2">{showPreview.format}</span>
          </div>
          <div>
            <span class="font-medium text-gray-700 dark:text-gray-300">大小:</span>
            <span class="text-gray-600 dark:text-gray-400 ml-2">{formatFileSize(showPreview.size)}</span>
          </div>
          {#if showPreview.duration}
            <div>
              <span class="font-medium text-gray-700 dark:text-gray-300">時長:</span>
              <span class="text-gray-600 dark:text-gray-400 ml-2">{formatDuration(showPreview.duration)}</span>
            </div>
          {/if}
          <div>
            <span class="font-medium text-gray-700 dark:text-gray-300">使用次數:</span>
            <span class="text-gray-600 dark:text-gray-400 ml-2">{showPreview.usedCount}</span>
          </div>
          <div class="col-span-2">
            <span class="font-medium text-gray-700 dark:text-gray-300">建立時間:</span>
            <span class="text-gray-600 dark:text-gray-400 ml-2">
              {new Date(showPreview.createdAt).toLocaleString('zh-TW')}
            </span>
          </div>
          {#if showPreview.tags?.length > 0}
            <div class="col-span-2">
              <span class="font-medium text-gray-700 dark:text-gray-300">標籤:</span>
              <div class="mt-1">
                {#each showPreview.tags as tag}
                  <span class="inline-block bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 px-2 py-1 rounded text-xs mr-2 mb-1">
                    {tag}
                  </span>
                {/each}
              </div>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
{/if}