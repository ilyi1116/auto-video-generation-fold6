// Auto Video PWA Service Worker
// 提供離線支援、快取管理和背景同步功能

const CACHE_NAME = 'auto-video-v1.0.0';
const STATIC_CACHE = 'auto-video-static-v1.0.0';
const DYNAMIC_CACHE = 'auto-video-dynamic-v1.0.0';
const API_CACHE = 'auto-video-api-v1.0.0';

// 需要快取的靜態資源
const STATIC_ASSETS = [
  '/',
  '/dashboard',
  '/projects',
  '/ai/script',
  '/ai/voice',
  '/ai/images',
  '/create',
  '/trends',
  '/social',
  '/analytics',
  '/settings',
  '/profile',
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/offline.html'
];

// 需要快取的 API 端點模式
const API_CACHE_PATTERNS = [
  /\/api\/trends/,
  /\/api\/user\/profile/,
  /\/api\/projects\/\d+/,
  /\/api\/scripts/
];

// 安裝事件 - 預快取靜態資源
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    Promise.all([
      // 快取靜態資源
      caches.open(STATIC_CACHE).then((cache) => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      }),
      
      // 跳過等待，立即激活
      self.skipWaiting()
    ])
  );
});

// 激活事件 - 清理舊快取
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    Promise.all([
      // 清理舊快取
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter(cacheName => 
              cacheName.startsWith('auto-video-') && 
              cacheName !== STATIC_CACHE &&
              cacheName !== DYNAMIC_CACHE &&
              cacheName !== API_CACHE
            )
            .map(cacheName => {
              console.log('Service Worker: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            })
        );
      }),
      
      // 立即控制所有客戶端
      self.clients.claim()
    ])
  );
});

// 拦截網路請求
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // 跳過非 HTTP(S) 請求
  if (!request.url.startsWith('http')) {
    return;
  }
  
  // 跳過 Chrome 擴展請求
  if (url.protocol === 'chrome-extension:') {
    return;
  }
  
  // API 請求處理
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }
  
  // 靜態資源處理
  if (request.destination === 'image' || 
      request.destination === 'script' || 
      request.destination === 'style' ||
      request.destination === 'font') {
    event.respondWith(handleStaticAsset(request));
    return;
  }
  
  // 頁面請求處理
  if (request.destination === 'document') {
    event.respondWith(handlePageRequest(request));
    return;
  }
  
  // 其他請求使用網路優先策略
  event.respondWith(handleOtherRequests(request));
});

// 處理 API 請求 - 網路優先，失敗時使用快取
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  try {
    // 嘗試網路請求
    const networkResponse = await fetch(request);
    
    // 如果請求成功且是可快取的 API
    if (networkResponse.ok && shouldCacheApi(url.pathname)) {
      const cache = await caches.open(API_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Network failed for API, trying cache:', request.url);
    
    // 網路失敗，嘗試快取
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // 如果是 GET 請求且沒有快取，返回離線響應
    if (request.method === 'GET') {
      return new Response(JSON.stringify({
        error: 'offline',
        message: '目前處於離線狀態，請稍後再試'
      }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      });
    }
    
    throw error;
  }
}

// 處理靜態資源 - 快取優先
async function handleStaticAsset(request) {
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Failed to fetch static asset:', request.url);
    
    // 返回備用圖片或樣式
    if (request.destination === 'image') {
      return new Response(
        '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200" viewBox="0 0 200 200"><rect width="200" height="200" fill="#f3f4f6"/><text x="100" y="100" text-anchor="middle" dy=".3em" fill="#6b7280">圖片載入失敗</text></svg>',
        { headers: { 'Content-Type': 'image/svg+xml' } }
      );
    }
    
    throw error;
  }
}

