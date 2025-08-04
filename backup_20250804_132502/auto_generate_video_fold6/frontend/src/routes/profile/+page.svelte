<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { apiClient } from '$lib/api/client';
  import { toastStore } from '$lib/stores/toast';
  import { LoadingSpinner } from '$lib/components/ui';
  
  // Import refactored components
  import ProfileHeader from '$lib/components/profile/ProfileHeader.svelte';
  import ContentTabs from '$lib/components/profile/ContentTabs.svelte';
  import VideoGrid from '$lib/components/profile/VideoGrid.svelte';
  import AchievementsList from '$lib/components/profile/AchievementsList.svelte';

  let isLoading = true;
  let activeTab = 'videos';
  let viewMode = 'grid';
  let isOwnProfile = true;
  let isFollowing = false;
  let isFollowLoading = false;

  let profile = {
    user: {},
    videos: [],
    collections: [],
    achievements: [],
    activityFeed: [],
    stats: {}
  };

  onMount(async () => {
    await loadProfile();
  });

  async function loadProfile() {
    try {
      isLoading = true;
      
      // Simulate API call with mock data
      await new Promise(resolve => setTimeout(resolve, 1200));
      
      profile = {
        // User Profile Data
        name: 'Alex Johnson',
        username: 'alex_creates',
        title: 'Content Creator & AI Enthusiast',
        bio: 'Passionate about creating engaging content using AI tools. Sharing tips, tutorials, and behind-the-scenes insights from my creative journey. Always exploring new technologies and pushing creative boundaries.',
        avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face',
        coverImage: 'https://images.unsplash.com/photo-1557804506-669a67965ba0?w=1200&h=400&fit=crop',
        location: 'San Francisco, CA',
        website: 'https://alexcreates.io',
        email: 'alex@alexcreates.io',
        joinDate: '2023-03-15T00:00:00Z',
        verified: true,
        
        // Statistics
        stats: {
          videos: 24,
          followers: 15600,
          following: 892,
          totalViews: 287000,
          totalLikes: 12400
        },

        // Videos
        videos: [
          {
            id: 1,
            title: 'AI Video Generation: Complete Beginner\'s Guide',
            thumbnail: 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400&h=225&fit=crop',
            duration: 720,
            views: 25600,
            likes: 1200,
            comments: 89,
            status: 'published',
            createdAt: '2024-01-15T10:30:00Z'
          },
          {
            id: 2,
            title: 'Creating Viral Content with AI Tools',
            thumbnail: 'https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=400&h=225&fit=crop',
            duration: 540,
            views: 18900,
            likes: 950,
            comments: 67,
            status: 'published',
            createdAt: '2024-01-10T14:20:00Z'
          },
          {
            id: 3,
            title: 'Behind the Scenes: My Content Creation Setup',
            thumbnail: 'https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?w=400&h=225&fit=crop',
            duration: 480,
            views: 12300,
            likes: 720,
            comments: 45,
            status: 'published',
            createdAt: '2024-01-05T09:15:00Z'
          },
          {
            id: 4,
            title: 'Advanced AI Editing Techniques',
            thumbnail: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400&h=225&fit=crop',
            duration: 0,
            views: 0,
            likes: 0,
            comments: 0,
            status: 'processing',
            createdAt: '2024-01-20T16:45:00Z'
          }
        ],

        // Collections
        collections: [
          {
            id: 1,
            name: 'AI Tutorials',
            description: 'Complete guide to AI-powered content creation',
            thumbnail: 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=300&h=200&fit=crop',
            videoCount: 8,
            isPublic: true,
            createdAt: '2023-12-01T00:00:00Z'
          },
          {
            id: 2,
            name: 'Behind the Scenes',
            description: 'My creative process and setup tours',
            thumbnail: 'https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?w=300&h=200&fit=crop',
            videoCount: 5,
            isPublic: true,
            createdAt: '2023-11-15T00:00:00Z'
          }
        ],

        // Achievements
        achievements: [
          {
            id: 1,
            type: 'first-video',
            title: 'First Upload',
            description: 'Published your first video',
            rarity: 'common',
            points: 100,
            unlocked: true,
            unlockedAt: '2023-03-20T00:00:00Z'
          },
          {
            id: 2,
            type: 'viral-hit',
            title: 'Viral Sensation',
            description: 'Achieved over 10K views on a single video',
            rarity: 'rare',
            points: 500,
            unlocked: true,
            unlockedAt: '2023-08-15T00:00:00Z'
          },
          {
            id: 3,
            type: 'milestone-views',
            title: 'View Master',
            description: 'Reached 100K total views across all videos',
            rarity: 'epic',
            points: 1000,
            unlocked: true,
            unlockedAt: '2023-12-01T00:00:00Z'
          },
          {
            id: 4,
            type: 'consistency',
            title: 'Consistent Creator',
            description: 'Upload at least one video per week for a month',
            rarity: 'rare',
            points: 750,
            unlocked: false,
            progress: {
              current: 3,
              target: 4
            }
          },
          {
            id: 5,
            type: 'milestone-subscriber',
            title: 'Subscriber Milestone',
            description: 'Reach 50K subscribers',
            rarity: 'legendary',
            points: 2500,
            unlocked: false,
            progress: {
              current: 15600,
              target: 50000
            }
          }
        ],

        // Activity Feed
        activityFeed: [
          {
            id: 1,
            type: 'video_published',
            content: 'Published "AI Video Generation: Complete Beginner\'s Guide"',
            timestamp: '2024-01-15T10:30:00Z'
          },
          {
            id: 2,
            type: 'achievement_unlocked',
            content: 'Unlocked "View Master" achievement',
            timestamp: '2023-12-01T00:00:00Z'
          },
          {
            id: 3,
            type: 'milestone_reached',
            content: 'Reached 15K subscribers',
            timestamp: '2023-11-20T00:00:00Z'
          }
        ]
      };
    } catch (error) {
      toastStore.error('Failed to load profile');
      console.error('Error loading profile:', error);
    } finally {
      isLoading = false;
    }
  }

  // Event handlers
  async function handleFollow() {
    try {
      isFollowLoading = true;
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      isFollowing = true;
      profile.stats.followers += 1;
      toastStore.success('Following successfully!');
    } catch (error) {
      toastStore.error('Failed to follow user');
    } finally {
      isFollowLoading = false;
    }
  }

  async function handleUnfollow() {
    try {
      isFollowLoading = true;
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      isFollowing = false;
      profile.stats.followers -= 1;
      toastStore.success('Unfollowed successfully!');
    } catch (error) {
      toastStore.error('Failed to unfollow user');
    } finally {
      isFollowLoading = false;
    }
  }

  function handleEdit() {
    goto('/settings');
  }

  function handleShare() {
    navigator.clipboard.writeText(window.location.href);
    toastStore.success('Profile link copied to clipboard!');
  }

  function handleMessage() {
    toastStore.info('Messaging feature coming soon!');
  }

  function handleChangeAvatar() {
    toastStore.info('Avatar upload feature coming soon!');
  }

  function handleChangeCover() {
    toastStore.info('Cover image upload feature coming soon!');
  }

  function handleTabChange(event) {
    activeTab = event.detail;
  }

  function handleViewModeChange(event) {
    viewMode = event.detail;
  }

  function handleVideoClick(event) {
    const video = event.detail;
    toastStore.info(`Would open video: ${video.title}`);
  }

  function handleVideoAction(event) {
    const { video, action } = event.detail;
    toastStore.info(`${action} action for video: ${video.title}`);
  }

  function handleSearch(event) {
    console.log('Search:', event.detail);
  }

  function handleToggleFilters(event) {
    console.log('Toggle filters:', event.detail);
  }

  // Get current tab content
  $: currentContent = (() => {
    switch (activeTab) {
      case 'videos':
        return profile.videos;
      case 'collections':
        return profile.collections;
      case 'achievements':
        return profile.achievements;
      case 'activity':
        return profile.activityFeed;
      default:
        return [];
    }
  })();
