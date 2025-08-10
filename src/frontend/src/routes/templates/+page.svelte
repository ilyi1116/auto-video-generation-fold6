<script>
  import { onMount } from 'svelte';
  import { apiClient } from '$lib/api/client.js';
  import { toastStore } from '$lib/stores/toast.js';
  import Navigation from '$lib/components/layout/Navigation.svelte';
  
  let templates = {};
  let categories = {};
  let selectedCategory = 'all';
  let selectedPlatform = 'all';
  let loading = true;
  let generating = false;
  let availableCategories = [];
  let availablePlatforms = [];
  
  // 生成相關變量
  let selectedTemplate = null;
  let showGenerateModal = false;
  let templateParameters = {};
  let generatedContent = '';
  let generationInfo = null;

  onMount(async () => {
    await loadTemplates();
    await loadCategories();
  });

  async function loadTemplates() {
    try {
      loading = true;
      const params = {};
      if (selectedCategory !== 'all') params.category = selectedCategory;
      if (selectedPlatform !== 'all') params.platform = selectedPlatform;
      
      const response = await apiClient.templates.list(params);
      if (response.success) {
        templates = response.data.templates;
        availableCategories = response.data.filters.categories;
        availablePlatforms = response.data.filters.platforms;
      }
    } catch (error) {
      console.error('加載模板失敗:', error);
      toastStore.error('載入模板失敗: ' + error.message);
    } finally {
      loading = false;
    }
  }

  async function loadCategories() {
    try {
      const response = await apiClient.templates.getCategories();
      if (response.success) {
        categories = response.data.categories;
      }
    } catch (error) {
      console.error('加載分類失敗:', error);
    }
  }

  async function handleCategoryChange() {
    await loadTemplates();
  }

  async function handlePlatformChange() {
    await loadTemplates();
  }

  function openGenerateModal(template) {
    selectedTemplate = template;
    templateParameters = {};
    generatedContent = '';
    generationInfo = null;
    showGenerateModal = true;
  }

  function closeGenerateModal() {
    showGenerateModal = false;
    selectedTemplate = null;
    templateParameters = {};
    generatedContent = '';
  }

  async function generateContent() {
    if (!selectedTemplate) return;
    
    try {
      generating = true;
      const response = await apiClient.templates.generate(
        selectedTemplate.id, 
        templateParameters, 
        true
      );
      
      if (response.success) {
        generatedContent = response.data.content;
        generationInfo = response.data.generation_info;
        toastStore.success('內容生成成功！');
      } else {
        toastStore.error('生成失敗: ' + response.error);
      }
    } catch (error) {
      console.error('生成內容失敗:', error);
      toastStore.error('生成內容失敗: ' + error.message);
    } finally {
      generating = false;
    }
  }

  function copyToClipboard() {
    navigator.clipboard.writeText(generatedContent).then(() => {
      toastStore.success('內容已複製到剪貼簿');
    });
  }

  function getCategoryDisplayName(categoryKey) {
    const displayNames = {
      'social_media': '社群媒體',
      'content_marketing': '內容行銷',
      'advertising': '廣告文案',
      'email_marketing': '電子郵件行銷',
      'video_content': '影片內容',
      'ecommerce': '電子商務'
    };
    return displayNames[categoryKey] || categoryKey;
  }

  function getSuccessRateColor(rate) {
    if (rate >= 90) return 'text-green-600';
    if (rate >= 80) return 'text-blue-600';
    if (rate >= 70) return 'text-yellow-600';
    return 'text-red-600';
  }
</script>

