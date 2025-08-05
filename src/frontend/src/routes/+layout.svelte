<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { authStore } from '$lib/stores/auth.js';

  let mounted = false;

  onMount(() => {
    // Initialize auth state automatically
    authStore.init();
    mounted = true;
  });
</script>

{#if mounted}
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <slot />
  </div>
{:else}
  <!-- Loading state while initializing -->
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
  </div>
{/if}