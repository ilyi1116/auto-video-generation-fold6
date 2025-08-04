<script>
  import { authStore } from '$lib/stores/auth';
  import { toastStore } from '$lib/stores/toast';
  import { Mail, ArrowLeft, CheckCircle } from 'lucide-svelte';

  let email = '';
  let isLoading = false;
  let isSubmitted = false;
  let errors = {};

  // Form validation
  function validateForm() {
    errors = {};

    if (!email) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = 'Please enter a valid email address';
    }

    return Object.keys(errors).length === 0;
  }

  // Handle form submission
  async function handleSubmit() {
    if (!validateForm()) return;

    isLoading = true;

    try {
      const result = await authStore.requestPasswordReset(email);
      
      if (result.success) {
        isSubmitted = true;
      }
      
      isLoading = false;
    } catch (error) {
      console.error('Password reset error:', error);
      toastStore.error('An unexpected error occurred. Please try again.');
      isLoading = false;
    }
  }

  // Reset form to try again
  function resetForm() {
    isSubmitted = false;
    email = '';
    errors = {};
  }
</script>

<svelte:head>
  <title>Forgot Password - AutoVideo</title>
  <meta name="description" content="Reset your AutoVideo account password" />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
  <!-- Back to login -->
  <div class="absolute top-8 left-8">
    <a
      href="/login"
      class="inline-flex items-center text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
    >
      <ArrowLeft class="w-4 h-4 mr-2" />
      Back to sign in
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

    {#if !isSubmitted}
      <!-- Reset password form -->
      <div class="text-center mb-8">
        <h2 class="text-3xl font-bold text-gray-900 dark:text-white">
          Forgot your password?
        </h2>
        <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
          No worries! Enter your email address and we'll send you a link to reset your password.
        </p>
      </div>

      <div class="bg-white dark:bg-gray-800 py-8 px-4 shadow-lg sm:rounded-lg sm:px-10 border border-gray-200 dark:border-gray-700">
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
                placeholder="Enter your email address"
                disabled={isLoading}
              />
            </div>
            {#if errors.email}
              <p class="form-error">{errors.email}</p>
            {/if}
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
                Sending reset link...
              {:else}
                Send reset link
              {/if}
            </button>
          </div>
        </form>

        <!-- Additional help -->
        <div class="mt-6 text-center">
          <p class="text-sm text-gray-600 dark:text-gray-400">
            Remember your password?
            <a href="/login" class="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400">
              Sign in
            </a>
          </p>
        </div>
      </div>
    {:else}
      <!-- Success message -->
      <div class="text-center mb-8">
        <div class="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle class="w-8 h-8 text-green-600 dark:text-green-400" />
        </div>
        <h2 class="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Check your email
        </h2>
        <p class="text-gray-600 dark:text-gray-300 mb-6">
          We've sent a password reset link to:
        </p>
        <p class="text-lg font-medium text-gray-900 dark:text-white mb-6">
          {email}
        </p>
      </div>

      <div class="bg-white dark:bg-gray-800 py-8 px-4 shadow-lg sm:rounded-lg sm:px-10 border border-gray-200 dark:border-gray-700">
        <!-- Instructions -->
        <div class="space-y-4 mb-6">
          <div class="flex items-start space-x-3">
            <div class="w-6 h-6 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              <span class="text-primary-600 dark:text-primary-400 text-sm font-bold">1</span>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-300">
              Check your email inbox (and spam folder)
            </p>
          </div>
          
          <div class="flex items-start space-x-3">
            <div class="w-6 h-6 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              <span class="text-primary-600 dark:text-primary-400 text-sm font-bold">2</span>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-300">
              Click the reset link in the email
            </p>
          </div>
          
          <div class="flex items-start space-x-3">
            <div class="w-6 h-6 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
              <span class="text-primary-600 dark:text-primary-400 text-sm font-bold">3</span>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-300">
              Create a new password and sign in
            </p>
          </div>
        </div>

        <!-- Actions -->
        <div class="space-y-4">
          <button
            type="button"
            class="btn-secondary w-full"
            on:click={resetForm}
          >
            Try a different email
          </button>
          
          <div class="text-center">
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Didn't receive the email?
              <button
                type="button"
                class="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400 underline"
                on:click={handleSubmit}
                disabled={isLoading}
              >
                Resend
              </button>
            </p>
          </div>
        </div>
      </div>
    {/if}

    <!-- Help section -->
    <div class="mt-8 text-center">
      <p class="text-sm text-gray-600 dark:text-gray-400">
        Still having trouble? 
        <a href="/help" class="text-primary-600 hover:text-primary-500 dark:text-primary-400 font-medium">
          Contact Support
        </a>
      </p>
    </div>
  </div>
</div>