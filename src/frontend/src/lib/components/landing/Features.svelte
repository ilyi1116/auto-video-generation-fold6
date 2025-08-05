<!-- Features Section Component -->
<script>
  import { Bot, Zap, TrendingUp, Users, Globe, Shield, Clock, BarChart3 } from 'lucide-svelte';

  const features = [
    {
      icon: Bot,
      title: 'AI 腳本生成',
      description: '基於熱門趨勢和您的品牌風格，AI 自動生成引人入勝的影片腳本',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      icon: Zap,
      title: '自動化視覺創建',
      description: '利用 Stable Diffusion 生成高質量圖像，配合動畫效果創造視覺衝擊',
      color: 'from-purple-500 to-pink-500'
    },
    {
      icon: Users,
      title: 'AI 語音合成',
      description: '多種自然語音選擇，支援多語言，讓您的內容更具親和力',
      color: 'from-green-500 to-emerald-500'
    },
    {
      icon: TrendingUp,
      title: '趨勢分析',
      description: '實時分析社交媒體趨勢，確保您的內容始終處於潮流前端',
      color: 'from-orange-500 to-red-500'
    },
    {
      icon: Globe,
      title: '多平台發佈',
      description: '一鍵發佈到 TikTok、YouTube Shorts、Instagram Reels 等所有主流平台',
      color: 'from-indigo-500 to-blue-500'
    },
    {
      icon: BarChart3,
      title: '深度分析',
      description: '詳細的表現數據分析，幫助您優化內容策略和提升參與度',
      color: 'from-teal-500 to-green-500'
    },
    {
      icon: Clock,
      title: '快速生成',
      description: '平均 2-5 分鐘完成整個影片製作流程，讓創意不再等待',
      color: 'from-yellow-500 to-orange-500'
    },
    {
      icon: Shield,
      title: '企業級安全',
      description: '端到端加密，確保您的創意內容和用戶數據絕對安全',
      color: 'from-gray-500 to-slate-500'
    }
  ];
</script>

<section class="py-20 bg-white dark:bg-gray-900">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Section Header -->
    <div class="text-center mb-16">
      <h2 class="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
        強大的 AI 功能
      </h2>
      <p class="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
        從創意構思到內容發佈，我們的 AI 技術覆蓋整個影片製作流程，讓您專注於創意本身
      </p>
    </div>

    <!-- Features Grid -->
    <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
      {#each features as feature, index}
        <div class="group relative">
          <!-- Card -->
          <div class="relative h-full p-6 bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-lg hover:shadow-2xl transform hover:-translate-y-2 transition-all duration-300">
            <!-- Icon Background -->
            <div class="absolute top-0 left-0 w-full h-32 bg-gradient-to-br {feature.color} opacity-10 rounded-t-2xl"></div>
            
            <!-- Icon -->
            <div class="relative z-10 w-14 h-14 bg-gradient-to-br {feature.color} rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
              <svelte:component this={feature.icon} class="w-7 h-7 text-white" />
            </div>

            <!-- Content -->
            <div class="relative z-10">
              <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-3 group-hover:text-transparent group-hover:bg-clip-text group-hover:bg-gradient-to-r group-hover:{feature.color} transition-all duration-300">
                {feature.title}
              </h3>
              <p class="text-gray-600 dark:text-gray-300 leading-relaxed">
                {feature.description}
              </p>
            </div>

            <!-- Hover Effect -->
            <div class="absolute inset-0 bg-gradient-to-br {feature.color} opacity-0 group-hover:opacity-5 rounded-2xl transition-opacity duration-300"></div>
          </div>

          <!-- Floating Animation -->
          <div class="absolute -z-10 inset-0 bg-gradient-to-br {feature.color} opacity-20 rounded-2xl blur-xl group-hover:opacity-30 transition-opacity duration-300 animate-pulse" style="animation-delay: {index * 0.2}s"></div>
        </div>
      {/each}
    </div>

    <!-- Additional Info -->
    <div class="mt-16 text-center">
      <div class="inline-flex items-center px-6 py-3 bg-gradient-to-r from-primary-50 to-secondary-50 dark:from-primary-900/20 dark:to-secondary-900/20 rounded-full border border-primary-200 dark:border-primary-800">
        <Bot class="w-5 h-5 text-primary-600 dark:text-primary-400 mr-3" />
        <span class="text-primary-800 dark:text-primary-200 font-medium">
          AI 技術持續升級，功能不斷擴展
        </span>
      </div>
    </div>
  </div>
</section>

<!-- Feature Showcase Section -->
<section class="py-20 bg-gradient-to-br from-gray-50 to-primary-50 dark:from-gray-800 dark:to-gray-900">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="grid lg:grid-cols-2 gap-12 items-center">
      <!-- Left Side - Content -->
      <div>
        <h3 class="text-3xl font-bold text-gray-900 dark:text-white mb-6">
          從創意到病毒式傳播
          <span class="text-primary-600 dark:text-primary-400">只需三步</span>
        </h3>
        <p class="text-lg text-gray-600 dark:text-gray-300 mb-8">
          我們的 AI 工作流程設計簡潔高效，讓任何人都能創作出專業級的短影片內容。
        </p>

        <!-- Steps -->
        <div class="space-y-6">
          <div class="flex items-start">
            <div class="flex-shrink-0 w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold text-sm mr-4">
              1
            </div>
            <div>
              <h4 class="font-semibold text-gray-900 dark:text-white mb-2">輸入創意想法</h4>
              <p class="text-gray-600 dark:text-gray-300">只需簡單描述您的想法或選擇熱門話題，AI 就能理解您的創作意圖。</p>
            </div>
          </div>

          <div class="flex items-start">
            <div class="flex-shrink-0 w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold text-sm mr-4">
              2
            </div>
            <div>
              <h4 class="font-semibold text-gray-900 dark:text-white mb-2">AI 自動製作</h4>
              <p class="text-gray-600 dark:text-gray-300">AI 同時生成腳本、創建視覺效果、合成語音，整個過程完全自動化。</p>
            </div>
          </div>

          <div class="flex items-start">
            <div class="flex-shrink-0 w-8 h-8 bg-primary-600 text-white rounded-full flex items-center justify-center font-bold text-sm mr-4">
              3
            </div>
            <div>
              <h4 class="font-semibold text-gray-900 dark:text-white mb-2">發佈與分析</h4>
              <p class="text-gray-600 dark:text-gray-300">一鍵發佈到所有平台，並獲得詳細的表現分析報告。</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Side - Visual -->
      <div class="relative">
        <!-- Placeholder for demo video or animation -->
        <div class="aspect-video bg-gradient-to-br from-primary-100 to-secondary-100 dark:from-primary-900 to-secondary-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 flex items-center justify-center">
          <div class="text-center">
            <div class="w-16 h-16 bg-primary-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <Bot class="w-8 h-8 text-white" />
            </div>
            <p class="text-gray-600 dark:text-gray-300 font-medium">AI 工作流程展示</p>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">即將推出互動式演示</p>
          </div>
        </div>

        <!-- Floating Elements -->
        <div class="absolute -top-4 -right-4 w-20 h-20 bg-primary-200 dark:bg-primary-800 rounded-full blur-xl opacity-70 animate-pulse"></div>
        <div class="absolute -bottom-4 -left-4 w-16 h-16 bg-secondary-200 dark:bg-secondary-800 rounded-full blur-xl opacity-60 animate-pulse delay-1000"></div>
      </div>
    </div>
  </div>
</section>