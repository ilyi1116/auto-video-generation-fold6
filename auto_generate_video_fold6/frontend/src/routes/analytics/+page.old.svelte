<script>
  import { onMount } from 'svelte';
  import { apiClient } from '$lib/api/client';
  import { toastStore } from '$lib/stores/toast';
  import { 
    BarChart3,
    TrendingUp,
    TrendingDown,
    Eye,
    Heart,
    Share2,
    MessageCircle,
    Users,
    Clock,
    Target,
    Award,
    Calendar,
    Filter,
    Download,
    RefreshCw,
    Play,
    Pause,
    ArrowUpRight,
    ArrowDownRight,
    Zap,
    Globe
  } from 'lucide-svelte';

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

  const metrics = [
    { value: 'views', label: 'Views', icon: Eye },
    { value: 'engagement', label: 'Engagement', icon: Heart },
    { value: 'shares', label: 'Shares', icon: Share2 },
    { value: 'comments', label: 'Comments', icon: MessageCircle },
    { value: 'subscribers', label: 'Subscribers', icon: Users }
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
      month: 'short',
      day: 'numeric'
    });
  }

  function getGrowthColor(growth) {
    return growth >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
  }

  function getGrowthIcon(growth) {
    return growth >= 0 ? ArrowUpRight : ArrowDownRight;
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
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <!-- Total Views -->
      <div class="card">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Views</p>
              <p class="text-3xl font-bold text-gray-900 dark:text-white">
                {formatNumber(analyticsData.overview.totalViews)}
              </p>
            </div>
            <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
              <Eye class="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
          <div class="mt-4 flex items-center">
            <svelte:component this={getGrowthIcon(analyticsData.overview.monthlyGrowth.views)} class="w-4 h-4 {getGrowthColor(analyticsData.overview.monthlyGrowth.views)} mr-1" />
            <span class="text-sm {getGrowthColor(analyticsData.overview.monthlyGrowth.views)}">
              {analyticsData.overview.monthlyGrowth.views > 0 ? '+' : ''}{analyticsData.overview.monthlyGrowth.views}% from last month
            </span>
          </div>
        </div>
      </div>

      <!-- Total Engagement -->
      <div class="card">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Engagement</p>
              <p class="text-3xl font-bold text-gray-900 dark:text-white">
                {formatNumber(analyticsData.overview.totalEngagement)}
              </p>
            </div>
            <div class="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
              <Heart class="w-6 h-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
          <div class="mt-4 flex items-center">
            <svelte:component this={getGrowthIcon(analyticsData.overview.monthlyGrowth.engagement)} class="w-4 h-4 {getGrowthColor(analyticsData.overview.monthlyGrowth.engagement)} mr-1" />
            <span class="text-sm {getGrowthColor(analyticsData.overview.monthlyGrowth.engagement)}">
              {analyticsData.overview.monthlyGrowth.engagement > 0 ? '+' : ''}{analyticsData.overview.monthlyGrowth.engagement}% from last month
            </span>
          </div>
        </div>
      </div>

      <!-- Engagement Rate -->
      <div class="card">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Engagement Rate</p>
              <p class="text-3xl font-bold text-gray-900 dark:text-white">
                {analyticsData.overview.avgEngagementRate}%
              </p>
            </div>
            <div class="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center">
              <TrendingUp class="w-6 h-6 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
          <div class="mt-4 flex items-center">
            <Target class="w-4 h-4 text-gray-500 mr-1" />
            <span class="text-sm text-gray-500 dark:text-gray-400">Above industry average</span>
          </div>
        </div>
      </div>

      <!-- Subscribers -->
      <div class="card">
        <div class="card-body">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Subscribers</p>
              <p class="text-3xl font-bold text-gray-900 dark:text-white">
                {formatNumber(analyticsData.overview.totalSubscribers)}
              </p>
            </div>
            <div class="w-12 h-12 bg-orange-100 dark:bg-orange-900 rounded-lg flex items-center justify-center">
              <Users class="w-6 h-6 text-orange-600 dark:text-orange-400" />
            </div>
          </div>
          <div class="mt-4 flex items-center">
            <svelte:component this={getGrowthIcon(analyticsData.overview.monthlyGrowth.subscribers)} class="w-4 h-4 {getGrowthColor(analyticsData.overview.monthlyGrowth.subscribers)} mr-1" />
            <span class="text-sm {getGrowthColor(analyticsData.overview.monthlyGrowth.subscribers)}">
              {analyticsData.overview.monthlyGrowth.subscribers > 0 ? '+' : ''}{analyticsData.overview.monthlyGrowth.subscribers}% from last month
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Performance Chart & Top Videos -->
    <div class="grid lg:grid-cols-3 gap-8">
      <!-- Performance Chart -->
      <div class="lg:col-span-2">
        <div class="card">
          <div class="card-header">
            <div class="flex items-center justify-between">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Performance Trends</h2>
              <div class="flex space-x-2">
                {#each metrics as metric}
                  <button
                    type="button"
                    class="px-3 py-1 text-sm rounded-md transition-colors {selectedMetric === metric.value
                      ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                      : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}"
                    on:click={() => selectedMetric = metric.value}
                  >
                    <svelte:component this={metric.icon} class="w-4 h-4 inline mr-1" />
                    {metric.label}
                  </button>
                {/each}
              </div>
            </div>
          </div>
          <div class="card-body">
            <!-- Simulated Chart -->
            <div class="h-64 bg-gray-50 dark:bg-gray-700 rounded-lg flex items-center justify-center">
              <div class="text-center">
                <BarChart3 class="w-12 h-12 text-gray-400 mx-auto mb-2" />
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  Interactive chart for {selectedPeriodLabel}
                </p>
                <div class="mt-4 flex items-center justify-center space-x-8">
                  {#each analyticsData.performance.chartData.labels as label, index}
                    <div class="text-center">
                      <div class="w-8 h-16 bg-primary-200 dark:bg-primary-800 rounded-t mb-1"
                           style="height: {20 + (analyticsData.performance.chartData.views[index] / 1000)}px"></div>
                      <div class="text-xs text-gray-500 dark:text-gray-400">{label}</div>
                    </div>
                  {/each}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Top Videos -->
      <div>
        <div class="card">
          <div class="card-header">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Top Performing Videos</h2>
          </div>
          <div class="card-body">
            <div class="space-y-4">
              {#each analyticsData.performance.topVideos as video, index}
                <div class="flex items-center space-x-3">
                  <!-- Rank -->
                  <div class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold {
                    index === 0 ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200' :
                    index === 1 ? 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200' :
                    'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200'
                  }">
                    {index + 1}
                  </div>
                  
                  <!-- Thumbnail -->
                  <div class="w-12 h-8 bg-gray-200 dark:bg-gray-600 rounded flex items-center justify-center flex-shrink-0">
                    <Play class="w-3 h-3 text-gray-400" />
                  </div>
                  
                  <!-- Content -->
                  <div class="flex-1 min-w-0">
                    <h3 class="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {video.title}
                    </h3>
                    <div class="flex items-center space-x-2 mt-1">
                      <div class="flex items-center text-xs text-gray-500 dark:text-gray-400">
                        <Eye class="w-3 h-3 mr-1" />
                        {formatNumber(video.views)}
                      </div>
                      <div class="flex items-center text-xs text-gray-500 dark:text-gray-400">
                        <Heart class="w-3 h-3 mr-1" />
                        {video.engagementRate}%
                      </div>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Platform Performance & Audience -->
    <div class="grid lg:grid-cols-2 gap-8">
      <!-- Platform Performance -->
      <div class="card">
        <div class="card-header">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Platform Performance</h2>
        </div>
        <div class="card-body">
          <div class="space-y-4">
            {#each analyticsData.platforms.performance as platform}
              <div class="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div class="flex items-center justify-between mb-3">
                  <div class="flex items-center space-x-2">
                    <span class="text-lg">{platform.icon}</span>
                    <span class="font-medium text-gray-900 dark:text-white">{platform.platform}</span>
                  </div>
                  <div class="flex items-center space-x-1">
                    <svelte:component this={getGrowthIcon(platform.growth)} class="w-4 h-4 {getGrowthColor(platform.growth)}" />
                    <span class="text-sm {getGrowthColor(platform.growth)}">
                      {platform.growth > 0 ? '+' : ''}{platform.growth}%
                    </span>
                  </div>
                </div>
                
                <div class="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div class="text-lg font-semibold text-gray-900 dark:text-white">
                      {formatNumber(platform.views)}
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">Views</div>
                  </div>
                  <div>
                    <div class="text-lg font-semibold text-gray-900 dark:text-white">
                      {formatNumber(platform.engagement)}
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">Engagement</div>
                  </div>
                  <div>
                    <div class="text-lg font-semibold text-gray-900 dark:text-white">
                      {formatNumber(platform.subscribers)}
                    </div>
                    <div class="text-xs text-gray-500 dark:text-gray-400">Subscribers</div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      </div>

      <!-- Audience Demographics -->
      <div class="card">
        <div class="card-header">
          <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Audience Demographics</h2>
        </div>
        <div class="card-body space-y-6">
          <!-- Age Groups -->
          <div>
            <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-3">Age Groups</h3>
            <div class="space-y-2">
              {#each analyticsData.audience.demographics.ageGroups as group}
                <div class="flex items-center justify-between">
                  <span class="text-sm text-gray-600 dark:text-gray-400">{group.range}</span>
                  <div class="flex items-center space-x-2">
                    <div class="w-24 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                      <div class="bg-primary-600 h-2 rounded-full" style="width: {group.percentage}%"></div>
                    </div>
                    <span class="text-sm font-medium text-gray-900 dark:text-white w-12 text-right">
                      {group.percentage}%
                    </span>
                  </div>
                </div>
              {/each}
            </div>
          </div>

          <!-- Top Countries -->
          <div>
            <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-3">Top Countries</h3>
            <div class="space-y-2">
              {#each analyticsData.audience.demographics.topCountries as country}
                <div class="flex items-center justify-between">
                  <div class="flex items-center space-x-2">
                    <span class="text-sm">{country.flag}</span>
                    <span class="text-sm text-gray-600 dark:text-gray-400">{country.country}</span>
                  </div>
                  <span class="text-sm font-medium text-gray-900 dark:text-white">
                    {country.percentage}%
                  </span>
                </div>
              {/each}
            </div>
          </div>

          <!-- Watch Time -->
          <div>
            <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-3">Engagement Metrics</h3>
            <div class="grid grid-cols-2 gap-4">
              <div class="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div class="text-lg font-semibold text-gray-900 dark:text-white">
                  {formatDuration(analyticsData.audience.behavior.avgWatchTime)}
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Avg Watch Time</div>
              </div>
              <div class="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div class="text-lg font-semibold text-gray-900 dark:text-white">
                  {analyticsData.audience.behavior.retentionRate}%
                </div>
                <div class="text-xs text-gray-500 dark:text-gray-400">Retention Rate</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Trending Keywords -->
    <div class="card">
      <div class="card-header">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Trending Keywords</h2>
      </div>
      <div class="card-body">
        <div class="grid md:grid-cols-2 gap-8">
          <!-- Rising Trends -->
          <div>
            <h3 class="text-sm font-medium text-green-600 dark:text-green-400 mb-4 flex items-center">
              <TrendingUp class="w-4 h-4 mr-2" />
              Rising Trends
            </h3>
            <div class="space-y-3">
              {#each analyticsData.trends.rising as trend}
                <div class="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div>
                    <span class="text-sm font-medium text-gray-900 dark:text-white">{trend.keyword}</span>
                    <span class="text-xs text-gray-500 dark:text-gray-400 ml-2">({trend.difficulty})</span>
                  </div>
                  <div class="flex items-center space-x-1 text-green-600 dark:text-green-400">
                    <TrendingUp class="w-4 h-4" />
                    <span class="text-sm font-medium">+{trend.growth}%</span>
                  </div>
                </div>
              {/each}
            </div>
          </div>

          <!-- Declining Trends -->
          <div>
            <h3 class="text-sm font-medium text-red-600 dark:text-red-400 mb-4 flex items-center">
              <TrendingDown class="w-4 h-4 mr-2" />
              Declining Trends
            </h3>
            <div class="space-y-3">
              {#each analyticsData.trends.declining as trend}
                <div class="flex items-center justify-between p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                  <div>
                    <span class="text-sm font-medium text-gray-900 dark:text-white">{trend.keyword}</span>
                    <span class="text-xs text-gray-500 dark:text-gray-400 ml-2">({trend.difficulty})</span>
                  </div>
                  <div class="flex items-center space-x-1 text-red-600 dark:text-red-400">
                    <TrendingDown class="w-4 h-4" />
                    <span class="text-sm font-medium">{trend.growth}%</span>
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