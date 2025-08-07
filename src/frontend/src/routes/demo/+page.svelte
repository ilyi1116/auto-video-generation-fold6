<script>
  import { onMount } from 'svelte';
  import { notifications, trackVideoProgress, simulateProgress, NOTIFICATION_TYPES } from '$lib/stores/notifications.js';
  import Navigation from '$lib/components/layout/Navigation.svelte';
  import { Play, Bell, CheckCircle, AlertCircle, Info } from 'lucide-svelte';
  
  let demoCount = 1;
  
  function showSuccessNotification() {
    notifications.add({
      type: NOTIFICATION_TYPES.SUCCESS,
      title: '操作成功',
      message: '您的操作已成功完成',
      icon: '✅'
    });
  }
  
  function showErrorNotification() {
    notifications.add({
      type: NOTIFICATION_TYPES.ERROR,
      title: '操作失敗',
      message: '抱歉，操作執行過程中發生錯誤',
      icon: '❌',
      persistent: true
    });
  }
  
  function showInfoNotification() {
    notifications.add({
      type: NOTIFICATION_TYPES.INFO,
      title: '系統消息',
      message: '這是一則重要的系統通知消息',
      icon: '📢'
    });
  }
  
  function showWarningNotification() {
    notifications.add({
      type: NOTIFICATION_TYPES.WARNING,
      title: '警告提醒',
      message: '請注意，此操作可能會影響您的數據',
      icon: '⚠️'
    });
  }
  
  function startVideoProcessing() {
    const videoTitle = `演示影片 ${demoCount++}`;
    const notificationId = trackVideoProgress(
      `demo_video_${Date.now()}`,
      videoTitle
    );
    
    simulateProgress(notificationId, videoTitle);
  }
  
  function showNotificationWithAction() {
    notifications.add({
      type: NOTIFICATION_TYPES.SUCCESS,
      title: '新影片已生成',
      message: '您的 AI 影片已成功生成完成！',
      icon: '🎬',
      action: {
        label: '查看影片',
        url: `/video/demo-${Date.now()}`
      }
    });
  }
  
  function addMultipleNotifications() {
    const notifications_data = [
      { type: NOTIFICATION_TYPES.INFO, title: '腳本生成完成', message: 'AI 已為您生成新的腳本內容', icon: '📝' },
      { type: NOTIFICATION_TYPES.SUCCESS, title: '圖像生成完成', message: '已成功生成 4 張高質量圖像', icon: '🎨' },
      { type: NOTIFICATION_TYPES.SUCCESS, title: '語音合成完成', message: '語音合成已完成，音質清晰自然', icon: '🎤' },
      { type: NOTIFICATION_TYPES.WARNING, title: '存儲空間不足', message: '您的存儲空間即將用完', icon: '💾' }
    ];
    
    notifications_data.forEach((notif, index) => {
      setTimeout(() => {
        notifications.add(notif);
      }, index * 500);
    });
  }
  
  function clearAllNotifications() {
    notifications.clear();
  }
</script>

<svelte:head>
  <title>通知系統演示 - AI Video Creator</title>
  <meta name="description" content="演示即時通知和進度追蹤功能" />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gray-900">
  <!-- Navigation -->
  <Navigation />
  
  <div class="max-w-4xl mx-auto px-4 py-8">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
        通知系統演示
      </h1>
      <p class="text-gray-600 dark:text-gray-400">
        測試各種通知類型和即時進度追蹤功能
      </p>
    </div>
    
    <!-- Demo Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      <!-- Basic Notifications -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <Bell class="w-5 h-5 mr-2" />
          基本通知類型
        </h2>
        <div class="space-y-3">
          <button
            on:click={showSuccessNotification}
            class="w-full px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors flex items-center justify-center"
          >
            <CheckCircle class="w-4 h-4 mr-2" />
            成功通知
          </button>
          
          <button
            on:click={showErrorNotification}
            class="w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center justify-center"
          >
            <AlertCircle class="w-4 h-4 mr-2" />
            錯誤通知
          </button>
          
          <button
            on:click={showInfoNotification}
            class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center justify-center"
          >
            <Info class="w-4 h-4 mr-2" />
            資訊通知
          </button>
          
          <button
            on:click={showWarningNotification}
            class="w-full px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors flex items-center justify-center"
          >
            <AlertCircle class="w-4 h-4 mr-2" />
            警告通知
          </button>
        </div>
      </div>
      
      <!-- Progress Notifications -->
      <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <Play class="w-5 h-5 mr-2" />
          進度追蹤演示
        </h2>
        <div class="space-y-3">
          <button
            on:click={startVideoProcessing}
            class="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors flex items-center justify-center"
          >
            🎬 開始影片處理
          </button>
          
          <button
            on:click={showNotificationWithAction}
            class="w-full px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors flex items-center justify-center"
          >
            🎯 帶操作的通知
          </button>
          
          <button
            on:click={addMultipleNotifications}
            class="w-full px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors flex items-center justify-center"
          >
            📚 批量通知
          </button>
          
          <button
            on:click={clearAllNotifications}
            class="w-full px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors flex items-center justify-center"
          >
            🗑️ 清除所有通知
          </button>
        </div>
      </div>
    </div>
    
    <!-- Instructions -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
      <h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        使用說明
      </h2>
      
      <div class="prose dark:prose-invert max-w-none">
        <ul class="text-sm text-gray-600 dark:text-gray-400 space-y-2">
          <li>
            <strong>通知鈴鐺：</strong>點擊頁面右上角的鈴鐺圖示可以查看所有通知
          </li>
          <li>
            <strong>進度 Toast：</strong>進度類型的通知會在頁面右下角顯示為浮動卡片
          </li>
          <li>
            <strong>自動消失：</strong>一般通知會在 5 秒後自動消失，持久性通知需要手動關閉
          </li>
          <li>
            <strong>未讀計數：</strong>鈴鐺圖示上的紅色圓點顯示未讀通知數量
          </li>
          <li>
            <strong>操作按鈕：</strong>某些通知包含操作按鈕，可以直接跳轉到相關頁面
          </li>
          <li>
            <strong>進度追蹤：</strong>影片處理等長時間任務會顯示實時進度條
          </li>
        </ul>
      </div>
      
      <div class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
        <p class="text-sm text-blue-800 dark:text-blue-300">
          <strong>提示：</strong>在實際應用中，這些通知會通過 WebSocket 連接從後端服務器實時推送，
          包括影片處理進度、AI 任務狀態、系統通知等。
        </p>
      </div>
    </div>
  </div>
</div>