<svelte:head>
  <title>內容模板 - AutoVideo</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <Navigation />
  
  <div class="max-w-7xl mx-auto px-4 py-8">
    <!-- 頁面標題 -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">🎨 內容模板</h1>
      <p class="text-gray-600 dark:text-gray-400">
        使用專業模板快速生成各種類型的內容，提升創作效率
      </p>
    </div>

    <!-- 篩選器 -->
    <div class="mb-6 bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            按分類篩選
          </label>
          <select 
            bind:value={selectedCategory} 
            on:change={handleCategoryChange}
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                   focus:ring-2 focus:ring-blue-500 focus:border-transparent
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="all">所有分類</option>
            {#each availableCategories as category}
              <option value={category}>{getCategoryDisplayName(category)}</option>
            {/each}
          </select>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            按平台篩選
          </label>
          <select 
            bind:value={selectedPlatform} 
            on:change={handlePlatformChange}
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                   focus:ring-2 focus:ring-blue-500 focus:border-transparent
                   bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
          >
            <option value="all">所有平台</option>
            {#each availablePlatforms as platform}
              <option value={platform}>{platform}</option>
            {/each}
          </select>
        </div>
      </div>
    </div>

    <!-- 模板網格 -->
    {#if loading}
      <div class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <p class="mt-4 text-gray-600 dark:text-gray-400">載入模板中...</p>
      </div>
    {:else if Object.keys(templates).length === 0}
      <div class="text-center py-12">
        <div class="text-gray-400 mb-4">
          <svg class="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" 
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">找不到模板</h3>
        <p class="text-gray-600 dark:text-gray-400">嘗試調整篩選條件或稍後重試</p>
      </div>
    {:else}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each Object.values(templates) as template}
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 
                      hover:shadow-md transition-shadow duration-200">
            <!-- 模板標題區域 -->
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <div class="flex items-start justify-between">
                <div>
                  <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {template.name}
                  </h3>
                  <p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {template.description}
                  </p>
                </div>
              </div>
              
              <!-- 分類和平台標籤 -->
              <div class="flex flex-wrap gap-2 mb-3">
                <span class="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 
                           text-xs rounded-full">
                  {getCategoryDisplayName(template.category)}
                </span>
                {#each template.platform as platform}
                  <span class="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 
                             text-xs rounded-full">
                    {platform}
                  </span>
                {/each}
              </div>
              
              <!-- 使用統計 -->
              <div class="flex items-center justify-between text-sm">
                <div class="flex items-center space-x-4">
                  <span class="text-gray-600 dark:text-gray-400">
                    使用次數: <span class="font-medium">{template.usage_count}</span>
                  </span>
                  <span class="text-gray-600 dark:text-gray-400">
                    成功率: <span class="font-medium {getSuccessRateColor(template.success_rate)}">
                      {template.success_rate}%
                    </span>
                  </span>
                </div>
              </div>
            </div>
            
            <!-- 模板預覽 -->
            <div class="p-6">
              <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">內容預覽：</h4>
              <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 text-sm text-gray-600 dark:text-gray-400 
                          max-h-32 overflow-hidden relative">
                <pre class="whitespace-pre-wrap font-sans">{template.example}</pre>
                <div class="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t 
                           from-gray-50 dark:from-gray-700 to-transparent"></div>
              </div>
            </div>
            
            <!-- 操作按鈕 -->
            <div class="p-6 pt-0">
              <button
                on:click={() => openGenerateModal(template)}
                class="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg 
                       transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              >
                🚀 使用模板生成內容
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<!-- 生成內容模態框 -->
{#if showGenerateModal && selectedTemplate}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
      <!-- 模態框標題 -->
      <div class="p-6 border-b border-gray-200 dark:border-gray-700">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white">
              使用模板生成內容
            </h2>
            <p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
              模板：{selectedTemplate.name}
            </p>
          </div>
          <button
            on:click={closeGenerateModal}
            class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      
      <div class="p-6 space-y-6">
        <!-- 參數設定區域 -->
        <div>
          <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-4">設定參數</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- 動態生成參數輸入欄位 -->
            <div class="md:col-span-2">
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                主題 *
              </label>
              <input
                type="text"
                bind:value={templateParameters.topic}
                placeholder="輸入內容主題..."
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                風格
              </label>
              <select
                bind:value={templateParameters.style}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="professional">專業</option>
                <option value="casual">輕鬆</option>
                <option value="friendly">親切</option>
                <option value="authoritative">權威</option>
                <option value="creative">創意</option>
              </select>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                語調
              </label>
              <select
                bind:value={templateParameters.tone}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="conversational">對話式</option>
                <option value="formal">正式</option>
                <option value="enthusiastic">熱情</option>
                <option value="informative">資訊性</option>
                <option value="persuasive">說服性</option>
              </select>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                目標受眾
              </label>
              <input
                type="text"
                bind:value={templateParameters.target_audience}
                placeholder="例如：25-35歲的上班族"
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                內容長度
              </label>
              <select
                bind:value={templateParameters.length}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg 
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="100">短文 (~100字)</option>
                <option value="300">中文 (~300字)</option>
                <option value="500">長文 (~500字)</option>
                <option value="1000">詳細 (~1000字)</option>
              </select>
            </div>
          </div>
        </div>
        
        <!-- 生成按鈕 -->
        <div class="flex justify-center">
          <button
            on:click={generateContent}
            disabled={generating || !templateParameters.topic}
            class="px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 
                   text-white font-medium rounded-lg transition-colors duration-200 
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            {#if generating}
              <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white inline" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              AI 生成中...
            {:else}
              🤖 生成內容
            {/if}
          </button>
        </div>
        
        <!-- 生成結果 -->
        {#if generatedContent}
          <div class="border-t border-gray-200 dark:border-gray-700 pt-6">
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-medium text-gray-900 dark:text-white">生成結果</h3>
              <div class="flex space-x-2">
                <button
                  on:click={copyToClipboard}
                  class="px-3 py-1 bg-gray-500 hover:bg-gray-600 text-white text-sm rounded 
                         transition-colors duration-200"
                >
                  📋 複製
                </button>
              </div>
            </div>
            
            <!-- 生成資訊 -->
            {#if generationInfo}
              <div class="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-sm">
                <div class="flex items-center justify-between">
                  <span class="text-blue-700 dark:text-blue-300">
                    提供者：{generationInfo.provider}
                  </span>
                  <span class="text-blue-600 dark:text-blue-400">
                    {generationInfo.word_count} 字 | {generationInfo.content_length} 字符
                  </span>
                </div>
              </div>
            {/if}
            
            <!-- 生成的內容 -->
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <pre class="whitespace-pre-wrap font-sans text-gray-900 dark:text-white text-sm leading-relaxed">
{generatedContent}
              </pre>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}