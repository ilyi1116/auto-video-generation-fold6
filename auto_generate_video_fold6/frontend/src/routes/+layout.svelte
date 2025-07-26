<script>
  import '../app.css';
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { authStore } from '$lib/stores/auth';
  import Header from '$lib/components/Header.svelte';
  import Sidebar from '$lib/components/Sidebar.svelte';
  import Toast from '$lib/components/Toast.svelte';
  import LoadingOverlay from '$lib/components/LoadingOverlay.svelte';

  let mounted = false;
  let sidebarOpen = false;

  onMount(() => {
    // Initialize auth state from localStorage
    authStore.initialize();
    mounted = true;
  });

  // Close sidebar when route changes
  $: if ($page.route) {
    sidebarOpen = false;
  }

  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
  }

  // Check if current route requires authentication
  $: requiresAuth = $page.route?.id?.startsWith('/(protected)') || 
                   $page.route?.id?.includes('/dashboard') ||
                   $page.route?.id?.includes('/projects');

  // Redirect to login if not authenticated and route requires auth
  $: if (mounted && requiresAuth && !$authStore.isAuthenticated) {
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }
</script>

{#if mounted}
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Loading overlay -->
    <LoadingOverlay />
    
    <!-- Header -->
    <Header bind:sidebarOpen />
    
    <div class="flex">
      <!-- Sidebar -->
      {#if $authStore.isAuthenticated}
        <Sidebar bind:open={sidebarOpen} />
      {/if}
      
      <!-- Main content -->
      <main class="flex-1 {$authStore.isAuthenticated ? 'lg:ml-64' : ''} pt-16">
        <div class="container mx-auto px-4 py-8">
          <slot />
        </div>
      </main>
    </div>

    <!-- Toast notifications -->
    <Toast />
  </div>
{:else}
  <!-- Loading state while initializing -->
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
  </div>
{/if}