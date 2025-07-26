<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { apiClient } from '$lib/api/client';
  import { toastStore } from '$lib/stores/toast';
  import { 
    User,
    MapPin,
    Globe,
    Calendar,
    Mail,
    Edit3,
    Share2,
    MoreHorizontal,
    Play,
    Eye,
    Heart,
    MessageCircle,
    Download,
    Grid,
    List,
    Filter,
    Search,
    Trophy,
    Star,
    Clock,
    Video,
    Image,
    Mic,
    Settings,
    Camera,
    Users,
    TrendingUp,
    Award,
    Bookmark,
    Copy,
    ExternalLink,
    UserPlus,
    UserMinus,
    Flag
  } from 'lucide-svelte';

  let isLoading = true;
  let activeTab = 'videos';
  let viewMode = 'grid';
  let isOwnProfile = true; // In a real app, this would be determined by comparing user IDs
  let isFollowing = false;

  let profile = {
    user: {},
    stats: {},
    videos: [],
    collections: [],
    activity: [],
    achievements: []
  };

  const tabs = [
    { id: 'videos', label: 'Videos', icon: Video, count: 0 },
    { id: 'collections', label: 'Collections', icon: Bookmark, count: 0 },
    { id: 'activity', label: 'Activity', icon: Clock, count: 0 },
    { id: 'achievements', label: 'Achievements', icon: Trophy, count: 0 }
  ];

  onMount(async () => {
    await loadProfile();
  });

  async function loadProfile() {
    try {
      isLoading = true;
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      profile = {
        user: {
          id: 1,
          name: 'Alex Johnson',
          username: 'alexj_creator',
          email: 'alex.johnson@example.com',
          bio: 'Content creator passionate about AI and technology. Creating amazing videos with AutoVideo! 🎥✨',
          avatar: '/api/placeholder/120/120',
          cover: '/api/placeholder/800/200',
          location: 'San Francisco, CA',
          website: 'https://alexjohnson.dev',
          joinDate: '2023-06-15',
          verified: true,
          followers: 12500,
          following: 345,
          totalViews: 1250000,
          totalVideos: 89
        },
        stats: {
          totalViews: 1250000,
          totalLikes: 89200,
          totalComments: 5600,
          avgEngagement: 7.2,
          topVideo: {
            title: '10 AI Tools That Will Change Everything',
            views: 245600
          },
          monthlyGrowth: {
            views: 23.5,
            followers: 12.7,
            engagement: 18.3
          }
        },
        videos: [
          {
            id: 1,
            title: '10 AI Tools That Will Change Everything',
            thumbnail: '/api/placeholder/300/200',
            duration: 185,
            views: 245600,
            likes: 18900,
            comments: 892,
            publishedAt: '2024-01-10T14:30:00Z',
            status: 'published',
            visibility: 'public',
            tags: ['AI', 'Technology', 'Tutorial']
          },
          {
            id: 2,
            title: 'Secret TikTok Algorithm Hack',
            thumbnail: '/api/placeholder/300/200',
            duration: 58,
            views: 198300,
            likes: 24100,
            comments: 567,
            publishedAt: '2024-01-08T16:15:00Z',
            status: 'published',
            visibility: 'public',
            tags: ['TikTok', 'Algorithm', 'Tips']
          },
          {
            id: 3,
            title: 'Remote Work Productivity Tips',
            thumbnail: '/api/placeholder/300/200',
            duration: 142,
            views: 156700,
            likes: 11200,
            comments: 423,
            publishedAt: '2024-01-05T10:20:00Z',
            status: 'published',
            visibility: 'public',
            tags: ['Productivity', 'Remote Work', 'Tips']
          },
          {
            id: 4,
            title: 'How I Create Viral Content',
            thumbnail: '/api/placeholder/300/200',
            duration: 267,
            views: 134500,
            likes: 9800,
            comments: 334,
            publishedAt: '2024-01-03T12:45:00Z',
            status: 'published',
            visibility: 'public',
            tags: ['Content Creation', 'Viral', 'Strategy']
          },
          {
            id: 5,
            title: 'AI Voice Cloning Tutorial',
            thumbnail: '/api/placeholder/300/200',
            duration: 198,
            views: 89200,
            likes: 6700,
            comments: 289,
            publishedAt: '2024-01-01T09:30:00Z',
            status: 'published',
            visibility: 'public',
            tags: ['AI', 'Voice', 'Tutorial']
          },
          {
            id: 6,
            title: 'Behind the Scenes - Studio Setup',
            thumbnail: '/api/placeholder/300/200',
            duration: 234,
            views: 67800,
            likes: 4500,
            comments: 156,
            publishedAt: '2023-12-28T15:20:00Z',
            status: 'published',
            visibility: 'public',
            tags: ['Behind The Scenes', 'Setup', 'Studio']
          }
        ],
        collections: [
          {
            id: 1,
            name: 'AI Tutorials',
            description: 'Complete collection of AI-related tutorials and tips',
            thumbnail: '/api/placeholder/300/200',
            videoCount: 12,
            totalViews: 456700,
            createdAt: '2023-11-15T10:00:00Z',
            isPublic: true
          },
          {
            id: 2,
            name: 'Content Creation Tips',
            description: 'Everything you need to know about creating viral content',
            thumbnail: '/api/placeholder/300/200',
            videoCount: 8,
            totalViews: 234500,
            createdAt: '2023-10-20T14:30:00Z',
            isPublic: true
          },
          {
            id: 3,
            name: 'Behind the Scenes',
            description: 'Personal insights and behind-the-scenes content',
            thumbnail: '/api/placeholder/300/200',
            videoCount: 5,
            totalViews: 89200,
            createdAt: '2023-09-10T16:45:00Z',
            isPublic: false
          }
        ],
        activity: [
          {
            id: 1,
            type: 'video_published',
            action: 'Published new video',
            target: '10 AI Tools That Will Change Everything',
            timestamp: '2024-01-10T14:30:00Z',
            metadata: { views: 245600, likes: 18900 }
          },
          {
            id: 2,
            type: 'milestone',
            action: 'Reached 10K followers',
            target: null,
            timestamp: '2024-01-08T12:00:00Z',
            metadata: { followers: 10000 }
          },
          {
            id: 3,
            type: 'video_viral',
            action: 'Video went viral',
            target: 'Secret TikTok Algorithm Hack',
            timestamp: '2024-01-08T20:15:00Z',
            metadata: { views: 100000 }
          },
          {
            id: 4,
            type: 'collaboration',
            action: 'Collaborated with TechReviewer',
            target: 'AI Tools Review',
            timestamp: '2024-01-05T16:30:00Z',
            metadata: {}
          },
          {
            id: 5,
            type: 'achievement',
            action: 'Earned "Content Creator" badge',
            target: null,
            timestamp: '2024-01-03T09:45:00Z',
            metadata: {}
          }
        ],
        achievements: [
          {
            id: 1,
            name: 'Content Creator',
            description: 'Published 50+ videos',
            icon: '🎥',
            unlockedAt: '2024-01-03T09:45:00Z',
            rarity: 'common'
          },
          {
            id: 2,
            name: 'Viral Sensation',
            description: 'Created a video with 100K+ views',
            icon: '🔥',
            unlockedAt: '2024-01-08T20:15:00Z',
            rarity: 'rare'
          },
          {
            id: 3,
            name: 'Community Builder',
            description: 'Reached 10K followers',
            icon: '👥',
            unlockedAt: '2024-01-08T12:00:00Z',
            rarity: 'epic'
          },
          {
            id: 4,
            name: 'AI Pioneer',
            description: 'Created 20+ AI-related videos',
            icon: '🤖',
            unlockedAt: '2023-12-15T14:20:00Z',
            rarity: 'legendary'
          },
          {
            id: 5,
            name: 'Consistency King',
            description: 'Posted videos for 30 consecutive days',
            icon: '📅',
            unlockedAt: '2023-11-30T23:59:00Z',
            rarity: 'rare'
          }
        ]
      };

      // Update tab counts
      tabs[0].count = profile.videos.length;
      tabs[1].count = profile.collections.length;
      tabs[2].count = profile.activity.length;
      tabs[3].count = profile.achievements.length;
      
    } catch (error) {
      console.error('Error loading profile:', error);
      toastStore.error('Failed to load profile');
    } finally {
      isLoading = false;
    }
  }

  async function followUser() {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      isFollowing = !isFollowing;
      
      if (isFollowing) {
        profile.user.followers++;
        toastStore.success('Now following ' + profile.user.name);
      } else {
        profile.user.followers--;
        toastStore.success('Unfollowed ' + profile.user.name);
      }
    } catch (error) {
      toastStore.error('Failed to update follow status');
    }
  }

  function shareProfile() {
    const url = `https://autovideo.app/profile/${profile.user.username}`;
    navigator.clipboard.writeText(url);
    toastStore.success('Profile link copied to clipboard!');
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
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  }

  function formatRelativeDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now - date) / (1000 * 60 * 60 * 24));
    
    if (diffInDays === 0) return 'Today';
    if (diffInDays === 1) return 'Yesterday';
    if (diffInDays < 7) return `${diffInDays} days ago`;
    if (diffInDays < 30) return `${Math.floor(diffInDays / 7)} weeks ago`;
    if (diffInDays < 365) return `${Math.floor(diffInDays / 30)} months ago`;
    return `${Math.floor(diffInDays / 365)} years ago`;
  }

  function getRarityColor(rarity) {
    switch (rarity) {
      case 'common': return 'text-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-gray-300';
      case 'rare': return 'text-blue-600 bg-blue-100 dark:bg-blue-900 dark:text-blue-300';
      case 'epic': return 'text-purple-600 bg-purple-100 dark:bg-purple-900 dark:text-purple-300';
      case 'legendary': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-300';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-gray-300';
    }
  }

  function getActivityIcon(type) {
    switch (type) {
      case 'video_published': return Video;
      case 'milestone': return Trophy;
      case 'video_viral': return TrendingUp;
      case 'collaboration': return Users;
      case 'achievement': return Award;
      default: return Clock;
    }
  }

  function goToVideo(videoId) {
    // In a real app, this would navigate to the video page
    toastStore.info(`Navigating to video ${videoId}`);
  }

  function editProfile() {
    goto('/settings?tab=profile');
  }
