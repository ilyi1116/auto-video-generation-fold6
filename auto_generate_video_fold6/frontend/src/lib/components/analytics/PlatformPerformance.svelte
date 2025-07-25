<script>
  import { ArrowUpRight, ArrowDownRight } from 'lucide-svelte';

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

<div class="card">
  <div class="card-header">
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Platform Performance</h2>
  </div>
  <div class="card-body">
    <div class="space-y-4">
      {#each analyticsData.platforms?.performance || [] as platform}
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