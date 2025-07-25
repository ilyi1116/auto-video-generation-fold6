<script>
  export let analyticsData = {};

  function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
</script>

<div class="card">
  <div class="card-header">
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Audience Demographics</h2>
  </div>
  <div class="card-body space-y-6">
    <!-- Age Groups -->
    <div>
      <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-3">Age Groups</h3>
      <div class="space-y-2">
        {#each analyticsData.audience?.demographics?.ageGroups || [] as group}
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
        {#each analyticsData.audience?.demographics?.topCountries || [] as country}
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
            {formatDuration(analyticsData.audience?.behavior?.avgWatchTime || 0)}
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">Avg Watch Time</div>
        </div>
        <div class="text-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
          <div class="text-lg font-semibold text-gray-900 dark:text-white">
            {analyticsData.audience?.behavior?.retentionRate || 0}%
          </div>
          <div class="text-xs text-gray-500 dark:text-gray-400">Retention Rate</div>
        </div>
      </div>
    </div>
  </div>
</div>