/**
 * 開發者調試工具
 * 提供開發環境下的各種調試和開發工具
 */

import { dev } from '$app/environment';

class DebugTools {
  constructor() {
    this.enabled = dev;
    this.logs = [];
    this.maxLogs = 1000;
    
    if (this.enabled) {
      this.init();
    }
  }
  
  init() {
    // 只在瀏覽器環境中初始化
    if (typeof window === 'undefined') {
      return;
    }
    
    // 將調試工具添加到全域 window 對象
    window.debugTools = this;
    
    // 監聽錯誤
    this.setupErrorHandling();
    
    // 監聽性能事件
    this.setupPerformanceMonitoring();
    
    // 設置鍵盤快捷鍵
    this.setupKeyboardShortcuts();
    
    // 添加 CSS 調試樣式
    this.addDebugStyles();
    
    console.log('🔧 Debug Tools 已啟用');
    console.log('🚀 可用指令:', {
      'debugTools.showInfo()': '顯示系統信息',
      'debugTools.showLogs()': '顯示日誌',
      'debugTools.clearLogs()': '清除日誌',
      'debugTools.exportLogs()': '導出日誌',
      'debugTools.toggleGrid()': '切換網格線',
      'debugTools.highlightComponents()': '高亮組件邊界',
      'debugTools.showBreakpoints()': '顯示斷點信息'
    });
  }
  
  setupErrorHandling() {
    if (typeof window === 'undefined') {
      return;
    }
    
    const originalError = console.error;
    const originalWarn = console.warn;
    
    console.error = (...args) => {
      this.log('error', args);
      originalError.apply(console, args);
    };
    
    console.warn = (...args) => {
      this.log('warn', args);
      originalWarn.apply(console, args);
    };
    
    window.addEventListener('error', (event) => {
      this.log('error', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error
      });
    });
    
