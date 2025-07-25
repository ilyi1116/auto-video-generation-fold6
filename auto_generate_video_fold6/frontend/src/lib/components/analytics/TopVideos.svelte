<script>
  import { Eye, Heart, Play } from 'lucide-svelte';

  export let analyticsData = {};

  function formatNumber(num) {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  }
</script>

<div class="card">
  <div class="card-header">
    <h2 class="text-lg font-semibold text-gray-900 dark:text-white">Top Performing Videos</h2>
  </div>
  <div class="card-body">
    <div class="space-y-4">
      {#each analyticsData.performance?.topVideos || [] as video, index}
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