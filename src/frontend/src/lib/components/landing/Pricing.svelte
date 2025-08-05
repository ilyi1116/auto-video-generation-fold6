<!-- Pricing Section Component -->
<script>
  import { Check, Zap, Crown, Building } from 'lucide-svelte';
  
  let billingCycle = 'monthly'; // 'monthly' or 'yearly'
  
  const plans = [
    {
      name: '入門版',
      icon: Zap,
      price: { monthly: 0, yearly: 0 },
      description: '適合初學者和個人創作者',
      features: [
        '每月 5 個影片',
        '基礎 AI 腳本生成',
        '標準視覺效果',
        '3 種語音選擇',
        '720p 影片輸出',
        '基礎分析報告',
        '社群支援'
      ],
      limitations: [
        '影片長度限制 30 秒',
        '浮水印',
        '有限的自定義選項'
      ],
      buttonText: '免費開始',
      popular: false,
      color: 'from-gray-500 to-gray-600'
    },
    {
      name: '專業版',
      icon: Crown,
      price: { monthly: 29, yearly: 290 },
      description: '適合內容創作者和小企業',
      features: [
        '每月 50 個影片',
        '高級 AI 腳本生成',
        '專業視覺效果',
        '10+ 語音選擇',
        '1080p 影片輸出',
        '無浮水印',
        '多平台自動發佈',
        '詳細分析報告',
        '優先客服支援',
        '自定義品牌元素'
      ],
      limitations: [],
      buttonText: '開始專業版',
      popular: true,
      color: 'from-primary-500 to-secondary-500'
    },
    {
      name: '企業版',
      icon: Building,
      price: { monthly: 99, yearly: 990 },
      description: '適合大型企業和代理商',
      features: [
        '無限影片生成',
        '企業級 AI 定制',
        '高級視覺效果庫',
        '無限語音選擇',
        '4K 影片輸出',
        '白標解決方案',
        'API 接入',
        '多團隊管理',
        '高級分析儀表板',
        '專屬客戶經理',
        '24/7 技術支援',
        '自定義整合'
      ],
      limitations: [],
      buttonText: '聯繫銷售',
      popular: false,
      color: 'from-purple-500 to-indigo-500'
    }
  ];

  $: discountPercent = billingCycle === 'yearly' ? 17 : 0;

  const handlePlanSelect = (plan) => {
    if (plan.name === '入門版') {
      window.location.href = '/register?plan=free';
    } else if (plan.name === '企業版') {
      window.location.href = '/contact?type=enterprise';
    } else {
      window.location.href = `/register?plan=${plan.name.toLowerCase()}&billing=${billingCycle}`;
    }
  };
</script>

