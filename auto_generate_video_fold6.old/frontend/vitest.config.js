/**
 * Vitest 測試配置
 * 單元測試和覆蓋率報告設定
 */

import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';
import { resolve } from 'path';

export default defineConfig({
  plugins: [sveltekit()],

  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['src/tests/setup.js'],

    include: [
      'src/**/*.{test,spec}.{js,ts}',
      'src/tests/**/*.{test,spec}.{js,ts}'
    ],
    exclude: [
      'src/tests/e2e/**/*',
      'node_modules/**/*',
      'dist/**/*'
    ],

    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'json', 'lcov'],
      reportsDirectory: './coverage',

      include: [
        'src/lib/**/*.{js,ts,svelte}',
        'src/routes/**/*.{js,ts,svelte}'
      ],

      exclude: [
        '**/*.test.{js,ts}',
        '**/*.spec.{js,ts}',
        '**/tests/**',
        '**/__tests__/**'
      ],

      // TDD 標準: 90%+ 覆蓋率要求
      statements: 90,
      branches: 85,
      functions: 90,
      lines: 90,

      check: true,
      all: true
    },

    testTimeout: 10000,
    hookTimeout: 10000
  },

  resolve: {
    alias: {
      $lib: resolve('./src/lib')
    }
  }
});
