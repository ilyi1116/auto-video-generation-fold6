<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import Button from '$lib/components/ui/Button.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import { Check, Star, Zap, Shield } from 'lucide-svelte';
  import { SUBSCRIPTION_PLANS, createCheckoutSession, formatPrice } from '$lib/payments/stripe.js';
  import { authStore } from '$lib/stores/auth.js';
  import { toast } from '$lib/stores/toast.js';

  let loading = {};
  let currentUser = null;

  $: currentUser = $authStore.user;

  const planOrder = ['standard', 'professional', 'enterprise'];
  const orderedPlans = planOrder.map(id => ({
    ...SUBSCRIPTION_PLANS[id],
    id
  }));

  function getPlanIcon(planId) {
    switch (planId) {
      case 'standard':
        return Check;
      case 'professional':
        return Star;
      case 'enterprise':
        return Shield;
      default:
        return Zap;
    }
  }

  function getPlanColor(planId) {
    switch (planId) {
      case 'standard':
        return 'border-blue-200 bg-blue-50';
      case 'professional':
        return 'border-purple-200 bg-purple-50 ring-2 ring-purple-500';
      case 'enterprise':
        return 'border-gray-900 bg-gray-50';
      default:
        return 'border-gray-200';
    }
  }

  async function handleSubscribe(planId) {
    if (!currentUser) {
      toast.add({
        message: '請先登入才能訂閱',
        type: 'warning'
      });
      goto('/login?redirect=/pricing');
      return;
    }

    loading[planId] = true;

    try {
      await createCheckoutSession(planId, currentUser.id);
    } catch (error) {
      console.error('訂閱錯誤:', error);
      toast.add({
        message: error.message || '訂閱失敗，請稍後再試',
        type: 'error'
      });
    } finally {
      loading[planId] = false;
    }
  }

  function isPopular(planId) {
    return planId === 'professional';
  }
</script>

<svelte:head>
  <title>定價方案 - Auto Video</title>
  <meta name="description" content="選擇最適合您的 AI 影片生成方案，立即開始創作高品質短影音內容" />
</svelte:head>

