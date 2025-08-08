import { tokens } from './src/lib/design/tokens.js';

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{html,js,svelte,ts}"],
  darkMode: "class",
  theme: {
    // 使用設計 tokens 來定義基礎主題
    extend: {
      // 顏色系統 - 從設計 tokens 引入
      colors: {
        ...tokens.colors,
        // 保持向後兼容的語義化命名
        success: tokens.colors.semantic.success,
        warning: tokens.colors.semantic.warning,
        error: tokens.colors.semantic.error,
        info: tokens.colors.semantic.info,
      },
      
      // 字體系統
      fontFamily: tokens.typography.fontFamily,
      fontSize: tokens.typography.fontSize,
      fontWeight: tokens.typography.fontWeight,
      
      // 間距系統
      spacing: {
        ...tokens.spacing,
        // 保持現有的自定義間距
        18: "4.5rem",
        88: "22rem",
      },
      
      // 邊框半徑
      borderRadius: tokens.borderRadius,
      
      // 陰影系統 - 結合 tokens 和現有配置
      boxShadow: {
        ...tokens.shadow,
        // 保持現有的自定義陰影
        soft: "0 2px 15px 0 rgba(0, 0, 0, 0.05)",
        medium: "0 4px 25px 0 rgba(0, 0, 0, 0.1)",
        hard: "0 10px 40px 0 rgba(0, 0, 0, 0.15)",
      },
      
      // Z-index 層級
      zIndex: tokens.zIndex,
      
      // 斷點系統
      screens: tokens.breakpoints,
      
      // 動畫系統 - 結合 tokens 和現有配置
      transitionDuration: tokens.animation.duration,
      transitionTimingFunction: tokens.animation.timingFunction,
      animation: {
        // 從 tokens 繼承基礎動畫時間
        "fade-in": `fadeIn ${tokens.animation.duration[500]} ${tokens.animation.timingFunction.out}`,
        "slide-up": `slideUp ${tokens.animation.duration[300]} ${tokens.animation.timingFunction.out}`,
        "slide-in": `slideIn ${tokens.animation.duration[300]} ${tokens.animation.timingFunction.out}`,
        "scale-in": `scaleIn ${tokens.animation.duration[200]} ${tokens.animation.timingFunction.out}`,
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "bounce-subtle": "bounceSubtle 2s infinite",
        
        // 新增基於 tokens 的動畫
        "fade-in-fast": `fadeIn ${tokens.animation.duration[200]} ${tokens.animation.timingFunction.out}`,
        "slide-up-fast": `slideUp ${tokens.animation.duration[150]} ${tokens.animation.timingFunction.out}`,
        "scale-in-fast": `scaleIn ${tokens.animation.duration[100]} ${tokens.animation.timingFunction.out}`,
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        slideIn: {
          "0%": { transform: "translateX(-100%)" },
          "100%": { transform: "translateX(0)" },
        },
        scaleIn: {
          "0%": { transform: "scale(0.9)", opacity: "0" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
        bounceSubtle: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-5px)" },
        },
        // 新增旋轉動畫
        spin: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
        // 新增彈性動畫
        bounce: {
          "0%, 100%": { 
            transform: "translateY(-25%)",
            animationTimingFunction: "cubic-bezier(0.8, 0, 1, 1)"
          },
          "50%": {
            transform: "translateY(0)",
            animationTimingFunction: "cubic-bezier(0, 0, 0.2, 1)"
          }
        }
      },
      
      // 最大寬度
      maxWidth: {
        "8xl": "88rem",
        "9xl": "96rem",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms"),
    require("@tailwindcss/typography"),
    
    // 自定義插件：生成 CSS 變量
    function({ addBase }) {
      const cssVariables = {};
      
      // 生成顏色 CSS 變量
      const addColorVariables = (colors, prefix = '') => {
        Object.entries(colors).forEach(([key, value]) => {
          if (typeof value === 'object' && value !== null) {
            addColorVariables(value, `${prefix}${key}-`);
          } else {
            cssVariables[`--color-${prefix}${key}`] = value;
          }
        });
      };
      
      addColorVariables(tokens.colors);
      
      // 生成其他設計變量
      Object.entries(tokens.spacing).forEach(([key, value]) => {
        cssVariables[`--spacing-${key}`] = value;
      });
      
      addBase({
        ':root': cssVariables
      });
    }
  ],
};