// 處理頁面請求 - 網路優先，失敗時返回離線頁面
async function handlePageRequest(request) {
  try {
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Network failed for page, trying cache:', request.url);
    
    // 嘗試快取
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // 返回離線頁面
    const offlineResponse = await caches.match('/offline.html');
    if (offlineResponse) {
      return offlineResponse;
    }
    
    // 最後的備用方案
    return new Response(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>離線狀態</title>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            body { 
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
              text-align: center; 
              padding: 50px; 
              background: #f8fafc;
            }
            .container {
              max-width: 400px;
              margin: 0 auto;
              padding: 30px;
              background: white;
              border-radius: 10px;
              box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            h1 { color: #1f2937; margin-bottom: 20px; }
            p { color: #6b7280; line-height: 1.6; }
            button {
              background: #3b82f6;
              color: white;
              border: none;
              padding: 10px 20px;
              border-radius: 5px;
              cursor: pointer;
              margin-top: 20px;
            }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>🔌 離線狀態</h1>
            <p>目前無法連接到網路。請檢查您的網路連接後重試。</p>
            <button onclick="window.location.reload()">重新載入</button>
          </div>
        </body>
      </html>
    `, {
      status: 503,
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

// 處理其他請求
async function handleOtherRequests(request) {
  try {
    return await fetch(request);
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    throw error;
  }
}

// 判斷是否應該快取 API 請求
function shouldCacheApi(pathname) {
  return API_CACHE_PATTERNS.some(pattern => pattern.test(pathname));
}

// 背景同步事件
self.addEventListener('sync', (event) => {
  console.log('Service Worker: Background sync event:', event.tag);
  
  if (event.tag === 'background-upload') {
    event.waitUntil(handleBackgroundUpload());
  } else if (event.tag === 'background-analytics') {
    event.waitUntil(handleBackgroundAnalytics());
  }
});

// 處理背景上傳
async function handleBackgroundUpload() {
  try {
    const pendingUploads = await getFromIndexedDB('pending-uploads');
    
    for (const upload of pendingUploads) {
      try {
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: upload.formData,
          headers: upload.headers
        });
        
        if (response.ok) {
          await removeFromIndexedDB('pending-uploads', upload.id);
          
          // 通知客戶端上傳成功
          const clients = await self.clients.matchAll();
          clients.forEach(client => {
            client.postMessage({
              type: 'upload-success',
              id: upload.id,
              response: response.json()
            });
          });
        }
      } catch (error) {
        console.error('Background upload failed:', error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// 處理背景分析數據上傳
async function handleBackgroundAnalytics() {
  try {
    const pendingAnalytics = await getFromIndexedDB('pending-analytics');
    
    if (pendingAnalytics.length > 0) {
      const response = await fetch('/api/analytics/batch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(pendingAnalytics)
      });
      
      if (response.ok) {
        await clearIndexedDB('pending-analytics');
      }
    }
  } catch (error) {
    console.error('Background analytics sync failed:', error);
  }
}

// 推送通知事件
self.addEventListener('push', (event) => {
  console.log('Service Worker: Push event received');
  
  let notificationData = {};
  
  if (event.data) {
    try {
      notificationData = event.data.json();
    } catch (error) {
      notificationData = {
        title: 'Auto Video',
        body: event.data.text() || '您有新的通知'
      };
    }
  }
  
  const options = {
    body: notificationData.body || '您有新的通知',
    icon: '/icons/icon-192.png',
    badge: '/icons/badge-72.png',
    image: notificationData.image,
    data: notificationData.data,
    actions: notificationData.actions || [
      {
        action: 'view',
        title: '查看',
        icon: '/icons/action-view.png'
      },
      {
        action: 'dismiss',
        title: '忽略',
        icon: '/icons/action-dismiss.png'
      }
    ],
    requireInteraction: notificationData.requireInteraction || false,
    silent: notificationData.silent || false
  };
  
  event.waitUntil(
    self.registration.showNotification(
      notificationData.title || 'Auto Video',
      options
    )
  );
});

// 通知點擊事件
self.addEventListener('notificationclick', (event) => {
  console.log('Service Worker: Notification clicked');
  
  event.notification.close();
  
  const action = event.action;
  const data = event.notification.data;
  
  if (action === 'dismiss') {
    return;
  }
  
  let url = '/';
  if (data && data.url) {
    url = data.url;
  } else if (action === 'view' && data && data.projectId) {
    url = `/projects/${data.projectId}`;
  }
  
  event.waitUntil(
    clients.matchAll({ type: 'window' }).then((clientList) => {
      // 嘗試找到已打開的窗口
      for (const client of clientList) {
        if (client.url === url && 'focus' in client) {
          return client.focus();
        }
      }
      
      // 沒有找到，打開新窗口
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});

// 消息事件處理
self.addEventListener('message', (event) => {
  console.log('Service Worker: Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_NAME });
  }
});

// IndexedDB 輔助函數
async function getFromIndexedDB(storeName) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('AutoVideoSW', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction([storeName], 'readonly');
      const store = transaction.objectStore(storeName);
      const getRequest = store.getAll();
      
      getRequest.onsuccess = () => resolve(getRequest.result || []);
      getRequest.onerror = () => reject(getRequest.error);
    };
    
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(storeName)) {
        db.createObjectStore(storeName, { keyPath: 'id', autoIncrement: true });
      }
    };
  });
}

async function removeFromIndexedDB(storeName, id) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('AutoVideoSW', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const deleteRequest = store.delete(id);
      
      deleteRequest.onsuccess = () => resolve();
      deleteRequest.onerror = () => reject(deleteRequest.error);
    };
  });
}

async function clearIndexedDB(storeName) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('AutoVideoSW', 1);
    
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      const transaction = db.transaction([storeName], 'readwrite');
      const store = transaction.objectStore(storeName);
      const clearRequest = store.clear();
      
      clearRequest.onsuccess = () => resolve();
      clearRequest.onerror = () => reject(clearRequest.error);
    };
  });
}