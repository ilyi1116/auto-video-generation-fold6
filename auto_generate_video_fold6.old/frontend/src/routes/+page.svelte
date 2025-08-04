<script>
  import { onMount } from 'svelte';
  import { Play, Zap, TrendingUp, Users, ArrowRight, Star, CheckCircle } from 'lucide-svelte';
  import { authStore } from '$lib/stores/auth';
  import Hero from '$lib/components/landing/Hero.svelte';
  import Features from '$lib/components/landing/Features.svelte';
  import Testimonials from '$lib/components/landing/Testimonials.svelte';
  import Pricing from '$lib/components/landing/Pricing.svelte';
  import CTA from '$lib/components/landing/CTA.svelte';

  let mounted = false;

  onMount(() => {
    mounted = true;
  });

  // Redirect to dashboard if already logged in
  $: if (mounted && $authStore.isAuthenticated) {
    if (typeof window !== 'undefined') {
      window.location.href = '/dashboard';
    }
  }
</script>

<svelte:head>
  <title>Auto Video Generation - Create Viral Videos with AI</title>
  <meta name="description" content="Transform your ideas into viral short-form videos using cutting-edge AI. Generate scripts, create visuals, synthesize voices, and publish across all platforms automatically." />
  <meta property="og:title" content="Auto Video Generation - Create Viral Videos with AI" />
  <meta property="og:description" content="Transform your ideas into viral short-form videos using cutting-edge AI" />
  <meta property="og:type" content="website" />
  <link rel="canonical" href="https://autovideo.com" />
</svelte:head>

{#if mounted && !$authStore.isAuthenticated}
  <div class="bg-white dark:bg-gray-900">
    <!-- Hero Section -->
    <Hero />

    <!-- Features Section -->
    <Features />

    <!-- Stats Section -->
    <section class="py-16 bg-primary-600">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          <div>
            <div class="text-4xl font-bold text-white mb-2">10M+</div>
            <div class="text-primary-100">Videos Generated</div>
          </div>
          <div>
            <div class="text-4xl font-bold text-white mb-2">500K+</div>
            <div class="text-primary-100">Active Creators</div>
          </div>
          <div>
            <div class="text-4xl font-bold text-white mb-2">2.5B+</div>
            <div class="text-primary-100">Total Views</div>
          </div>
          <div>
            <div class="text-4xl font-bold text-white mb-2">98%</div>
            <div class="text-primary-100">Success Rate</div>
          </div>
        </div>
      </div>
    </section>

    <!-- How It Works Section -->
    <section class="py-20 bg-gray-50 dark:bg-gray-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
            How It Works
          </h2>
          <p class="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Create viral videos in minutes with our AI-powered workflow
          </p>
        </div>

        <div class="grid md:grid-cols-3 gap-8">
          <div class="text-center">
            <div class="w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center mx-auto mb-6">
              <Zap class="w-8 h-8 text-primary-600 dark:text-primary-400" />
            </div>
            <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              1. Generate Script
            </h3>
            <p class="text-gray-600 dark:text-gray-300">
              AI analyzes trending topics and creates engaging scripts tailored to your audience and style preferences.
            </p>
          </div>

          <div class="text-center">
            <div class="w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center mx-auto mb-6">
              <Play class="w-8 h-8 text-primary-600 dark:text-primary-400" />
            </div>
            <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              2. Create Visuals & Audio
            </h3>
            <p class="text-gray-600 dark:text-gray-300">
              Generate stunning visuals and natural-sounding voiceovers that perfectly match your script and brand.
            </p>
          </div>

          <div class="text-center">
            <div class="w-16 h-16 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center mx-auto mb-6">
              <TrendingUp class="w-8 h-8 text-primary-600 dark:text-primary-400" />
            </div>
            <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
              3. Publish & Analyze
            </h3>
            <p class="text-gray-600 dark:text-gray-300">
              Automatically publish to all your social platforms and track performance with detailed analytics.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Testimonials Section -->
    <Testimonials />

    <!-- Pricing Section -->
    <Pricing />

    <!-- FAQ Section -->
    <section class="py-20 bg-white dark:bg-gray-900">
      <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Frequently Asked Questions
          </h2>
          <p class="text-xl text-gray-600 dark:text-gray-300">
            Everything you need to know about our platform
          </p>
        </div>

        <div class="space-y-8">
          <div class="border-b border-gray-200 dark:border-gray-700 pb-8">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              How long does it take to generate a video?
            </h3>
            <p class="text-gray-600 dark:text-gray-300">
              Most videos are generated within 2-5 minutes, depending on length and complexity. Our AI processes scripts, creates visuals, and synthesizes audio simultaneously for maximum efficiency.
            </p>
          </div>

          <div class="border-b border-gray-200 dark:border-gray-700 pb-8">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              Can I customize the AI-generated content?
            </h3>
            <p class="text-gray-600 dark:text-gray-300">
              Absolutely! You can edit scripts, regenerate specific images, adjust voice settings, and customize every aspect of your video before publishing.
            </p>
          </div>

          <div class="border-b border-gray-200 dark:border-gray-700 pb-8">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              Which social media platforms are supported?
            </h3>
            <p class="text-gray-600 dark:text-gray-300">
              We support all major platforms including TikTok, YouTube Shorts, Instagram Reels, Facebook Stories, Twitter, and LinkedIn. More platforms are added regularly.
            </p>
          </div>

          <div class="border-b border-gray-200 dark:border-gray-700 pb-8">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              Do I own the rights to the generated content?
            </h3>
            <p class="text-gray-600 dark:text-gray-300">
              Yes! You have full commercial rights to all content generated through our platform. Use it for your business, clients, or personal projects without restrictions.
            </p>
          </div>

          <div>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              Is there a free trial available?
            </h3>
            <p class="text-gray-600 dark:text-gray-300">
              Yes! We offer a 7-day free trial with access to all features and the ability to generate up to 5 videos. No credit card required to start.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Final CTA Section -->
    <CTA />
  </div>
{:else}
  <!-- Loading state -->
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
  </div>
{/if}

<style>
  /* Add any component-specific styles here */
</style>