<script>
  import { dev } from '$app/environment';
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { Button, Input, Card, tokens } from '$lib/components/ui/index.js';
  
  // 如果不是開發環境，重定向到首頁
  onMount(() => {
    if (!dev) {
      goto('/');
    }
  });
  
  // 示例狀態
  let inputValue = '';
  let inputError = '';
  let loadingStates = {
    primary: false,
    secondary: false,
    outline: false
  };
  
  // 組件變體示例
  const buttonVariants = ['primary', 'secondary', 'outline', 'ghost', 'destructive'];
  const buttonSizes = ['xs', 'sm', 'md', 'lg', 'xl'];
  const inputVariants = ['default', 'filled', 'borderless'];
  const cardVariants = ['default', 'elevated', 'outlined', 'filled'];
  
  function handleButtonClick(variant) {
    loadingStates[variant] = true;
    setTimeout(() => {
      loadingStates[variant] = false;
    }, 2000);
  }
  
  function validateInput() {
    if (inputValue.length < 3) {
      inputError = '至少需要 3 個字符';
    } else {
      inputError = '';
    }
  }
  
  // 顏色展示
  const colorCategories = [
    { name: '主要色彩', key: 'primary' },
    { name: '次要色彩', key: 'secondary' },
    { name: '成功色彩', key: 'success' },
    { name: '警告色彩', key: 'warning' },
    { name: '錯誤色彩', key: 'error' },
    { name: '中性色彩', key: 'neutral' }
  ];
</script>

<svelte:head>
  <title>組件庫文檔 - Auto Video</title>
</svelte:head>