<section class="py-20 bg-gray-50 dark:bg-gray-800">
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <!-- Section Header -->
    <div class="text-center mb-16">
      <h2 class="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
        選擇適合您的方案
      </h2>
      <p class="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto mb-8">
        從免費試用到企業級解決方案，我們為每個階段的創作者提供最合適的工具
      </p>

      <!-- Billing Toggle -->
      <div class="inline-flex items-center p-1 bg-white dark:bg-gray-900 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700">
        <button 
          class="px-6 py-2 rounded-lg font-medium transition-all duration-200 {billingCycle === 'monthly' ? 'bg-primary-600 text-white shadow-md' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}"
          on:click={() => billingCycle = 'monthly'}>
          月付
        </button>
        <button 
          class="px-6 py-2 rounded-lg font-medium transition-all duration-200 relative {billingCycle === 'yearly' ? 'bg-primary-600 text-white shadow-md' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}"
          on:click={() => billingCycle = 'yearly'}>
          年付
          <span class="absolute -top-2 -right-2 px-2 py-1 bg-green-500 text-white text-xs rounded-full">
            省{discountPercent}%
          </span>
        </button>
      </div>
    </div>

    <!-- Pricing Cards -->
    <div class="grid md:grid-cols-3 gap-8 lg:gap-12">
      {#each plans as plan}
        <div class="relative group">
          <!-- Popular Badge -->
          {#if plan.popular}
            <div class="absolute -top-4 left-1/2 transform -translate-x-1/2 px-4 py-2 bg-gradient-to-r from-primary-500 to-secondary-500 text-white text-sm font-medium rounded-full shadow-lg z-10">
              最受歡迎
            </div>
          {/if}

          <!-- Card -->
          <div class="relative h-full p-8 bg-white dark:bg-gray-900 rounded-2xl shadow-lg hover:shadow-2xl border-2 transition-all duration-300 {plan.popular ? 'border-primary-200 dark:border-primary-800 scale-105' : 'border-gray-200 dark:border-gray-700 hover:border-primary-200 dark:hover:border-primary-800'}">
            
            <!-- Header -->
            <div class="text-center mb-8">
              <div class="w-16 h-16 mx-auto mb-4 bg-gradient-to-br {plan.color} rounded-2xl flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                <svelte:component this={plan.icon} class="w-8 h-8 text-white" />
              </div>
              
              <h3 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                {plan.name}
              </h3>
              
              <p class="text-gray-600 dark:text-gray-400 mb-6">
                {plan.description}
              </p>

              <!-- Price -->
              <div class="mb-6">
                {#if plan.price[billingCycle] === 0}
                  <div class="text-4xl font-bold text-gray-900 dark:text-white">
                    免費
                  </div>
                {:else}
                  <div class="flex items-baseline justify-center">
                    <span class="text-4xl font-bold text-gray-900 dark:text-white">
                      ${plan.price[billingCycle]}
                    </span>
                    <span class="text-gray-600 dark:text-gray-400 ml-2">
                      /{billingCycle === 'monthly' ? '月' : '年'}
                    </span>
                  </div>
                  {#if billingCycle === 'yearly'}
                    <div class="text-sm text-green-600 dark:text-green-400 mt-1">
                      相當於 ${Math.round(plan.price.yearly / 12)}/月
                    </div>
                  {/if}
                {/if}
              </div>
            </div>

            <!-- Features -->
            <div class="mb-8">
              <h4 class="font-semibold text-gray-900 dark:text-white mb-4">包含功能：</h4>
              <ul class="space-y-3">
                {#each plan.features as feature}
                  <li class="flex items-start">
                    <Check class="w-5 h-5 text-green-500 mt-0.5 mr-3 flex-shrink-0" />
                    <span class="text-gray-600 dark:text-gray-300">{feature}</span>
                  </li>
                {/each}
              </ul>

              {#if plan.limitations.length > 0}
                <div class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                  <h5 class="font-medium text-gray-700 dark:text-gray-300 mb-3">限制：</h5>
                  <ul class="space-y-2">
                    {#each plan.limitations as limitation}
                      <li class="text-sm text-gray-500 dark:text-gray-400">
                        • {limitation}
                      </li>
                    {/each}
                  </ul>
                </div>
              {/if}
            </div>

            <!-- CTA Button -->
            <button 
              on:click={() => handlePlanSelect(plan)}
              class="w-full py-4 px-6 rounded-xl font-semibold transition-all duration-200 transform hover:scale-105 {plan.popular ? 'bg-gradient-to-r from-primary-600 to-secondary-600 hover:from-primary-700 hover:to-secondary-700 text-white shadow-lg hover:shadow-xl' : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white hover:bg-gray-200 dark:hover:bg-gray-700 border border-gray-300 dark:border-gray-600'}">
              {plan.buttonText}
            </button>

            <!-- Hover Effect -->
            {#if plan.popular}
              <div class="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-secondary-500/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
            {/if}
          </div>
        </div>
      {/each}
    </div>

    <!-- Additional Info -->
    <div class="mt-16 text-center">
      <div class="bg-white dark:bg-gray-900 rounded-2xl p-8 shadow-lg border border-gray-200 dark:border-gray-700 max-w-4xl mx-auto">
        <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-4">
          所有方案都包含
        </h3>
        
        <div class="grid md:grid-cols-3 gap-6 text-left">
          <div class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mt-1 mr-3 flex-shrink-0" />
            <div>
              <h4 class="font-medium text-gray-900 dark:text-white">7 天免費試用</h4>
              <p class="text-sm text-gray-600 dark:text-gray-400">所有功能無限制試用</p>
            </div>
          </div>
          
          <div class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mt-1 mr-3 flex-shrink-0" />
            <div>
              <h4 class="font-medium text-gray-900 dark:text-white">隨時取消</h4>
              <p class="text-sm text-gray-600 dark:text-gray-400">無合約約束，隨時可以取消</p>
            </div>
          </div>
          
          <div class="flex items-start">
            <Check class="w-5 h-5 text-green-500 mt-1 mr-3 flex-shrink-0" />
            <div>
              <h4 class="font-medium text-gray-900 dark:text-white">安全保障</h4>
              <p class="text-sm text-gray-600 dark:text-gray-400">SSL 加密，數據安全保障</p>
            </div>
          </div>
        </div>

        <div class="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl">
          <p class="text-blue-800 dark:text-blue-200 font-medium">
            🎉 限時優惠：年付方案享受 17% 折扣，相當於免費獲得 2 個月服務！
          </p>
        </div>
      </div>
    </div>

    <!-- FAQ Section -->
    <div class="mt-16">
      <h3 class="text-2xl font-bold text-gray-900 dark:text-white text-center mb-8">
        常見問題
      </h3>
      
      <div class="max-w-3xl mx-auto space-y-6">
        <div class="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
          <h4 class="font-semibold text-gray-900 dark:text-white mb-2">
            可以隨時更改方案嗎？
          </h4>
          <p class="text-gray-600 dark:text-gray-300">
            是的，您可以隨時升級或降級您的方案。升級立即生效，降級將在下個計費週期生效。
          </p>
        </div>

        <div class="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
          <h4 class="font-semibold text-gray-900 dark:text-white mb-2">
            如果超過月度影片限制怎麼辦？
          </h4>
          <p class="text-gray-600 dark:text-gray-300">
            您可以購買額外的影片包，或者升級到更高級的方案。我們會在您接近限制時提前通知您。
          </p>
        </div>

        <div class="bg-white dark:bg-gray-900 rounded-xl p-6 shadow-lg border border-gray-200 dark:border-gray-700">
          <h4 class="font-semibold text-gray-900 dark:text-white mb-2">
            支援哪些付款方式？
          </h4>
          <p class="text-gray-600 dark:text-gray-300">
            我們支援信用卡、PayPal、銀行轉帳等多種付款方式。企業客戶還可以申請發票付款。
          </p>
        </div>
      </div>
    </div>
  </div>
</section>