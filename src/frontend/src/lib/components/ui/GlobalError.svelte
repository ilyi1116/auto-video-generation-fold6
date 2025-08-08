<script>
  import { onMount } from 'svelte';
  import { errorStore } from '$lib/stores/loading.js';
  import { AlertCircle, X, RefreshCw, Info, AlertTriangle, XCircle, CheckCircle } from 'lucide-svelte';
  import { fade, fly } from 'svelte/transition';
  
  let mounted = false;
  
  onMount(() => {
    mounted = true;
  });
  
  function getErrorIcon(type) {
    switch (type) {
      case 'critical':
        return XCircle;
      case 'warning':
        return AlertTriangle;
      case 'info':
        return Info;
      case 'success':
        return CheckCircle;
      default:
        return AlertCircle;
    }
  }
  
  function getErrorColors(type) {
    switch (type) {
      case 'critical':
        return {
          bg: 'bg-red-50 dark:bg-red-900/20',
          border: 'border-red-200 dark:border-red-800',
          icon: 'text-red-600 dark:text-red-400',
          title: 'text-red-800 dark:text-red-300',
          text: 'text-red-700 dark:text-red-400',
          button: 'bg-red-600 hover:bg-red-700 text-white'
        };
      case 'warning':
        return {
          bg: 'bg-yellow-50 dark:bg-yellow-900/20',
          border: 'border-yellow-200 dark:border-yellow-800',
          icon: 'text-yellow-600 dark:text-yellow-400',
          title: 'text-yellow-800 dark:text-yellow-300',
          text: 'text-yellow-700 dark:text-yellow-400',
          button: 'bg-yellow-600 hover:bg-yellow-700 text-white'
        };
      case 'info':
        return {
          bg: 'bg-blue-50 dark:bg-blue-900/20',
          border: 'border-blue-200 dark:border-blue-800',
          icon: 'text-blue-600 dark:text-blue-400',
          title: 'text-blue-800 dark:text-blue-300',
          text: 'text-blue-700 dark:text-blue-400',
          button: 'bg-blue-600 hover:bg-blue-700 text-white'
        };
      case 'success':
        return {
          bg: 'bg-green-50 dark:bg-green-900/20',
          border: 'border-green-200 dark:border-green-800',
          icon: 'text-green-600 dark:text-green-400',
          title: 'text-green-800 dark:text-green-300',
          text: 'text-green-700 dark:text-green-400',
          button: 'bg-green-600 hover:bg-green-700 text-white'
        };
      default:
        return {
          bg: 'bg-gray-50 dark:bg-gray-900/20',
          border: 'border-gray-200 dark:border-gray-800',
          icon: 'text-gray-600 dark:text-gray-400',
          title: 'text-gray-800 dark:text-gray-300',
          text: 'text-gray-700 dark:text-gray-400',
          button: 'bg-gray-600 hover:bg-gray-700 text-white'
        };
    }
  }
  
  function dismissError(errorId) {
    errorStore.dismiss(errorId);
  }
  
  function retryAction() {
    // This would typically trigger a retry of the failed operation
    // For now, just hide the modal
    errorStore.hideModal();
  }
  
  function copyErrorDetails(error) {
    const details = {
      message: error.message,
      timestamp: error.timestamp,
      details: error.details,
      stack: error.stack
    };
    
    navigator.clipboard.writeText(JSON.stringify(details, null, 2))
      .then(() => {
        // Could show a small toast here
        console.log('Error details copied to clipboard');
      })
      .catch(err => {
        console.error('Failed to copy error details:', err);
      });
  }
  
  // Get active errors for toast notifications
  $: activeErrors = $errorStore.errors.filter(error => !error.dismissed);
  $: recentErrors = activeErrors.slice(-3); // Show only the 3 most recent errors
</script>

