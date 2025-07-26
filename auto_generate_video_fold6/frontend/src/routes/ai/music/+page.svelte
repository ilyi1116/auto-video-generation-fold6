<script>
  import { onMount } from 'svelte';
  import { apiClient } from '$lib/api/client.js';
  import MusicGenerator from '$lib/components/ai/music/MusicGenerator.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import Badge from '$lib/components/ui/Badge.svelte';
  import Alert from '$lib/components/ui/Alert.svelte';
  import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';

  let recentGenerations = [];
  let musicCapabilities = null;
  let isLoading = true;
  let error = null;

  onMount(async () => {
    await loadMusicCapabilities();
    await loadRecentGenerations();
    isLoading = false;
  });

  async function loadMusicCapabilities() {
    try {
      const response = await apiClient.getAICapabilities();
      musicCapabilities = response.data.capabilities.music_generation;
    } catch (err) {
      console.error('Failed to load music capabilities:', err);
    }
  }

  async function loadRecentGenerations() {
    try {
      // This would typically load from a user's music generation history
      // For now, we'll simulate some recent generations
      recentGenerations = [
        {
          id: '1',
          prompt: 'Upbeat electronic music for TikTok',
          style: 'energetic',
          created_at: new Date(Date.now() - 86400000).toISOString(),
          duration_seconds: 30,
          platform: 'tiktok'
        },
        {
          id: '2', 
          prompt: 'Calm background music for meditation',
          style: 'background',
          created_at: new Date(Date.now() - 172800000).toISOString(),
          duration_seconds: 180,
          platform: 'youtube'
        }
      ];
    } catch (err) {
      console.error('Failed to load recent generations:', err);
    }
  }

  function handleMusicGenerated(music) {
    // Add the new generation to the top of the list
    recentGenerations = [
      {
        id: music.music_id,
        prompt: music.original_prompt,
        style: music.style,
        created_at: new Date().toISOString(),
        duration_seconds: music.duration_seconds,
        platform: music.platform,
        music_url: music.music_url
      },
      ...recentGenerations
    ];
  }

  function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function getPlatformColor(platform) {
    const colors = {
      'tiktok': 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-300',
      'youtube': 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
      'instagram': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
      'podcast': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
    };
    return colors[platform] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
  }

  function getStyleColor(style) {
    const colors = {
      'background': 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
      'energetic': 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
      'cinematic': 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
      'acoustic': 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
      'corporate': 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300',
      'hip_hop': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
      'jazz': 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300'
    };
    return colors[style] || 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
  }
</script>

<svelte:head>
  <title>AI Music Generator - Auto Video Generation</title>
  <meta name="description" content="Generate custom background music and audio for your videos using AI" />
</svelte:head>

