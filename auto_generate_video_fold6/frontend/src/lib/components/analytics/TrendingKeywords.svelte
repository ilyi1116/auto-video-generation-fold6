<script>
  import { TrendingUp, TrendingDown } from 'lucide-svelte';

  export let analyticsData = {};
</script>

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
          {#each analyticsData.trends?.rising || [] as trend}
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
          {#each analyticsData.trends?.declining || [] as trend}
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