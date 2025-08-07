<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { authStore } from '$lib/stores/auth.js';
  import { webSocket } from '$lib/stores/notifications.js';
  import Toast from '$lib/components/Toast.svelte';
  import ProgressToast from '$lib/components/notifications/ProgressToast.svelte';

  let mounted = false;

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
    <!-- Toast Notifications -->
    <Toast />
    <!-- Progress Notifications -->
    <ProgressToast />
  </div>
{:else}
  <!-- Loading state while initializing -->
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
  </div>
{/if}