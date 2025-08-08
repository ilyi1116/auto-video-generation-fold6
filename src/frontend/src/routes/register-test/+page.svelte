<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  
  export let data;

  let formData = {
    first_name: '',
    last_name: '',
    email: data?.email || '',
    password: '',
    confirmPassword: ''
  };
  
  let isLoading = false;
  let errors = {};
  let acceptTerms = false;

  // 不調用複雜的store初始化
  onMount(() => {
    console.log('Register test page mounted successfully');
  });

  // 簡單的表單驗證
  function validateForm() {
    errors = {};
    if (!formData.first_name.trim()) errors.first_name = 'First name is required';
    if (!formData.last_name.trim()) errors.last_name = 'Last name is required';
    if (!formData.email) errors.email = 'Email is required';
    if (!formData.password) errors.password = 'Password is required';
    if (formData.password !== formData.confirmPassword) errors.confirmPassword = 'Passwords do not match';
    if (!acceptTerms) errors.terms = 'You must accept the Terms of Service';
    return Object.keys(errors).length === 0;
  }

  // 簡單的提交處理
  async function handleSubmit() {
    if (!validateForm()) return;
    
    isLoading = true;
    
    try {
      // 模擬API調用
      const response = await fetch('http://localhost:8000/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          first_name: formData.first_name,
          last_name: formData.last_name,
          email: formData.email,
          password: formData.password
        })
      });
      
      const result = await response.json();
      
      if (result.success) {
        alert('註冊成功！');
        goto('/login');
      } else {
        errors.general = result.error || 'Registration failed';
      }
    } catch (error) {
      console.error('Registration error:', error);
      errors.general = 'Network error occurred';
    } finally {
      isLoading = false;
    }
  }
</script>

<svelte:head>
  <title>註冊測試頁面 - AutoVideo</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 flex items-center justify-center py-12 px-4">
  <div class="max-w-md w-full space-y-8">
    <!-- Header -->
    <div>
      <h2 class="mt-6 text-center text-3xl font-bold text-gray-900">
        註冊測試頁面
      </h2>
      <p class="mt-2 text-center text-sm text-gray-600">
        這是一個簡化版本，不依賴複雜的store
      </p>
    </div>

    <!-- Form -->
    <div class="bg-white py-8 px-6 shadow rounded-lg">
      {#if errors.general}
        <div class="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
          <p class="text-sm text-red-800">{errors.general}</p>
        </div>
      {/if}

      <form on:submit|preventDefault={handleSubmit} class="space-y-6">
        <!-- Name fields -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700">名</label>
            <input
              type="text"
              bind:value={formData.first_name}
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 {errors.first_name ? 'border-red-500' : ''}"
              placeholder="名"
              disabled={isLoading}
            />
            {#if errors.first_name}
              <p class="text-red-600 text-xs mt-1">{errors.first_name}</p>
            {/if}
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700">姓</label>
            <input
              type="text"
              bind:value={formData.last_name}
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 {errors.last_name ? 'border-red-500' : ''}"
              placeholder="姓"
              disabled={isLoading}
            />
            {#if errors.last_name}
              <p class="text-red-600 text-xs mt-1">{errors.last_name}</p>
            {/if}
          </div>
        </div>

        <!-- Email field -->
        <div>
          <label class="block text-sm font-medium text-gray-700">Email</label>
          <input
            type="email"
            bind:value={formData.email}
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 {errors.email ? 'border-red-500' : ''}"
            placeholder="your@email.com"
            disabled={isLoading}
          />
          {#if errors.email}
            <p class="text-red-600 text-xs mt-1">{errors.email}</p>
          {/if}
        </div>

        <!-- Password field -->
        <div>
          <label class="block text-sm font-medium text-gray-700">密碼</label>
          <input
            type="password"
            bind:value={formData.password}
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 {errors.password ? 'border-red-500' : ''}"
            placeholder="創建一個強密碼"
            disabled={isLoading}
          />
          {#if errors.password}
            <p class="text-red-600 text-xs mt-1">{errors.password}</p>
          {/if}
        </div>

        <!-- Confirm password field -->
        <div>
          <label class="block text-sm font-medium text-gray-700">確認密碼</label>
          <input
            type="password"
            bind:value={formData.confirmPassword}
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 {errors.confirmPassword ? 'border-red-500' : ''}"
            placeholder="再次輸入密碼"
            disabled={isLoading}
          />
          {#if errors.confirmPassword}
            <p class="text-red-600 text-xs mt-1">{errors.confirmPassword}</p>
          {/if}
        </div>

        <!-- Terms checkbox -->
        <div class="flex items-start">
          <input
            type="checkbox"
            bind:checked={acceptTerms}
            class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded {errors.terms ? 'border-red-500' : ''}"
          />
          <label class="ml-2 block text-sm text-gray-700">
            我同意服務條款和隱私政策
          </label>
        </div>
        {#if errors.terms}
          <p class="text-red-600 text-xs">{errors.terms}</p>
        {/if}

        <!-- Submit button -->
        <button
          type="submit"
          disabled={isLoading || !acceptTerms}
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {#if isLoading}
            處理中...
          {:else}
            創建帳戶
          {/if}
        </button>
      </form>

      <div class="mt-6 text-center space-y-2">
        <a href="/login" class="text-blue-600 hover:text-blue-500">已有帳戶？登入</a><br>
        <a href="/register" class="text-gray-600 hover:text-gray-800">回到完整註冊頁面</a><br>
        <a href="/register-simple" class="text-gray-600 hover:text-gray-800">超簡單版本</a>
      </div>
    </div>
  </div>
</div>