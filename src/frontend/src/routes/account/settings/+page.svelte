<script>
  import { onMount } from 'svelte';
  import { authStore } from '$lib/stores/auth.js';
  import { toastStore } from '$lib/stores/toast.js';
  import { apiClient } from '$lib/api/client.js';
  import Navigation from '$lib/components/layout/Navigation.svelte';
  import { User, Key, Shield, CreditCard, Bell, Globe, Trash2, Copy, RefreshCw, Eye, EyeOff } from 'lucide-svelte';
  
  let activeTab = 'profile';
  let isLoading = false;
  let showPassword = false;
  let showNewPassword = false;
  let showConfirmPassword = false;
  
  // Profile data
  let profileData = {
    name: '',
    email: '',
    avatar: '',
    timezone: 'UTC',
    language: 'zh-TW'
  };
  
  // Password change data
  let passwordData = {
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  };
  
  // API Keys data
  let apiKeys = [];
  let newApiKeyName = '';
  let generatedApiKey = null;
  
  // Notification settings
  let notificationSettings = {
    emailNotifications: true,
    pushNotifications: true,
    marketingEmails: false,
    videoCompletionNotify: true,
    systemUpdates: true
  };
  
  // Account stats
  let accountStats = {
    videosCreated: 0,
    totalProcessingTime: 0,
    storageUsed: 0,
    apiCallsThisMonth: 0
  };
  
  onMount(async () => {
    if ($authStore.user) {
      profileData.name = $authStore.user.name || '';
      profileData.email = $authStore.user.email || '';
      await loadAccountData();
    }
  });
  
  async function loadAccountData() {
    try {
      // Load API keys
      const keysResponse = await apiClient.get('/api/v1/account/api-keys');
      if (keysResponse.success) {
        apiKeys = keysResponse.data || [];
      }
      
      // Load notification settings
      const notifResponse = await apiClient.get('/api/v1/account/notifications');
      if (notifResponse.success) {
        notificationSettings = { ...notificationSettings, ...notifResponse.data };
      }
      
      // Load account stats
      const statsResponse = await apiClient.get('/api/v1/account/stats');
      if (statsResponse.success) {
        accountStats = { ...accountStats, ...statsResponse.data };
      }
    } catch (error) {
      console.error('Failed to load account data:', error);
    }
  }
  
  async function updateProfile() {
    if (!profileData.name.trim()) {
      toastStore.error('請輸入姓名');
      return;
    }
    
    isLoading = true;
    try {
      const response = await apiClient.put('/api/v1/account/profile', profileData);
      if (response.success) {
        authStore.updateUser(response.data);
        toastStore.success('個人資料更新成功');
      } else {
        toastStore.error(response.error || '更新失敗');
      }
    } catch (error) {
      toastStore.error('更新個人資料時發生錯誤');
    } finally {
      isLoading = false;
    }
  }
  
  async function changePassword() {
    if (!passwordData.currentPassword.trim()) {
      toastStore.error('請輸入目前密碼');
      return;
    }
    
    if (!passwordData.newPassword.trim()) {
      toastStore.error('請輸入新密碼');
      return;
    }
    
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toastStore.error('新密碼與確認密碼不一致');
      return;
    }
    
    if (passwordData.newPassword.length < 8) {
      toastStore.error('新密碼長度至少需要8個字元');
      return;
    }
    
    isLoading = true;
    try {
      const response = await apiClient.put('/api/v1/account/password', {
        currentPassword: passwordData.currentPassword,
        newPassword: passwordData.newPassword
      });
      
      if (response.success) {
        passwordData = { currentPassword: '', newPassword: '', confirmPassword: '' };
        toastStore.success('密碼更新成功');
      } else {
        toastStore.error(response.error || '密碼更新失敗');
      }
    } catch (error) {
      toastStore.error('更新密碼時發生錯誤');
    } finally {
      isLoading = false;
    }
  }
  
  async function generateApiKey() {
    if (!newApiKeyName.trim()) {
      toastStore.error('請輸入API金鑰名稱');
      return;
    }
    
    isLoading = true;
    try {
      const response = await apiClient.post('/api/v1/account/api-keys', {
        name: newApiKeyName
      });
      
      if (response.success) {
        generatedApiKey = response.data;
        apiKeys = [...apiKeys, response.data];
        newApiKeyName = '';
        toastStore.success('API金鑰產生成功');
      } else {
        toastStore.error(response.error || 'API金鑰產生失敗');
      }
    } catch (error) {
      toastStore.error('產生API金鑰時發生錯誤');
    } finally {
      isLoading = false;
    }
  }
  
  async function deleteApiKey(keyId) {
    if (!confirm('確定要刪除此API金鑰嗎？此操作無法復原。')) {
      return;
    }
    
    try {
      const response = await apiClient.delete(`/api/v1/account/api-keys/${keyId}`);
      if (response.success) {
        apiKeys = apiKeys.filter(key => key.id !== keyId);
        toastStore.success('API金鑰已刪除');
      } else {
        toastStore.error(response.error || 'API金鑰刪除失敗');
      }
    } catch (error) {
      toastStore.error('刪除API金鑰時發生錯誤');
    }
  }
  
  function copyApiKey(apiKey) {
    navigator.clipboard.writeText(apiKey).then(() => {
      toastStore.success('API金鑰已複製到剪貼簿');
    }).catch(() => {
      toastStore.error('複製失敗');
    });
  }
  
  async function updateNotifications() {
    isLoading = true;
    try {
      const response = await apiClient.put('/api/v1/account/notifications', notificationSettings);
      if (response.success) {
        toastStore.success('通知設定更新成功');
      } else {
        toastStore.error(response.error || '通知設定更新失敗');
      }
    } catch (error) {
      toastStore.error('更新通知設定時發生錯誤');
    } finally {
      isLoading = false;
    }
  }
  
  function formatBytes(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round((bytes / Math.pow(1024, i)) * 100) / 100 + ' ' + sizes[i];
  }
  
  function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
