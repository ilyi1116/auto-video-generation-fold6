<script>
  import { onMount } from 'svelte';
  import { apiClient } from '$lib/api/client';
  import { toastStore } from '$lib/stores/toast';
  import { 
    Plus,
    Settings,
    Calendar,
    Share2,
    BarChart3,
    Users,
    Clock,
    Play,
    Pause,
    Edit3,
    Trash2,
    ExternalLink,
    CheckCircle,
    AlertCircle,
    XCircle,
    Upload,
    Image,
    Video,
    FileText,
    Globe,
    RefreshCw,
    TrendingUp,
    Eye,
    Heart,
    MessageCircle,
    Send,
    Copy,
    Download
  } from 'lucide-svelte';

  let isLoading = true;
  let activeTab = 'schedule';
  let selectedPlatforms = new Set(['youtube', 'tiktok']);
  let isPublishing = false;
  
  let socialData = {
    accounts: [],
    scheduledPosts: [],
    publishedPosts: [],
    analytics: {},
    drafts: []
  };

  // New post form data
  let newPost = {
    content: '',
    platforms: [],
    mediaFiles: [],
    scheduledTime: '',
    tags: '',
    location: ''
  };

  const platforms = [
    { 
      id: 'youtube', 
      name: 'YouTube', 
      icon: '📺', 
      color: 'bg-red-500',
      connected: true,
      maxLength: 5000,
      supports: ['video', 'image', 'text']
    },
    { 
      id: 'tiktok', 
      name: 'TikTok', 
      icon: '🎵', 
      color: 'bg-black',
      connected: true,
      maxLength: 2200,
      supports: ['video', 'image', 'text']
    },
    { 
      id: 'instagram', 
      name: 'Instagram', 
      icon: '📷', 
      color: 'bg-gradient-to-br from-purple-500 to-pink-500',
      connected: false,
      maxLength: 2200,
      supports: ['video', 'image', 'text']
    },
    { 
      id: 'twitter', 
      name: 'Twitter', 
      icon: '🐦', 
      color: 'bg-blue-500',
      connected: false,
      maxLength: 280,
      supports: ['video', 'image', 'text']
    },
    { 
      id: 'linkedin', 
      name: 'LinkedIn', 
      icon: '💼', 
      color: 'bg-blue-600',
      connected: false,
      maxLength: 3000,
      supports: ['video', 'image', 'text']
    },
    { 
      id: 'facebook', 
      name: 'Facebook', 
      icon: '📘', 
      color: 'bg-blue-700',
      connected: false,
      maxLength: 63206,
      supports: ['video', 'image', 'text']
    }
  ];

  const tabs = [
    { id: 'schedule', label: 'Schedule', icon: Calendar },
    { id: 'published', label: 'Published', icon: CheckCircle },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'accounts', label: 'Accounts', icon: Settings }
  ];

  onMount(async () => {
    await loadSocialData();
  });

  async function loadSocialData() {
    try {
      isLoading = true;
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      socialData = {
        accounts: [
          {
            platform: 'youtube',
            username: '@AutoVideoChannel',
            followers: 12500,
            connected: true,
            lastSync: new Date().toISOString()
          },
          {
            platform: 'tiktok',
            username: '@autovideo_ai',
            followers: 8900,
            connected: true,
            lastSync: new Date().toISOString()
          }
        ],
        scheduledPosts: [
          {
            id: 1,
            content: 'Check out our latest AI video creation tutorial! 🎥✨ #AI #VideoCreation #Tutorial',
            platforms: ['youtube', 'tiktok'],
            scheduledTime: '2024-01-20T14:00:00Z',
            status: 'scheduled',
            mediaType: 'video',
            videoTitle: '10 AI Tools That Will Change Everything',
            estimatedReach: 15000
          },
          {
            id: 2,
            content: 'Behind the scenes of creating viral content with AI 🤖 What would you like to see next?',
            platforms: ['youtube', 'tiktok', 'instagram'],
            scheduledTime: '2024-01-21T18:30:00Z',
            status: 'scheduled',
            mediaType: 'video',
            videoTitle: 'AI Content Creation Secrets',
            estimatedReach: 25000
          }
        ],
        publishedPosts: [
          {
            id: 3,
            content: 'Just published: How to create amazing videos with AI in under 5 minutes! 🚀',
            platforms: ['youtube', 'tiktok'],
            publishedTime: '2024-01-15T12:00:00Z',
            status: 'published',
            performance: {
              views: 45600,
              likes: 2800,
              comments: 156,
              shares: 89,
              engagement_rate: 6.8
            },
            mediaType: 'video',
            videoTitle: '5-Minute AI Video Tutorial'
          },
          {
            id: 4,
            content: 'The future of content creation is here! What do you think about AI-generated videos?',
            platforms: ['youtube'],
            publishedTime: '2024-01-12T16:15:00Z',
            status: 'published',
            performance: {
              views: 28900,
              likes: 1560,
              comments: 78,
              shares: 45,
              engagement_rate: 5.9
            },
            mediaType: 'video',
            videoTitle: 'Future of AI Content'
          }
        ],
        analytics: {
          totalReach: 125000,
          totalEngagement: 8400,
          avgEngagementRate: 6.7,
          topPerformingPost: 3,
          platformStats: [
            { platform: 'youtube', views: 89000, engagement: 5200 },
            { platform: 'tiktok', views: 36000, engagement: 3200 }
          ],
          recentGrowth: {
            followers: 12.5,
            engagement: 8.3,
            reach: 15.7
          }
        },
        drafts: [
          {
            id: 5,
            content: 'Draft: Exploring the latest AI trends in 2024...',
            platforms: ['youtube'],
            lastEdited: '2024-01-18T10:30:00Z',
            mediaType: 'video'
          }
        ]
      };
      
    } catch (error) {
      console.error('Error loading social data:', error);
      toastStore.error('Failed to load social media data');
    } finally {
      isLoading = false;
    }
  }

  async function connectPlatform(platformId) {
    try {
      // Simulate platform connection
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const platform = platforms.find(p => p.id === platformId);
      if (platform) {
        platform.connected = true;
        toastStore.success(`Connected to ${platform.name} successfully!`);
      }
      
      // Refresh data
      await loadSocialData();
    } catch (error) {
      toastStore.error('Failed to connect platform');
    }
  }

  async function disconnectPlatform(platformId) {
    try {
      const platform = platforms.find(p => p.id === platformId);
      if (platform) {
        platform.connected = false;
        toastStore.success(`Disconnected from ${platform.name}`);
      }
      
      // Remove from social data accounts
      socialData.accounts = socialData.accounts.filter(acc => acc.platform !== platformId);
    } catch (error) {
      toastStore.error('Failed to disconnect platform');
    }
  }

  async function schedulePost() {
    if (!newPost.content.trim()) {
      toastStore.error('Please enter content for your post');
      return;
    }
    
    if (newPost.platforms.length === 0) {
      toastStore.error('Please select at least one platform');
      return;
    }

    try {
      isPublishing = true;
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const post = {
        id: Date.now(),
        content: newPost.content,
        platforms: newPost.platforms,
        scheduledTime: newPost.scheduledTime || new Date(Date.now() + 3600000).toISOString(),
        status: 'scheduled',
        mediaType: 'text',
        estimatedReach: Math.floor(Math.random() * 20000) + 5000
      };
      
      socialData.scheduledPosts.unshift(post);
      
      // Reset form
      newPost = {
        content: '',
        platforms: [],
        mediaFiles: [],
        scheduledTime: '',
        tags: '',
        location: ''
      };
      
      toastStore.success('Post scheduled successfully!');
    } catch (error) {
      toastStore.error('Failed to schedule post');
    } finally {
      isPublishing = false;
    }
  }

  async function publishNow(postId) {
    try {
      const post = socialData.scheduledPosts.find(p => p.id === postId);
      if (!post) return;
      
      // Simulate publishing
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      post.status = 'published';
      post.publishedTime = new Date().toISOString();
      post.performance = {
        views: 0,
        likes: 0,
        comments: 0,
        shares: 0,
        engagement_rate: 0
      };
      
      // Move to published
      socialData.publishedPosts.unshift(post);
      socialData.scheduledPosts = socialData.scheduledPosts.filter(p => p.id !== postId);
      
      toastStore.success('Post published successfully!');
    } catch (error) {
      toastStore.error('Failed to publish post');
    }
  }

  async function deletePost(postId, type) {
    try {
      if (type === 'scheduled') {
        socialData.scheduledPosts = socialData.scheduledPosts.filter(p => p.id !== postId);
      } else {
        socialData.publishedPosts = socialData.publishedPosts.filter(p => p.id !== postId);
      }
      
      toastStore.success('Post deleted successfully!');
    } catch (error) {
      toastStore.error('Failed to delete post');
    }
  }

  function togglePlatformSelection(platformId) {
    if (newPost.platforms.includes(platformId)) {
      newPost.platforms = newPost.platforms.filter(p => p !== platformId);
    } else {
      newPost.platforms = [...newPost.platforms, platformId];
    }
  }

  function getPlatformIcon(platformId) {
    const platform = platforms.find(p => p.id === platformId);
    return platform ? platform.icon : '🌐';
  }

  function getPlatformName(platformId) {
    const platform = platforms.find(p => p.id === platformId);
    return platform ? platform.name : platformId;
  }

  function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function formatNumber(num) {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  }

  function getCharacterLimit() {
    if (newPost.platforms.length === 0) return null;
    
    const limits = newPost.platforms.map(platformId => {
      const platform = platforms.find(p => p.id === platformId);
      return platform ? platform.maxLength : 1000;
    });
    
    return Math.min(...limits);
  }

  function copyPostContent(content) {
    navigator.clipboard.writeText(content);
    toastStore.success('Content copied to clipboard!');
  }

  $: characterLimit = getCharacterLimit();
  $: charactersUsed = newPost.content.length;
  $: charactersRemaining = characterLimit ? characterLimit - charactersUsed : null;
