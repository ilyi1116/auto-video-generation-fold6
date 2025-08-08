/**
 * Web Vitals 性能監控系統
 * 基於 Google Web Vitals 標準實現的性能監控
 */

import { onCLS, onFCP, onLCP, onTTFB, onINP } from 'web-vitals';

class VitalsMonitor {
  constructor(options = {}) {
    this.options = {
      // 是否啟用性能監控
      enabled: true,
      // 是否啟用調試模式
      debug: false,
      // 採樣率 (0-1)
      samplingRate: 1.0,
      // API 端點
      endpoint: '/api/analytics/vitals',
      // 批量發送大小
      batchSize: 10,
      // 發送間隔 (毫秒)
      flushInterval: 30000,
      // 自定義標籤
      customTags: {},
      ...options
    };
    
    this.metrics = [];
    this.sessionId = this.generateSessionId();
    this.pageLoadTime = Date.now();
    
    if (this.options.enabled) {
      this.init();
    }
  }
  
  init() {
    // 監聽 Web Vitals 指標
    this.setupVitalsListeners();
    
    // 設置定時批量發送
    this.setupBatchSending();
    
    // 監聽頁面可見性變化
    this.setupVisibilityListener();
    
    // 監聽頁面卸載
    this.setupUnloadListener();
    
    if (this.options.debug) {
      console.log('🔍 Web Vitals 監控已啟動', {
        sessionId: this.sessionId,
        options: this.options
      });
    }
  }
  
  setupVitalsListeners() {
    // Largest Contentful Paint (LCP) - 最大內容繪製
    onLCP((metric) => {
      this.recordMetric('LCP', metric);
    });
    
    // Interaction to Next Paint (INP) - 互動到下次繪製 (替代 FID)
    onINP((metric) => {
      this.recordMetric('INP', metric);
    });
    
    // Cumulative Layout Shift (CLS) - 累積佈局位移
    onCLS((metric) => {
      this.recordMetric('CLS', metric);
    });
    
    // First Contentful Paint (FCP) - 首次內容繪製
    onFCP((metric) => {
      this.recordMetric('FCP', metric);
    });
    
    // Time to First Byte (TTFB) - 首位元組時間
    onTTFB((metric) => {
      this.recordMetric('TTFB', metric);
    });
    
    // Interaction to Next Paint (INP) - 交互到下次繪製
    onINP((metric) => {
      this.recordMetric('INP', metric);
    });
  }
  
  recordMetric(name, metric) {
    // 檢查採樣率
    if (Math.random() > this.options.samplingRate) {
      return;
    }
    
    const enhancedMetric = {
      name,
      value: metric.value,
      rating: metric.rating, // good | needs-improvement | poor
      delta: metric.delta,
      id: metric.id,
      
      // 會話信息
      sessionId: this.sessionId,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      
      // 頁面信息
      referrer: document.referrer,
      pageLoadTime: this.pageLoadTime,
      
      // 設備信息
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      },
      screen: {
        width: window.screen.width,
        height: window.screen.height
      },
      devicePixelRatio: window.devicePixelRatio,
      
      // 連接信息 (如果可用)
      connection: this.getConnectionInfo(),
      
      // 自定義標籤
      ...this.options.customTags
    };
    
    this.metrics.push(enhancedMetric);
    
    if (this.options.debug) {
      console.log(`📊 Web Vitals - ${name}:`, enhancedMetric);
    }
    
    // 如果達到批量大小，立即發送
    if (this.metrics.length >= this.options.batchSize) {
      this.flush();
    }
    
