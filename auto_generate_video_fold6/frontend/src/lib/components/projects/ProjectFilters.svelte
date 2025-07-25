<script>
  import { Search, Filter } from 'lucide-svelte';

  export let searchQuery = '';
  export let selectedFilter = 'all';
  export let filters = [];

  function handleSearch(event) {
    searchQuery = event.target.value;
  }

  function handleFilterChange(filterValue) {
    selectedFilter = filterValue;
  }
</script>

<div class="flex flex-col sm:flex-row gap-4 mb-6">
  <!-- Search -->
  <div class="relative flex-1">
    <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
      <Search class="h-5 w-5 text-gray-400" />
    </div>
    <input
      type="text"
      bind:value={searchQuery}
      on:input={handleSearch}
      placeholder="Search projects..."
      class="form-input pl-10 w-full"
    />
  </div>

  <!-- Filter Tabs -->
  <div class="flex space-x-1 bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
    {#each filters as filter}
      <button
        type="button"
        class="px-3 py-2 text-sm font-medium rounded-md transition-colors {
          selectedFilter === filter.value
            ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
            : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
        }"
        on:click={() => handleFilterChange(filter.value)}
      >
        {filter.label}
        {#if filter.count > 0}
          <span class="ml-1 text-xs px-1.5 py-0.5 bg-gray-200 dark:bg-gray-600 rounded-full">
            {filter.count}
          </span>
        {/if}
      </button>
    {/each}
  </div>
</div>