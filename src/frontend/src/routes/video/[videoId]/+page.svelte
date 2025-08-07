<script>
  import { page } from '$app/stores';
  import { onMount, onDestroy } from 'svelte';
  import Navigation from '$lib/components/layout/Navigation.svelte';
  import { Play, Pause, Volume2, VolumeX, Maximize2, Download, Share, Heart, Eye, Calendar, Tag, User } from 'lucide-svelte';
  
  export let data;
  
  let videoElement;
  let isPlaying = false;
  let isMuted = false;
  let volume = 1;
  let currentTime = 0;
  let duration = 0;
  let isFullscreen = false;
  let showControls = true;
  let controlsTimeout;
  let isLoading = true;
  let playbackRate = 1;
  
  // 模擬影片資料
  let video = {
    id: $page.params.videoId,
    title: '如何使用 AI 生成影片內容',
    description: '這是一個展示如何使用人工智慧技術生成高質量影片內容的教學影片。從腳本生成到視覺素材創建，再到最終的影片合成，我們將一步步帶您了解整個製作流程。',
    url: '/api/videos/sample-video.mp4',
    thumbnail: 'https://via.placeholder.com/1280x720/4f46e5/ffffff?text=AI+Video+Generation',
    duration: 180, // 3 minutes
    views: 15420,
    likes: 892,
    createdAt: '2024-01-15T10:30:00Z',
    updatedAt: '2024-01-20T15:45:00Z',
    author: {
      name: 'AI Creator Studio',
      avatar: 'https://via.placeholder.com/40/6366f1/ffffff?text=AI'
    },
    platforms: ['youtube', 'tiktok', 'instagram'],
    tags: ['AI', '影片生成', '教學', '科技', '創作'],
    status: 'published',
    downloadUrl: '/api/videos/sample-video.mp4?download=true'
  };
  
  // 播放速度選項
  const playbackRates = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 2];
  
  onMount(() => {
    // 在實際應用中，這裡會從 API 獲取影片資料
    // video = await fetch(`/api/videos/${$page.params.videoId}`).then(r => r.json());
    
    if (videoElement) {
      videoElement.addEventListener('loadedmetadata', handleLoadedMetadata);
      videoElement.addEventListener('timeupdate', handleTimeUpdate);
      videoElement.addEventListener('ended', handleEnded);
    }
  });
  
  onDestroy(() => {
    if (controlsTimeout) {
      clearTimeout(controlsTimeout);
    }
  });
  
  function handleLoadedMetadata() {
    duration = videoElement.duration;
    isLoading = false;
  }
  
  function handleTimeUpdate() {
    currentTime = videoElement.currentTime;
  }
  
  function handleEnded() {
    isPlaying = false;
  }
  
  function togglePlay() {
    if (isPlaying) {
      videoElement.pause();
    } else {
      videoElement.play();
    }
    isPlaying = !isPlaying;
  }
  
  function toggleMute() {
    isMuted = !isMuted;
    videoElement.muted = isMuted;
  }
  
  function handleVolumeChange(e) {
    volume = e.target.value;
    videoElement.volume = volume;
    if (volume > 0 && isMuted) {
      isMuted = false;
      videoElement.muted = false;
    }
  }
  
  function handleSeek(e) {
    const rect = e.target.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    currentTime = percent * duration;
    videoElement.currentTime = currentTime;
  }
  
  function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }
  
  function toggleFullscreen() {
    if (!isFullscreen) {
      if (videoElement.requestFullscreen) {
        videoElement.requestFullscreen();
      } else if (videoElement.webkitRequestFullscreen) {
        videoElement.webkitRequestFullscreen();
      } else if (videoElement.msRequestFullscreen) {
        videoElement.msRequestFullscreen();
      }
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
      }
    }
    isFullscreen = !isFullscreen;
  }
  
  function handleMouseMove() {
    showControls = true;
    if (controlsTimeout) {
      clearTimeout(controlsTimeout);
    }
    controlsTimeout = setTimeout(() => {
      if (isPlaying) {
        showControls = false;
      }
    }, 3000);
  }
  
  function changePlaybackRate(rate) {
    playbackRate = rate;
    videoElement.playbackRate = rate;
  }
  
  function handleDownload() {
    const link = document.createElement('a');
    link.href = video.downloadUrl;
    link.download = `${video.title}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
  
  function handleShare() {
    if (navigator.share) {
      navigator.share({
        title: video.title,
        text: video.description,
        url: window.location.href
      });
    } else {
      // 降級方案：複製到剪貼簿
      navigator.clipboard.writeText(window.location.href);
      // 這裡可以顯示一個提示
      alert('連結已複製到剪貼簿');
    }
  }
  
  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('zh-TW', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
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
  
  // 響應式設計：根據螢幕大小調整控制項
  let screenWidth;
  $: isMobile = screenWidth < 768;
</script>

<svelte:window bind:innerWidth={screenWidth} />

<svelte:head>
  <title>{video.title} - AI Video Creator</title>
  <meta name="description" content={video.description} />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <!-- Navigation -->
  <Navigation />
  
  <!-- Video Player Container -->
  <div class="relative bg-black">
    <div 
      class="relative max-w-6xl mx-auto"
      on:mousemove={handleMouseMove}
      role="button"
      tabindex="0"
      on:keydown={(e) => e.key === ' ' && togglePlay()}
    >
      <!-- Video Element -->
      <video
        bind:this={videoElement}
        class="w-full aspect-video"
        poster={video.thumbnail}
        preload="metadata"
        on:click={togglePlay}
      >
        <source src={video.url} type="video/mp4" />
        <track kind="captions" src="/api/videos/captions.vtt" srclang="zh" label="繁體中文" />
        您的瀏覽器不支援 HTML5 影片播放。
      </video>
      
      <!-- Loading Overlay -->
      {#if isLoading}
        <div class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-75">
          <div class="text-white text-center">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
            <p>載入中...</p>
          </div>
        </div>
      {/if}
      
      <!-- Video Controls -->
      {#if showControls && !isLoading}
        <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black to-transparent p-4 transition-opacity duration-300">
          <!-- Progress Bar -->
          <div class="mb-4">
            <div 
              class="w-full h-2 bg-gray-600 rounded-full cursor-pointer"
              on:click={handleSeek}
              role="button"
              tabindex="0"
              on:keydown={(e) => e.key === 'Enter' && handleSeek(e)}
            >
              <div 
                class="h-full bg-red-600 rounded-full"
                style="width: {duration > 0 ? (currentTime / duration) * 100 : 0}%"
              ></div>
            </div>
          </div>
          
          <div class="flex items-center justify-between text-white">
            <!-- Left Controls -->
            <div class="flex items-center space-x-4">
              <!-- Play/Pause -->
              <button
                type="button"
                on:click={togglePlay}
                class="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
              >
                {#if isPlaying}
                  <Pause class="w-6 h-6" />
                {:else}
                  <Play class="w-6 h-6" />
                {/if}
              </button>
              
              <!-- Volume -->
              {#if !isMobile}
                <div class="flex items-center space-x-2">
                  <button
                    type="button"
                    on:click={toggleMute}
                    class="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
                  >
                    {#if isMuted || volume === 0}
                      <VolumeX class="w-5 h-5" />
                    {:else}
                      <Volume2 class="w-5 h-5" />
                    {/if}
                  </button>
                  
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={isMuted ? 0 : volume}
                    on:input={handleVolumeChange}
                    class="w-20 h-1 bg-gray-600 rounded-lg appearance-none slider"
                  />
                </div>
              {/if}
              
              <!-- Time Display -->
              <div class="text-sm font-mono">
                {formatTime(currentTime)} / {formatTime(duration)}
              </div>
            </div>
            
            <!-- Right Controls -->
            <div class="flex items-center space-x-2">
              <!-- Playback Rate -->
              {#if !isMobile}
                <div class="relative group">
                  <button
                    type="button"
                    class="px-2 py-1 text-sm hover:bg-white hover:bg-opacity-20 rounded transition-colors"
                  >
                    {playbackRate}x
                  </button>
                  
                  <div class="absolute bottom-full mb-2 right-0 bg-black bg-opacity-90 rounded p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div class="space-y-1">
                      {#each playbackRates as rate}
                        <button
                          type="button"
                          on:click={() => changePlaybackRate(rate)}
                          class="block w-full text-left px-3 py-1 text-sm hover:bg-white hover:bg-opacity-20 rounded
                                 {rate === playbackRate ? 'text-red-400' : ''}"
                        >
                          {rate}x
                        </button>
                      {/each}
                    </div>
                  </div>
                </div>
              {/if}
              
              <!-- Fullscreen -->
              <button
                type="button"
                on:click={toggleFullscreen}
                class="p-2 hover:bg-white hover:bg-opacity-20 rounded-full transition-colors"
              >
                <Maximize2 class="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      {/if}
    </div>
  </div>
  
  <!-- Video Information -->
  <div class="max-w-6xl mx-auto px-4 py-6">
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
      <!-- Main Content -->
      <div class="lg:col-span-2">
        <!-- Title and Actions -->
        <div class="mb-6">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            {video.title}
          </h1>
          
          <!-- Stats and Actions -->
          <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <!-- Stats -->
            <div class="flex items-center space-x-6 text-sm text-gray-600 dark:text-gray-400">
              <span class="flex items-center">
                <Eye class="w-4 h-4 mr-1" />
                {video.views.toLocaleString()} 次觀看
              </span>
              <span class="flex items-center">
                <Heart class="w-4 h-4 mr-1" />
                {video.likes.toLocaleString()} 個讚
              </span>
              <span class="flex items-center">
                <Calendar class="w-4 h-4 mr-1" />
                {formatDate(video.createdAt)}
              </span>
            </div>
            
            <!-- Action Buttons -->
            <div class="flex items-center space-x-3">
              <button
                type="button"
                on:click={handleDownload}
                class="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                <Download class="w-4 h-4 mr-2" />
                下載
              </button>
              <button
                type="button"
                on:click={handleShare}
                class="flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <Share class="w-4 h-4 mr-2" />
                分享
              </button>
            </div>
          </div>
        </div>
        
        <!-- Description -->
        <div class="bg-white dark:bg-gray-800 rounded-lg p-6 mb-6">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">描述</h2>
          <p class="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">
            {video.description}
          </p>
        </div>
        
        <!-- Tags -->
        {#if video.tags && video.tags.length > 0}
          <div class="bg-white dark:bg-gray-800 rounded-lg p-6">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
              <Tag class="w-5 h-5 mr-2" />
              標籤
            </h2>
            <div class="flex flex-wrap gap-2">
              {#each video.tags as tag}
                <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200">
                  #{tag}
                </span>
              {/each}
            </div>
          </div>
        {/if}
      </div>
      
      <!-- Sidebar -->
      <div class="lg:col-span-1">
        <!-- Author Info -->
        <div class="bg-white dark:bg-gray-800 rounded-lg p-6 mb-6">
          <div class="flex items-center mb-4">
            <img
              src={video.author.avatar}
              alt={video.author.name}
              class="w-12 h-12 rounded-full mr-4"
            />
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {video.author.name}
              </h3>
              <p class="text-sm text-gray-600 dark:text-gray-400">內容創作者</p>
            </div>
          </div>
          <button
            type="button"
            class="w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
          >
            關注
          </button>
        </div>
        
        <!-- Video Details -->
        <div class="bg-white dark:bg-gray-800 rounded-lg p-6 mb-6">
          <h3 class="font-semibold text-gray-900 dark:text-white mb-4">影片資訊</h3>
          <div class="space-y-3 text-sm">
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">時長:</span>
              <span class="text-gray-900 dark:text-white">{formatTime(video.duration)}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">建立於:</span>
              <span class="text-gray-900 dark:text-white">{formatDate(video.createdAt)}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-600 dark:text-gray-400">最後更新:</span>
              <span class="text-gray-900 dark:text-white">{formatDate(video.updatedAt)}</span>
            </div>
            <div>
              <span class="text-gray-600 dark:text-gray-400">發布平台:</span>
              <div class="flex space-x-1 mt-1">
                {#each video.platforms as platform}
                  <span class="text-lg" title={platform}>
                    {getPlatformIcon(platform)}
                  </span>
                {/each}
              </div>
            </div>
          </div>
        </div>
        
        <!-- Related Videos (Placeholder) -->
        <div class="bg-white dark:bg-gray-800 rounded-lg p-6">
          <h3 class="font-semibold text-gray-900 dark:text-white mb-4">相關影片</h3>
          <div class="space-y-3">
            {#each Array(3) as _, i}
              <div class="flex space-x-3">
                <div class="w-24 h-16 bg-gray-200 dark:bg-gray-700 rounded flex-shrink-0"></div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-900 dark:text-white line-clamp-2">
                    相關影片標題 {i + 1}
                  </p>
                  <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    2.5K 次觀看 • 3 天前
                  </p>
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .slider {
    outline: none;
  }
  
  .slider::-webkit-slider-thumb {
    appearance: none;
    width: 16px;
    height: 16px;
    background: white;
    cursor: pointer;
    border-radius: 50%;
  }
  
  .slider::-moz-range-thumb {
    width: 16px;
    height: 16px;
    background: white;
    cursor: pointer;
    border-radius: 50%;
    border: none;
  }
  
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>