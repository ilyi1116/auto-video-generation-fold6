<script>
  import { onMount } from 'svelte';
  import { toastStore } from '$lib/stores/toast.js';
  import { apiClient } from '$lib/api/client.js';
  import Navigation from '$lib/components/layout/Navigation.svelte';
  import LazyImage from '$lib/components/ui/LazyImage.svelte';
  import VirtualGrid from '$lib/components/ui/VirtualGrid.svelte';
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
    
    // Validate file types and sizes
    const validTypes = {
      images: ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp', 'image/tiff'],
      videos: ['video/mp4', 'video/webm', 'video/mov', 'video/avi', 'video/mkv'],
      audio: ['audio/mp3', 'audio/wav', 'audio/ogg', 'audio/aac', 'audio/flac'],
      music: ['audio/mp3', 'audio/wav', 'audio/ogg', 'audio/aac', 'audio/flac']
    };
    
    const maxFileSize = {
      images: 10 * 1024 * 1024,   // 10MB
      videos: 500 * 1024 * 1024,  // 500MB
      audio: 50 * 1024 * 1024,    // 50MB
      music: 50 * 1024 * 1024     // 50MB
    };
    
    const validFiles = [];
    const errors = [];
    
    for (const file of files) {
      // Check file type
      if (!validTypes[activeTab]?.includes(file.type)) {
        errors.push(`${file.name}: 不支援的檔案類型 (${file.type})`);
        continue;
      }
      
      // Check file size
      if (file.size > maxFileSize[activeTab]) {
        errors.push(`${file.name}: 檔案過大 (最大 ${formatFileSize(maxFileSize[activeTab])})`);
        continue;
      }
      
      // Check file name
      if (file.name.length > 255) {
        errors.push(`${file.name}: 檔案名稱過長`);
        continue;
      }
      
      validFiles.push(file);
    }
    
    // Show errors if any
    if (errors.length > 0) {
      toastStore.error(`檔案驗證失敗:\n${errors.slice(0, 3).join('\n')}${errors.length > 3 ? `\n...等 ${errors.length - 3} 個錯誤` : ''}`);
    }
    
    if (validFiles.length === 0) return;
    
    isUploading = true;
    let uploadedCount = 0;
    const totalCount = validFiles.length;
    
    toastStore.info(`開始上傳 ${totalCount} 個檔案...`);
    
    const uploadPromises = validFiles.map(async (file, index) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', activeTab);
      
      // Add metadata
      if (activeTab === 'images') {
        // For images, we could extract EXIF data here
        formData.append('metadata', JSON.stringify({
          originalName: file.name,
          uploadedAt: new Date().toISOString()
        }));
      }
      
      try {
        const response = await apiClient.post('/api/v1/assets/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            // You could update individual file progress here
          }
        });
        
        uploadedCount++;
        
        if (response.success) {
          // Update progress
          toastStore.info(`上傳進度: ${uploadedCount}/${totalCount} 完成`);
          return response.data;
        } else {
          // Mock upload for development with more realistic data
          const mockAsset = {
            id: `uploaded_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            name: file.name,
            url: URL.createObjectURL(file),
            thumbnail: activeTab === 'images' ? URL.createObjectURL(file) : '/api/placeholder/200/150',
            size: file.size,
            format: file.type.split('/')[1].toUpperCase(),
            createdAt: new Date().toISOString(),
            usedCount: 0,
            isFavorite: false,
            tags: ['用戶上傳', activeTab === 'images' ? '圖片' : activeTab === 'videos' ? '影片' : '音頻'],
            metadata: {
              originalName: file.name,
              uploadedAt: new Date().toISOString(),
              fileType: file.type,
              ...(activeTab === 'images' ? { width: 1920, height: 1080 } : {}),
              ...(activeTab === 'videos' || activeTab === 'audio' || activeTab === 'music' ? { bitrate: '128kbps' } : {})
            }
          };
          
          toastStore.info(`上傳進度: ${uploadedCount}/${totalCount} 完成`);
          return mockAsset;
        }
      } catch (error) {
        console.error(`Failed to upload ${file.name}:`, error);
        throw new Error(`${file.name} 上傳失敗: ${error.message || '未知錯誤'}`);
      }
    });
    
    try {
      const uploadedAssets = await Promise.allSettled(uploadPromises);
      
      const successful = uploadedAssets
        .filter(result => result.status === 'fulfilled')
        .map(result => result.value);
      
      const failed = uploadedAssets
        .filter(result => result.status === 'rejected')
        .map(result => result.reason.message);
      
      if (successful.length > 0) {
        assets[activeTab] = [...assets[activeTab], ...successful];
        updateCategoryCounts();
        toastStore.success(`成功上傳 ${successful.length} 個檔案`);
      }
      
      if (failed.length > 0) {
        toastStore.error(`${failed.length} 個檔案上傳失敗:\n${failed.slice(0, 2).join('\n')}${failed.length > 2 ? '\n...' : ''}`);
      }
      
    } catch (error) {
      console.error('Upload error:', error);
      toastStore.error('檔案上傳過程中發生錯誤');
    } finally {
      isUploading = false;
    }
  }
  
  // Helper functions for file formats and sizes
  function getFileFormats(category) {
    const formatMap = {
      images: ['jpg', 'png', 'webp', 'gif', 'bmp', 'tiff'],
      videos: ['mp4', 'webm', 'mov', 'avi', 'mkv'],
      audio: ['mp3', 'wav', 'ogg', 'aac', 'flac'],
      music: ['mp3', 'wav', 'ogg', 'aac', 'flac']
    };
    return formatMap[category] || [];
  }
  
  function getMaxFileSize(category) {
    const sizeMap = {
      images: 10 * 1024 * 1024,   // 10MB
      videos: 500 * 1024 * 1024,  // 500MB
      audio: 50 * 1024 * 1024,    // 50MB
      music: 50 * 1024 * 1024     // 50MB
    };
    return sizeMap[category] || 10 * 1024 * 1024;
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
            <option value={category.id}>{category.label} ({category.count})</option>
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
        class="fixed inset-0 bg-primary-600/30 backdrop-blur-md z-50 flex items-center justify-center p-4"
        on:dragover={handleDragOver}
        on:dragleave={handleDragLeave}
        on:drop={handleDrop}
        role="region"
        aria-label="檔案拖放上傳區域"
        tabindex="-1"
      >
        <div class="bg-white dark:bg-gray-800 rounded-2xl p-8 sm:p-12 shadow-2xl border-2 border-dashed border-primary-500 max-w-md w-full mx-4 transform transition-transform duration-300 scale-105">
          <div class="text-center">
            <!-- Animated Upload Icon -->
            <div class="relative mb-6">
              <div class="w-20 h-20 mx-auto bg-primary-100 dark:bg-primary-900/30 rounded-full flex items-center justify-center">
                <Upload class="w-10 h-10 text-primary-600 dark:text-primary-400 animate-bounce" aria-hidden="true" />
              </div>
              <!-- Floating particles animation -->
              <div class="absolute inset-0 -z-10">
                <div class="absolute top-2 left-4 w-2 h-2 bg-primary-400 rounded-full animate-ping" style="animation-delay: 0s;"></div>
                <div class="absolute top-6 right-6 w-1.5 h-1.5 bg-primary-500 rounded-full animate-ping" style="animation-delay: 0.5s;"></div>
                <div class="absolute bottom-4 left-8 w-1 h-1 bg-primary-300 rounded-full animate-ping" style="animation-delay: 1s;"></div>
                <div class="absolute bottom-8 right-4 w-1.5 h-1.5 bg-primary-400 rounded-full animate-ping" style="animation-delay: 1.5s;"></div>
              </div>
            </div>
            
            <h3 class="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white mb-3">
              拖放檔案到這裡
            </h3>
            
            <p class="text-gray-600 dark:text-gray-300 mb-4">
              支援多個檔案同時上傳
            </p>
            
            <!-- Supported formats -->
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 mb-4">
              <p class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                支援格式：
              </p>
              <div class="flex flex-wrap gap-2 justify-center">
                {#each getFileFormats(activeTab) as format}
                  <span class="px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded text-xs font-mono">
                    .{format}
                  </span>
                {/each}
              </div>
            </div>
            
            <!-- File size limit -->
            <p class="text-xs text-gray-500 dark:text-gray-400">
              單檔案大小限制：{formatFileSize(getMaxFileSize(activeTab))}
            </p>
          </div>
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
                  <LazyImage
                    src={asset.thumbnail || asset.url}
                    alt={asset.name}
                    className="w-full h-full object-cover rounded-t-lg"
                    placeholder="/api/placeholder/300/300"
                    threshold={0.1}
                  />
                {:else if activeTab === 'videos'}
                  <div class="w-full h-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                    <Video class="w-8 sm:w-12 h-8 sm:h-12 text-gray-400" aria-hidden="true" />
                  </div>
                  {#if asset.duration}
                    <div class="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded" aria-label="影片長度 {formatDuration(asset.duration)}">
                      {formatDuration(asset.duration)}
                    </div>
                  {/if}
                {:else}
                  <div class="w-full h-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                    <Music class="w-8 sm:w-12 h-8 sm:h-12 text-gray-400" aria-hidden="true" />
                  </div>
                  {#if asset.duration}
                    <div class="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-1.5 sm:px-2 py-0.5 sm:py-1 rounded" aria-label="音檔長度 {formatDuration(asset.duration)}">
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
    on:click|self={() => showPreview = null}
    on:keydown={(e) => e.key === 'Escape' && (showPreview = null)}
    role="dialog"
    aria-modal="true"
    aria-labelledby="preview-title"
    aria-describedby="preview-description"
    tabindex="-1"
  >
    <div class="bg-white dark:bg-gray-800 rounded-lg max-w-6xl w-full max-h-[95vh] overflow-auto shadow-2xl">
      <div class="p-4 sm:p-6">
        <div class="flex items-center justify-between mb-4">
          <div class="min-w-0 flex-1 pr-4">
            <h3 id="preview-title" class="text-lg sm:text-xl font-semibold text-gray-900 dark:text-white truncate">
              {showPreview.name}
            </h3>
            <p id="preview-description" class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              {showPreview.format} • {formatFileSize(showPreview.size)}
              {#if showPreview.duration} • {formatDuration(showPreview.duration)}{/if}
            </p>
          </div>
          <button
            on:click={() => showPreview = null}
            class="flex-shrink-0 p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-label="關閉預覽"
          >
            <svg class="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div class="mb-6">
          <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 flex items-center justify-center min-h-[300px] sm:min-h-[400px]">
            {#if activeTab === 'images'}
              <LazyImage
                src={showPreview.url}
                alt={showPreview.name}
                className="max-w-full max-h-[60vh] object-contain rounded-lg shadow-lg"
                placeholder="/api/placeholder/600/400"
                threshold={0}
              />
            {:else if activeTab === 'videos'}
              <video 
                src={showPreview.url} 
                controls
                preload="metadata"
                class="max-w-full max-h-[60vh] rounded-lg shadow-lg bg-black"
                style="min-width: 300px;"
              >
                <track kind="captions" srclang="zh" label="繁體中文" />
                您的瀏覽器不支援 HTML5 影片播放。
              </video>
            {:else}
              <div class="w-full max-w-lg">
                <div class="flex items-center justify-center mb-4">
                  <div class="w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center">
                    <Music class="w-8 h-8 text-primary-600 dark:text-primary-400" aria-hidden="true" />
                  </div>
                </div>
                <audio 
                  src={showPreview.url} 
                  controls
                  preload="metadata"
                  class="w-full rounded-lg"
                >
                  您的瀏覽器不支援 HTML5 音頻播放。
                </audio>
              </div>
            {/if}
          </div>
        </div>
        
        <!-- Asset Details -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm mb-6">
          <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
            <span class="font-medium text-gray-700 dark:text-gray-300 block mb-2">檔案資訊</span>
            <div class="space-y-1">
              <div class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">格式:</span>
                <span class="font-mono text-gray-800 dark:text-gray-200">{showPreview.format}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">大小:</span>
                <span class="font-mono text-gray-800 dark:text-gray-200">{formatFileSize(showPreview.size)}</span>
              </div>
              {#if showPreview.duration}
                <div class="flex justify-between">
                  <span class="text-gray-600 dark:text-gray-400">時長:</span>
                  <span class="font-mono text-gray-800 dark:text-gray-200">{formatDuration(showPreview.duration)}</span>
                </div>
              {/if}
              {#if showPreview.metadata?.width && showPreview.metadata?.height}
                <div class="flex justify-between">
                  <span class="text-gray-600 dark:text-gray-400">解析度:</span>
                  <span class="font-mono text-gray-800 dark:text-gray-200">{showPreview.metadata.width}×{showPreview.metadata.height}</span>
                </div>
              {/if}
            </div>
          </div>
          
          <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
            <span class="font-medium text-gray-700 dark:text-gray-300 block mb-2">使用統計</span>
            <div class="space-y-1">
              <div class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">使用次數:</span>
                <span class="font-mono text-gray-800 dark:text-gray-200">{showPreview.usedCount} 次</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">建立時間:</span>
                <span class="font-mono text-gray-800 dark:text-gray-200 text-xs">
                  {new Date(showPreview.createdAt).toLocaleDateString('zh-TW')}
                </span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-gray-600 dark:text-gray-400">收藏狀態:</span>
                <span class="flex items-center">
                  {#if showPreview.isFavorite}
                    <Star class="w-4 h-4 text-yellow-400 fill-current mr-1" aria-hidden="true" />
                    <span class="text-yellow-600 dark:text-yellow-400">已收藏</span>
                  {:else}
                    <span class="text-gray-500 dark:text-gray-400">未收藏</span>
                  {/if}
                </span>
              </div>
            </div>
          </div>
          
          {#if showPreview.tags?.length > 0}
            <div class="sm:col-span-2">
              <span class="font-medium text-gray-700 dark:text-gray-300 block mb-2">標籤</span>
              <div class="flex flex-wrap gap-2">
                {#each showPreview.tags as tag}
                  <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900/20 dark:text-primary-200 border border-primary-200 dark:border-primary-800">
                    <Tag class="w-3 h-3 mr-1" aria-hidden="true" />
                    {tag}
                  </span>
                {/each}
              </div>
            </div>
          {/if}
        </div>
        
        <!-- Action Buttons -->
        <div class="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200 dark:border-gray-600">
          <button
            on:click={() => downloadAsset(showPreview)}
            class="flex items-center justify-center px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-800"
          >
            <Download class="w-4 h-4 mr-2" aria-hidden="true" />
            下載檔案
          </button>
          
          <button
            on:click={() => toggleFavorite(showPreview.id)}
            class="flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-800"
          >
            <Star class="w-4 h-4 mr-2 {showPreview.isFavorite ? 'text-yellow-400 fill-current' : ''}" aria-hidden="true" />
            {showPreview.isFavorite ? '移除收藏' : '加入收藏'}
          </button>
          
          <button
            on:click={() => {
              navigator.clipboard.writeText(showPreview.url);
              // You could add a toast notification here
            }}
            class="flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-800"
          >
            <Copy class="w-4 h-4 mr-2" aria-hidden="true" />
            複製連結
          </button>
          
          <div class="sm:ml-auto">
            <button
              on:click={() => deleteAsset(showPreview.id)}
              class="flex items-center justify-center px-4 py-2 border border-red-300 dark:border-red-600 text-red-700 dark:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/10 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-800"
            >
              <Trash2 class="w-4 h-4 mr-2" aria-hidden="true" />
              刪除素材
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
{/if}