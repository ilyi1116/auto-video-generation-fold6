<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { dev } from '$app/environment';
  import { authStore } from '$lib/stores/auth.js';
  import { webSocket } from '$lib/stores/notifications.js';
  import Toast from '$lib/components/Toast.svelte';
  import ProgressToast from '$lib/components/notifications/ProgressToast.svelte';
  import GlobalLoading from '$lib/components/ui/GlobalLoading.svelte';
  import GlobalError from '$lib/components/ui/GlobalError.svelte';
  import VitalsMonitor from '$lib/components/performance/VitalsMonitor.svelte';
  
  // 開發環境下導入調試工具
  let debugTools;
  if (dev) {
    import('$lib/dev/debugTools.js').then(module => {
      debugTools = module.default;
    });
  }

  let mounted = false;
  
  // 性能監控配置
  $: vitalsConfig = {
    enabled: true, // 總是啟用性能監控
    debug: dev, // 開發環境下啟用調試
    showWidget: dev, // 開發環境下顯示監控小組件
    position: 'bottom-right',
    customTags: {
      app: 'auto-video-frontend',
      version: '1.0.0',
      env: dev ? 'development' : 'production'
    }
  };

  onMount(() => {
    // Initialize auth state automatically
    authStore.init();
    
    // Connect WebSocket if authenticated
    authStore.subscribe((auth) => {
      if (auth.isAuthenticated && auth.user) {
        webSocket.connect(auth.user.id || auth.user.email);
      } else {
        webSocket.disconnect();
      }
    });
    
    mounted = true;
  });
</script>

{#if mounted}
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <slot />
    
    <!-- Global Components -->
    <Toast />
    <ProgressToast />
    <GlobalLoading />
    <GlobalError />
    
    <!-- Performance Monitoring -->
    <VitalsMonitor {...vitalsConfig} />
  </div>
{:else}
  <!-- Loading state while initializing -->
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
  </div>
{/if}