{#if mounted}
  <!-- Error Toast Notifications -->
  <div class="fixed top-4 right-4 z-50 space-y-3 max-w-sm">
    {#each recentErrors as error (error.id)}
      {@const colors = getErrorColors(error.type)}
      {@const ErrorIcon = getErrorIcon(error.type)}
      
      <div
        class="p-4 rounded-lg shadow-lg border {colors.bg} {colors.border}"
        transition:fly={{ x: 300, duration: 300 }}
      >
        <div class="flex items-start justify-between">
          <div class="flex items-start space-x-3 flex-1">
            <svelte:component this={ErrorIcon} class="w-5 h-5 {colors.icon} flex-shrink-0 mt-0.5" />
            
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium {colors.title}">
                {error.type === 'critical' ? '嚴重錯誤' : 
                 error.type === 'warning' ? '警告' :
                 error.type === 'info' ? '資訊' :
                 error.type === 'success' ? '成功' : '錯誤'}
              </p>
              <p class="text-sm {colors.text} mt-1 break-words">
                {error.message}
              </p>
              {#if error.details}
                <p class="text-xs {colors.text} mt-2 opacity-75">
                  {error.details}
                </p>
              {/if}
            </div>
          </div>
          
          <div class="flex items-center space-x-1 ml-2">
            {#if error.type === 'critical' || error.type === 'error'}
              <button
                type="button"
                on:click={() => errorStore.showError(error)}
                class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded"
                title="查看詳細資訊"
              >
                <Info class="w-4 h-4" />
              </button>
            {/if}
            <button
              type="button"
              on:click={() => dismissError(error.id)}
              class="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded"
              title="關閉"
            >
              <X class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    {/each}
  </div>

  <!-- Error Detail Modal -->
  {#if $errorStore.showModal && $errorStore.currentError}
    {@const error = $errorStore.currentError}
    {@const colors = getErrorColors(error.type)}
    {@const ErrorIcon = getErrorIcon(error.type)}
    
    <div
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      transition:fade={{ duration: 200 }}
    >
      <!-- Backdrop -->
      <div 
        class="absolute inset-0 bg-black bg-opacity-50 backdrop-blur-sm"
        role="button"
        tabindex="0"
        aria-label="關閉錯誤對話框"
        on:click={() => errorStore.hideModal()}
        on:keydown={(e) => (e.key === 'Enter' || e.key === ' ') && errorStore.hideModal()}
      ></div>
      
      <!-- Modal Content -->
      <div
        class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden"
        transition:fly={{ y: 20, duration: 300 }}
      >
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div class="flex items-center space-x-3">
            <svelte:component this={ErrorIcon} class="w-6 h-6 {colors.icon}" />
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
              {error.type === 'critical' ? '嚴重錯誤詳情' : '錯誤詳情'}
            </h3>
          </div>
          <button
            type="button"
            on:click={() => errorStore.hideModal()}
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            <X class="w-6 h-6" />
          </button>
        </div>
        
        <!-- Body -->
        <div class="p-6 overflow-y-auto max-h-96">
          <!-- Error Message -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
              錯誤訊息
            </h4>
            <p class="text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
              {error.message}
            </p>
          </div>
          
          <!-- Additional Details -->
          {#if error.details}
            <div class="mb-6">
              <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
                詳細資訊
              </h4>
              <p class="text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 p-3 rounded-lg whitespace-pre-wrap">
                {error.details}
              </p>
            </div>
          {/if}
          
          <!-- Timestamp -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
              發生時間
            </h4>
            <p class="text-sm text-gray-700 dark:text-gray-300">
              {error.timestamp.toLocaleString('zh-TW')}
            </p>
          </div>
          
          <!-- Stack Trace (only in development or for critical errors) -->
          {#if (import.meta.env.DEV || error.type === 'critical') && error.stack}
            <div class="mb-6">
              <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-2">
                技術詳情
              </h4>
              <details class="bg-gray-50 dark:bg-gray-700 rounded-lg">
                <summary class="p-3 cursor-pointer text-sm text-gray-600 dark:text-gray-400">
                  點擊查看技術詳情
                </summary>
                <pre class="p-3 text-xs font-mono text-gray-600 dark:text-gray-400 border-t border-gray-200 dark:border-gray-600 overflow-x-auto">{error.stack}</pre>
              </details>
            </div>
          {/if}
          
          <!-- Suggested Actions -->
          <div class="mb-6">
            <h4 class="text-sm font-medium text-gray-900 dark:text-white mb-3">
              建議動作
            </h4>
            <ul class="text-sm text-gray-700 dark:text-gray-300 space-y-2">
              <li class="flex items-start space-x-2">
                <span class="text-primary-600 dark:text-primary-400">•</span>
                <span>重新整理頁面並再試一次</span>
              </li>
              <li class="flex items-start space-x-2">
                <span class="text-primary-600 dark:text-primary-400">•</span>
                <span>檢查您的網路連線</span>
              </li>
              {#if error.type === 'critical'}
                <li class="flex items-start space-x-2">
                  <span class="text-primary-600 dark:text-primary-400">•</span>
                  <span>如果問題持續發生，請聯繫技術支援</span>
                </li>
              {/if}
            </ul>
          </div>
        </div>
        
        <!-- Footer -->
        <div class="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700">
          <div class="flex space-x-3">
            <button
              type="button"
              on:click={() => copyErrorDetails(error)}
              class="px-4 py-2 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
            >
              複製詳細資訊
            </button>
          </div>
          
          <div class="flex space-x-3">
            <button
              type="button"
              on:click={() => errorStore.hideModal()}
              class="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 transition-colors"
            >
              關閉
            </button>
            {#if error.type === 'error' || error.type === 'critical'}
              <button
                type="button"
                on:click={retryAction}
                class="px-4 py-2 text-sm {colors.button} rounded-lg transition-colors flex items-center space-x-2"
              >
                <RefreshCw class="w-4 h-4" />
                <span>重試</span>
              </button>
            {/if}
          </div>
        </div>
      </div>
    </div>
  {/if}
{/if}