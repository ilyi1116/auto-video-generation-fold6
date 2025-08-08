<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/stores/auth';
  import { toastStore } from '$lib/stores/toast';
  import { Eye, EyeOff, Mail, Lock, User, ArrowLeft, Github, Google, Check } from 'lucide-svelte';

  let formData = {
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirmPassword: ''
  };
  
  let showPassword = false;
  let showConfirmPassword = false;
  let isLoading = false;
  let errors = {};
  let acceptTerms = false;
  let subscribeNewsletter = true;

  // Password strength indicators
  let passwordStrength = {
    score: 0,
    checks: {
      length: false,
      lowercase: false,
      uppercase: false,
      number: false,
      special: false
    }
  };

  // Redirect if already authenticated
  onMount(() => {
    if ($authStore.isAuthenticated) {
      goto('/dashboard');
    }
  });

  // Check password strength
  function checkPasswordStrength(password) {
    const checks = {
      length: password.length >= 8,
      lowercase: /[a-z]/.test(password),
      uppercase: /[A-Z]/.test(password),
      number: /[0-9]/.test(password),
      special: /[^A-Za-z0-9]/.test(password)
    };
    
    const score = Object.values(checks).filter(Boolean).length;
    
    passwordStrength = { score, checks };
  }

  // Form validation
  function validateForm() {
    errors = {};

    if (!formData.first_name.trim()) {
      errors.first_name = 'First name is required';
    }

    if (!formData.last_name.trim()) {
      errors.last_name = 'Last name is required';
    }

    if (!formData.email) {
      errors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email address';
    }

    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    } else if (passwordStrength.score < 3) {
      errors.password = 'Password is too weak. Please include uppercase, lowercase, numbers, and special characters.';
    }

    if (!formData.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    if (!acceptTerms) {
      errors.terms = 'You must accept the Terms of Service';
    }

    return Object.keys(errors).length === 0;
  }

  // Handle form submission
  async function handleSubmit() {
    if (!validateForm()) return;

    isLoading = true;

    try {
      const userData = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        email: formData.email.toLowerCase(),
        password: formData.password,
        subscribe_newsletter: subscribeNewsletter
      };

      const result = await authStore.register(userData);
      
      if (!result.success) {
        isLoading = false;
        toastStore.error(result.error || 'Registration failed. Please try again.');
      } else {
        // 註冊成功，顯示成功消息並重定向
        toastStore.success('Account created successfully! Welcome to AutoVideo!');
        isLoading = false;
        
        // 等待一下讓用戶看到成功消息，然後重定向
        setTimeout(() => {
          goto('/dashboard');
        }, 1500);
      }
    } catch (error) {
      console.error('Registration error:', error);
      toastStore.error('An unexpected error occurred. Please try again.');
      isLoading = false;
    }
  }

  // Social login handlers
  function handleGoogleLogin() {
    toastStore.info('Google registration coming soon!');
  }

  function handleGithubLogin() {
    toastStore.info('GitHub registration coming soon!');
  }

  // Password visibility toggles
  function togglePassword() {
    showPassword = !showPassword;
  }

  function toggleConfirmPassword() {
    showConfirmPassword = !showConfirmPassword;
  }

  // Reactive password strength checking
  $: checkPasswordStrength(formData.password);

  // Get password strength color
  function getStrengthColor(score) {
    if (score < 2) return 'bg-red-500';
    if (score < 4) return 'bg-yellow-500';
    return 'bg-green-500';
  }

  function getStrengthText(score) {
    if (score < 2) return 'Weak';
    if (score < 4) return 'Medium';
    return 'Strong';
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
        Create your account
      </h2>
      <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
        Already have an account?
        <a href="/login" class="font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400">
          Sign in here
        </a>
      </p>
    </div>
  </div>

  <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
    <div class="bg-white dark:bg-gray-800 py-8 px-4 shadow-lg sm:rounded-lg sm:px-10 border border-gray-200 dark:border-gray-700">
      <!-- Benefits reminder -->
      <div class="mb-6 p-4 bg-primary-50 dark:bg-primary-900/20 rounded-lg border border-primary-200 dark:border-primary-800">
        <h3 class="text-sm font-medium text-primary-800 dark:text-primary-200 mb-2">
          🎉 Get started with your free account:
        </h3>
        <ul class="text-xs text-primary-700 dark:text-primary-300 space-y-1">
          <li>• 5 AI-generated videos per month</li>
          <li>• Access to basic templates</li>
          <li>• Community support</li>
        </ul>
      </div>

      <!-- Social registration -->
      <div class="space-y-3 mb-6">
        <button
          type="button"
          class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
          on:click={handleGoogleLogin}
        >
          <Google class="w-4 h-4 mr-2" />
          Sign up with Google
        </button>

        <button
          type="button"
          class="w-full flex justify-center items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 transition-colors"
          on:click={handleGithubLogin}
        >
          <Github class="w-4 h-4 mr-2" />
          Sign up with GitHub
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
            <label for="first_name" class="form-label">
              First name
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <User class="h-5 w-5 text-gray-400" />
              </div>
              <input
                id="first_name"
                name="first_name"
                type="text"
                autocomplete="given-name"
                bind:value={formData.first_name}
                class="form-input pl-10 {errors.first_name ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}"
                placeholder="John"
                disabled={isLoading}
              />
            </div>
            {#if errors.first_name}
              <p class="form-error">{errors.first_name}</p>
            {/if}
          </div>

          <div>
            <label for="last_name" class="form-label">
              Last name
            </label>
            <input
              id="last_name"
              name="last_name"
              type="text"
              autocomplete="family-name"
              bind:value={formData.last_name}
              class="form-input {errors.last_name ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}"
              placeholder="Doe"
              disabled={isLoading}
            />
            {#if errors.last_name}
              <p class="form-error">{errors.last_name}</p>
            {/if}
          </div>
        </div>

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
              bind:value={formData.email}
              class="form-input pl-10 {errors.email ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}"
              placeholder="john@example.com"
              disabled={isLoading}
            />
          </div>
          {#if errors.email}
            <p class="form-error">{errors.email}</p>
          {/if}
        </div>

        <!-- Password field -->
        <div>
          <label for="password" class="form-label">
            Password
          </label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock class="h-5 w-5 text-gray-400" />
            </div>
            {#if showPassword}
              <input
                id="password"
                name="password"
                type="text"
                autocomplete="new-password"
                bind:value={formData.password}
                class="form-input pl-10 pr-10 {errors.password ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}"
                placeholder="Create a strong password"
                disabled={isLoading}
              />
            {:else}
              <input
                id="password"
                name="password"
                type="password"
                autocomplete="new-password"
                bind:value={formData.password}
                class="form-input pl-10 pr-10 {errors.password ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}"
                placeholder="Create a strong password"
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
          
          <!-- Password strength indicator -->
          {#if formData.password}
            <div class="mt-2">
              <div class="flex items-center space-x-2 mb-2">
                <div class="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div 
                    class="h-2 rounded-full transition-all duration-300 {getStrengthColor(passwordStrength.score)}"
                    style="width: {(passwordStrength.score / 5) * 100}%"
                  ></div>
                </div>
                <span class="text-xs font-medium {passwordStrength.score < 2 ? 'text-red-600' : passwordStrength.score < 4 ? 'text-yellow-600' : 'text-green-600'}">
                  {getStrengthText(passwordStrength.score)}
                </span>
              </div>
              
              <div class="grid grid-cols-2 gap-2 text-xs">
                {#each Object.entries(passwordStrength.checks) as [key, passed]}
                  <div class="flex items-center space-x-1 {passed ? 'text-green-600 dark:text-green-400' : 'text-gray-400'}">
                    <Check class="w-3 h-3" />
                    <span>
                      {key === 'length' ? '8+ characters' :
                       key === 'lowercase' ? 'Lowercase' :
                       key === 'uppercase' ? 'Uppercase' :
                       key === 'number' ? 'Number' :
                       'Special char'}
                    </span>
                  </div>
                {/each}
              </div>
            </div>
          {/if}
          
          {#if errors.password}
            <p class="form-error">{errors.password}</p>
          {/if}
        </div>

        <!-- Confirm password field -->
        <div>
          <label for="confirmPassword" class="form-label">
            Confirm password
          </label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock class="h-5 w-5 text-gray-400" />
            </div>
            {#if showConfirmPassword}
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="text"
                autocomplete="new-password"
                bind:value={formData.confirmPassword}
                class="form-input pl-10 pr-10 {errors.confirmPassword ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}"
                placeholder="Confirm your password"
                disabled={isLoading}
              />
            {:else}
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                autocomplete="new-password"
                bind:value={formData.confirmPassword}
                class="form-input pl-10 pr-10 {errors.confirmPassword ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''}"
                placeholder="Confirm your password"
                disabled={isLoading}
              />
            {/if}
            <button
              type="button"
              class="absolute inset-y-0 right-0 pr-3 flex items-center"
              on:click={toggleConfirmPassword}
            >
              {#if showConfirmPassword}
                <EyeOff class="h-5 w-5 text-gray-400 hover:text-gray-600" />
              {:else}
                <Eye class="h-5 w-5 text-gray-400 hover:text-gray-600" />
              {/if}
            </button>
          </div>
          {#if errors.confirmPassword}
            <p class="form-error">{errors.confirmPassword}</p>
          {/if}
        </div>

        <!-- Checkboxes -->
        <div class="space-y-4">
          <!-- Terms acceptance -->
          <div class="flex items-start">
            <input
              id="accept-terms"
              name="accept-terms"
              type="checkbox"
              bind:checked={acceptTerms}
              class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 dark:border-gray-600 rounded {errors.terms ? 'border-red-500' : ''}"
            />
            <label for="accept-terms" class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
              I agree to the
              <a href="/terms" class="text-primary-600 hover:text-primary-500 dark:text-primary-400" target="_blank">
                Terms of Service
              </a>
              and
              <a href="/privacy" class="text-primary-600 hover:text-primary-500 dark:text-primary-400" target="_blank">
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
              id="subscribe-newsletter"
              name="subscribe-newsletter"
              type="checkbox"
              bind:checked={subscribeNewsletter}
              class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 dark:border-gray-600 rounded"
            />
            <label for="subscribe-newsletter" class="ml-2 block text-sm text-gray-700 dark:text-gray-300">
              Send me updates about new features and tips
            </label>
          </div>
        </div>

        <!-- Submit button -->
        <div>
          <button
            type="submit"
            disabled={isLoading || !acceptTerms}
            class="btn-primary w-full flex justify-center items-center"
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