<script>
  import { onMount } from 'svelte';
  import { apiClient } from '$lib/api/client';
  import { toastStore } from '$lib/stores/toast';
  import { LoadingSpinner } from '$lib/components/ui';
  
  // Import refactored components
  import PlatformConnections from '$lib/components/social/PlatformConnections.svelte';
  import PostScheduler from '$lib/components/social/PostScheduler.svelte';
  import AnalyticsOverview from '$lib/components/social/AnalyticsOverview.svelte';
  import PostsList from '$lib/components/social/PostsList.svelte';

  let isLoading = true;
  let isPublishing = false;
  let activeTab = 'schedule';
  
  let socialData = {
    platforms: [],
    scheduledPosts: [],
    publishedPosts: [],
    drafts: [],
    analytics: {}
  };

  const tabs = [
    { id: 'schedule', name: 'Schedule', icon: '📅' },
    { id: 'published', name: 'Published', icon: '📢' },
    { id: 'analytics', name: 'Analytics', icon: '📊' },
    { id: 'platforms', name: 'Platforms', icon: '🔗' }
  ];

  onMount(async () => {
    await loadSocialData();
  });

  async function loadSocialData() {
    try {
      isLoading = true;
      
      // Simulate API calls with mock data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      socialData = {
        platforms: [
          {
            id: 1,
            type: 'youtube',
            username: 'mychannel',
            status: 'connected',
            followers: 15600,
            lastSync: '2024-01-20T10:30:00Z'
          },
          {
            id: 2,
            type: 'tiktok',
            username: 'myaccount',
            status: 'connected',
            followers: 8300,
            lastSync: '2024-01-20T09:15:00Z'
          },
          {
            id: 3,
            type: 'instagram',
            username: 'myinsta',
            status: 'error',
            followers: 12400,
            lastSync: '2024-01-19T16:45:00Z'
          }
        ],
        scheduledPosts: [
          {
            id: 1,
            content: 'Exciting new video about AI automation coming tomorrow! 🚀 #AI #TechTips',
            platforms: ['youtube', 'twitter'],
            scheduledTime: '2024-01-21T14:00:00Z',
            status: 'scheduled',
            estimatedReach: 15000
          },
          {
            id: 2,
            content: 'Quick tutorial on optimizing your workflow 💡',
            platforms: ['tiktok', 'instagram'],
            scheduledTime: '2024-01-21T18:30:00Z',
            status: 'scheduled',
            estimatedReach: 8500
          }
        ],
        publishedPosts: [
          {
            id: 3,
            content: 'Just published a comprehensive guide on social media automation! Check it out 👆',
            platforms: ['youtube', 'twitter', 'linkedin'],
            scheduledTime: '2024-01-20T12:00:00Z',
            status: 'published',
            metrics: {
              views: 12500,
              likes: 890,
              comments: 156,
              shares: 234
            }
          }
        ],
        drafts: [
          {
            id: 4,
            content: 'Draft post about upcoming features...',
            platforms: ['youtube'],
            status: 'draft',
            lastModified: '2024-01-20T15:30:00Z'
          }
        ],
        analytics: {
          totalPosts: 45,
          totalViews: 125000,
          totalLikes: 8900,
          totalComments: 1200,
          postsChange: 12,
          viewsChange: 25,
          likesChange: 18,
          commentsChange: -5,
          platformPerformance: [
            { name: 'YouTube', icon: '🎥', posts: 15, engagement: 45600, performance: 85 },
            { name: 'TikTok', icon: '🎵', posts: 12, engagement: 32100, performance: 72 },
            { name: 'Instagram', icon: '📷', posts: 18, engagement: 28900, performance: 68 }
          ]
        }
      };
    } catch (error) {
      toastStore.error('Failed to load social media data');
      console.error('Error loading social data:', error);
    } finally {
      isLoading = false;
    }
  }

  // Event handlers
  async function handleSchedulePost(event) {
    const postData = event.detail;
    try {
      isPublishing = true;
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const newPost = {
        id: Date.now(),
        ...postData,
        status: postData.scheduledTime ? 'scheduled' : 'published',
        estimatedReach: Math.floor(Math.random() * 20000) + 5000
      };
      
      if (postData.scheduledTime) {
        socialData.scheduledPosts = [newPost, ...socialData.scheduledPosts];
        toastStore.success('Post scheduled successfully!');
      } else {
        socialData.publishedPosts = [newPost, ...socialData.publishedPosts];
        toastStore.success('Post published successfully!');
      }
    } catch (error) {
      toastStore.error('Failed to schedule post');
    } finally {
      isPublishing = false;
    }
  }

  async function handlePublishNow(event) {
    await handleSchedulePost(event);
  }

  function handleConnectPlatform(event) {
    console.log('Connect platform:', event.detail);
    toastStore.info('Platform connection feature coming soon!');
  }

  function handleDisconnectPlatform(event) {
    const platform = event.detail;
    socialData.platforms = socialData.platforms.filter(p => p.id !== platform.id);
    toastStore.success(`Disconnected from ${platform.type}`);
  }

  function handleEditPost(event) {
    console.log('Edit post:', event.detail);
    toastStore.info('Edit post feature coming soon!');
  }

  function handleDeletePost(event) {
    const post = event.detail;
    if (post.status === 'scheduled') {
      socialData.scheduledPosts = socialData.scheduledPosts.filter(p => p.id !== post.id);
    } else if (post.status === 'published') {
      socialData.publishedPosts = socialData.publishedPosts.filter(p => p.id !== post.id);
    }
    toastStore.success('Post deleted successfully');
  }

  function handlePausePost(event) {
    const post = event.detail;
    post.status = 'paused';
    socialData.scheduledPosts = [...socialData.scheduledPosts];
    toastStore.success('Post paused');
  }

  function handleResumePost(event) {
    const post = event.detail;
    post.status = 'scheduled';
    socialData.scheduledPosts = [...socialData.scheduledPosts];
    toastStore.success('Post resumed');
  }
