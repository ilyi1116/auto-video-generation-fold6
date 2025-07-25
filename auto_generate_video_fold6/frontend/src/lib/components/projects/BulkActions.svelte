<script>
  import { createEventDispatcher } from 'svelte';
  import { Trash2, Share2, Download, Copy, Archive } from 'lucide-svelte';

  export let selectedCount = 0;
  export let visible = false;

  const dispatch = createEventDispatcher();

  function handleBulkDelete() {
    dispatch('bulkDelete');
  }

  function handleBulkShare() {
    dispatch('bulkShare');
  }

  function handleBulkDownload() {
    dispatch('bulkDownload');
  }

  function handleBulkDuplicate() {
    dispatch('bulkDuplicate');
  }

  function handleBulkArchive() {
    dispatch('bulkArchive');
  }

  function handleClearSelection() {
    dispatch('clearSelection');
  }
</script>

{#if visible && selectedCount > 0}
  <div class="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-white dark:bg-gray-800 shadow-lg border dark:border-gray-700 rounded-lg px-6 py-3 z-50">
    <div class="flex items-center space-x-4">
      <span class="text-sm font-medium text-gray-900 dark:text-white">
        {selectedCount} project{selectedCount > 1 ? 's' : ''} selected
      </span>
      
      <div class="flex items-center space-x-2">
        <button
          type="button"
          class="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
          on:click={handleBulkShare}
        >
          <Share2 class="w-4 h-4 mr-1" />
          Share
        </button>
        
        <button
          type="button"
          class="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
          on:click={handleBulkDownload}
        >
          <Download class="w-4 h-4 mr-1" />
          Download
        </button>
        
        <button
          type="button"
          class="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
          on:click={handleBulkDuplicate}
        >
          <Copy class="w-4 h-4 mr-1" />
          Duplicate
        </button>
        
        <button
          type="button"
          class="inline-flex items-center px-3 py-1.5 border border-gray-300 dark:border-gray-600 text-sm font-medium rounded text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600"
          on:click={handleBulkArchive}
        >
          <Archive class="w-4 h-4 mr-1" />
          Archive
        </button>
        
        <button
          type="button"
          class="inline-flex items-center px-3 py-1.5 border border-red-300 dark:border-red-600 text-sm font-medium rounded text-red-700 dark:text-red-400 bg-white dark:bg-gray-700 hover:bg-red-50 dark:hover:bg-red-900/20"
          on:click={handleBulkDelete}
        >
          <Trash2 class="w-4 h-4 mr-1" />
          Delete
        </button>
      </div>
      
      <button
        type="button"
        class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
        on:click={handleClearSelection}
      >
        ✕
      </button>
    </div>
  </div>
{/if}