</script>

<svelte:head>
  <title>{profile.name ? `${profile.name} (@${profile.username}) - AutoVideo` : 'Profile - AutoVideo'}</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  {#if isLoading}
    <LoadingSpinner size="lg" text="Loading profile..." fullscreen />
  {:else}
    <div class="max-w-6xl mx-auto px-4 py-8">
      <!-- Profile Header -->
      <div class="mb-8">
        <ProfileHeader
          {profile}
          {isOwnProfile}
          {isFollowing}
          isLoading={isFollowLoading}
          on:follow={handleFollow}
          on:unfollow={handleUnfollow}
          on:edit={handleEdit}
          on:share={handleShare}
          on:message={handleMessage}
          on:changeAvatar={handleChangeAvatar}
          on:changeCover={handleChangeCover}
        />
      </div>

      <!-- Content Tabs -->
      <ContentTabs
        {activeTab}
        {viewMode}
        {isOwnProfile}
        on:tabChange={handleTabChange}
        on:viewModeChange={handleViewModeChange}
        on:search={handleSearch}
        on:toggleFilters={handleToggleFilters}
      >
        <!-- Tab content based on active tab -->
        {#if activeTab === 'videos'}
          <VideoGrid
            videos={currentContent}
            {viewMode}
            on:videoClick={handleVideoClick}
            on:videoAction={handleVideoAction}
          />

        {:else if activeTab === 'collections'}
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each currentContent as collection}
              <div class="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow cursor-pointer">
                <div class="aspect-video bg-gray-100 dark:bg-gray-700 rounded-t-lg overflow-hidden">
                  {#if collection.thumbnail}
                    <img
                      src={collection.thumbnail}
                      alt={collection.name}
                      class="w-full h-full object-cover"
                    />
                  {/if}
                </div>
                <div class="p-4">
                  <h3 class="font-medium text-gray-900 dark:text-white mb-2">
                    {collection.name}
                  </h3>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {collection.description}
                  </p>
                  <div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
                    <span>{collection.videoCount} videos</span>
                    <span>{collection.isPublic ? 'Public' : 'Private'}</span>
                  </div>
                </div>
              </div>
            {/each}
          </div>

        {:else if activeTab === 'achievements'}
          <AchievementsList achievements={currentContent} />

        {:else if activeTab === 'activity'}
          <div class="space-y-4">
            {#each currentContent as activity}
              <div class="flex items-start space-x-4 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                <div class="w-2 h-2 bg-primary-500 rounded-full mt-2"></div>
                <div class="flex-1">
                  <p class="text-gray-900 dark:text-white">
                    {activity.content}
                  </p>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {new Date(activity.timestamp).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </ContentTabs>
    </div>
  {/if}
</div>