<div class="container mx-auto px-4 py-8">
  <!-- Page Header -->
  <div class="mb-8">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">AI Music Generator</h1>
        <p class="text-gray-600 dark:text-gray-400 mt-2">
          Create custom background music and audio tracks for your videos using advanced AI
        </p>
      </div>
      
      <!-- Service Status -->
      <div class="flex items-center space-x-2">
        {#if musicCapabilities}
          <div class="flex items-center">
            <div class="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
            <span class="text-sm text-gray-600 dark:text-gray-400">Service Online</span>
          </div>
        {:else}
          <div class="flex items-center">
            <div class="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
            <span class="text-sm text-gray-600 dark:text-gray-400">Service Offline</span>
          </div>
        {/if}
      </div>
    </div>
  </div>

  {#if isLoading}
    <div class="flex justify-center items-center h-64">
      <LoadingSpinner size="lg" />
    </div>
  {:else if error}
    <Alert type="error" message={error} />
  {:else}
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
      <!-- Main Generator -->
      <div class="xl:col-span-2">
        <MusicGenerator onMusicGenerated={handleMusicGenerated} />
      </div>

      <!-- Sidebar -->
      <div class="space-y-6">
        <!-- Service Capabilities -->
        {#if musicCapabilities}
          <Card>
            <div slot="header">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Music Generation Features</h3>
            </div>
            
            <div class="space-y-4">
              <div>
                <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2">Available Features</h4>
                <div class="flex flex-wrap gap-1">
                  {#each musicCapabilities.features as feature}
                    <Badge class="text-xs">{feature.replace('_', ' ')}</Badge>
                  {/each}
                </div>
              </div>

              <div>
                <h4 class="font-medium text-gray-700 dark:text-gray-300 mb-2">Supported Styles</h4>
                <div class="flex flex-wrap gap-1">
                  {#each musicCapabilities.supported_styles as style}
                    <Badge variant="outline" class="text-xs">{style}</Badge>
                  {/each}
                </div>
              </div>

              <div class="text-sm text-gray-600 dark:text-gray-400">
                Status: 
                <span class="font-medium {musicCapabilities.available ? 'text-green-600' : 'text-red-600'}">
                  {musicCapabilities.available ? 'Available' : 'Unavailable'}
                </span>
              </div>
            </div>
          </Card>
        {/if}

        <!-- Recent Generations -->
        {#if recentGenerations.length > 0}
          <Card>
            <div slot="header">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Recent Generations</h3>
            </div>
            
            <div class="space-y-3">
              {#each recentGenerations.slice(0, 5) as generation}
                <div class="border-b border-gray-200 dark:border-gray-700 last:border-b-0 pb-3 last:pb-0">
                  <div class="flex items-start justify-between mb-2">
                    <p class="text-sm font-medium text-gray-900 dark:text-white line-clamp-2">
                      {generation.prompt}
                    </p>
                  </div>
                  
                  <div class="flex items-center space-x-2 mb-2">
                    <Badge class={getStyleColor(generation.style)} size="xs">
                      {generation.style}
                    </Badge>
                    <Badge class={getPlatformColor(generation.platform)} size="xs">
                      {generation.platform}
                    </Badge>
                    <span class="text-xs text-gray-500">
                      {generation.duration_seconds}s
                    </span>
                  </div>
                  
                  {#if generation.music_url}
                    <audio controls class="w-full h-8">
                      <source src={generation.music_url} type="audio/mpeg">
                    </audio>
                  {/if}
                  
                  <p class="text-xs text-gray-500 mt-2">
                    {formatDate(generation.created_at)}
                  </p>
                </div>
              {/each}
            </div>
          </Card>
        {/if}

        <!-- Tips & Best Practices -->
        <Card>
          <div slot="header">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Music Generation Tips</h3>
          </div>
          
          <div class="space-y-3 text-sm">
            <div>
              <h4 class="font-medium text-gray-700 dark:text-gray-300">Prompt Writing</h4>
              <ul class="text-gray-600 dark:text-gray-400 mt-1 space-y-1">
                <li>• Be specific about the mood and energy level</li>
                <li>• Mention target platform for optimization</li>
                <li>• Include genre references when relevant</li>
              </ul>
            </div>
            
            <div>
              <h4 class="font-medium text-gray-700 dark:text-gray-300">Platform Optimization</h4>
              <ul class="text-gray-600 dark:text-gray-400 mt-1 space-y-1">
                <li>• TikTok: 15-60s, high energy</li>
                <li>• YouTube: 30-300s, balanced</li>
                <li>• Instagram: 15-90s, engaging</li>
                <li>• Podcast: 60-600s, subtle</li>
              </ul>
            </div>
            
            <div>
              <h4 class="font-medium text-gray-700 dark:text-gray-300">Quality Tips</h4>
              <ul class="text-gray-600 dark:text-gray-400 mt-1 space-y-1">
                <li>• Use instrumental for background music</li>
                <li>• Match tempo to content pacing</li>
                <li>• Generate variations for options</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </div>
  {/if}
</div>

<style>
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  
  audio {
    height: 32px;
  }
</style>