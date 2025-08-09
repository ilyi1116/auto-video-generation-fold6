<script>
  import { errorStore } from '$lib/stores/error.js';
  import { fade } from 'svelte/transition';

  let error = null;

  errorStore.subscribe((state) => {
    error = state;
  });

  function closeError() {
    errorStore.clear();
  }
</script>

{#if error}
  <div 
    class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
    transition:fade="{{ duration: 200 }}"
  >
    <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md mx-4 shadow-xl">
      <!-- Error Icon -->
      <div class="flex items-center mb-4">
        <div class="flex-shrink-0">
          <svg class="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L4.232 15.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h3 class="ml-3 text-lg font-medium text-gray-900 dark:text-white">
          {error.title || 'Error'}
        </h3>
      </div>
      
      <!-- Error Message -->
      <div class="mb-4">
        <p class="text-gray-700 dark:text-gray-300">
          {error.message || 'An unexpected error occurred.'}
        </p>
        {#if error.details}
          <details class="mt-2">
            <summary class="text-sm text-gray-500 dark:text-gray-400 cursor-pointer">
              Show details
            </summary>
            <pre class="mt-2 text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 p-2 rounded overflow-auto max-h-32">
{error.details}
            </pre>
          </details>
        {/if}
      </div>
      
      <!-- Actions -->
      <div class="flex justify-end space-x-3">
        {#if error.retry}
          <button
            class="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 text-sm"
            on:click={() => { error.retry(); closeError(); }}
          >
            Retry
          </button>
        {/if}
        <button
          class="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-400 dark:hover:bg-gray-500 focus:outline-none focus:ring-2 focus:ring-gray-500 text-sm"
          on:click={closeError}
        >
          Close
        </button>
      </div>
    </div>
  </div>
{/if}