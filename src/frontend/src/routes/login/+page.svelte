<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { authStore } from '$lib/stores/auth.js';

  export let data;

  let email = data?.email || '';
  let password = '';
  let errors = {};
  let message = '';

  // 使用 authStore 檢查認證狀態
  onMount(() => {
    if ($authStore.isAuthenticated) {
      goto('/dashboard');
    }
  });

  // 響應認證狀態變化
  $: {
    if ($authStore.isAuthenticated) {
      goto('/dashboard');
    }
  }

  // 表單驗證
  function validateForm() {
    errors = {};
    if (!email) errors.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.email = 'Invalid email address';
    if (!password) errors.password = 'Password is required';
    else if (password.length < 6) errors.password = 'Password must be at least 6 characters';
    return Object.keys(errors).length === 0;
  }

  // 處理登入 - 使用 authStore
  async function handleSubmit() {
    if (!validateForm()) return;

    message = '';
    errors = {};
    
    try {
      const result = await authStore.login(email.toLowerCase(), password);
      
      if (result.success) {
        message = '登入成功！正在重定向...';
        // authStore 會自動觸發重定向，不需要手動調用
      } else {
        errors.general = result.error || 'Login failed. Please check your credentials.';
      }
    } catch (error) {
      console.error('Login error:', error);
      errors.general = 'Network error occurred. Please try again.';
    }
  }

  // Demo登入
  function demoLogin() {
    email = 'demo@example.com';
    password = 'demo123';
  }

  // 社交登入處理
  function handleSocialLogin(provider) {
    alert(`${provider} login coming soon!`);
  }
</script>

<svelte:head>
  <title>Sign In - AutoVideo</title>
  <meta name="description" content="Sign in to your AutoVideo account to create AI-powered viral videos" />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
  <!-- Back to home -->
  <div class="absolute top-8 left-8">
    <a
      href="/"
      class="inline-flex items-center text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
    >
      ← Back to home
    </a>
  </div>

  <div class="sm:mx-auto sm:w-full sm:max-w-md">
    <!-- Logo -->
    <div class="flex justify-center mb-6">
      <div class="flex items-center space-x-2">
        <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
          <span class="text-white font-bold text-lg">AV</span>
        </div>
        <span class="text-2xl font-bold text-gray-900 dark:text-white">AutoVideo</span>
      </div>
    </div>

    <!-- Header -->
    <div class="text-center">
      <h2 class="text-3xl font-bold text-gray-900 dark:text-white">
        Welcome back
      </h2>
      <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
        Don't have an account?
        <a href="/register" class="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400">
          Sign up for free
        </a>
      </p>
    </div>
  </div>

  <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
    <div class="bg-white dark:bg-gray-800 py-8 px-4 shadow-lg sm:rounded-lg sm:px-10 border border-gray-200 dark:border-gray-700">
      
      <!-- 成功消息 -->
      {#if message}
        <div class="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
          <p class="text-sm text-green-800">{message}</p>
        </div>
      {/if}

      <!-- 一般錯誤 -->
      {#if errors.general}
        <div class="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <p class="text-sm text-red-800">{errors.general}</p>
        </div>
      {/if}

      <!-- Demo login button -->
      <div class="mb-6">
        <button
          type="button"
          class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          on:click={demoLogin}
        >
          <span class="mr-2">🚀</span>
          Try Demo Account
        </button>
      </div>

      <!-- Social login -->
      <div class="space-y-3 mb-6">
        <button
          type="button"
          class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          on:click={() => handleSocialLogin('Google')}
        >
          G Continue with Google
        </button>

        <button
          type="button"
          class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          on:click={() => handleSocialLogin('GitHub')}
        >
          GH Continue with GitHub
        </button>
      </div>

      <!-- Divider -->
      <div class="relative mb-6">
        <div class="absolute inset-0 flex items-center">
          <div class="w-full border-t border-gray-300 dark:border-gray-600" />
        </div>
        <div class="relative flex justify-center text-sm">
          <span class="px-2 bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400">
            Or continue with email
          </span>
        </div>
      </div>

      <!-- Login form -->
      <form on:submit|preventDefault={handleSubmit} class="space-y-6">
        <!-- Email field -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Email address
          </label>
          <input
            type="email"
            autocomplete="email"
            bind:value={email}
            class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white {errors.email ? 'border-red-500' : ''}"
            placeholder="Enter your email"
            disabled={$authStore.loading}
          />
          {#if errors.email}
            <p class="text-red-600 text-xs mt-1">{errors.email}</p>
          {/if}
        </div>

        <!-- Password field -->
        <div>
          <div class="flex justify-between">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Password
            </label>
            <a href="/forgot-password" class="text-sm text-blue-600 hover:text-blue-500 dark:text-blue-400">
              Forgot password?
            </a>
          </div>
          <input
            type="password"
            autocomplete="current-password"
            bind:value={password}
            class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white {errors.password ? 'border-red-500' : ''}"
            placeholder="Enter your password"
            disabled={$authStore.loading}
          />
          {#if errors.password}
            <p class="text-red-600 text-xs mt-1">{errors.password}</p>
          {/if}
        </div>

        <!-- Remember me -->
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <input
              type="checkbox"
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600 rounded"
            />
            <label class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
              Remember me
            </label>
          </div>
        </div>

        <!-- Submit button -->
        <div>
          <button
            type="submit"
            disabled={$authStore.loading}
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {#if $authStore.loading}
              <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Signing in...
            {:else}
              Sign in
            {/if}
          </button>
        </div>
      </form>

      <!-- Additional links -->
      <div class="mt-6 text-center">
        <p class="text-xs text-gray-500 dark:text-gray-400">
          By signing in, you agree to our
          <a href="/terms" class="text-blue-600 hover:text-blue-500 dark:text-blue-400">Terms of Service</a>
          and
          <a href="/privacy" class="text-blue-600 hover:text-blue-500 dark:text-blue-400">Privacy Policy</a>
        </p>
      </div>
    </div>

    <!-- Help section -->
    <div class="mt-8 text-center">
      <p class="text-sm text-gray-600 dark:text-gray-400">
        Need help? 
        <a href="/help" class="text-blue-600 hover:text-blue-500 dark:text-blue-400 font-medium">
          Contact Support
        </a>
      </p>
    </div>
  </div>
</div>