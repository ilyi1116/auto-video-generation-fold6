<script>
  import { BarChart3, Eye, Heart, Share2, MessageCircle, Users } from 'lucide-svelte';

  export let analyticsData = {};
  export let selectedMetric = 'views';
  export let selectedPeriodLabel = 'Last 7 Days';

  const metrics = [
    { value: 'views', label: 'Views', icon: Eye },
    { value: 'engagement', label: 'Engagement', icon: Heart },
    { value: 'shares', label: 'Shares', icon: Share2 },
    { value: 'comments', label: 'Comments', icon: MessageCircle },
    { value: 'subscribers', label: 'Subscribers', icon: Users }
  ];

  function handleMetricChange(metric) {
    selectedMetric = metric;
  }
</script>

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
            on:click={() => handleMetricChange(metric.value)}
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
          {#each analyticsData.performance?.chartData?.labels || [] as label, index}
            <div class="text-center">
              <div class="w-8 h-16 bg-primary-200 dark:bg-primary-800 rounded-t mb-1"
                   style="height: {20 + ((analyticsData.performance?.chartData?.views?.[index] || 0) / 1000)}px"></div>
              <div class="text-xs text-gray-500 dark:text-gray-400">{label}</div>
            </div>
          {/each}
        </div>
      </div>
    </div>
  </div>
</div>