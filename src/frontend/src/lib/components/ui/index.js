// 標準化 UI 組件庫索引
// 基於設計 tokens 的統一組件系統

// 基礎組件
export { default as Button } from './Button.svelte';
export { default as Input } from './Input.svelte';
export { default as Card } from './Card.svelte';
export { default as LazyImage } from './LazyImage.svelte';
export { default as VirtualGrid } from './VirtualGrid.svelte';
export { default as GlobalLoading } from './GlobalLoading.svelte';
export { default as GlobalError } from './GlobalError.svelte';

// Import components for default export
import ButtonComponent from './Button.svelte';
import InputComponent from './Input.svelte';
import CardComponent from './Card.svelte';

// 設計 tokens 和工具函數
export { tokens, getColor, getSpacing, getBreakpoint } from '../../design/tokens.js';

// 組件變體配置
export const componentVariants = {
  button: {
    variants: ['primary', 'secondary', 'outline', 'ghost', 'destructive'],
    sizes: ['xs', 'sm', 'md', 'lg', 'xl']
  },
  input: {
    variants: ['default', 'filled', 'borderless'],
    sizes: ['sm', 'md', 'lg'],
    types: ['text', 'email', 'password', 'number', 'search', 'tel', 'url', 'textarea']
  },
  card: {
    variants: ['default', 'elevated', 'outlined', 'filled'],
    sizes: ['sm', 'md', 'lg', 'xl', 'full'],
    paddings: ['none', 'sm', 'default', 'lg', 'xl']
  }
};

// 主題相關的工具函數
export const themeUtils = {
  /**
   * 獲取響應式類名
   * @param {Object} breakpoints - 斷點配置 { sm: 'class1', md: 'class2', lg: 'class3' }
   * @returns {string} 響應式類名
   */
  responsive(breakpoints) {
    return Object.entries(breakpoints)
      .map(([bp, className]) => bp === 'base' ? className : `${bp}:${className}`)
      .join(' ');
  },
  
  /**
   * 獲取深色模式類名
   * @param {string} lightClass - 淺色模式類名
   * @param {string} darkClass - 深色模式類名
   * @returns {string} 包含深色模式的類名
   */
  darkMode(lightClass, darkClass) {
    return `${lightClass} dark:${darkClass}`;
  },
  
  /**
   * 組合多個條件類名
   * @param {Object} conditions - 條件配置
   * @returns {string} 組合後的類名
   */
  conditional(conditions) {
    return Object.entries(conditions)
      .filter(([condition, _]) => condition)
      .map(([_, className]) => className)
      .join(' ');
  }
};

// CSS 變量生成工具
export const cssVariables = {
  /**
   * 生成 CSS 自定義屬性
   * @param {Object} vars - 變量配置
   * @param {string} prefix - 前綴
   * @returns {string} CSS 變量字符串
   */
  generate(vars, prefix = '') {
    return Object.entries(vars)
      .map(([key, value]) => `--${prefix}${key}: ${value};`)
      .join('\n');
  },
  
  /**
   * 使用 CSS 變量
   * @param {string} varName - 變量名
   * @param {string} fallback - 回退值
   * @returns {string} CSS var() 函數
   */
  use(varName, fallback = '') {
    return `var(--${varName}${fallback ? `, ${fallback}` : ''})`;
  }
};

// 組件組合模式
export const patterns = {
  /**
   * 表單組合
   * 包含 Input + Button 的常見表單模式
   */
  form: {
    newsletter: {
      input: { variant: 'filled', placeholder: '輸入您的電子郵件' },
      button: { variant: 'primary', size: 'md' }
    },
    search: {
      input: { variant: 'borderless', leftIcon: 'search' },
      button: { variant: 'ghost', size: 'md' }
    }
  },
  
  /**
   * 卡片組合
   * 常見的卡片佈局模式
   */
  cards: {
    feature: {
      variant: 'default',
      padding: 'lg',
      interactive: true
    },
    product: {
      variant: 'elevated',
      padding: 'default',
      interactive: true,
      clickable: true
    }
  }
};

// 輔助函數
export const helpers = {
  /**
   * 生成隨機 ID
   * @param {string} prefix - ID 前綴
   * @returns {string} 唯一 ID
   */
  generateId(prefix = 'component') {
    return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
  },
  
  /**
   * 合併類名
   * @param {...string} classNames - 類名列表
   * @returns {string} 合併後的類名
   */
  classNames(...classNames) {
    return classNames.filter(Boolean).join(' ');
  },
  
  /**
   * 格式化文件大小
   * @param {number} bytes - 位元組數
   * @returns {string} 格式化後的大小
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
  },
  
  /**
   * 截斷文本
   * @param {string} text - 原始文本
   * @param {number} maxLength - 最大長度
   * @returns {string} 截斷後的文本
   */
  truncate(text, maxLength = 100) {
    if (text.length <= maxLength) return text;
    return `${text.substring(0, maxLength)}...`;
  }
};

export default {
  Button: ButtonComponent,
  Input: InputComponent,
  Card: CardComponent,
  LazyImage,
  VirtualGrid,
  GlobalLoading,
  GlobalError,
  tokens,
  componentVariants,
  themeUtils,
  cssVariables,
  patterns,
  helpers
};