</script>

<svelte:head>
  <title>Social Media Management - AutoVideo</title>
</svelte:head>

<div class="p-6 max-w-7xl mx-auto">
  <!-- Header -->
  <div class="mb-8">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Social Media</h1>
    <p class="mt-2 text-gray-600 dark:text-gray-400">
      Manage your social media presence across all platforms
    </p>
  </div>

  {#if isLoading}
    <LoadingSpinner size="lg" text="Loading social media data..." />
  {:else}
    <!-- Tabs -->
    <div class="mb-6">
      <div class="border-b border-gray-200 dark:border-gray-700">
        <nav class="-mb-px flex space-x-8">
          {#each tabs as tab}
            <button
              class="py-2 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === tab.id
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'}"
              on:click={() => activeTab = tab.id}
            >
              <span class="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          {/each}
        </nav>
      </div>
    </div>

    <!-- Tab Content -->
    <div class="space-y-6">
      {#if activeTab === 'schedule'}
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div class="space-y-6">
            <PostScheduler
              platforms={socialData.platforms}
              {isPublishing}
              on:schedule={handleSchedulePost}
              on:publishNow={handlePublishNow}
            />
          </div>
          <div>
            <PostsList
              posts={socialData.scheduledPosts}
              type="scheduled"
              on:edit={handleEditPost}
              on:delete={handleDeletePost}
              on:pause={handlePausePost}
              on:resume={handleResumePost}
            />
          </div>
        </div>

      {:else if activeTab === 'published'}
        <PostsList
          posts={socialData.publishedPosts}
          type="published"
          on:delete={handleDeletePost}
          on:view={(e) => console.log('View post:', e.detail)}
        />

      {:else if activeTab === 'analytics'}
        <div class="space-y-6">
          <AnalyticsOverview analytics={socialData.analytics} />
          
          <!-- Additional analytics content can go here -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <!-- Engagement Chart Placeholder -->
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Engagement Trends
              </h3>
              <div class="h-64 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center">
                <p class="text-gray-500 dark:text-gray-400">Chart placeholder</p>
              </div>
            </div>
            
            <!-- Top Performing Posts -->
            <div class="bg-white dark:bg-gray-800 p-6 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Top Performing Posts
              </h3>
              <div class="space-y-3">
                {#each socialData.publishedPosts.slice(0, 3) as post}
                  <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <div class="flex-1 min-w-0">
                      <p class="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {post.content.substring(0, 40)}...
                      </p>
                    </div>
                    <div class="text-sm text-gray-500 dark:text-gray-400">
                      {post.metrics?.views || 0} views
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          </div>
        </div>

      {:else if activeTab === 'platforms'}
        <PlatformConnections
          platforms={socialData.platforms}
          on:connect={handleConnectPlatform}
          on:disconnect={handleDisconnectPlatform}
          on:settings={(e) => console.log('Platform settings:', e.detail)}
          on:add={() => toastStore.info('Add platform feature coming soon!')}
        />
      {/if}
    </div>
  {/if}
</div>