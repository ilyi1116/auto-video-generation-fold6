<!-- Call to Action Section Component -->
<script>
  import { ArrowRight, Sparkles, Play, Star } from 'lucide-svelte';
  import { authStore } from '$lib/stores/auth.js';
  
  let email = '';
  let isSubmitting = false;
  
  const handleGetStarted = async () => {
    if ($authStore.isAuthenticated) {
      window.location.href = '/dashboard';
      return;
    }
    
    if (email) {
      isSubmitting = true;
      try {
        // Redirect to registration with email pre-filled
        window.location.href = `/register?email=${encodeURIComponent(email)}`;
      } finally {
        isSubmitting = false;
      }
    } else {
      window.location.href = '/register';
    }
  };

  const handleWatchDemo = () => {
    // Scroll to demo video or open modal
    const demoSection = document.getElementById('demo-section');
    if (demoSection) {
      demoSection.scrollIntoView({ behavior: 'smooth' });
    } else {
      // Fallback to demo page
      window.location.href = '/demo';
    }
  };
</script>

<section class="relative py-20 bg-gradient-to-br from-primary-600 via-primary-700 to-secondary-600 overflow-hidden">
  <!-- Background Effects -->
  <div class="absolute inset-0">
    <!-- Animated Background Pattern -->
    <div class="absolute inset-0 opacity-10">
      <div class="absolute top-0 left-0 w-full h-full"
           style="background-image: radial-gradient(circle, white 1px, transparent 1px); background-size: 60px 60px; animation: float 20s ease-in-out infinite;">
      </div>
    </div>
    
    <!-- Floating Elements -->
    <div class="absolute top-10 left-10 w-32 h-32 bg-white/10 rounded-full blur-2xl animate-pulse"></div>
    <div class="absolute top-1/2 right-20 w-24 h-24 bg-secondary-300/20 rounded-full blur-xl animate-pulse delay-1000"></div>
    <div class="absolute bottom-20 left-1/4 w-40 h-40 bg-white/5 rounded-full blur-3xl animate-pulse delay-2000"></div>
  </div>

  <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Main CTA Content -->
    <div class="text-center">
      <!-- Badge -->
      <div class="inline-flex items-center px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full text-white text-sm font-medium mb-8 animate-fade-in">
        <Sparkles class="w-4 h-4 mr-2" />
        限時免費試用，無需信用卡
      </div>

      <!-- Headline -->
      <h2 class="text-4xl md:text-5xl lg:text-6xl font-bold text-white leading-tight mb-6 animate-fade-in-up">
        準備好創造
        <span class="text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 to-orange-300">
          下一個病毒式影片
        </span>
        了嗎？
      </h2>

      <!-- Subtitle -->
      <p class="text-xl md:text-2xl text-primary-100 max-w-3xl mx-auto leading-relaxed mb-12 animate-fade-in-up delay-200">
        加入 50 萬創作者的行列，用 AI 的力量讓您的內容在社交媒體上脫穎而出
      </p>

      <!-- Stats Row -->
      <div class="flex flex-wrap justify-center gap-8 mb-12 animate-fade-in-up delay-300">
        <div class="text-center">
          <div class="text-3xl font-bold text-white mb-1">500K+</div>
          <div class="text-primary-200 text-sm">滿意用戶</div>
        </div>
        <div class="text-center">
          <div class="text-3xl font-bold text-white mb-1">10M+</div>
          <div class="text-primary-200 text-sm">成功影片</div>
        </div>
        <div class="text-center">
          <div class="flex items-center justify-center mb-1">
            {#each Array(5) as _}
              <Star class="w-5 h-5 text-yellow-400 fill-current" />
            {/each}
          </div>
          <div class="text-primary-200 text-sm">4.9/5 評分</div>
        </div>
      </div>

      <!-- Email Signup Form -->
      <div class="max-w-lg mx-auto mb-8 animate-fade-in-up delay-400">
        <div class="flex flex-col sm:flex-row gap-3 p-3 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20">
          <input 
            type="email" 
            bind:value={email}
            placeholder="輸入您的電子郵件地址"
            class="flex-1 px-6 py-4 bg-white/90 backdrop-blur-sm text-gray-900 placeholder-gray-500 rounded-xl border-0 focus:outline-none focus:ring-2 focus:ring-yellow-400 transition-all duration-200"
          />
          <button 
            on:click={handleGetStarted}
            disabled={isSubmitting}
            class="group px-8 py-4 bg-gradient-to-r from-yellow-400 to-orange-400 hover:from-yellow-500 hover:to-orange-500 disabled:from-gray-400 disabled:to-gray-500 text-gray-900 font-bold rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 disabled:transform-none transition-all duration-200 flex items-center justify-center min-w-[140px]">
            {#if isSubmitting}
              <div class="w-5 h-5 border-2 border-gray-700 border-t-transparent rounded-full animate-spin mr-2"></div>
              處理中...
            {:else}
              立即開始
              <ArrowRight class="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
            {/if}
          </button>
        </div>
      </div>

      <!-- Alternative CTA -->
      <div class="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12 animate-fade-in-up delay-500">
        <button 
          on:click={handleWatchDemo}
          class="group px-6 py-3 bg-white/10 hover:bg-white/20 backdrop-blur-sm text-white font-semibold rounded-xl border border-white/30 hover:border-white/50 shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200 flex items-center">
          <Play class="w-5 h-5 mr-2 group-hover:scale-110 transition-transform" />
          觀看 2 分鐘演示
        </button>
        
        <div class="text-primary-200 text-sm">
          或 <a href="/pricing" class="underline hover:text-white transition-colors">查看所有方案</a>
        </div>
      </div>

      <!-- Trust Indicators -->
      <div class="animate-fade-in-up delay-600">
        <p class="text-primary-200 text-sm mb-6">
          7 天免費試用 • 隨時取消 • 無隱藏費用
        </p>
        
        <!-- Security Badges -->
        <div class="flex flex-wrap justify-center items-center gap-6 opacity-70">
          <div class="flex items-center text-primary-200 text-xs">
            <div class="w-4 h-4 bg-green-400 rounded-full mr-2"></div>
            SSL 安全加密
          </div>
          <div class="flex items-center text-primary-200 text-xs">
            <div class="w-4 h-4 bg-blue-400 rounded-full mr-2"></div>
            GDPR 合規
          </div>
          <div class="flex items-center text-primary-200 text-xs">
            <div class="w-4 h-4 bg-purple-400 rounded-full mr-2"></div>
            SOC2 認證
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Decorative Elements -->
  <div class="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-yellow-400 via-orange-400 to-red-400"></div>
</section>

<!-- Success Stories Ticker -->
<section class="py-8 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="text-center mb-6">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
        最新成功案例
      </h3>
    </div>
    
    <!-- Scrolling Success Stories -->
    <div class="overflow-hidden">
      <div class="flex animate-scroll space-x-8">
        <div class="flex-shrink-0 px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
          <div class="text-sm text-gray-600 dark:text-gray-300">
            <strong>@創作者小李</strong> 的影片在 TikTok 獲得 <strong>100萬</strong> 觀看量
          </div>
        </div>
        
        <div class="flex-shrink-0 px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
          <div class="text-sm text-gray-600 dark:text-gray-300">
            <strong>美食達人王小明</strong> 的粉絲數在一個月內增長 <strong>50%</strong>
          </div>
        </div>
        
        <div class="flex-shrink-0 px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
          <div class="text-sm text-gray-600 dark:text-gray-300">
            <strong>電商品牌 ABC</strong> 的轉換率提升 <strong>300%</strong>
          </div>
        </div>
        
        <div class="flex-shrink-0 px-4 py-2 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700">
          <div class="text-sm text-gray-600 dark:text-gray-300">
            <strong>教育工作者張老師</strong> 的教學影片平均觀看時長增加 <strong>150%</strong>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<style>
  @keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    50% { transform: translateY(-20px) rotate(180deg); }
  }

  @keyframes scroll {
    0% { transform: translateX(0); }
    100% { transform: translateX(-50%); }
  }

  .animate-scroll {
    animation: scroll 30s linear infinite;
  }

  @keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
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

  .delay-600 {
    animation-delay: 0.6s;
    animation-fill-mode: both;
  }

  .delay-1000 {
    animation-delay: 1s;
  }

  .delay-2000 {
    animation-delay: 2s;
  }
</style>