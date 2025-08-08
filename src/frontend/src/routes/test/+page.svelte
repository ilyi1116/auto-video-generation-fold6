<script>
  console.log('Test page loaded');
</script>

<svelte:head>
  <title>Test Page</title>
</svelte:head>

<div class="p-8">
  <h1 class="text-2xl font-bold">Test Page</h1>
  <p>如果你看到這個頁面，說明基本的 SvelteKit 功能正常運行。</p>
  
  <div class="mt-4 space-y-2">
    <a href="/register" class="block text-blue-600 hover:underline">Go to Register</a>
    <a href="/login" class="block text-blue-600 hover:underline">Go to Login</a>
  </div>
</div>