<div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-12 px-4 sm:px-6 lg:px-8">
  <div class="max-w-7xl mx-auto">
    <!-- 標題區域 -->
    <div class="text-center mb-16">
      <h1 class="text-4xl font-bold text-gray-900 sm:text-5xl mb-4">
        選擇您的
        <span class="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
          完美方案
        </span>
      </h1>
      <p class="text-xl text-gray-600 max-w-3xl mx-auto mb-8">
        從個人創作者到企業客戶，我們為每個需求提供量身定制的 AI 影片生成解決方案
      </p>
      
      <!-- 特色亮點 -->
      <div class="flex flex-wrap justify-center gap-6 text-sm text-gray-600">
        <div class="flex items-center gap-2">
          <Zap class="w-4 h-4 text-yellow-500" />
          <span>30 秒快速生成</span>
        </div>
        <div class="flex items-center gap-2">
          <Check class="w-4 h-4 text-green-500" />
          <span>無需技術背景</span>
        </div>
        <div class="flex items-center gap-2">
          <Shield class="w-4 h-4 text-blue-500" />
          <span>商用授權包含</span>
        </div>
      </div>
    </div>

    <!-- 定價卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
      {#each orderedPlans as plan (plan.id)}
        <div class="relative">
          {#if isPopular(plan.id)}
            <div class="absolute -top-4 left-1/2 transform -translate-x-1/2">
              <span class="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                最受歡迎
              </span>
            </div>
          {/if}
          
          <Card class="h-full p-8 relative overflow-hidden {getPlanColor(plan.id)}">
            <!-- 背景裝飾 -->
            <div class="absolute top-0 right-0 w-20 h-20 opacity-10">
              <svelte:component this={getPlanIcon(plan.id)} class="w-full h-full" />
            </div>

            <div class="relative">
              <!-- 方案標題 -->
              <div class="flex items-center gap-3 mb-4">
                <div class="p-2 rounded-lg bg-white shadow-sm">
                  <svelte:component this={getPlanIcon(plan.id)} class="w-6 h-6 text-gray-700" />
                </div>
                <h3 class="text-2xl font-bold text-gray-900">{plan.name}</h3>
              </div>

              <!-- 價格 -->
              <div class="mb-6">
                <span class="text-4xl font-bold text-gray-900">{formatPrice(plan.price)}</span>
                <span class="text-gray-600 ml-1">/月</span>
                {#if plan.id === 'professional'}
                  <div class="text-sm text-green-600 font-medium mt-1">
                    節省 20% (年付)
                  </div>
                {/if}
              </div>

              <!-- 功能列表 -->
              <ul class="space-y-3 mb-8">
                {#each plan.features as feature}
                  <li class="flex items-start gap-3">
                    <Check class="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span class="text-gray-700">{feature}</span>
                  </li>
                {/each}
              </ul>

              <!-- CTA 按鈕 -->
              <Button
                variant={isPopular(plan.id) ? 'primary' : 'outline'}
                size="lg"
                class="w-full"
                loading={loading[plan.id]}
                on:click={() => handleSubscribe(plan.id)}
              >
                {loading[plan.id] ? '處理中...' : '開始使用'}
              </Button>

              {#if plan.id === 'enterprise'}
                <p class="text-center text-sm text-gray-600 mt-3">
                  或 <button class="text-blue-600 hover:underline">聯絡業務團隊</button>
                </p>
              {/if}
            </div>
          </Card>
        </div>
      {/each}
    </div>

    <!-- 常見問題 -->
    <div class="mt-20 max-w-4xl mx-auto">
      <h2 class="text-3xl font-bold text-center text-gray-900 mb-12">常見問題</h2>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div class="space-y-6">
          <div>
            <h3 class="font-semibold text-gray-900 mb-2">可以隨時取消訂閱嗎？</h3>
            <p class="text-gray-600">是的，您可以隨時取消訂閱，取消後可繼續使用至當前計費週期結束。</p>
          </div>
          
          <div>
            <h3 class="font-semibold text-gray-900 mb-2">支援哪些付款方式？</h3>
            <p class="text-gray-600">我們接受所有主要信用卡、PayPal 以及企業用戶的發票付款。</p>
          </div>
          
          <div>
            <h3 class="font-semibold text-gray-900 mb-2">有免費試用嗎？</h3>
            <p class="text-gray-600">所有新用戶都可以免費體驗，包含 3 個影片生成額度。</p>
          </div>
        </div>
        
        <div class="space-y-6">
          <div>
            <h3 class="font-semibold text-gray-900 mb-2">影片版權歸誰所有？</h3>
            <p class="text-gray-600">所有生成的影片內容版權完全歸您所有，可用於任何商業用途。</p>
          </div>
          
          <div>
            <h3 class="font-semibold text-gray-900 mb-2">可以升級或降級方案嗎？</h3>
            <p class="text-gray-600">可以，方案變更會在下個計費週期生效，您可在設定中隨時調整。</p>
          </div>
          
          <div>
            <h3 class="font-semibold text-gray-900 mb-2">提供技術支援嗎？</h3>
            <p class="text-gray-600">所有付費用戶都享有完整技術支援，企業用戶更有專屬客服。</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部 CTA -->
    <div class="mt-20 text-center">
      <div class="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
        <h2 class="text-3xl font-bold mb-4">準備開始您的 AI 影片創作之旅？</h2>
        <p class="text-xl opacity-90 mb-6">加入數千位創作者，體驗 AI 影片生成的魅力</p>
        <Button
          variant="secondary"
          size="lg"
          class="bg-white text-blue-600 hover:bg-gray-50"
          on:click={() => currentUser ? goto('/dashboard') : goto('/register')}
        >
          {currentUser ? '前往控制台' : '立即註冊'}
        </Button>
      </div>
    </div>
  </div>
</div>

<style>
  /* 添加一些動畫效果 */
  :global(.pricing-card) {
    transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
  }
  
  :global(.pricing-card:hover) {
    transform: translateY(-4px);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  }
</style>