    window.addEventListener('unhandledrejection', (event) => {
      this.log('error', {
        type: 'unhandledrejection',
        reason: event.reason
      });
    });
  }
  
  setupPerformanceMonitoring() {
    if (typeof window === 'undefined') {
      return;
    }
    
    // 監聽 Web Vitals 事件
    window.addEventListener('webvital', (event) => {
      this.log('performance', {
        name: event.detail.name,
        value: event.detail.metric.value,
        rating: event.detail.metric.rating
      });
    });
    
    // 監聽導航事件
    if ('performance' in window && 'getEntriesByType' in performance) {
      const observer = new PerformanceObserver((entries) => {
        entries.getEntries().forEach(entry => {
          if (entry.entryType === 'navigation') {
            this.log('navigation', {
              type: entry.type,
              duration: entry.duration,
              domContentLoaded: entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart,
              loadComplete: entry.loadEventEnd - entry.loadEventStart
            });
          }
        });
      });
      observer.observe({ entryTypes: ['navigation'] });
    }
  }
  
  setupKeyboardShortcuts() {
    if (typeof document === 'undefined') return;
    
    document.addEventListener('keydown', (event) => {
      // Ctrl/Cmd + Shift + D: 顯示調試信息
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'D') {
        event.preventDefault();
        this.showDebugPanel();
      }
      
      // Ctrl/Cmd + Shift + G: 切換網格線
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'G') {
        event.preventDefault();
        this.toggleGrid();
      }
      
      // Ctrl/Cmd + Shift + C: 高亮組件
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'C') {
        event.preventDefault();
        this.highlightComponents();
      }
    });
  }
  
  addDebugStyles() {
    if (typeof document === 'undefined') return;
    
    const style = document.createElement('style');
    style.id = 'debug-tools-styles';
    style.textContent = `
      /* 網格線樣式 */
      .debug-grid {
        background-image: 
          linear-gradient(rgba(255, 0, 0, 0.1) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255, 0, 0, 0.1) 1px, transparent 1px);
        background-size: 20px 20px;
      }
      
      /* 組件邊界高亮 */
      .debug-highlight * {
        outline: 1px solid rgba(255, 0, 0, 0.5) !important;
        background: rgba(255, 0, 0, 0.05) !important;
      }
      
      /* 斷點指示器 */
      .debug-breakpoint-indicator {
        position: fixed;
        top: 10px;
        left: 10px;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-family: monospace;
        font-size: 12px;
        z-index: 9999;
        pointer-events: none;
      }
      
      /* 調試面板 */
      .debug-panel {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        border: 1px solid #ccc;
        border-radius: 8px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        max-width: 80vw;
        max-height: 80vh;
        overflow: auto;
        z-index: 10000;
        font-family: monospace;
        font-size: 12px;
      }
      
      .debug-panel-header {
        background: #f5f5f5;
        padding: 10px;
        border-bottom: 1px solid #ccc;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .debug-panel-content {
        padding: 10px;
      }
      
      .debug-log-entry {
        margin-bottom: 5px;
        padding: 5px;
        border-radius: 3px;
      }
      
      .debug-log-error { background: #fee; color: #c00; }
      .debug-log-warn { background: #fff3cd; color: #856404; }
      .debug-log-info { background: #d1ecf1; color: #0c5460; }
      .debug-log-performance { background: #d4edda; color: #155724; }
    `;
    
    document.head.appendChild(style);
  }
  
  log(type, data) {
    const entry = {
      timestamp: new Date(),
      type,
      data
    };
    
    this.logs.push(entry);
    
    // 限制日誌數量
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(-this.maxLogs);
    }
  }
  
  showInfo() {
    if (typeof window === 'undefined') {
      console.log('ℹ️ Debug info only available in browser');
      return { error: 'Not in browser environment' };
    }
    
    const info = {
      userAgent: navigator.userAgent,
      viewport: `${window.innerWidth}x${window.innerHeight}`,
      screen: `${window.screen.width}x${window.screen.height}`,
      pixelRatio: window.devicePixelRatio,
      connection: navigator.connection ? {
        effectiveType: navigator.connection.effectiveType,
        downlink: navigator.connection.downlink,
        rtt: navigator.connection.rtt
      } : 'unknown',
      memory: navigator.deviceMemory || 'unknown',
      cores: navigator.hardwareConcurrency || 'unknown',
      online: navigator.onLine,
      cookieEnabled: navigator.cookieEnabled,
      language: navigator.language,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      colorScheme: window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light',
      reduceMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches
    };
    
    console.table(info);
    return info;
  }
  
  showLogs(type = null) {
    const filteredLogs = type ? 
      this.logs.filter(log => log.type === type) : 
      this.logs;
      
    console.group('🗂️ Debug Logs');
    filteredLogs.forEach(log => {
      const time = log.timestamp.toLocaleTimeString();
      console.log(`[${time}] ${log.type}:`, log.data);
    });
    console.groupEnd();
    
    return filteredLogs;
  }
  
  clearLogs() {
    this.logs = [];
    console.log('🗑️ 日誌已清除');
  }
  
  exportLogs() {
    if (typeof window === 'undefined' || typeof document === 'undefined') {
      console.log('📤 日誌導出僅在瀏覽器中可用');
      return;
    }
    
    const data = {
      timestamp: new Date().toISOString(),
      logs: this.logs,
      systemInfo: this.showInfo()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `debug-logs-${Date.now()}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
    console.log('📤 日誌已導出');
  }
  
  toggleGrid() {
    if (typeof document === 'undefined') return;
    document.body.classList.toggle('debug-grid');
    console.log('📐 網格線已切換');
  }
  
  highlightComponents() {
    if (typeof document === 'undefined') return;
    document.body.classList.toggle('debug-highlight');
    console.log('🎯 組件高亮已切換');
  }
  
  showBreakpoints() {
    if (typeof window === 'undefined') {
      console.log('📱 斷點信息僅在瀏覽器中可用');
      return { error: 'Not in browser environment' };
    }
    
    const breakpoints = {
      xs: window.matchMedia('(min-width: 475px)').matches,
      sm: window.matchMedia('(min-width: 640px)').matches,
      md: window.matchMedia('(min-width: 768px)').matches,
      lg: window.matchMedia('(min-width: 1024px)').matches,
      xl: window.matchMedia('(min-width: 1280px)').matches,
      '2xl': window.matchMedia('(min-width: 1536px)').matches
    };
    
    const current = Object.entries(breakpoints)
      .filter(([_, matches]) => matches)
      .map(([bp, _]) => bp)
      .slice(-1)[0] || 'xs';
    
    // 顯示當前斷點
    this.showBreakpointIndicator(current);
    
    console.log('📱 斷點信息:', { current, all: breakpoints });
    return { current, all: breakpoints };
  }
  
  showBreakpointIndicator(current) {
    if (typeof window === 'undefined' || typeof document === 'undefined') return;
    
    let indicator = document.querySelector('.debug-breakpoint-indicator');
    
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.className = 'debug-breakpoint-indicator';
      document.body.appendChild(indicator);
    }
    
    indicator.textContent = `Breakpoint: ${current} (${window.innerWidth}px)`;
    
    // 自動隱藏
    setTimeout(() => {
      if (indicator) {
        indicator.remove();
      }
    }, 3000);
  }
  
  showDebugPanel() {
    if (typeof document === 'undefined') {
      console.log('🔧 Debug Panel 僅在瀏覽器中可用');
      return;
    }
    
    // 移除現有面板
    const existingPanel = document.querySelector('.debug-panel');
    if (existingPanel) {
      existingPanel.remove();
      return;
    }
    
    const panel = document.createElement('div');
    panel.className = 'debug-panel';
    
    const recentLogs = this.logs.slice(-20);
    const systemInfo = this.showInfo();
    
    panel.innerHTML = `
      <div class="debug-panel-header">
        <h3>🔧 Debug Panel</h3>
        <button onclick="this.parentElement.parentElement.remove()">✕</button>
      </div>
      <div class="debug-panel-content">
        <h4>系統信息</h4>
        <pre>${JSON.stringify(systemInfo, null, 2)}</pre>
        
        <h4>最近日誌 (${recentLogs.length})</h4>
        <div class="debug-logs">
          ${recentLogs.map(log => `
            <div class="debug-log-entry debug-log-${log.type}">
              <strong>[${log.timestamp.toLocaleTimeString()}] ${log.type}:</strong>
              <pre>${JSON.stringify(log.data, null, 2)}</pre>
            </div>
          `).join('')}
        </div>
        
        <div style="margin-top: 10px; text-align: center;">
          <button onclick="debugTools.exportLogs()" style="margin: 0 5px;">導出日誌</button>
          <button onclick="debugTools.clearLogs()" style="margin: 0 5px;">清除日誌</button>
          <button onclick="debugTools.toggleGrid()" style="margin: 0 5px;">切換網格</button>
          <button onclick="debugTools.highlightComponents()" style="margin: 0 5px;">高亮組件</button>
        </div>
      </div>
    `;
    
    document.body.appendChild(panel);
    
    // 點擊外部關閉
    setTimeout(() => {
      document.addEventListener('click', function closePanel(e) {
        if (!panel.contains(e.target)) {
          panel.remove();
          document.removeEventListener('click', closePanel);
        }
      });
    }, 100);
  }
  
  // 監控 Svelte 組件
  trackComponent(name, instance) {
    if (!this.enabled) return;
    
    this.log('component', {
      name,
      mounted: Date.now(),
      instance: instance ? 'with-instance' : 'no-instance'
    });
  }
  
  // 性能計時器
  startTimer(name) {
    if (!this.enabled) return;
    
    this.timers = this.timers || {};
    this.timers[name] = performance.now();
  }
  
  endTimer(name) {
    if (!this.enabled || !this.timers || !this.timers[name]) return;
    
    const duration = performance.now() - this.timers[name];
    delete this.timers[name];
    
    this.log('performance', {
      timer: name,
      duration: `${duration.toFixed(2)}ms`
    });
    
    return duration;
  }
}

// 創建全域實例 (僅在瀏覽器環境中)
let debugTools;

if (typeof window !== 'undefined') {
  debugTools = new DebugTools();
  
  // 響應式斷點監控
  if (debugTools.enabled) {
    // 監聽視窗大小變化
    let resizeTimeout;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        debugTools.showBreakpoints();
      }, 300);
    });
  }
} else {
  // 服務器端提供空對象
  debugTools = {
    enabled: false,
    showInfo: () => ({ error: 'Not in browser environment' }),
    showLogs: () => [],
    clearLogs: () => {},
    exportLogs: () => {},
    toggleGrid: () => {},
    highlightComponents: () => {},
    showBreakpoints: () => ({ error: 'Not in browser environment' }),
    log: () => {},
    startTimer: () => {},
    endTimer: () => 0
  };
}

export default debugTools;