</script>

<svelte:head>
  <title>{profile.user.name || 'Profile'} - AutoVideo</title>
</svelte:head>

<div class="max-w-7xl mx-auto space-y-8">
  {#if isLoading}
    <div class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>
  {:else}
    <!-- Profile Header -->
    <div class="relative">
      <!-- Cover Image -->
      <div class="h-48 md:h-64 bg-gradient-to-r from-primary-500 to-purple-600 rounded-lg overflow-hidden">
        {#if profile.user.cover}
          <img src={profile.user.cover} alt="Cover" class="w-full h-full object-cover" />
        {/if}
      </div>
      
      <!-- Profile Info -->
      <div class="relative px-6 pb-6">
        <!-- Avatar -->
        <div class="flex flex-col sm:flex-row sm:items-end sm:space-x-6 -mt-16 sm:-mt-20">
          <div class="relative">
            <div class="w-32 h-32 bg-white dark:bg-gray-800 rounded-full p-2 shadow-lg">
              <div class="w-full h-full bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                {#if profile.user.avatar}
                  <img src={profile.user.avatar} alt={profile.user.name} class="w-full h-full object-cover" />
                {:else}
                  <div class="w-full h-full flex items-center justify-center">
                    <User class="w-16 h-16 text-gray-400" />
                  </div>
                {/if}
              </div>
            </div>
            {#if profile.user.verified}
              <div class="absolute bottom-2 right-2 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <Star class="w-4 h-4 text-white" />
              </div>
            {/if}
          </div>
          
          <!-- Profile Details -->
          <div class="flex-1 mt-4 sm:mt-0">
            <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h1 class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white flex items-center">
                  {profile.user.name}
                  {#if profile.user.verified}
                    <Star class="w-6 h-6 text-blue-500 ml-2" />
                  {/if}
                </h1>
                <p class="text-lg text-gray-600 dark:text-gray-400">@{profile.user.username}</p>
              </div>
              
              <!-- Action Buttons -->
              <div class="flex items-center space-x-3 mt-4 sm:mt-0">
                {#if isOwnProfile}
                  <button type="button" class="btn-secondary flex items-center" on:click={editProfile}>
                    <Edit3 class="w-4 h-4 mr-2" />
                    Edit Profile
                  </button>
                {:else}
                  <button 
                    type="button" 
                    class="btn-primary flex items-center"
                    on:click={followUser}
                  >
                    {#if isFollowing}
                      <UserMinus class="w-4 h-4 mr-2" />
                      Unfollow
                    {:else}
                      <UserPlus class="w-4 h-4 mr-2" />
                      Follow
                    {/if}
                  </button>
                {/if}
                
                <button type="button" class="btn-secondary flex items-center" on:click={shareProfile}>
                  <Share2 class="w-4 h-4 mr-2" />
                  Share
                </button>
                
                <div class="relative">
                  <button type="button" class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                    <MoreHorizontal class="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
            
            <!-- Bio -->
            {#if profile.user.bio}
              <p class="mt-4 text-gray-700 dark:text-gray-300 max-w-2xl">
                {profile.user.bio}
              </p>
            {/if}
            
            <!-- Meta Info -->
            <div class="mt-4 flex flex-wrap items-center space-x-6 text-sm text-gray-600 dark:text-gray-400">
              {#if profile.user.location}
                <div class="flex items-center">
                  <MapPin class="w-4 h-4 mr-1" />
                  {profile.user.location}
                </div>
              {/if}
              
              {#if profile.user.website}
                <a href={profile.user.website} target="_blank" class="flex items-center hover:text-primary-600 dark:hover:text-primary-400">
                  <Globe class="w-4 h-4 mr-1" />
                  {profile.user.website.replace('https://', '')}
                  <ExternalLink class="w-3 h-3 ml-1" />
                </a>
              {/if}
              
              <div class="flex items-center">
                <Calendar class="w-4 h-4 mr-1" />
                Joined {formatDate(profile.user.joinDate)}
              </div>
            </div>
            
            <!-- Stats -->
            <div class="mt-4 flex items-center space-x-6">
              <div class="text-center">
                <div class="text-xl font-bold text-gray-900 dark:text-white">
                  {formatNumber(profile.user.followers)}
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-400">Followers</div>
              </div>
              
              <div class="text-center">
                <div class="text-xl font-bold text-gray-900 dark:text-white">
                  {formatNumber(profile.user.following)}
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-400">Following</div>
              </div>
              
              <div class="text-center">
                <div class="text-xl font-bold text-gray-900 dark:text-white">
                  {formatNumber(profile.user.totalViews)}
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-400">Total Views</div>
              </div>
              
              <div class="text-center">
                <div class="text-xl font-bold text-gray-900 dark:text-white">
                  {profile.user.totalVideos}
                </div>
                <div class="text-sm text-gray-600 dark:text-gray-400">Videos</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Stats Overview -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div class="card">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Views</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">
                {formatNumber(profile.stats.totalViews)}
              </p>
            </div>
            <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
              <Eye class="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <div class="mt-4 flex items-center">
            <TrendingUp class="w-4 h-4 text-green-500 mr-1" />
            <span class="text-sm text-green-600 dark:text-green-400">
              +{profile.stats.monthlyGrowth.views}% this month
            </span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Likes</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">
                {formatNumber(profile.stats.totalLikes)}
              </p>
            </div>
            <div class="w-12 h-12 bg-red-100 dark:bg-red-900 rounded-lg flex items-center justify-center">
              <Heart class="w-6 h-6 text-red-600 dark:text-red-400" />
            </div>
          </div>
          <div class="mt-4 flex items-center">
            <TrendingUp class="w-4 h-4 text-green-500 mr-1" />
            <span class="text-sm text-green-600 dark:text-green-400">
              +{profile.stats.monthlyGrowth.engagement}% this month
            </span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Comments</p>
              <p class="text-2xl font-bold text-gray-900 dark:text-white">
                {formatNumber(profile.stats.totalComments)}
              </p>
            </div>
            <div class="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
              <MessageCircle class="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
          <div class="mt-4 flex items-center">
            <span class="text-sm text-gray-500 dark:text-gray-400">
              {profile.stats.avgEngagement}% avg engagement
            </span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Top Video</p>
              <p class="text-lg font-bold text-gray-900 dark:text-white">
                {formatNumber(profile.stats.topVideo.views)}
              </p>
            </div>
            <div class="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
              <Trophy class="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
          <div class="mt-4">
            <span class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
              {profile.stats.topVideo.title}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Content Tabs -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
      <!-- Tab Navigation -->
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
                <span class="ml-2 px-2 py-1 bg-gray-100 dark:bg-gray-700 text-xs rounded-full">
                  {tab.count}
                </span>
              </div>
            </button>
          {/each}
        </nav>
      </div>

      <!-- Tab Content -->
      <div class="p-6">
        {#if activeTab === 'videos'}
          <!-- Videos Tab -->
          <div class="space-y-6">
            <!-- Filter Bar -->
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-4">
                <div class="relative">
                  <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search videos..."
                    class="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                  />
                </div>
                <select class="form-input">
                  <option>All Videos</option>
                  <option>Published</option>
                  <option>Drafts</option>
                  <option>Private</option>
                </select>
              </div>
              
              <div class="flex items-center space-x-2">
                <button
                  type="button"
                  class="p-2 rounded {viewMode === 'grid' ? 'bg-gray-200 dark:bg-gray-600' : 'text-gray-400'}"
                  on:click={() => viewMode = 'grid'}
                >
                  <Grid class="w-4 h-4" />
                </button>
                <button
                  type="button"
                  class="p-2 rounded {viewMode === 'list' ? 'bg-gray-200 dark:bg-gray-600' : 'text-gray-400'}"
                  on:click={() => viewMode = 'list'}
                >
                  <List class="w-4 h-4" />
                </button>
              </div>
            </div>

            <!-- Videos Grid/List -->
            {#if viewMode === 'grid'}
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {#each profile.videos as video}
                  <div class="group cursor-pointer" on:click={() => goToVideo(video.id)}>
                    <div class="relative bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden aspect-video mb-3">
                      <!-- Thumbnail -->
                      <div class="absolute inset-0 bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                        <Play class="w-12 h-12 text-gray-400" />
                      </div>
                      
                      <!-- Duration -->
                      <div class="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                        {formatDuration(video.duration)}
                      </div>
                      
                      <!-- Hover Overlay -->
                      <div class="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-200 flex items-center justify-center opacity-0 group-hover:opacity-100">
                        <Play class="w-16 h-16 text-white" />
                      </div>
                    </div>
                    
                    <!-- Video Info -->
                    <div>
                      <h3 class="font-medium text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors line-clamp-2">
                        {video.title}
                      </h3>
                      <div class="flex items-center space-x-4 mt-2 text-sm text-gray-600 dark:text-gray-400">
                        <div class="flex items-center">
                          <Eye class="w-4 h-4 mr-1" />
                          {formatNumber(video.views)}
                        </div>
                        <div class="flex items-center">
                          <Heart class="w-4 h-4 mr-1" />
                          {formatNumber(video.likes)}
                        </div>
                        <span>{formatRelativeDate(video.publishedAt)}</span>
                      </div>
                      <div class="flex flex-wrap gap-1 mt-2">
                        {#each video.tags.slice(0, 3) as tag}
                          <span class="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-xs text-gray-600 dark:text-gray-400 rounded">
                            #{tag}
                          </span>
                        {/each}
                      </div>
                    </div>
                  </div>
                {/each}
              </div>
            {:else}
              <div class="space-y-4">
                {#each profile.videos as video}
                  <div class="flex items-center space-x-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors cursor-pointer"
                       on:click={() => goToVideo(video.id)}>
                    <!-- Thumbnail -->
                    <div class="w-24 h-16 bg-gray-200 dark:bg-gray-600 rounded flex items-center justify-center flex-shrink-0">
                      <Play class="w-6 h-6 text-gray-400" />
                    </div>
                    
                    <!-- Video Info -->
                    <div class="flex-1 min-w-0">
                      <h3 class="font-medium text-gray-900 dark:text-white truncate">
                        {video.title}
                      </h3>
                      <div class="flex items-center space-x-4 mt-1 text-sm text-gray-600 dark:text-gray-400">
                        <span>{formatNumber(video.views)} views</span>
                        <span>{formatNumber(video.likes)} likes</span>
                        <span>{formatRelativeDate(video.publishedAt)}</span>
                        <span>{formatDuration(video.duration)}</span>
                      </div>
                    </div>
                    
                    <!-- Actions -->
                    <div class="flex items-center space-x-2">
                      {#if isOwnProfile}
                        <button type="button" class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                          <Edit3 class="w-4 h-4" />
                        </button>
                      {/if}
                      <button type="button" class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                        <Share2 class="w-4 h-4" />
                      </button>
                      <button type="button" class="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
                        <MoreHorizontal class="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                {/each}
              </div>
            {/if}
          </div>

        {:else if activeTab === 'collections'}
          <!-- Collections Tab -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each profile.collections as collection}
              <div class="group cursor-pointer">
                <div class="relative bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden aspect-video mb-3">
                  <div class="absolute inset-0 bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                    <Bookmark class="w-12 h-12 text-gray-400" />
                  </div>
                  <div class="absolute top-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                    {collection.videoCount} videos
                  </div>
                  {#if !collection.isPublic}
                    <div class="absolute top-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                      Private
                    </div>
                  {/if}
                </div>
                
                <div>
                  <h3 class="font-medium text-gray-900 dark:text-white group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                    {collection.name}
                  </h3>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mt-1 line-clamp-2">
                    {collection.description}
                  </p>
                  <div class="flex items-center space-x-4 mt-2 text-sm text-gray-600 dark:text-gray-400">
                    <span>{formatNumber(collection.totalViews)} views</span>
                    <span>{formatRelativeDate(collection.createdAt)}</span>
                  </div>
                </div>
              </div>
            {/each}
          </div>

        {:else if activeTab === 'activity'}
          <!-- Activity Tab -->
          <div class="space-y-4">
            {#each profile.activity as activity}
              <div class="flex items-start space-x-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div class="w-10 h-10 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center flex-shrink-0">
                  <svelte:component this={getActivityIcon(activity.type)} class="w-5 h-5 text-primary-600 dark:text-primary-400" />
                </div>
                
                <div class="flex-1">
                  <p class="text-gray-900 dark:text-white">
                    <span class="font-medium">{activity.action}</span>
                    {#if activity.target}
                      <span class="text-primary-600 dark:text-primary-400">"{activity.target}"</span>
                    {/if}
                  </p>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {formatRelativeDate(activity.timestamp)}
                  </p>
                  
                  {#if activity.metadata && Object.keys(activity.metadata).length > 0}
                    <div class="flex items-center space-x-4 mt-2 text-sm text-gray-600 dark:text-gray-400">
                      {#if activity.metadata.views}
                        <span>{formatNumber(activity.metadata.views)} views</span>
                      {/if}
                      {#if activity.metadata.likes}
                        <span>{formatNumber(activity.metadata.likes)} likes</span>
                      {/if}
                      {#if activity.metadata.followers}
                        <span>{formatNumber(activity.metadata.followers)} followers</span>
                      {/if}
                    </div>
                  {/if}
                </div>
              </div>
            {/each}
          </div>

        {:else if activeTab === 'achievements'}
          <!-- Achievements Tab -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each profile.achievements as achievement}
              <div class="group">
                <div class="p-6 border-2 border-dashed rounded-lg transition-colors {getRarityColor(achievement.rarity)} border-current">
                  <div class="text-center">
                    <div class="text-4xl mb-4">{achievement.icon}</div>
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      {achievement.name}
                    </h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      {achievement.description}
                    </p>
                    <div class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium {getRarityColor(achievement.rarity)}">
                      {achievement.rarity}
                    </div>
                    <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      Unlocked {formatDate(achievement.unlockedAt)}
                    </p>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {/if}
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