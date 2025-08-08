<script>
  console.log('Simple register page loaded successfully');
</script>

<svelte:head>
  <title>Simple Register - AutoVideo</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 flex items-center justify-center">
  <div class="max-w-md w-full space-y-6">
    <div>
      <h2 class="text-center text-3xl font-bold text-gray-900">
        簡單註冊頁面測試
      </h2>
      <p class="mt-2 text-center text-sm text-gray-600">
        如果你看到這個頁面，表示基本的 Svelte 組件正常運行
      </p>
    </div>
    
    <div class="bg-white py-8 px-4 shadow rounded-lg">
      <form class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-700">
            Email
          </label>
          <input 
            type="email" 
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="your@email.com"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700">
            Password
          </label>
          <input 
            type="password"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="密碼"
          />
        </div>
        
        <button 
          type="button"
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          onclick="alert('測試按鈕點擊成功！')"
        >
          測試註冊
        </button>
      </form>
      
      <div class="mt-6 text-center">
        <a href="/register" class="text-blue-600 hover:text-blue-500">
          回到完整註冊頁面
        </a>
      </div>
    </div>
  </div>
</div>