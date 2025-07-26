<script>
  import { onMount } from 'svelte';
  import { toastStore } from '$lib/stores/toast';
  import { goto } from '$app/navigation';
  import { 
    TrendingUp,
    Search,
    Filter,
    Globe,
    Clock,
    Target,
    Fire,
    ArrowUpRight,
    Lightbulb,
    Play
  } from 'lucide-svelte';

  let isLoading = true;
  let searchQuery = '';
  let selectedCategory = 'all';
  let selectedRegion = 'global';
  let selectedTimeframe = '24h';
  let trendsData = {
    trending: [],
    rising: [],
    viral: []
  };

  const categories = [
    { value: 'all', label: 'All Categories', icon: '🌐' },
    { value: 'technology', label: 'Technology', icon: '💻' },
    { value: 'entertainment', label: 'Entertainment', icon: '🎭' },
    { value: 'education', label: 'Education', icon: '📚' },
    { value: 'lifestyle', label: 'Lifestyle', icon: '🌟' },
    { value: 'business', label: 'Business', icon: '💼' }
  ];

  const regions = [
    { value: 'global', label: 'Global' },
    { value: 'us', label: 'United States' },
    { value: 'uk', label: 'United Kingdom' },
    { value: 'ca', label: 'Canada' },
    { value: 'au', label: 'Australia' }
  ];

  const timeframes = [
    { value: '1h', label: 'Last Hour' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last Week' },
    { value: '30d', label: 'Last Month' }
  ];

  onMount(() => {
    loadTrends();
  });

  async function loadTrends() {
    try {
      isLoading = true;
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      trendsData = {
        trending: [
          {
            id: 1,
            topic: "AI productivity tools for 2024",
            category: "technology",
            growth: 156,
            volume: 24500,
            difficulty: "medium",
            potential: "high",
            trend_direction: "up",
            hashtags: ["#AI", "#productivity", "#tools2024"]
          },
          {
            id: 2,
            topic: "Remote work best practices",
            category: "business",
            growth: 89,
            volume: 18200,
            difficulty: "easy",
            potential: "high",
            trend_direction: "up",
            hashtags: ["#remotework", "#productivity", "#workfromhome"]
          },
          {
            id: 3,
            topic: "Sustainable living tips",
            category: "lifestyle",
            growth: 67,
            volume: 15800,
            difficulty: "easy",
            potential: "medium",
            trend_direction: "up",
            hashtags: ["#sustainability", "#ecofriendly", "#greenliving"]
          }
        ],
        rising: [
          {
            id: 4,
            topic: "TikTok algorithm updates 2024",
            category: "entertainment",
            growth: 234,
            volume: 8900,
            difficulty: "hard",
            potential: "high",
            trend_direction: "up"
          },
          {
            id: 5,
            topic: "Mindfulness meditation for beginners",
            category: "lifestyle",
            growth: 145,
            volume: 12400,
            difficulty: "easy",
            potential: "medium",
            trend_direction: "up"
          }
        ],
        viral: [
          {
            id: 6,
            topic: "ChatGPT writing prompts",
            category: "technology",
            growth: 892,
            volume: 45600,
            difficulty: "easy",
            potential: "high",
            trend_direction: "up"
          }
        ]
      };
    } catch (error) {
      console.error('Error loading trends:', error);
      toastStore.error('Failed to load trends data');
    } finally {
      isLoading = false;
    }
  }

  function getTrendColor(growth) {
    if (growth > 200) return 'text-red-600';
    if (growth > 100) return 'text-orange-600';
    if (growth > 50) return 'text-green-600';
    return 'text-blue-600';
  }

  function getDifficultyColor(difficulty) {
    switch (difficulty) {
      case 'easy': return 'text-green-600 bg-green-100 dark:bg-green-900 dark:text-green-300';
      case 'medium': return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900 dark:text-yellow-300';
      case 'hard': return 'text-red-600 bg-red-100 dark:bg-red-900 dark:text-red-300';
      default: return 'text-gray-600 bg-gray-100 dark:bg-gray-700 dark:text-gray-300';
    }
  }

  function handleUseTrend(trend) {
    goto(`/ai/script?topic=${encodeURIComponent(trend.topic)}`);
  }

  function handleRefresh() {
    loadTrends();
  }

  // Reactive filtering
  $: filteredTrends = trendsData.trending.filter(trend => {
    if (selectedCategory !== 'all' && trend.category !== selectedCategory) return false;
    if (searchQuery && !trend.topic.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });
</script>

<svelte:head>
  <title>Trending Topics - AutoVideo</title>
</svelte:head>

<div class="max-w-7xl mx-auto">
  <!-- Header -->
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        Trending Topics
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        Discover what's trending and create viral content
      </p>
    </div>
    <button
      type="button"
      class="btn-primary flex items-center mt-4 sm:mt-0"
      on:click={handleRefresh}
    >
      <RefreshCw class="w-4 h-4 mr-2" />
      Refresh
    </button>
  </div>

  <!-- Filters -->
  <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
    <!-- Search -->
    <div class="relative">
      <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
      <input
        type="text"
        bind:value={searchQuery}
        placeholder="Search trends..."
        class="input pl-10 w-full"
      />
    </div>

    <!-- Category -->
    <select bind:value={selectedCategory} class="select w-full">
      {#each categories as category}
        <option value={category.value}>{category.icon} {category.label}</option>
      {/each}
    </select>

    <!-- Region -->
    <select bind:value={selectedRegion} class="select w-full">
      {#each regions as region}
        <option value={region.value}>{region.label}</option>
      {/each}
    </select>

    <!-- Timeframe -->
    <select bind:value={selectedTimeframe} class="select w-full">
      {#each timeframes as timeframe}
        <option value={timeframe.value}>{timeframe.label}</option>
      {/each}
    </select>
  </div>

  {#if isLoading}
    <div class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
    </div>
  {:else}
    <div class="grid lg:grid-cols-3 gap-8">
      <!-- Trending Topics -->
      <div class="lg:col-span-2">
        <div class="card">
          <div class="card-header">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
              <TrendingUp class="w-5 h-5 mr-2 text-primary-600" />
              Trending Now
            </h2>
          </div>
          <div class="card-body">
            <div class="space-y-4">
              {#each filteredTrends as trend, index}
                <div class="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors">
                  <div class="flex items-center space-x-4">
                    <div class="text-xl font-bold text-gray-400">
                      #{index + 1}
                    </div>
                    <div class="flex-1">
                      <h3 class="text-sm font-medium text-gray-900 dark:text-white mb-1">
                        {trend.topic}
                      </h3>
                      <div class="flex items-center space-x-3 text-xs">
                        <span class="inline-flex items-center px-2 py-1 rounded-full {getDifficultyColor(trend.difficulty)}">
                          {trend.difficulty}
                        </span>
                        <div class="flex items-center {getTrendColor(trend.growth)}">
                          <ArrowUpRight class="w-3 h-3 mr-1" />
                          +{trend.growth}%
                        </div>
                        <span class="text-gray-500">
                          {trend.volume.toLocaleString()} searches
                        </span>
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    class="btn-primary text-sm"
                    on:click={() => handleUseTrend(trend)}
                  >
                    <Play class="w-3 h-3 mr-1" />
                    Use
                  </button>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- Rising Topics -->
        <div class="card">
          <div class="card-header">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <Fire class="w-5 h-5 mr-2 text-orange-500" />
              Rising Fast
            </h3>
          </div>
          <div class="card-body">
            <div class="space-y-3">
              {#each trendsData.rising as trend}
                <div class="flex items-center justify-between">
                  <div class="flex-1">
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      {trend.topic}
                    </p>
                    <div class="flex items-center mt-1 text-xs">
                      <ArrowUpRight class="w-3 h-3 text-red-500 mr-1" />
                      <span class="text-red-600 dark:text-red-400">
                        +{trend.growth}%
                      </span>
                    </div>
                  </div>
                  <button
                    class="text-xs text-primary-600 hover:text-primary-700 dark:text-primary-400 font-medium"
                    on:click={() => handleUseTrend(trend)}
                  >
                    Use
                  </button>
                </div>
              {/each}
            </div>
          </div>
        </div>

        <!-- Viral Content -->
        <div class="card">
          <div class="card-header">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <Lightbulb class="w-5 h-5 mr-2 text-yellow-500" />
              Viral Content
            </h3>
          </div>
          <div class="card-body">
            <div class="space-y-3">
              {#each trendsData.viral as trend}
                <div class="flex items-center justify-between">
                  <div class="flex-1">
                    <p class="text-sm font-medium text-gray-900 dark:text-white">
                      {trend.topic}
                    </p>
                    <div class="flex items-center mt-1 text-xs">
                      <span class="text-red-600 dark:text-red-400">
                        🔥 {trend.volume.toLocaleString()} views
                      </span>
                    </div>
                  </div>
                  <button
                    class="text-xs text-primary-600 hover:text-primary-700 dark:text-primary-400 font-medium"
                    on:click={() => handleUseTrend(trend)}
                  >
                    Use
                  </button>
                </div>
              {/each}
            </div>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>