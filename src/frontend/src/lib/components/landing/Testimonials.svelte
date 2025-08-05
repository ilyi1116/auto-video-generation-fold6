<!-- Testimonials Section Component -->
<script>
  import { Star, Quote } from 'lucide-svelte';

  const testimonials = [
    {
      name: '張小明',
      role: 'TikTok 創作者',
      avatar: '👨‍💼',
      rating: 5,
      content: '這個平台完全改變了我的內容創作方式！以前需要花費幾小時製作的影片，現在只需要幾分鐘就能完成。AI 生成的腳本非常有趣，觀眾參與度提升了 300%。',
      metrics: '+300% 參與度'
    },
    {
      name: '李美琪',
      role: '電商品牌經理',
      avatar: '👩‍💻',
      rating: 5,
      content: '作為品牌經理，我需要快速響應市場趨勢。這個 AI 工具幫我在 48 小時內創建了 20 個產品宣傳影片，每個都獲得了極高的點擊率。投資回報率超出預期。',
      metrics: '投資回報率 +450%'
    },
    {
      name: '王小華',
      role: 'YouTube 頻道主',
      avatar: '🎬',
      rating: 5,
      content: '我一直擔心 AI 會讓內容失去個人特色，但這個平台完全打消了我的疑慮。它不僅保留了我的風格，還幫我發現了更多創意可能性。訂閱者數量在三個月內翻了一倍。',
      metrics: '訂閱者 +200%'
    },
    {
      name: '陳建國',
      role: '數位行銷專家',
      avatar: '📊',
      rating: 5,
      content: '作為行銷專家，我見過太多工具承諾過度。但這個平台真的做到了它所承諾的一切。客戶的影片觀看量平均提升了 250%，我們的業務也因此快速增長。',
      metrics: '觀看量 +250%'
    },
    {
      name: '劉雅婷',
      role: '美食博主',
      avatar: '🍳',
      rating: 5,
      content: '我原本對技術一竅不通，但這個平台的操作非常直觀。現在我可以專注於料理本身，而 AI 幫我處理所有技術細節。我的美食影片現在在多個平台都很受歡迎。',
      metrics: '多平台熱門'
    },
    {
      name: '黃志明',
      role: '教育內容創作者',
      avatar: '📚',
      rating: 5,
      content: '教育內容需要既有趣又準確。這個 AI 工具幫我創作了許多寓教於樂的短影片，學生們的學習積極性明顯提高。現在我的教學影片在社交媒體上廣受歡迎。',
      metrics: '學習參與度 +180%'
    }
  ];
</script>

<section class="py-20 bg-gradient-to-br from-primary-50 via-white to-secondary-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Section Header -->
    <div class="text-center mb-16">
      <h2 class="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
        用戶真實評價
      </h2>
      <p class="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
        看看我們的用戶如何利用 AI 技術創造出令人驚豔的內容成果
      </p>

      <!-- Trust Metrics -->
      <div class="flex flex-wrap justify-center gap-8 mt-8">
        <div class="text-center">
          <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">4.9/5</div>
          <div class="text-sm text-gray-600 dark:text-gray-400">用戶評分</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">50萬+</div>
          <div class="text-sm text-gray-600 dark:text-gray-400">滿意用戶</div>
        </div>
        <div class="text-center">
          <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">1000萬+</div>
          <div class="text-sm text-gray-600 dark:text-gray-400">成功影片</div>
        </div>
      </div>
    </div>

    <!-- Testimonials Grid -->
    <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
      {#each testimonials as testimonial, index}
        <div class="group">
          <!-- Card -->
          <div class="relative h-full p-6 bg-white dark:bg-gray-800 rounded-2xl shadow-lg hover:shadow-2xl border border-gray-200 dark:border-gray-700 transform hover:-translate-y-2 transition-all duration-300">
            <!-- Quote Icon -->
            <div class="absolute top-4 right-4 w-8 h-8 bg-primary-100 dark:bg-primary-900 rounded-full flex items-center justify-center opacity-50 group-hover:opacity-100 transition-opacity">
              <Quote class="w-4 h-4 text-primary-600 dark:text-primary-400" />
            </div>

            <!-- Rating -->
            <div class="flex items-center mb-4">
              {#each Array(testimonial.rating) as _}
                <Star class="w-4 h-4 text-yellow-400 fill-current" />
              {/each}
            </div>

            <!-- Content -->
            <p class="text-gray-700 dark:text-gray-300 leading-relaxed mb-6 italic">
              "{testimonial.content}"
            </p>

            <!-- User Info -->
            <div class="flex items-center justify-between">
              <div class="flex items-center">
                <div class="w-12 h-12 bg-gradient-to-br from-primary-400 to-secondary-400 rounded-full flex items-center justify-center text-white font-bold text-lg mr-4">
                  {testimonial.avatar}
                </div>
                <div>
                  <h4 class="font-semibold text-gray-900 dark:text-white">
                    {testimonial.name}
                  </h4>
                  <p class="text-sm text-gray-600 dark:text-gray-400">
                    {testimonial.role}
                  </p>
                </div>
              </div>

              <!-- Metrics Badge -->
              <div class="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs font-medium rounded-full">
                {testimonial.metrics}
              </div>
            </div>

            <!-- Hover Effect Gradient -->
            <div class="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-secondary-500/5 opacity-0 group-hover:opacity-100 rounded-2xl transition-opacity duration-300 pointer-events-none"></div>
          </div>
        </div>
      {/each}
    </div>

    <!-- Bottom CTA -->
    <div class="text-center mt-16">
      <div class="inline-flex flex-col items-center p-8 bg-white dark:bg-gray-800 rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700">
        <div class="flex items-center mb-4">
          {#each Array(5) as _}
            <Star class="w-6 h-6 text-yellow-400 fill-current" />
          {/each}
        </div>
        <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
          加入 50 萬滿意用戶的行列
        </h3>
        <p class="text-gray-600 dark:text-gray-300 mb-6">
          立即體驗 AI 影片生成的強大功能
        </p>
        <button class="px-8 py-3 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200">
          開始免費試用
        </button>
      </div>
    </div>
  </div>
</section>

<!-- Success Stories Section -->
<section class="py-16 bg-white dark:bg-gray-900">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-8">
      成功案例數據
    </h3>
    
    <div class="grid md:grid-cols-4 gap-6">
      <div class="p-4">
        <div class="text-3xl font-bold text-primary-600 dark:text-primary-400 mb-2">
          平均 2.5x
        </div>
        <div class="text-sm text-gray-600 dark:text-gray-400">
          觀看量提升
        </div>
      </div>
      
      <div class="p-4">
        <div class="text-3xl font-bold text-primary-600 dark:text-primary-400 mb-2">
          節省 80%
        </div>
        <div class="text-sm text-gray-600 dark:text-gray-400">
          製作時間
        </div>
      </div>
      
      <div class="p-4">
        <div class="text-3xl font-bold text-primary-600 dark:text-primary-400 mb-2">
          提升 300%
        </div>
        <div class="text-sm text-gray-600 dark:text-gray-400">
          用戶參與度
        </div>
      </div>
      
      <div class="p-4">
        <div class="text-3xl font-bold text-primary-600 dark:text-primary-400 mb-2">
          增長 250%
        </div>
        <div class="text-sm text-gray-600 dark:text-gray-400">
          追蹤者數量
        </div>
      </div>
    </div>
  </div>
</section>