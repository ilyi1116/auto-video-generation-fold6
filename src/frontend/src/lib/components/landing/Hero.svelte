<!-- Hero Section Component -->
<script>
  import { Play, ArrowRight, Sparkles } from 'lucide-svelte';
  import { authStore } from '$lib/stores/auth.js';
  
  let email = '';
  let showSignup = false;
  
  const handleGetStarted = () => {
    if ($authStore.isAuthenticated) {
      window.location.href = '/dashboard';
    } else {
      showSignup = true;
    }
  };
  
  const handleEmailSubmit = () => {
    if (email) {
      window.location.href = `/register?email=${encodeURIComponent(email)}`;
    }
  };
</script>

<section class="relative min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 via-white to-secondary-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 overflow-hidden">
  <!-- Background Pattern -->
  <div class="absolute inset-0 opacity-5">
    <div class="absolute top-0 left-0 w-full h-full"
         style="background-image: radial-gradient(circle, #3B82F6 1px, transparent 1px); background-size: 50px 50px;">
    </div>
  </div>

  <!-- Floating Elements -->
  <div class="absolute top-20 left-10 w-20 h-20 bg-primary-200 dark:bg-primary-800 rounded-full blur-xl opacity-70 animate-pulse"></div>
  <div class="absolute top-40 right-20 w-32 h-32 bg-secondary-200 dark:bg-secondary-800 rounded-full blur-2xl opacity-50 animate-pulse delay-1000"></div>
  <div class="absolute bottom-20 left-20 w-24 h-24 bg-accent-200 dark:bg-accent-800 rounded-full blur-xl opacity-60 animate-pulse delay-2000"></div>

  <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <!-- Badge -->
    <div class="inline-flex items-center px-4 py-2 bg-primary-100 dark:bg-primary-900 rounded-full text-primary-800 dark:text-primary-200 text-sm font-medium mb-8 animate-fade-in">
      <Sparkles class="w-4 h-4 mr-2" />
      全新 AI 影片生成技術現已推出
    </div>

    <!-- Main Heading -->
    <h1 class="text-4xl md:text-6xl lg:text-7xl font-bold text-gray-900 dark:text-white leading-tight mb-8 animate-fade-in-up">
      使用 AI 創建
      <span class="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-secondary-600">
        病毒式短影片
      </span>
    </h1>

    <!-- Subtitle -->
    <p class="text-xl md:text-2xl text-gray-600 dark:text-gray-300 max-w-4xl mx-auto leading-relaxed mb-12 animate-fade-in-up delay-200">
      將您的創意想法轉化為引人注目的短影片。我們的 AI 技術能自動生成腳本、創建視覺效果、合成語音，並發佈到所有社交平台。
    </p>

    <!-- Stats -->
    <div class="flex flex-wrap justify-center gap-8 mb-12 animate-fade-in-up delay-300">
      <div class="text-center">
        <div class="text-3xl font-bold text-primary-600 dark:text-primary-400">10M+</div>
        <div class="text-gray-600 dark:text-gray-400 text-sm">已生成影片</div>
      </div>
      <div class="text-center">
        <div class="text-3xl font-bold text-primary-600 dark:text-primary-400">2 分鐘</div>
        <div class="text-gray-600 dark:text-gray-400 text-sm">平均生成時間</div>
      </div>
      <div class="text-center">
        <div class="text-3xl font-bold text-primary-600 dark:text-primary-400">98%</div>
        <div class="text-gray-600 dark:text-gray-400 text-sm">用戶滿意度</div>
      </div>
    </div>

    <!-- CTA Buttons -->
    {#if !showSignup}
      <div class="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12 animate-fade-in-up delay-400">
        <button 
          on:click={handleGetStarted}
          class="group px-8 py-4 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 flex items-center">
          立即開始創建
          <ArrowRight class="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
        </button>
        
        <button class="group px-8 py-4 bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-semibold rounded-xl border-2 border-gray-200 dark:border-gray-700 hover:border-primary-300 dark:hover:border-primary-600 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 flex items-center">
          <Play class="w-5 h-5 mr-2 group-hover:scale-110 transition-transform" />
          觀看示範影片
        </button>
      </div>
    {:else}
      <!-- Email Signup Form -->
      <div class="max-w-md mx-auto animate-fade-in-up delay-400">
        <div class="flex flex-col sm:flex-row gap-3 p-2 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700">
          <input 
            type="email" 
            bind:value={email}
            placeholder="輸入您的電子郵件"
            class="flex-1 px-4 py-3 bg-transparent text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 border-0 focus:outline-none focus:ring-0"
          />
          <button 
            on:click={handleEmailSubmit}
            disabled={!email}
            class="px-6 py-3 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white font-semibold rounded-lg shadow-md hover:shadow-lg transform hover:scale-105 disabled:transform-none transition-all duration-200 flex items-center justify-center">
            開始免費試用
            <ArrowRight class="w-4 h-4 ml-2" />
          </button>
        </div>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-3">
          7 天免費試用，無需信用卡
        </p>
      </div>
    {/if}

    <!-- Trust Indicators -->
    <div class="mt-16 animate-fade-in-up delay-500">
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">超過 500,000 名內容創作者的信賴選擇</p>
      <div class="flex flex-wrap justify-center items-center gap-8 opacity-60">
        <!-- Placeholder for client logos -->
        <div class="w-24 h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div class="w-20 h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div class="w-28 h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
        <div class="w-22 h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
    </div>
  </div>
</section>

<style>
  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes fade-in-up {
    from {
      opacity: 0;
      transform: translateY(30px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .animate-fade-in {
    animation: fade-in 0.8s ease-out;
  }

  .animate-fade-in-up {
    animation: fade-in-up 0.8s ease-out;
  }

  .delay-200 {
    animation-delay: 0.2s;
    animation-fill-mode: both;
  }

  .delay-300 {
    animation-delay: 0.3s;
    animation-fill-mode: both;
  }

  .delay-400 {
    animation-delay: 0.4s;
    animation-fill-mode: both;
  }

  .delay-500 {
    animation-delay: 0.5s;
    animation-fill-mode: both;
  }

  .delay-1000 {
    animation-delay: 1s;
  }

  .delay-2000 {
    animation-delay: 2s;
  }
</style>