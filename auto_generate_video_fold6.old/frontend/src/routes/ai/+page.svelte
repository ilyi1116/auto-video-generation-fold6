<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { apiClient } from '$lib/api/client';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Badge from '$lib/components/ui/Badge.svelte';
  import LoadingSpinner from '$lib/components/ui/LoadingSpinner.svelte';
  import Alert from '$lib/components/ui/Alert.svelte';

  let capabilities = null;
  let healthStatus = null;
  let isLoading = true;
  let error = null;

  const aiServices = [
    {
      id: 'text_generation',
      name: 'Script Generation',
      description: 'Generate engaging scripts and titles for your videos',
      icon: '📝',
      route: '/ai/script',
      features: ['Script Generation', 'Title Creation', 'Content Optimization']
    },
    {
      id: 'image_generation', 
      name: 'Image Generation',
      description: 'Create stunning visuals and graphics with AI',
      icon: '🎨',
      route: '/ai/images',
      features: ['Image Generation', 'Style Transfer', 'Upscaling', 'Variations']
    },
    {
      id: 'audio_processing',
      name: 'Voice Synthesis',
      description: 'Convert text to natural-sounding speech',
      icon: '🎤',
      route: '/ai/voice',
      features: ['Voice Synthesis', 'Voice Cloning', 'Audio Enhancement']
    },
    {
      id: 'music_generation',
      name: 'Music Generation',
      description: 'Generate custom background music for your videos',
      icon: '🎵',
      route: '/ai/music',
      features: ['Music Generation', 'Variations', 'Platform Optimization']
    }
  ];

  onMount(async () => {
    await Promise.all([
      loadCapabilities(),
      loadHealthStatus()
    ]);
    isLoading = false;
  });

  async function loadCapabilities() {
    try {
      const response = await apiClient.getAICapabilities();
      capabilities = response.data.capabilities;
    } catch (err) {
      console.error('Failed to load capabilities:', err);
      error = 'Failed to load AI service capabilities';
    }
  }

  async function loadHealthStatus() {
    try {
      const response = await apiClient.getAIHealthStatus();
      healthStatus = response.data.details;
    } catch (err) {
      console.error('Failed to load health status:', err);
    }
  }

  function getServiceStatus(serviceId) {
    if (!capabilities || !healthStatus) return 'unknown';
    
    const available = capabilities[serviceId]?.available;
    const healthy = healthStatus.services[serviceId];
    
    if (available && healthy) return 'healthy';
    if (available && !healthy) return 'degraded';
    return 'unavailable';
  }

  function getStatusColor(status) {
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'degraded': return 'bg-yellow-500';
      case 'unavailable': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  }

  function getStatusText(status) {
    switch (status) {
      case 'healthy': return 'Online';
      case 'degraded': return 'Degraded';
      case 'unavailable': return 'Offline';
      default: return 'Unknown';
    }
  }

  async function generateCompleteContent() {
    goto('/create');
  }

  function navigateToService(route) {
    goto(route);
  }
</script>

<svelte:head>
  <title>AI Services - Auto Video Generation</title>
  <meta name="description" content="Comprehensive AI services for automated video content creation" />
</svelte:head>