    // 觸發自定義事件
    this.dispatchVitalEvent(name, enhancedMetric);
  }
  
  getConnectionInfo() {
    if ('connection' in navigator) {
      const conn = navigator.connection;
      return {
        effectiveType: conn.effectiveType,
        downlink: conn.downlink,
        rtt: conn.rtt,
        saveData: conn.saveData
      };
    }
    return null;
  }
  
  dispatchVitalEvent(name, metric) {
    const event = new CustomEvent('webvital', {
      detail: { name, metric }
    });
    window.dispatchEvent(event);
  }
  
  setupBatchSending() {
    this.flushTimer = setInterval(() => {
      if (this.metrics.length > 0) {
        this.flush();
      }
    }, this.options.flushInterval);
  }
  
  setupVisibilityListener() {
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') {
        this.flush();
      }
    });
  }
  
  setupUnloadListener() {
    window.addEventListener('beforeunload', () => {
      this.flush(true);
    });
  }
  
  async flush(isUnloading = false) {
    if (this.metrics.length === 0) return;
    
    const payload = {
      metrics: [...this.metrics],
      meta: {
        sessionId: this.sessionId,
        timestamp: Date.now(),
        userAgent: navigator.userAgent,
        url: window.location.href
      }
    };
    
    this.metrics = []; // 清空本地緩存
    
    try {
      if (isUnloading && 'sendBeacon' in navigator) {
        // 使用 sendBeacon 確保數據在頁面卸載時發送
        navigator.sendBeacon(
          this.options.endpoint,
          JSON.stringify(payload)
        );
      } else {
        await fetch(this.options.endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload)
        });
      }
      
      if (this.options.debug) {
        console.log('📤 Web Vitals 數據已發送:', payload);
      }
    } catch (error) {
      if (this.options.debug) {
        console.error('❌ Web Vitals 發送失敗:', error);
      }
      
      // 發送失敗時重新加入隊列
      this.metrics.unshift(...payload.metrics);
    }
  }
  
  // 手動記錄自定義性能指標
  recordCustomMetric(name, value, tags = {}) {
    const metric = {
      name: `custom_${name}`,
      value,
      rating: 'custom',
      timestamp: Date.now(),
      sessionId: this.sessionId,
      url: window.location.href,
      ...tags
    };
    
    this.metrics.push(metric);
    
    if (this.options.debug) {
      console.log(`📊 自定義指標 - ${name}:`, metric);
    }
  }
  
  // 記錄用戶互動事件
  recordInteraction(action, target, duration = null) {
    this.recordCustomMetric('user_interaction', duration || 1, {
      action,
      target: target?.tagName || 'unknown',
      targetId: target?.id || '',
      targetClass: target?.className || ''
    });
  }
  
  // 記錄頁面導航
  recordNavigation(from, to, duration) {
    this.recordCustomMetric('navigation', duration, {
      from: from || document.referrer,
      to: to || window.location.href
    });
  }
  
  // 記錄資源加載時間
  recordResourceTiming() {
    if ('performance' in window && 'getEntriesByType' in performance) {
      const resources = performance.getEntriesByType('resource');
      
      resources.forEach(resource => {
        if (resource.duration > 0) {
          this.recordCustomMetric('resource_timing', resource.duration, {
            name: resource.name,
            type: resource.initiatorType,
            size: resource.transferSize || 0
          });
        }
      });
    }
  }
  
  generateSessionId() {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  // 獲取當前性能摘要
  getPerformanceSummary() {
    const summary = {
      sessionId: this.sessionId,
      metricsCount: this.metrics.length,
      timestamp: Date.now(),
      vitals: {}
    };
    
    // 統計各類指標
    this.metrics.forEach(metric => {
      if (!summary.vitals[metric.name]) {
        summary.vitals[metric.name] = {
          count: 0,
          latest: null,
          average: 0,
          ratings: { good: 0, 'needs-improvement': 0, poor: 0 }
        };
      }
      
      const vital = summary.vitals[metric.name];
      vital.count++;
      vital.latest = metric;
      
      if (metric.rating && vital.ratings[metric.rating] !== undefined) {
        vital.ratings[metric.rating]++;
      }
    });
    
    return summary;
  }
  
  // 停止監控
  destroy() {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }
    
    // 發送剩餘數據
    this.flush();
    
    if (this.options.debug) {
      console.log('🛑 Web Vitals 監控已停止');
    }
  }
}

// 全域實例
let globalMonitor = null;

// 初始化函數
export function initVitalsMonitor(options = {}) {
  if (typeof window === 'undefined') {
    return null; // SSR 環境下不執行
  }
  
  if (globalMonitor) {
    globalMonitor.destroy();
  }
  
  globalMonitor = new VitalsMonitor(options);
  return globalMonitor;
}

// 獲取全域監控實例
export function getVitalsMonitor() {
  return globalMonitor;
}

// 便捷函數
export const vitals = {
  // 記錄自定義指標
  record: (name, value, tags) => {
    globalMonitor?.recordCustomMetric(name, value, tags);
  },
  
  // 記錄用戶互動
  interaction: (action, target, duration) => {
    globalMonitor?.recordInteraction(action, target, duration);
  },
  
  // 記錄導航
  navigation: (from, to, duration) => {
    globalMonitor?.recordNavigation(from, to, duration);
  },
  
  // 獲取性能摘要
  summary: () => {
    return globalMonitor?.getPerformanceSummary();
  },
  
  // 手動刷新數據
  flush: () => {
    globalMonitor?.flush();
  }
};

export default VitalsMonitor;