{#if dev}
<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <!-- 頁面標題 -->
  <div class="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">
            🎨 組件庫文檔
          </h1>
          <p class="mt-2 text-gray-600 dark:text-gray-400">
            基於設計 Tokens 的統一 UI 組件系統
          </p>
        </div>
        <div class="text-sm text-gray-500 dark:text-gray-400 font-mono">
          v1.0.0 • 開發環境
        </div>
      </div>
    </div>
  </div>
  
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">
    
    <!-- 設計 Tokens -->
    <section id="tokens">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
        設計 Tokens
      </h2>
      
      <!-- 顏色系統 -->
      <div class="space-y-6">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-gray-100">顏色系統</h3>
        
        {#each colorCategories as category}
          <div>
            <h4 class="text-lg font-medium text-gray-800 dark:text-gray-200 mb-3">
              {category.name}
            </h4>
            <div class="grid grid-cols-2 sm:grid-cols-5 lg:grid-cols-10 gap-2">
              {#each Object.entries(tokens.colors[category.key] || {}) as [shade, color]}
                <div class="text-center">
                  <div 
                    class="w-full h-12 rounded-md border border-gray-200 dark:border-gray-600 mb-2"
                    style="background-color: {color}"
                  ></div>
                  <div class="text-xs font-mono text-gray-600 dark:text-gray-400">
                    {shade}
                  </div>
                  <div class="text-xs font-mono text-gray-500 dark:text-gray-500">
                    {color}
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {/each}
      </div>
    </section>
    
    <!-- Button 組件 -->
    <section id="buttons">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
        Button 組件
      </h2>
      
      <div class="space-y-8">
        <!-- 變體展示 -->
        <Card variant="elevated" padding="lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            按鈕變體
          </h3>
          <div class="flex flex-wrap gap-3">
            {#each buttonVariants as variant}
              <Button 
                {variant} 
                loading={loadingStates[variant]}
                on:click={() => handleButtonClick(variant)}
              >
                {variant} Button
              </Button>
            {/each}
          </div>
        </Card>
        
        <!-- 大小展示 -->
        <Card variant="elevated" padding="lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            按鈕大小
          </h3>
          <div class="flex flex-wrap items-end gap-3">
            {#each buttonSizes as size}
              <Button variant="primary" {size}>
                {size.toUpperCase()}
              </Button>
            {/each}
          </div>
        </Card>
        
        <!-- 狀態展示 -->
        <Card variant="elevated" padding="lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            按鈕狀態
          </h3>
          <div class="flex flex-wrap gap-3">
            <Button variant="primary">正常</Button>
            <Button variant="primary" disabled>禁用</Button>
            <Button variant="primary" loading>載入中</Button>
            <Button variant="primary" fullWidth>全寬度</Button>
          </div>
        </Card>
      </div>
    </section>
    
    <!-- Input 組件 -->
    <section id="inputs">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
        Input 組件
      </h2>
      
      <div class="space-y-8">
        <!-- 變體展示 -->
        <Card variant="elevated" padding="lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            輸入框變體
          </h3>
          <div class="grid gap-4 max-w-md">
            {#each inputVariants as variant}
              <Input 
                {variant}
                label="{variant} Input"
                placeholder="請輸入內容..."
                hint="這是 {variant} 變體的輸入框"
              />
            {/each}
          </div>
        </Card>
        
        <!-- 狀態展示 -->
        <Card variant="elevated" padding="lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            輸入框狀態
          </h3>
          <div class="grid gap-4 max-w-md">
            <Input 
              label="正常狀態"
              placeholder="請輸入內容..."
              bind:value={inputValue}
              on:input={validateInput}
            />
            <Input 
              label="錯誤狀態"
              placeholder="請輸入內容..."
              error={inputError || "這是錯誤訊息"}
            />
            <Input 
              label="禁用狀態"
              placeholder="禁用的輸入框"
              disabled
            />
            <Input 
              type="textarea"
              label="文本域"
              placeholder="這是一個多行文本輸入框..."
              rows={4}
            />
          </div>
        </Card>
      </div>
    </section>
    
    <!-- Card 組件 -->
    <section id="cards">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
        Card 組件
      </h2>
      
      <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {#each cardVariants as variant}
          <Card {variant} interactive>
            <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              {variant} Card
            </h3>
            <p class="text-gray-600 dark:text-gray-400 text-sm">
              這是 {variant} 變體的卡片組件示例。卡片可以包含各種內容。
            </p>
            <div class="mt-4">
              <Button size="sm" variant="outline">
                了解更多
              </Button>
            </div>
          </Card>
        {/each}
      </div>
    </section>
    
    <!-- 組合示例 -->
    <section id="examples">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
        組合示例
      </h2>
      
      <div class="grid gap-8 lg:grid-cols-2">
        <!-- 登入表單 -->
        <Card variant="elevated" padding="lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            登入表單
          </h3>
          <div class="space-y-4">
            <Input 
              type="email"
              label="電子郵件"
              placeholder="your@email.com"
            />
            <Input 
              type="password"
              label="密碼"
              placeholder="請輸入密碼"
            />
            <div class="flex gap-2">
              <Button variant="primary" fullWidth>
                登入
              </Button>
              <Button variant="outline">
                註冊
              </Button>
            </div>
          </div>
        </Card>
        
        <!-- 設定面板 -->
        <Card variant="elevated" padding="lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            設定面板
          </h3>
          <div class="space-y-4">
            <Input 
              label="顯示名稱"
              placeholder="請輸入您的顯示名稱"
            />
            <Input 
              type="textarea"
              label="個人簡介"
              placeholder="介紹一下自己..."
              rows={3}
            />
            <div class="flex justify-end gap-2">
              <Button variant="ghost">
                取消
              </Button>
              <Button variant="primary">
                保存
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </section>
    
    <!-- 設計指南 -->
    <section id="guidelines">
      <h2 class="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
        設計指南
      </h2>
      
      <div class="space-y-6">
        <Card variant="default" padding="lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            使用原則
          </h3>
          <div class="prose dark:prose-invert max-w-none">
            <ul class="list-disc list-inside space-y-2 text-gray-700 dark:text-gray-300">
              <li>
                <strong>一致性</strong>：所有組件都基於統一的設計 Tokens
              </li>
              <li>
                <strong>可訪問性</strong>：遵循 WCAG 2.1 AA 標準
              </li>
              <li>
                <strong>響應式</strong>：適配各種設備和屏幕尺寸
              </li>
              <li>
                <strong>可維護性</strong>：組件化設計，便於更新和擴展
              </li>
              <li>
                <strong>性能優化</strong>：最小化 bundle 大小，優化載入速度
              </li>
            </ul>
          </div>
        </Card>
        
        <Card variant="default" padding="lg">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            使用方法
          </h3>
          <div class="bg-gray-900 rounded-lg p-4 text-sm font-mono text-gray-100 overflow-x-auto">
            <pre>{`import { Button, Input, Card } from '$lib/components/ui/index.js';

// 使用按鈕組件
<Button variant="primary" size="md">
  點擊我
</Button>

// 使用輸入框組件
<Input 
  label="用戶名"
  placeholder="請輸入用戶名"
  bind:value={username}
/>

// 使用卡片組件
<Card variant="elevated" interactive>
  <h3>卡片標題</h3>
  <p>卡片內容...</p>
</Card>`}</pre>
          </div>
        </Card>
      </div>
    </section>
    
  </div>
  
  <!-- 底部導航 -->
  <div class="fixed bottom-4 right-4">
    <Card variant="elevated" padding="sm">
      <div class="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
        <span>快捷鍵:</span>
        <kbd class="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs">Ctrl+Shift+D</kbd>
        <span>調試面板</span>
      </div>
    </Card>
  </div>
</div>
{/if}

<style>
  kbd {
    font-family: ui-monospace, monospace;
    border: 1px solid theme('colors.gray.300');
  }
</style>