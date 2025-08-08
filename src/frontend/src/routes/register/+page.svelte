<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  
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
  let subscribeNewsletter = true;
  let message = '';

  // 不依賴store的認證檢查
  onMount(() => {
    if (browser) {
      const token = localStorage.getItem('auth_token');
      if (token) {
        goto('/dashboard');
      }
    }
  });

  // 表單驗證
  function validateForm() {
    errors = {};
    if (!formData.first_name.trim()) errors.first_name = 'First name is required';
    if (!formData.last_name.trim()) errors.last_name = 'Last name is required';
    if (!formData.email) errors.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) errors.email = 'Invalid email';
    if (!formData.password) errors.password = 'Password is required';
    else if (formData.password.length < 6) errors.password = 'Password must be at least 6 characters';
    if (formData.password !== formData.confirmPassword) errors.confirmPassword = 'Passwords do not match';
    if (!acceptTerms) errors.terms = 'You must accept the Terms of Service';
    return Object.keys(errors).length === 0;
  }

  // 處理註冊
  async function handleSubmit() {
    if (!validateForm()) return;
    
    isLoading = true;
    message = '';
    
    try {
      const response = await fetch('/api/v1/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          first_name: formData.first_name.trim(),
          last_name: formData.last_name.trim(),
          email: formData.email.toLowerCase(),
          password: formData.password,
          subscribe_newsletter: subscribeNewsletter
        })
      });
      
      const result = await response.json();
      
      if (result.success && result.data) {
        message = '註冊成功！正在重定向...';
        
        // 保存token
        if (browser) {
          localStorage.setItem('auth_token', result.data.access_token);
        }
        
        setTimeout(() => {
          goto('/dashboard');
        }, 1500);
      } else {
        if (result.error && result.error.includes('already exists')) {
          message = 'This email is already registered.';
          setTimeout(() => {
            if (confirm('This email is already registered. Go to login page?')) {
              goto(`/login?email=${encodeURIComponent(formData.email)}`);
            }
          }, 2000);
        } else {
          errors.general = result.error || 'Registration failed. Please try again.';
        }
      }
    } catch (error) {
      console.error('Registration error:', error);
      errors.general = 'Network error occurred. Please try again.';
    } finally {
      isLoading = false;
    }
  }

  // 社交登入處理
  function handleSocialLogin(provider) {
    alert(`${provider} registration coming soon!`);
  }
</script>

<svelte:head>
  <title>Sign Up - AutoVideo</title>
  <meta name="description" content="Create your AutoVideo account and start generating AI-powered viral videos" />
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
        Create your account
      </h2>
      <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
        Already have an account?
        <a href="/login" class="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400">
          Sign in here
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

      <!-- Benefits reminder -->
      <div class="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <h3 class="text-sm font-medium text-blue-800 dark:text-blue-200 mb-2">
          🎉 Get started with your free account:
        </h3>
        <ul class="text-xs text-blue-700 dark:text-blue-300 space-y-1">
          <li>• 5 AI-generated videos per month</li>
          <li>• Access to basic templates</li>
          <li>• Community support</li>
        </ul>
      </div>

      <!-- Social registration -->
      <div class="space-y-3 mb-6">
        <button
          type="button"
          class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          on:click={() => handleSocialLogin('Google')}
        >
          G Sign up with Google
        </button>

        <button
          type="button"
          class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          on:click={() => handleSocialLogin('GitHub')}
        >
          GH Sign up with GitHub
        </button>
      </div>

      <!-- Divider -->
      <div class="relative mb-6">
        <div class="absolute inset-0 flex items-center">
          <div class="w-full border-t border-gray-300 dark:border-gray-600" />
        </div>
        <div class="relative flex justify-center text-sm">
          <span class="px-2 bg-white dark:bg-gray-800 text-gray-500 dark:text-gray-400">
            Or sign up with email
          </span>
        </div>
      </div>

      <!-- Registration form -->
      <form on:submit|preventDefault={handleSubmit} class="space-y-6">
        <!-- Name fields -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              First name
            </label>
            <input
              type="text"
              autocomplete="given-name"
              bind:value={formData.first_name}
              class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white {errors.first_name ? 'border-red-500' : ''}"
              placeholder="John"
              disabled={isLoading}
            />
            {#if errors.first_name}
              <p class="text-red-600 text-xs mt-1">{errors.first_name}</p>
            {/if}
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Last name
            </label>
            <input
              type="text"
              autocomplete="family-name"
              bind:value={formData.last_name}
              class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white {errors.last_name ? 'border-red-500' : ''}"
              placeholder="Doe"
              disabled={isLoading}
            />
            {#if errors.last_name}
              <p class="text-red-600 text-xs mt-1">{errors.last_name}</p>
            {/if}
          </div>
        </div>

        <!-- Email field -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Email address
          </label>
          <input
            type="email"
            autocomplete="email"
            bind:value={formData.email}
            class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white {errors.email ? 'border-red-500' : ''}"
            placeholder="john@example.com"
            disabled={isLoading}
          />
          {#if errors.email}
            <p class="text-red-600 text-xs mt-1">{errors.email}</p>
          {/if}
        </div>

        <!-- Password field -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Password
          </label>
          <input
            type="password"
            autocomplete="new-password"
            bind:value={formData.password}
            class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white {errors.password ? 'border-red-500' : ''}"
            placeholder="Create a strong password"
            disabled={isLoading}
          />
          {#if errors.password}
            <p class="text-red-600 text-xs mt-1">{errors.password}</p>
          {/if}
        </div>

        <!-- Confirm password field -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Confirm password
          </label>
          <input
            type="password"
            autocomplete="new-password"
            bind:value={formData.confirmPassword}
            class="mt-1 block w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white {errors.confirmPassword ? 'border-red-500' : ''}"
            placeholder="Confirm your password"
            disabled={isLoading}
          />
          {#if errors.confirmPassword}
            <p class="text-red-600 text-xs mt-1">{errors.confirmPassword}</p>
          {/if}
        </div>

        <!-- Checkboxes -->
        <div class="space-y-4">
          <!-- Terms acceptance -->
          <div class="flex items-start">
            <input
              type="checkbox"
              bind:checked={acceptTerms}
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600 rounded {errors.terms ? 'border-red-500' : ''}"
            />
            <label class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
              I agree to the
              <a href="/terms" class="text-blue-600 hover:text-blue-500 dark:text-blue-400" target="_blank">
                Terms of Service
              </a>
              and
              <a href="/privacy" class="text-blue-600 hover:text-blue-500 dark:text-blue-400" target="_blank">
                Privacy Policy
              </a>
            </label>
          </div>
          {#if errors.terms}
            <p class="text-red-600 text-xs mt-1">{errors.terms}</p>
          {/if}

          <!-- Newsletter subscription -->
          <div class="flex items-start">
            <input
              type="checkbox"
              bind:checked={subscribeNewsletter}
              class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 dark:border-gray-600 rounded"
            />
            <label class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
              Send me updates about new features and tips
            </label>
          </div>
        </div>

        <!-- Submit button -->
        <div>
          <button
            type="submit"
            disabled={isLoading || !acceptTerms}
            class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {#if isLoading}
              <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Creating account...
            {:else}
              Create account
            {/if}
          </button>
        </div>
      </form>
      
      <div class="mt-6 text-center space-y-2">
        <p class="text-xs text-gray-500 dark:text-gray-400">
          測試版本：
          <a href="/register-simple" class="text-blue-600 hover:text-blue-500">超簡單版本</a> |
          <a href="/register-test" class="text-blue-600 hover:text-blue-500">測試版本</a>
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