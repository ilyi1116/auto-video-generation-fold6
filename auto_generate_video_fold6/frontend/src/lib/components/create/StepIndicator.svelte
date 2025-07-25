<script>
  import { Check } from 'lucide-svelte';

  export let steps = [];
  export let currentStep = 1;
  export let onStepClick = () => {};
</script>

<div class="mb-8">
  <div class="flex items-center justify-between">
    {#each steps as step, index}
      <div class="flex items-center {index < steps.length - 1 ? 'flex-1' : ''}">
        <!-- Step Circle -->
        <button
          type="button"
          class="relative flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors {
            step.id < currentStep 
              ? 'bg-green-600 border-green-600 text-white'
              : step.id === currentStep
              ? 'bg-primary-600 border-primary-600 text-white'
              : 'bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600 text-gray-500 dark:text-gray-400'
          }"
          on:click={() => onStepClick(step.id)}
        >
          {#if step.id < currentStep}
            <Check class="w-5 h-5" />
          {:else}
            <span class="text-sm font-medium">{step.id}</span>
          {/if}
        </button>
        
        <!-- Step Info -->
        <div class="ml-3 min-w-0 flex-1">
          <p class="text-sm font-medium text-gray-900 dark:text-white">
            {step.title}
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            {step.description}
          </p>
        </div>
        
        <!-- Connector Line -->
        {#if index < steps.length - 1}
          <div class="hidden sm:block flex-1 mx-4">
            <div class="h-0.5 {
              step.id < currentStep 
                ? 'bg-green-600' 
                : 'bg-gray-300 dark:bg-gray-600'
            }"></div>
          </div>
        {/if}
      </div>
    {/each}
  </div>
</div>