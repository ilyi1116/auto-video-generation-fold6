<script>
  import { onMount } from 'svelte';
  import { toastStore } from '$lib/stores/toast';

  // Import dashboard components
  import WelcomeHeader from '$lib/components/dashboard/WelcomeHeader.svelte';
  import StatsGrid from '$lib/components/dashboard/StatsGrid.svelte';
  import RecentVideos from '$lib/components/dashboard/RecentVideos.svelte';
  import QuickActions from '$lib/components/dashboard/QuickActions.svelte';
  import TrendingTopics from '$lib/components/dashboard/TrendingTopics.svelte';
  import ScheduledPosts from '$lib/components/dashboard/ScheduledPosts.svelte';

  let isLoading = true;
  let dashboardData = {
    stats: {
      totalVideos: 0,
      totalViews: 0,
      totalEngagement: 0,
      monthlyGrowth: 0
    },
    recentVideos: [],
    upcomingScheduled: [],
    trends: []
  };

  onMount(async () => {
    await loadDashboardData();
  });

  async function loadDashboardData() {
    try {
      isLoading = true;
      
      // In a real app, this would be a single dashboard API call
      // For now, we'll simulate the data
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      dashboardData = {
        stats: {
          totalVideos: 47,
          totalViews: 125600,
          totalEngagement: 8.4,
          monthlyGrowth: 23.5
        },
        recentVideos: [
          {
            id: 1,
            title: "10 AI Tools That Will Change Everything",
            thumbnail: "/api/placeholder/160/90",
            views: 15400,
            engagement: 9.2,
            status: "published",
            createdAt: "2024-01-15",
            platform: "youtube"
          },
          {
            id: 2,
            title: "Secret TikTok Algorithm Hack",
            thumbnail: "/api/placeholder/160/90",
            views: 8900,
            engagement: 12.1,
            status: "published",
            createdAt: "2024-01-14",
            platform: "tiktok"
          },
          {
            id: 3,
            title: "Why Everyone Is Switching to AI",
            thumbnail: "/api/placeholder/160/90",
            views: 6200,
            engagement: 7.8,
            status: "processing",
            createdAt: "2024-01-13",
            platform: "instagram"
          }
        ],
        upcomingScheduled: [
          {
            id: 4,
            title: "Morning Motivation Tips",
            scheduledFor: "2024-01-16T08:00:00Z",
            platform: "all"
          },
          {
            id: 5,
            title: "Tech News Roundup",
            scheduledFor: "2024-01-16T12:00:00Z",
            platform: "youtube"
          }
        ],
        trends: [
          { keyword: "AI automation", growth: 156, difficulty: "medium" },
          { keyword: "productivity hacks", growth: 89, difficulty: "easy" },
          { keyword: "remote work tips", growth: 67, difficulty: "hard" }
        ]
      };
      
    } catch (error) {
      console.error('Error loading dashboard:', error);
      toastStore.error('Failed to load dashboard data');
    } finally {
      isLoading = false;
    }
  }

  function handleUseTrend(event) {
    const trend = event.detail;
    toastStore.info(`Using trend: ${trend.keyword}`);
    // Navigate to create page with pre-filled trend
    window.location.href = `/create?trend=${encodeURIComponent(trend.keyword)}`;
  }
</script>

<svelte:head>
  <title>Dashboard - AutoVideo</title>
</svelte:head>

{#if isLoading}
  <div class="flex justify-center items-center h-64">
    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
  </div>
{:else}
  <div class="space-y-8">
    <!-- Welcome Header -->
    <WelcomeHeader />

    <!-- Stats Grid -->
    <StatsGrid stats={dashboardData.stats} />

    <div class="grid lg:grid-cols-3 gap-8">
      <!-- Recent Videos -->
      <div class="lg:col-span-2">
        <RecentVideos videos={dashboardData.recentVideos} />
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- Quick Actions -->
        <QuickActions />

        <!-- Trending Topics -->
        <TrendingTopics 
          trends={dashboardData.trends} 
          on:useTrend={handleUseTrend}
        />

        <!-- Upcoming Scheduled -->
        <ScheduledPosts scheduledPosts={dashboardData.upcomingScheduled} />
      </div>
    </div>
  </div>
{/if}