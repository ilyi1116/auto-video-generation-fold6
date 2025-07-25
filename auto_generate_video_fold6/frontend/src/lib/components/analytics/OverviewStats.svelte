<script>
  import { Eye, Heart, TrendingUp, Users, ArrowUpRight, ArrowDownRight, Target } from 'lucide-svelte';

  export let analyticsData = {};

  function formatNumber(num) {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  }

  function getGrowthColor(growth) {
    return growth >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
  }

  function getGrowthIcon(growth) {
    return growth >= 0 ? ArrowUpRight : ArrowDownRight;
  }
</script>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
  <!-- Total Views -->
  <div class="card">
    <div class="card-body">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm font-medium text-gray-600 dark:text-gray-400">Total Views</p>
          <p class="text-3xl font-bold text-gray-900 dark:text-white">
            {formatNumber(analyticsData.overview?.totalViews || 0)}
          </p>
        </div>
        <div class="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
          <Eye class="w-6 h-6 text-blue-600 dark:text-blue-400" />
        </div>
      </div>
      <div class="mt-4 flex items-center">
        <svelte:component this={getGrowthIcon(analyticsData.overview?.monthlyGrowth?.views || 0)} class="w-4 h-4 {getGrowthColor(analyticsData.overview?.monthlyGrowth?.views || 0)} mr-1" />
        <span class="text-sm {getGrowthColor(analyticsData.overview?.monthlyGrowth?.views || 0)}">
          {analyticsData.overview?.monthlyGrowth?.views > 0 ? '+' : ''}{analyticsData.overview?.monthlyGrowth?.views || 0}% from last month
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
            {formatNumber(analyticsData.overview?.totalEngagement || 0)}
          </p>
        </div>
        <div class="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center">
          <Heart class="w-6 h-6 text-green-600 dark:text-green-400" />
        </div>
      </div>
      <div class="mt-4 flex items-center">
        <svelte:component this={getGrowthIcon(analyticsData.overview?.monthlyGrowth?.engagement || 0)} class="w-4 h-4 {getGrowthColor(analyticsData.overview?.monthlyGrowth?.engagement || 0)} mr-1" />
        <span class="text-sm {getGrowthColor(analyticsData.overview?.monthlyGrowth?.engagement || 0)}">
          {analyticsData.overview?.monthlyGrowth?.engagement > 0 ? '+' : ''}{analyticsData.overview?.monthlyGrowth?.engagement || 0}% from last month
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
            {analyticsData.overview?.avgEngagementRate || 0}%
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
            {formatNumber(analyticsData.overview?.totalSubscribers || 0)}
          </p>
        </div>
        <div class="w-12 h-12 bg-orange-100 dark:bg-orange-900 rounded-lg flex items-center justify-center">
          <Users class="w-6 h-6 text-orange-600 dark:text-orange-400" />
        </div>
      </div>
      <div class="mt-4 flex items-center">
        <svelte:component this={getGrowthIcon(analyticsData.overview?.monthlyGrowth?.subscribers || 0)} class="w-4 h-4 {getGrowthColor(analyticsData.overview?.monthlyGrowth?.subscribers || 0)} mr-1" />
        <span class="text-sm {getGrowthColor(analyticsData.overview?.monthlyGrowth?.subscribers || 0)}">
          {analyticsData.overview?.monthlyGrowth?.subscribers > 0 ? '+' : ''}{analyticsData.overview?.monthlyGrowth?.subscribers || 0}% from last month
        </span>
      </div>
    </div>
  </div>
</div>