</script>

<svelte:head>
  <title>Social Media Management - AutoVideo</title>
</svelte:head>

<div class="max-w-7xl mx-auto space-y-8">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Social Media</h1>
      <p class="mt-2 text-gray-600 dark:text-gray-400">
        Manage and schedule your content across all platforms
      </p>
    </div>
    <div class="mt-4 sm:mt-0 flex items-center space-x-3">
      <button type="button" class="btn-secondary flex items-center" on:click={loadSocialData}>
        <RefreshCw class="w-4 h-4 mr-2" />
        Refresh
      </button>
      <button type="button" class="btn-primary flex items-center">
        <Plus class="w-4 h-4 mr-2" />
        New Post
      </button>
    </div>
  </div>

  {#if isLoading}
    <div class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>
  {:else}
    <!-- Quick Stats -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div class="card">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Reach</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">
                {formatNumber(socialData.analytics.totalReach)}
              </p>
            </div>
            <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
              <Eye class="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <div class="mt-4 flex items-center">
            <TrendingUp class="w-4 h-4 text-green-500 mr-1" />
            <span class="text-sm text-green-600 dark:text-green-400">
              +{socialData.analytics.recentGrowth.reach}% this month
            </span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Engagement</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">
                {formatNumber(socialData.analytics.totalEngagement)}
              </p>
            </div>
            <div class="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
              <Heart class="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
          <div class="mt-4 flex items-center">
            <TrendingUp class="w-4 h-4 text-green-500 mr-1" />
            <span class="text-sm text-green-600 dark:text-green-400">
              +{socialData.analytics.recentGrowth.engagement}% this month
            </span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Engagement Rate</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">
                {socialData.analytics.avgEngagementRate}%
              </p>
            </div>
            <div class="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
              <BarChart3 class="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
          <div class="mt-4 flex items-center">
            <span class="text-sm text-gray-500 dark:text-gray-400">Above industry average</span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Scheduled Posts</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">
                {socialData.scheduledPosts.length}
              </p>
            </div>
            <div class="w-12 h-12 bg-orange-100 dark:bg-orange-900 rounded-lg flex items-center justify-center">
              <Calendar class="w-6 h-6 text-orange-600 dark:text-orange-400" />
            </div>
          </div>
          <div class="mt-4 flex items-center">
            <Clock class="w-4 h-4 text-gray-500 mr-1" />
            <span class="text-sm text-gray-500 dark:text-gray-400">Next in 2 hours</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="grid lg:grid-cols-3 gap-8">
      <!-- Post Creation -->
      <div class="lg:col-span-2 space-y-6">
        <!-- Create New Post -->
        <div class="card">
          <div class="card-header">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Create New Post</h2>
          </div>
          <div class="card-body space-y-6">
            <!-- Content Input -->
            <div>
              <label for="content" class="form-label">Content *</label>
              <textarea
                id="content"
                bind:value={newPost.content}
                placeholder="What's happening? Share your thoughts, updates, or insights..."
                rows="4"
                class="form-input resize-none"
                disabled={isPublishing}
              ></textarea>
              {#if characterLimit}
                <div class="mt-2 flex justify-between text-sm">
                  <span class="text-gray-500 dark:text-gray-400">
                    Characters: {charactersUsed}
                    {#if charactersRemaining !== null}
                      / {characterLimit}
                    {/if}
                  </span>
                  {#if charactersRemaining !== null}
                    <span class="text-{charactersRemaining < 0 ? 'red' : charactersRemaining < 50 ? 'orange' : 'gray'}-500">
                      {charactersRemaining} remaining
                    </span>
                  {/if}
                </div>
              {/if}
            </div>

            <!-- Platform Selection -->
            <div>
              <label class="form-label">Select Platforms *</label>
              <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                {#each platforms.filter(p => p.connected) as platform}
                  <button
                    type="button"
                    class="p-3 border-2 rounded-lg text-center transition-colors {newPost.platforms.includes(platform.id)
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'}"
                    on:click={() => togglePlatformSelection(platform.id)}
                    disabled={isPublishing}
                  >
                    <div class="text-2xl mb-1">{platform.icon}</div>
                    <div class="text-sm font-medium text-gray-900 dark:text-white">{platform.name}</div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">Max: {platform.maxLength}</div>
                  </button>
                {/each}
              </div>
            </div>

            <!-- Schedule Options -->
            <div class="grid md:grid-cols-2 gap-4">
              <div>
                <label for="scheduledTime" class="form-label">Schedule Time (Optional)</label>
                <input
                  id="scheduledTime"
                  type="datetime-local"
                  bind:value={newPost.scheduledTime}
                  class="form-input"
                  disabled={isPublishing}
                />
              </div>
              
              <div>
                <label for="tags" class="form-label">Tags</label>
                <input
                  id="tags"
                  type="text"
                  bind:value={newPost.tags}
                  placeholder="e.g., #AI #VideoCreation #Tutorial"
                  class="form-input"
                  disabled={isPublishing}
                />
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex space-x-3">
              <button
                type="button"
                class="btn-primary flex items-center"
                on:click={schedulePost}
                disabled={isPublishing || !newPost.content.trim() || newPost.platforms.length === 0}
              >
                {#if isPublishing}
                  <RefreshCw class="w-4 h-4 mr-2 animate-spin" />
                  Publishing...
                {:else}
                  {#if newPost.scheduledTime}
                    <Calendar class="w-4 h-4 mr-2" />
                    Schedule Post
                  {:else}
                    <Send class="w-4 h-4 mr-2" />
                    Publish Now
                  {/if}
                {/if}
              </button>
              
              <button type="button" class="btn-secondary flex items-center">
                <FileText class="w-4 h-4 mr-2" />
                Save Draft
              </button>
            </div>
          </div>
        </div>

        <!-- Tabs Navigation -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div class="border-b border-gray-200 dark:border-gray-700">
            <nav class="flex space-x-8 px-6">
              {#each tabs as tab}
                <button
                  type="button"
                  class="py-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === tab.id
                    ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'}"
                  on:click={() => activeTab = tab.id}
                >
                  <div class="flex items-center">
                    <svelte:component this={tab.icon} class="w-4 h-4 mr-2" />
                    {tab.label}
                  </div>
                </button>
              {/each}
            </nav>
          </div>

          <div class="p-6">
            {#if activeTab === 'schedule'}
              <!-- Scheduled Posts -->
              <div class="space-y-4">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Scheduled Posts ({socialData.scheduledPosts.length})
                </h3>
                
                {#if socialData.scheduledPosts.length > 0}
                  {#each socialData.scheduledPosts as post}
                    <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div class="flex items-start justify-between mb-3">
                        <div class="flex-1">
                          <p class="text-gray-900 dark:text-white mb-2">{post.content}</p>
                          <div class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                            <div class="flex items-center">
                              <Calendar class="w-4 h-4 mr-1" />
                              {formatDate(post.scheduledTime)}
                            </div>
                            <div class="flex items-center">
                              <Eye class="w-4 h-4 mr-1" />
                              Est. {formatNumber(post.estimatedReach)} reach
                            </div>
                          </div>
                        </div>
                        <div class="flex items-center space-x-2 ml-4">
                          <button type="button" class="btn-secondary text-sm" on:click={() => publishNow(post.id)}>
                            <Send class="w-4 h-4 mr-1" />
                            Publish Now
                          </button>
                          <button type="button" class="btn-secondary text-sm">
                            <Edit3 class="w-4 h-4 mr-1" />
                            Edit
                          </button>
                          <button type="button" class="text-red-600 hover:text-red-700 p-1" on:click={() => deletePost(post.id, 'scheduled')}>
                            <Trash2 class="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                      
                      <div class="flex items-center justify-between">
                        <div class="flex space-x-2">
                          {#each post.platforms as platformId}
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300">
                              {getPlatformIcon(platformId)} {getPlatformName(platformId)}
                            </span>
                          {/each}
                        </div>
                        
                        <span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200">
                          <Clock class="w-3 h-3 mr-1" />
                          Scheduled
                        </span>
                      </div>
                    </div>
                  {/each}
                {:else}
                  <div class="text-center py-8">
                    <Calendar class="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      No Scheduled Posts
                    </h3>
                    <p class="text-gray-600 dark:text-gray-400">
                      Schedule your first post to get started
                    </p>
                  </div>
                {/if}
              </div>

            {:else if activeTab === 'published'}
              <!-- Published Posts -->
              <div class="space-y-4">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">
                  Published Posts ({socialData.publishedPosts.length})
                </h3>
                
                {#if socialData.publishedPosts.length > 0}
                  {#each socialData.publishedPosts as post}
                    <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div class="flex items-start justify-between mb-3">
                        <div class="flex-1">
                          <p class="text-gray-900 dark:text-white mb-2">{post.content}</p>
                          <div class="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                            <span>{formatDate(post.publishedTime)}</span>
                            {#if post.videoTitle}
                              <span class="flex items-center">
                                <Video class="w-4 h-4 mr-1" />
                                {post.videoTitle}
                              </span>
                            {/if}
                          </div>
                        </div>
                        <div class="flex items-center space-x-2 ml-4">
                          <button type="button" class="text-gray-600 hover:text-gray-700 p-1" on:click={() => copyPostContent(post.content)}>
                            <Copy class="w-4 h-4" />
                          </button>
                          <button type="button" class="text-red-600 hover:text-red-700 p-1" on:click={() => deletePost(post.id, 'published')}>
                            <Trash2 class="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                      
                      <!-- Performance Metrics -->
                      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                        <div class="text-center p-2 bg-white dark:bg-gray-600 rounded">
                          <div class="text-lg font-semibold text-gray-900 dark:text-white">
                            {formatNumber(post.performance.views)}
                          </div>
                          <div class="text-xs text-gray-500 dark:text-gray-400">Views</div>
                        </div>
                        <div class="text-center p-2 bg-white dark:bg-gray-600 rounded">
                          <div class="text-lg font-semibold text-gray-900 dark:text-white">
                            {formatNumber(post.performance.likes)}
                          </div>
                          <div class="text-xs text-gray-500 dark:text-gray-400">Likes</div>
                        </div>
                        <div class="text-center p-2 bg-white dark:bg-gray-600 rounded">
                          <div class="text-lg font-semibold text-gray-900 dark:text-white">
                            {post.performance.comments}
                          </div>
                          <div class="text-xs text-gray-500 dark:text-gray-400">Comments</div>
                        </div>
                        <div class="text-center p-2 bg-white dark:bg-gray-600 rounded">
                          <div class="text-lg font-semibold text-gray-900 dark:text-white">
                            {post.performance.engagement_rate}%
                          </div>
                          <div class="text-xs text-gray-500 dark:text-gray-400">Engagement</div>
                        </div>
                      </div>
                      
                      <div class="flex items-center justify-between">
                        <div class="flex space-x-2">
                          {#each post.platforms as platformId}
                            <span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300">
                              {getPlatformIcon(platformId)} {getPlatformName(platformId)}
                            </span>
                          {/each}
                        </div>
                        
                        <span class="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                          <CheckCircle class="w-3 h-3 mr-1" />
                          Published
                        </span>
                      </div>
                    </div>
                  {/each}
                {:else}
                  <div class="text-center py-8">
                    <CheckCircle class="w-12 h-12 text-gray-400 mx-auto mb-4" />
                    <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
                      No Published Posts
                    </h3>
                    <p class="text-gray-600 dark:text-gray-400">
                      Published posts will appear here
                    </p>
                  </div>
                {/if}
              </div>

            {:else if activeTab === 'analytics'}
              <!-- Analytics -->
              <div class="space-y-6">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white">Analytics Overview</h3>
                
                <!-- Platform Performance -->
                <div class="grid md:grid-cols-2 gap-6">
                  {#each socialData.analytics.platformStats as platform}
                    <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div class="flex items-center justify-between mb-4">
                        <div class="flex items-center">
                          <span class="text-2xl mr-2">{getPlatformIcon(platform.platform)}</span>
                          <h4 class="font-medium text-gray-900 dark:text-white capitalize">{platform.platform}</h4>
                        </div>
                      </div>
                      
                      <div class="grid grid-cols-2 gap-4">
                        <div>
                          <div class="text-2xl font-bold text-gray-900 dark:text-white">
                            {formatNumber(platform.views)}
                          </div>
                          <div class="text-sm text-gray-500 dark:text-gray-400">Total Views</div>
                        </div>
                        <div>
                          <div class="text-2xl font-bold text-gray-900 dark:text-white">
                            {formatNumber(platform.engagement)}
                          </div>
                          <div class="text-sm text-gray-500 dark:text-gray-400">Engagement</div>
                        </div>
                      </div>
                    </div>
                  {/each}
                </div>
              </div>

            {:else if activeTab === 'accounts'}
              <!-- Account Management -->
              <div class="space-y-6">
                <h3 class="text-lg font-medium text-gray-900 dark:text-white">Connected Accounts</h3>
                
                <div class="grid md:grid-cols-2 gap-6">
                  {#each platforms as platform}
                    <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                      <div class="flex items-center justify-between mb-4">
                        <div class="flex items-center">
                          <span class="text-2xl mr-3">{platform.icon}</span>
                          <div>
                            <h4 class="font-medium text-gray-900 dark:text-white">{platform.name}</h4>
                            {#if platform.connected}
                              <p class="text-sm text-green-600 dark:text-green-400">Connected</p>
                            {:else}
                              <p class="text-sm text-gray-500 dark:text-gray-400">Not connected</p>
                            {/if}
                          </div>
                        </div>
                        
                        {#if platform.connected}
                          <button 
                            type="button" 
                            class="btn-secondary text-sm"
                            on:click={() => disconnectPlatform(platform.id)}
                          >
                            Disconnect
                          </button>
                        {:else}
                          <button 
                            type="button" 
                            class="btn-primary text-sm"
                            on:click={() => connectPlatform(platform.id)}
                          >
                            Connect
                          </button>
                        {/if}
                      </div>
                      
                      {#if platform.connected}
                        <div class="space-y-2 text-sm">
                          {#each socialData.accounts.filter(acc => acc.platform === platform.id) as account}
                            <div class="flex items-center justify-between">
                              <span class="text-gray-600 dark:text-gray-400">Username</span>
                              <span class="font-medium text-gray-900 dark:text-white">{account.username}</span>
                            </div>
                            <div class="flex items-center justify-between">
                              <span class="text-gray-600 dark:text-gray-400">Followers</span>
                              <span class="font-medium text-gray-900 dark:text-white">{formatNumber(account.followers)}</span>
                            </div>
                            <div class="flex items-center justify-between">
                              <span class="text-gray-600 dark:text-gray-400">Last Sync</span>
                              <span class="font-medium text-gray-900 dark:text-white">{formatDate(account.lastSync)}</span>
                            </div>
                          {/each}
                        </div>
                      {/if}
                    </div>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- Platform Status -->
        <div class="card">
          <div class="card-header">
            <div class="flex items-center">
              <Globe class="w-5 h-5 text-blue-500 mr-2" />
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Platform Status</h3>
            </div>
          </div>
          <div class="card-body">
            <div class="space-y-3">
              {#each platforms.slice(0, 4) as platform}
                <div class="flex items-center justify-between">
                  <div class="flex items-center">
                    <span class="text-lg mr-2">{platform.icon}</span>
                    <span class="text-sm text-gray-900 dark:text-white">{platform.name}</span>
                  </div>
                  <div class="flex items-center">
                    {#if platform.connected}
                      <CheckCircle class="w-4 h-4 text-green-500" />
                    {:else}
                      <XCircle class="w-4 h-4 text-gray-400" />
                    {/if}
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </div>

        <!-- Content Calendar -->
        <div class="card">
          <div class="card-header">
            <div class="flex items-center">
              <Calendar class="w-5 h-5 text-purple-500 mr-2" />
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Upcoming Posts</h3>
            </div>
          </div>
          <div class="card-body">
            {#if socialData.scheduledPosts.length > 0}
              <div class="space-y-3">
                {#each socialData.scheduledPosts.slice(0, 3) as post}
                  <div class="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div class="flex items-center justify-between mb-2">
                      <span class="text-sm font-medium text-gray-900 dark:text-white">
                        {formatDate(post.scheduledTime)}
                      </span>
                      <div class="flex space-x-1">
                        {#each post.platforms.slice(0, 2) as platformId}
                          <span class="text-xs">{getPlatformIcon(platformId)}</span>
                        {/each}
                      </div>
                    </div>
                    <p class="text-xs text-gray-600 dark:text-gray-300 line-clamp-2">
                      {post.content}
                    </p>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="text-center py-4">
                <Calendar class="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  No upcoming posts
                </p>
              </div>
            {/if}
          </div>
        </div>

        <!-- Best Times to Post -->
        <div class="card">
          <div class="card-header">
            <div class="flex items-center">
              <Clock class="w-5 h-5 text-green-500 mr-2" />
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Best Times to Post</h3>
            </div>
          </div>
          <div class="card-body">
            <div class="space-y-3">
              {#each [
                { time: '9:00 AM', engagement: 92, platform: 'youtube' },
                { time: '1:00 PM', engagement: 87, platform: 'tiktok' },
                { time: '6:00 PM', engagement: 94, platform: 'instagram' },
                { time: '8:00 PM', engagement: 89, platform: 'twitter' }
              ] as timeSlot}
                <div class="flex items-center justify-between">
                  <div class="flex items-center">
                    <span class="text-sm mr-2">{getPlatformIcon(timeSlot.platform)}</span>
                    <span class="text-sm text-gray-600 dark:text-gray-400">{timeSlot.time}</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <div class="w-16 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                      <div class="bg-green-600 h-2 rounded-full" style="width: {timeSlot.engagement}%"></div>
                    </div>
                    <span class="text-sm font-medium text-gray-900 dark:text-white w-8">
                      {timeSlot.engagement}
                    </span>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </div>
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