</script>

<svelte:head>
  <title>帳號設定 - AI Video Creator</title>
  <meta name="description" content="管理您的帳號設定、API金鑰和偏好設定" />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <!-- Navigation -->
  <Navigation />
  
  <div class="max-w-6xl mx-auto px-4 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        帳號設定
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        管理您的個人資料、安全設定和偏好設定
      </p>
    </div>
    
    <div class="grid grid-cols-1 xl:grid-cols-4 gap-6">
      <!-- Sidebar Navigation -->
      <div class="xl:col-span-1">
        <!-- Mobile Tab Navigation -->
        <div class="xl:hidden mb-6">
          <label for="tab-select" class="sr-only">選擇設定類別</label>
          <select 
            id="tab-select"
            class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            bind:value={activeTab}
          >
            <option value="profile">個人資料</option>
            <option value="security">安全設定</option>
            <option value="api-keys">API 金鑰</option>
            <option value="notifications">通知設定</option>
            <option value="usage">使用統計</option>
          </select>
        </div>
        
        <!-- Desktop Sidebar Navigation -->
        <nav class="hidden xl:block bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4" role="navigation" aria-label="帳號設定導航">
          <ul class="space-y-2">
            <li>
              <button
                class="w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-800
                       {activeTab === 'profile' 
                         ? 'text-primary-600 bg-primary-50 dark:text-primary-400 dark:bg-primary-900/20'
                         : 'text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700'}"
                on:click={() => activeTab = 'profile'}
                aria-pressed={activeTab === 'profile'}
                aria-label="個人資料設定"
              >
                <User class="w-4 h-4 mr-3" aria-hidden="true" />
                個人資料
              </button>
            </li>
            <li>
              <button
                class="w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-800
                       {activeTab === 'security' 
                         ? 'text-primary-600 bg-primary-50 dark:text-primary-400 dark:bg-primary-900/20'
                         : 'text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700'}"
                on:click={() => activeTab = 'security'}
                aria-pressed={activeTab === 'security'}
                aria-label="安全設定"
              >
                <Shield class="w-4 h-4 mr-3" aria-hidden="true" />
                安全設定
              </button>
            </li>
            <li>
              <button
                class="w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-800
                       {activeTab === 'api-keys' 
                         ? 'text-primary-600 bg-primary-50 dark:text-primary-400 dark:bg-primary-900/20'
                         : 'text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700'}"
                on:click={() => activeTab = 'api-keys'}
                aria-pressed={activeTab === 'api-keys'}
                aria-label="API 金鑰管理"
              >
                <Key class="w-4 h-4 mr-3" aria-hidden="true" />
                API 金鑰
              </button>
            </li>
            <li>
              <button
                class="w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-800
                       {activeTab === 'notifications' 
                         ? 'text-primary-600 bg-primary-50 dark:text-primary-400 dark:bg-primary-900/20'
                         : 'text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700'}"
                on:click={() => activeTab = 'notifications'}
                aria-pressed={activeTab === 'notifications'}
                aria-label="通知設定"
              >
                <Bell class="w-4 h-4 mr-3" aria-hidden="true" />
                通知設定
              </button>
            </li>
            <li>
              <button
                class="w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-gray-800
                       {activeTab === 'usage' 
                         ? 'text-primary-600 bg-primary-50 dark:text-primary-400 dark:bg-primary-900/20'
                         : 'text-gray-700 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 hover:bg-gray-50 dark:hover:bg-gray-700'}"
                on:click={() => activeTab = 'usage'}
                aria-pressed={activeTab === 'usage'}
                aria-label="使用統計"
              >
                <CreditCard class="w-4 h-4 mr-3" aria-hidden="true" />
                使用統計
              </button>
            </li>
          </ul>
        </nav>
      </div>
      
      <!-- Main Content -->
      <div class="xl:col-span-3">
        <!-- Profile Tab -->
        {#if activeTab === 'profile'}
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
              個人資料
            </h2>
            
            <form on:submit|preventDefault={updateProfile} class="space-y-6">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  姓名
                </label>
                <input
                  type="text"
                  bind:value={profileData.name}
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                  placeholder="請輸入您的姓名"
                />
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  電子郵件
                </label>
                <input
                  type="email"
                  bind:value={profileData.email}
                  disabled
                  class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed"
                />
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  電子郵件地址無法修改
                </p>
              </div>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    時區
                  </label>
                  <select
                    bind:value={profileData.timezone}
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="UTC">UTC</option>
                    <option value="Asia/Taipei">台北 (GMT+8)</option>
                    <option value="Asia/Tokyo">東京 (GMT+9)</option>
                    <option value="America/New_York">紐約 (GMT-5)</option>
                    <option value="Europe/London">倫敦 (GMT+0)</option>
                  </select>
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    語言
                  </label>
                  <select
                    bind:value={profileData.language}
                    class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                  >
                    <option value="zh-TW">繁體中文</option>
                    <option value="zh-CN">简体中文</option>
                    <option value="en-US">English</option>
                    <option value="ja-JP">日本語</option>
                  </select>
                </div>
              </div>
              
              <div class="flex justify-end">
                <button
                  type="submit"
                  disabled={isLoading}
                  class="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white rounded-lg transition-colors flex items-center"
                >
                  {#if isLoading}
                    <RefreshCw class="w-4 h-4 mr-2 animate-spin" />
                  {/if}
                  更新資料
                </button>
              </div>
            </form>
          </div>
        
        <!-- Security Tab -->
        {:else if activeTab === 'security'}
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
              安全設定
            </h2>
            
            <form on:submit|preventDefault={changePassword} class="space-y-6">
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  目前密碼
                </label>
                <div class="relative">
                  {#if showPassword}
                    <input
                      type="text"
                      bind:value={passwordData.currentPassword}
                      class="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                      placeholder="請輸入目前密碼"
                    />
                  {:else}
                    <input
                      type="password"
                      bind:value={passwordData.currentPassword}
                      class="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                      placeholder="請輸入目前密碼"
                    />
                  {/if}
                  <button
                    type="button"
                    class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                    on:click={() => showPassword = !showPassword}
                  >
                    {#if showPassword}
                      <EyeOff class="w-4 h-4" />
                    {:else}
                      <Eye class="w-4 h-4" />
                    {/if}
                  </button>
                </div>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  新密碼
                </label>
                <div class="relative">
                  {#if showNewPassword}
                    <input
                      type="text"
                      bind:value={passwordData.newPassword}
                      class="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                      placeholder="請輸入新密碼"
                    />
                  {:else}
                    <input
                      type="password"
                      bind:value={passwordData.newPassword}
                      class="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                      placeholder="請輸入新密碼"
                    />
                  {/if}
                  <button
                    type="button"
                    class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                    on:click={() => showNewPassword = !showNewPassword}
                  >
                    {#if showNewPassword}
                      <EyeOff class="w-4 h-4" />
                    {:else}
                      <Eye class="w-4 h-4" />
                    {/if}
                  </button>
                </div>
              </div>
              
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  確認新密碼
                </label>
                <div class="relative">
                  {#if showConfirmPassword}
                    <input
                      type="text"
                      bind:value={passwordData.confirmPassword}
                      class="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                      placeholder="請再次輸入新密碼"
                    />
                  {:else}
                    <input
                      type="password"
                      bind:value={passwordData.confirmPassword}
                      class="w-full px-3 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                      placeholder="請再次輸入新密碼"
                    />
                  {/if}
                  <button
                    type="button"
                    class="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                    on:click={() => showConfirmPassword = !showConfirmPassword}
                  >
                    {#if showConfirmPassword}
                      <EyeOff class="w-4 h-4" />
                    {:else}
                      <Eye class="w-4 h-4" />
                    {/if}
                  </button>
                </div>
              </div>
              
              <div class="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <h3 class="text-sm font-medium text-blue-800 dark:text-blue-300 mb-2">
                  密碼要求
                </h3>
                <ul class="text-sm text-blue-700 dark:text-blue-400 space-y-1">
                  <li>• 至少8個字元</li>
                  <li>• 建議包含大小寫字母、數字和特殊符號</li>
                  <li>• 不要使用常見密碼或個人資訊</li>
                </ul>
              </div>
              
              <div class="flex justify-end">
                <button
                  type="submit"
                  disabled={isLoading}
                  class="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white rounded-lg transition-colors flex items-center"
                >
                  {#if isLoading}
                    <RefreshCw class="w-4 h-4 mr-2 animate-spin" />
                  {/if}
                  更新密碼
                </button>
              </div>
            </form>
          </div>
        
        <!-- API Keys Tab -->
        {:else if activeTab === 'api-keys'}
          <div class="space-y-6">
            <!-- Generate New API Key -->
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                產生新的 API 金鑰
              </h2>
              
              <div class="flex space-x-4">
                <input
                  type="text"
                  bind:value={newApiKeyName}
                  placeholder="輸入金鑰名稱（例如：行動應用程式）"
                  class="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                />
                <button
                  on:click={generateApiKey}
                  disabled={isLoading || !newApiKeyName.trim()}
                  class="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white rounded-lg transition-colors flex items-center"
                >
                  {#if isLoading}
                    <RefreshCw class="w-4 h-4 mr-2 animate-spin" />
                  {/if}
                  產生金鑰
                </button>
              </div>
              
              {#if generatedApiKey}
                <div class="mt-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                  <p class="text-sm font-medium text-green-800 dark:text-green-300 mb-2">
                    新的 API 金鑰已產生
                  </p>
                  <div class="flex items-center space-x-2">
                    <code class="flex-1 px-3 py-2 bg-white dark:bg-gray-800 border rounded text-sm font-mono">
                      {generatedApiKey.key}
                    </code>
                    <button
                      on:click={() => copyApiKey(generatedApiKey.key)}
                      class="p-2 text-green-600 hover:text-green-700 rounded-lg hover:bg-green-100 dark:hover:bg-green-800/30"
                    >
                      <Copy class="w-4 h-4" />
                    </button>
                  </div>
                  <p class="text-xs text-green-700 dark:text-green-400 mt-2">
                    ⚠️ 請立即複製此金鑰，離開頁面後將無法再次查看
                  </p>
                </div>
              {/if}
            </div>
            
            <!-- Existing API Keys -->
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                現有 API 金鑰
              </h2>
              
              {#if apiKeys.length === 0}
                <div class="text-center py-8">
                  <Key class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                  <p class="text-gray-500 dark:text-gray-400">尚未建立任何 API 金鑰</p>
                </div>
              {:else}
                <div class="space-y-4">
                  {#each apiKeys as apiKey}
                    <div class="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                      <div class="flex-1">
                        <h3 class="font-medium text-gray-900 dark:text-white">
                          {apiKey.name}
                        </h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400">
                          建立於: {new Date(apiKey.createdAt || Date.now()).toLocaleDateString('zh-TW')}
                        </p>
                        <p class="text-sm text-gray-500 dark:text-gray-400">
                          最後使用: {apiKey.lastUsed ? new Date(apiKey.lastUsed).toLocaleDateString('zh-TW') : '從未使用'}
                        </p>
                        <div class="mt-2">
                          <code class="text-xs font-mono text-gray-600 dark:text-gray-400">
                            {apiKey.keyPreview || `${apiKey.key?.substring(0, 8)}...`}
                          </code>
                        </div>
                      </div>
                      
                      <div class="flex items-center space-x-2">
                        {#if apiKey.key}
                          <button
                            on:click={() => copyApiKey(apiKey.key)}
                            class="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
                            title="複製金鑰"
                          >
                            <Copy class="w-4 h-4" />
                          </button>
                        {/if}
                        <button
                          on:click={() => deleteApiKey(apiKey.id)}
                          class="p-2 text-red-400 hover:text-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
                          title="刪除金鑰"
                        >
                          <Trash2 class="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          </div>
        
        <!-- Notifications Tab -->
        {:else if activeTab === 'notifications'}
          <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-6">
              通知設定
            </h2>
            
            <form on:submit|preventDefault={updateNotifications} class="space-y-6">
              <div class="space-y-4">
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="text-sm font-medium text-gray-900 dark:text-white">
                      電子郵件通知
                    </h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                      接收重要通知的電子郵件
                    </p>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      bind:checked={notificationSettings.emailNotifications}
                      class="sr-only peer"
                    />
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </label>
                </div>
                
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="text-sm font-medium text-gray-900 dark:text-white">
                      推播通知
                    </h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                      在瀏覽器中接收即時通知
                    </p>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      bind:checked={notificationSettings.pushNotifications}
                      class="sr-only peer"
                    />
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </label>
                </div>
                
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="text-sm font-medium text-gray-900 dark:text-white">
                      影片完成通知
                    </h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                      影片處理完成時通知您
                    </p>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      bind:checked={notificationSettings.videoCompletionNotify}
                      class="sr-only peer"
                    />
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </label>
                </div>
                
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="text-sm font-medium text-gray-900 dark:text-white">
                      系統更新通知
                    </h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                      新功能和系統維護通知
                    </p>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      bind:checked={notificationSettings.systemUpdates}
                      class="sr-only peer"
                    />
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </label>
                </div>
                
                <div class="flex items-center justify-between">
                  <div>
                    <h3 class="text-sm font-medium text-gray-900 dark:text-white">
                      行銷電子郵件
                    </h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                      產品更新和促銷資訊
                    </p>
                  </div>
                  <label class="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      bind:checked={notificationSettings.marketingEmails}
                      class="sr-only peer"
                    />
                    <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary-600"></div>
                  </label>
                </div>
              </div>
              
              <div class="flex justify-end">
                <button
                  type="submit"
                  disabled={isLoading}
                  class="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-primary-400 text-white rounded-lg transition-colors flex items-center"
                >
                  {#if isLoading}
                    <RefreshCw class="w-4 h-4 mr-2 animate-spin" />
                  {/if}
                  儲存設定
                </button>
              </div>
            </form>
          </div>
        
        <!-- Usage Tab -->
        {:else if activeTab === 'usage'}
          <div class="space-y-6">
            <!-- Stats Overview -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-500 dark:text-gray-400">
                      影片總數
                    </p>
                    <p class="text-2xl font-bold text-gray-900 dark:text-white">
                      {accountStats.videosCreated}
                    </p>
                  </div>
                  <div class="p-3 bg-primary-100 dark:bg-primary-900/20 rounded-full">
                    <svg class="w-6 h-6 text-primary-600 dark:text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>
              </div>
              
              <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-500 dark:text-gray-400">
                      處理時間
                    </p>
                    <p class="text-2xl font-bold text-gray-900 dark:text-white">
                      {formatDuration(accountStats.totalProcessingTime)}
                    </p>
                  </div>
                  <div class="p-3 bg-green-100 dark:bg-green-900/20 rounded-full">
                    <svg class="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
              </div>
              
              <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-500 dark:text-gray-400">
                      儲存空間
                    </p>
                    <p class="text-2xl font-bold text-gray-900 dark:text-white">
                      {formatBytes(accountStats.storageUsed)}
                    </p>
                  </div>
                  <div class="p-3 bg-yellow-100 dark:bg-yellow-900/20 rounded-full">
                    <svg class="w-6 h-6 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2m-8 6V9m4 1v1m-4 0h4m5 0v8a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h12a2 2 0 012 2v8z" />
                    </svg>
                  </div>
                </div>
              </div>
              
              <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-sm font-medium text-gray-500 dark:text-gray-400">
                      本月 API 調用
                    </p>
                    <p class="text-2xl font-bold text-gray-900 dark:text-white">
                      {accountStats.apiCallsThisMonth.toLocaleString()}
                    </p>
                  </div>
                  <div class="p-3 bg-purple-100 dark:bg-purple-900/20 rounded-full">
                    <svg class="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Usage Details -->
            <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                使用明細
              </h2>
              
              <div class="text-center py-8">
                <CreditCard class="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                <p class="text-gray-500 dark:text-gray-400">
                  詳細的使用統計功能開發中...
                </p>
              </div>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>