<div class="container mx-auto px-4 py-8">
  <!-- Page Header -->
  <div class="mb-8">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white">AI Services Dashboard</h1>
        <p class="text-gray-600 dark:text-gray-400 mt-2">
          Manage and monitor your AI-powered content generation tools
        </p>
      </div>
      
      <Button on:click={generateCompleteContent} class="flex items-center">
        <span class="mr-2">🚀</span>
        Generate Complete Video
      </Button>
    </div>
  </div>

  {#if isLoading}
    <div class="flex justify-center items-center h-64">
      <LoadingSpinner size="lg" />
    </div>
  {:else if error}
    <Alert type="error" message={error} />
  {:else}
    <!-- System Health Overview -->
    {#if healthStatus}
      <Card class="mb-8">
        <div slot="header">
          <h2 class="text-xl font-semibold text-gray-900 dark:text-white">System Health</h2>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div class="text-center">
            <div class="text-2xl font-bold text-gray-900 dark:text-white">
              {healthStatus.healthy_services}/{healthStatus.total_services}
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400">Services Online</p>
          </div>
          
          <div class="text-center">
            <div class="text-2xl font-bold {healthStatus.overall_status === 'healthy' ? 'text-green-600' : 'text-yellow-600'}">
              {healthStatus.overall_status.charAt(0).toUpperCase() + healthStatus.overall_status.slice(1)}
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400">Overall Status</p>
          </div>
          
          <div class="text-center">
            <div class="text-2xl font-bold text-gray-900 dark:text-white">
              {Object.values(healthStatus.api_keys_configured).filter(Boolean).length}
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400">APIs Configured</p>
          </div>
          
          <div class="text-center">
            <div class="text-2xl font-bold {healthStatus.initialized ? 'text-green-600' : 'text-red-600'}">
              {healthStatus.initialized ? 'Ready' : 'Initializing'}
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-400">System Status</p>
          </div>
        </div>
      </Card>
    {/if}

    <!-- AI Services Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
      {#each aiServices as service}
        {@const status = getServiceStatus(service.id)}
        {@const serviceCapabilities = capabilities?.[service.id]}
        
        <Card class="hover:shadow-lg transition-shadow cursor-pointer" on:click={() => navigateToService(service.route)}>
          <div class="p-6">
            <!-- Service Header -->
            <div class="flex items-center justify-between mb-4">
              <div class="text-3xl">{service.icon}</div>
              <div class="flex items-center space-x-2">
                <div class="w-2 h-2 rounded-full {getStatusColor(status)}"></div>
                <span class="text-xs text-gray-600 dark:text-gray-400">
                  {getStatusText(status)}
                </span>
              </div>
            </div>
            
            <!-- Service Info -->
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              {service.name}
            </h3>
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
              {service.description}
            </p>
            
            <!-- Features -->
            {#if serviceCapabilities?.features}
              <div class="mb-4">
                <div class="flex flex-wrap gap-1">
                  {#each serviceCapabilities.features.slice(0, 3) as feature}
                    <Badge size="xs" variant="outline">{feature.replace('_', ' ')}</Badge>
                  {/each}
                  {#if serviceCapabilities.features.length > 3}
                    <Badge size="xs" variant="outline">+{serviceCapabilities.features.length - 3}</Badge>
                  {/if}
                </div>
              </div>
            {:else}
              <div class="mb-4">
                <div class="flex flex-wrap gap-1">
                  {#each service.features.slice(0, 3) as feature}
                    <Badge size="xs" variant="outline">{feature}</Badge>
                  {/each}
                </div>
              </div>
            {/if}
            
            <!-- Action Button -->
            <Button 
              variant="outline" 
              size="sm" 
              class="w-full"
              disabled={status === 'unavailable'}
              on:click={(e) => {
                e.stopPropagation();
                navigateToService(service.route);
              }}
            >
              {status === 'unavailable' ? 'Service Offline' : 'Open Service'}
            </Button>
          </div>
        </Card>
      {/each}
    </div>

    <!-- Quick Actions -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Complete Video Generation -->
      <Card>
        <div slot="header">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Complete Video Generation</h3>
        </div>
        
        <div class="space-y-4">
          <p class="text-gray-600 dark:text-gray-400">
            Generate a complete video with script, visuals, voice, and music in one workflow.
          </p>
          
          <div class="flex flex-wrap gap-2">
            <Badge>Script Generation</Badge>
            <Badge>Image Creation</Badge>
            <Badge>Voice Synthesis</Badge>
            <Badge>Background Music</Badge>
            <Badge>Platform Optimization</Badge>
          </div>
          
          <Button on:click={generateCompleteContent} class="w-full">
            Start Complete Generation
          </Button>
        </div>
      </Card>

      <!-- Service Configuration -->
      <Card>
        <div slot="header">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Service Configuration</h3>
        </div>
        
        <div class="space-y-4">
          <p class="text-gray-600 dark:text-gray-400">
            Manage API keys and service settings for optimal performance.
          </p>
          
          {#if healthStatus?.api_keys_configured}
            <div class="space-y-2">
              {#each Object.entries(healthStatus.api_keys_configured) as [service, configured]}
                <div class="flex items-center justify-between">
                  <span class="text-sm text-gray-700 dark:text-gray-300 capitalize">{service}</span>
                  <Badge variant={configured ? 'default' : 'outline'} size="xs">
                    {configured ? 'Configured' : 'Not Set'}
                  </Badge>
                </div>
              {/each}
            </div>
          {/if}
          
          <Button variant="outline" on:click={() => goto('/settings')} class="w-full">
            Manage Configuration
          </Button>
        </div>
      </Card>
    </div>
  {/if}
</div>