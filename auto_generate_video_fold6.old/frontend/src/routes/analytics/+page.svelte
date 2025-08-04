<script>
  import { onMount } from 'svelte';
  import { apiClient } from '$lib/api/client';
  import { toastStore } from '$lib/stores/toast';
  import { RefreshCw, Download } from 'lucide-svelte';

  // Import analytics components
  import OverviewStats from '$lib/components/analytics/OverviewStats.svelte';
  import PerformanceChart from '$lib/components/analytics/PerformanceChart.svelte';
  import TopVideos from '$lib/components/analytics/TopVideos.svelte';
  import PlatformPerformance from '$lib/components/analytics/PlatformPerformance.svelte';
  import AudienceDemographics from '$lib/components/analytics/AudienceDemographics.svelte';
  import TrendingKeywords from '$lib/components/analytics/TrendingKeywords.svelte';

  let isLoading = true;
  let selectedPeriod = '7d';
  let selectedMetric = 'views';
  let analyticsData = {
    overview: {},
    performance: {},
    audience: {},
    content: {},
    platforms: {},
    trends: {}
  };

  const periods = [
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 3 Months' },
    { value: '1y', label: 'Last Year' }
  ];

  onMount(async () => {
    await loadAnalytics();
  });

  async function loadAnalytics() {
    try {
      isLoading = true;
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      analyticsData = {
        overview: {
          totalViews: 1245600,
          totalEngagement: 89200,
          avgEngagementRate: 7.2,
          totalSubscribers: 12800,
          monthlyGrowth: {
            views: 23.5,
            engagement: 18.3,
            subscribers: 12.7
          }
        },
        performance: {
          topVideos: [
            {
              id: 1,
              title: "10 AI Tools That Will Change Everything",
              views: 245600,
              engagement: 18900,
              engagementRate: 7.7,
              duration: 185,
              publishedAt: "2024-01-10",
              thumbnail: "/api/placeholder/160/90"
            },
            {
              id: 2,
              title: "Secret TikTok Algorithm Hack",
              views: 198300,
              engagement: 24100,
              engagementRate: 12.1,
              duration: 58,
              publishedAt: "2024-01-08",
              thumbnail: "/api/placeholder/160/90"
            },
            {
              id: 3,
              title: "Remote Work Productivity Tips",
              views: 156700,
              engagement: 11200,
              engagementRate: 7.1,
              duration: 142,
              publishedAt: "2024-01-05",
              thumbnail: "/api/placeholder/160/90"
            }
          ],
          chartData: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            views: [12500, 15600, 18200, 22100, 19800, 24300, 21700],
            engagement: [890, 1120, 1340, 1580, 1420, 1890, 1650]
          }
        },
        audience: {
          demographics: {
            ageGroups: [
              { range: '18-24', percentage: 28.5 },
              { range: '25-34', percentage: 42.3 },
              { range: '35-44', percentage: 18.7 },
              { range: '45-54', percentage: 7.2 },
              { range: '55+', percentage: 3.3 }
            ],
            genders: [
              { type: 'Male', percentage: 62.4 },
              { type: 'Female', percentage: 35.8 },
              { type: 'Other', percentage: 1.8 }
            ],
            topCountries: [
              { country: 'United States', percentage: 45.2, flag: '🇺🇸' },
              { country: 'United Kingdom', percentage: 12.8, flag: '🇬🇧' },
              { country: 'Canada', percentage: 8.6, flag: '🇨🇦' },
              { country: 'Australia', percentage: 6.4, flag: '🇦🇺' },
              { country: 'Germany', percentage: 5.1, flag: '🇩🇪' }
            ]
          },
          behavior: {
            peakHours: [
              { hour: '9 AM', views: 1250 },
              { hour: '12 PM', views: 1890 },
              { hour: '3 PM', views: 1560 },
              { hour: '6 PM', views: 2340 },
              { hour: '9 PM', views: 2890 }
            ],
            avgWatchTime: 127,
            retentionRate: 68.4
          }
        },
        platforms: {
          performance: [
            {
              platform: 'YouTube',
              icon: '📺',
              views: 685400,
              engagement: 45600,
              subscribers: 8900,
              growth: 15.2
            },
            {
              platform: 'TikTok',
              icon: '🎵',
              views: 342100,
              engagement: 28900,
              subscribers: 2100,
              growth: 34.7
            },
            {
              platform: 'Instagram',
              icon: '📷',
              views: 156300,
              engagement: 12400,
              subscribers: 1500,
              growth: 8.9
            },
            {
              platform: 'Twitter',
              icon: '🐦',
              views: 61800,
              engagement: 2300,
              subscribers: 300,
              growth: -2.1
            }
          ]
        },
        trends: {
          rising: [
            { keyword: 'AI productivity', growth: 156, difficulty: 'medium' },
            { keyword: 'remote work tips', growth: 89, difficulty: 'easy' },
            { keyword: 'crypto investing', growth: 67, difficulty: 'hard' }
          ],
          declining: [
            { keyword: 'NFT trends', growth: -23, difficulty: 'hard' },
            { keyword: 'web3 basics', growth: -15, difficulty: 'medium' }
          ]
        }
      };
      
    } catch (error) {
      console.error('Error loading analytics:', error);
      toastStore.error('Failed to load analytics data');
    } finally {
      isLoading = false;
    }
  }

  function exportData() {
    // In a real app, this would export actual data
    toastStore.success('Analytics data exported!');
  }

  $: selectedPeriodLabel = periods.find(p => p.value === selectedPeriod)?.label || 'Last 7 Days';
</script>

<svelte:head>
  <title>Analytics - AutoVideo</title>
</svelte:head>

<div class="max-w-7xl mx-auto space-y-8">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white">Analytics</h1>
      <p class="mt-2 text-gray-600 dark:text-gray-400">
        Track your content performance and audience insights
      </p>
    </div>
    <div class="mt-4 sm:mt-0 flex items-center space-x-3">
      <!-- Period Selector -->
      <select bind:value={selectedPeriod} on:change={loadAnalytics} class="form-input text-sm">
        {#each periods as period}
          <option value={period.value}>{period.label}</option>
        {/each}
      </select>
      
      <!-- Actions -->
      <button type="button" class="btn-secondary flex items-center" on:click={loadAnalytics}>
        <RefreshCw class="w-4 h-4 mr-2" />
        Refresh
      </button>
      <button type="button" class="btn-secondary flex items-center" on:click={exportData}>
        <Download class="w-4 h-4 mr-2" />
        Export
      </button>
    </div>
  </div>

  {#if isLoading}
    <div class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>
  {:else}
    <!-- Overview Stats -->
    <OverviewStats {analyticsData} />

    <!-- Performance Chart & Top Videos -->
    <div class="grid lg:grid-cols-3 gap-8">
      <!-- Performance Chart -->
      <div class="lg:col-span-2">
        <PerformanceChart {analyticsData} bind:selectedMetric {selectedPeriodLabel} />
      </div>

      <!-- Top Videos -->
      <TopVideos {analyticsData} />
    </div>

    <!-- Platform Performance & Audience -->
    <div class="grid lg:grid-cols-2 gap-8">
      <PlatformPerformance {analyticsData} />
      <AudienceDemographics {analyticsData} />
    </div>

    <!-- Trending Keywords -->
    <TrendingKeywords {analyticsData} />
  {/if}
</div>