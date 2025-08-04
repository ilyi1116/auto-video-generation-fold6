<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/stores/auth';
  import { toastStore } from '$lib/stores/toast';
  import { Eye, EyeOff, Mail, Lock, ArrowLeft, Github, Google } from 'lucide-svelte';

  let email = '';
  let password = '';
  let showPassword = false;
  let isLoading = false;
  let errors = {};

  // Redirect if already authenticated
  onMount(() => {
    if ($authStore.isAuthenticated) {
      goto('/dashboard');
    }
  });

  // Form validation
  function validateForm() {
    errors = {};

    if (!email) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!password) {
      errors.password = 'Password is required';
    } else if (password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }

    return Object.keys(errors).length === 0;
  }

  // Handle form submission
  async function handleSubmit() {
    if (!validateForm()) return;

    isLoading = true;
    
    try {
      const result = await authStore.login(email, password);
      
      if (!result.success) {
        // Error handling is done in the auth store
        isLoading = false;
      }
      // Success redirect is handled in auth store
    } catch (error) {
      console.error('Login error:', error);
      toastStore.error('An unexpected error occurred. Please try again.');
      isLoading = false;
    }
  }

  // Demo login
  function demoLogin() {
    email = 'demo@example.com';
    password = 'demo123';
  }

  // Social login handlers
  function handleGoogleLogin() {
    toastStore.info('Google login coming soon!');
  }

  function handleGithubLogin() {
    toastStore.info('GitHub login coming soon!');
  }

  // Toggle password visibility
  function togglePassword() {
    showPassword = !showPassword;
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
      <ArrowLeft class="w-4 h-4 mr-2" />
      Back to home
    </a>
  </div>

  <div class="sm:mx-auto sm:w-full sm:max-w-md">
    <!-- Logo -->
    <div class="flex justify-center mb-6">
      <div class="flex items-center space-x-2">
        <div class="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg flex items-center justify-center">
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
        <a href="/register" class="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400">
          Sign up for free
        </a>
      </p>
    </div>
  </div>

  <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
    <div class="bg-white dark:bg-gray-800 py-8 px-4 shadow-lg sm:rounded-lg sm:px-10 border border-gray-200 dark:border-gray-700">
      <!-- Demo login button -->
      <div class="mb-6">
        <button
          type="button"
          class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
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
          class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
          on:click={handleGoogleLogin}
        >
          <Google class="w-4 h-4 mr-2" />
          Continue with Google
        </button>

        <button
          type="button"
          class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
          on:click={handleGithubLogin}
        >
          <Github class="w-4 h-4 mr-2" />
          Continue with GitHub
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
          <label for="email" class="form-label">
            Email address
          </label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Mail class="h-5 w-5 text-gray-400" />
            </div>
            <input
              id="email"
              name="email"
              type="email"
              autocomplete="email"
              bind:value={email}
              class="form-input pl-10 {errors.email ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}"
              placeholder="Enter your email"
              disabled={isLoading}
            />
          </div>
          {#if errors.email}
            <p class="form-error">{errors.email}</p>
          {/if}
        </div>

        <!-- Password field -->
        <div>
          <div class="flex justify-between">
            <label for="password" class="form-label">
              Password
            </label>
            <a href="/forgot-password" class="text-sm text-primary-600 hover:text-primary-500 dark:text-primary-400">
              Forgot password?
            </a>
          </div>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock class="h-5 w-5 text-gray-400" />
            </div>
            {#if showPassword}
              <input
                id="password"
                name="password"
                type="text"
                autocomplete="current-password"
                bind:value={password}
                class="form-input pl-10 pr-10 {errors.password ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}"
                placeholder="Enter your password"
                disabled={isLoading}
              />
            {:else}
              <input
                id="password"
                name="password"
                type="password"
                autocomplete="current-password"
                bind:value={password}
                class="form-input pl-10 pr-10 {errors.password ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}"
                placeholder="Enter your password"
                disabled={isLoading}
              />
            {/if}
            <button
              type="button"
              class="absolute inset-y-0 right-0 pr-3 flex items-center"
              on:click={togglePassword}
            >
              {#if showPassword}
                <EyeOff class="h-5 w-5 text-gray-400 hover:text-gray-600" />
              {:else}
                <Eye class="h-5 w-5 text-gray-400 hover:text-gray-600" />
              {/if}
            </button>
          </div>
          {#if errors.password}
            <p class="form-error">{errors.password}</p>
          {/if}
        </div>

        <!-- Remember me -->
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <input
              id="remember-me"
              name="remember-me"
              type="checkbox"
              class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 dark:border-gray-600 rounded"
            />
            <label for="remember-me" class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
              Remember me
            </label>
          </div>
        </div>

        <!-- Submit button -->
        <div>
          <button
            type="submit"
            disabled={isLoading}
            class="btn-primary w-full flex justify-center items-center"
          >
            {#if isLoading}
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
          <a href="/terms" class="text-primary-600 hover:text-primary-500 dark:text-primary-400">Terms of Service</a>
          and
          <a href="/privacy" class="text-primary-600 hover:text-primary-500 dark:text-primary-400">Privacy Policy</a>
        </p>
      </div>
    </div>

    <!-- Help section -->
    <div class="mt-8 text-center">
      <p class="text-sm text-gray-600 dark:text-gray-400">
        Need help? 
        <a href="/help" class="text-primary-600 hover:text-primary-500 dark:text-primary-400 font-medium">
          Contact Support
        </a>
      </p>
    </div>
  </div>
</div>