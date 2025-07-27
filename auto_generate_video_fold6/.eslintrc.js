module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
    'plugin:svelte/recommended',
    'prettier'
  ],
  plugins: ['@typescript-eslint'],
  ignorePatterns: [
    '*.cjs',
    'node_modules/',
    'dist/',
    'build/',
    '.svelte-kit/',
    'coverage/',
    'test-results/',
    'docker/',
    'k8s/',
    'scripts/'
  ],
  overrides: [
    {
      files: ['*.svelte'],
      parser: 'svelte-eslint-parser',
      parserOptions: {
        parser: '@typescript-eslint/parser'
      }
    },
    {
      files: ['*.js'],
      rules: {
        '@typescript-eslint/no-var-requires': 'off'
      }
    },
    {
      files: ['*.test.{js,ts}', '*.spec.{js,ts}'],
      rules: {
        '@typescript-eslint/no-explicit-any': 'off',
        '@typescript-eslint/no-unused-vars': 'off'
      }
    }
  ],
  parserOptions: {
    sourceType: 'module',
    ecmaVersion: 2020,
    extraFileExtensions: ['.svelte']
  },
  env: {
    browser: true,
    es2017: true,
    node: true,
    jest: true
  },
  rules: {
    // TypeScript 規則
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/prefer-const': 'error',
    '@typescript-eslint/no-var-requires': 'error',
    
    // 一般規則
    'no-console': 'warn',
    'no-debugger': 'error',
    'no-unused-vars': 'off', // 由 TypeScript 規則處理
    'prefer-const': 'error',
    'no-var': 'error',
    'object-shorthand': 'error',
    'prefer-arrow-callback': 'error',
    
    // Svelte 規則
    'svelte/no-at-html-tags': 'error',
    'svelte/no-unused-svelte-ignore': 'error',
    'svelte/no-at-debug-tags': 'warn',
    'svelte/valid-compile': 'error',
    
    // 程式碼風格
    'eqeqeq': 'error',
    'curly': 'error',
    'brace-style': ['error', '1tbs'],
    'comma-dangle': ['error', 'es5'],
    'quotes': ['error', 'single', { avoidEscape: true }],
    'semi': ['error', 'always'],
    
    // 最佳實踐
    'no-eval': 'error',
    'no-implied-eval': 'error',
    'no-new-func': 'error',
    'no-script-url': 'error',
    'no-alert': 'warn',
    'no-lone-blocks': 'error',
    'no-multi-spaces': 'error',
    'no-new': 'error',
    'no-new-wrappers': 'error',
    'no-octal-escape': 'error',
    'no-self-compare': 'error',
    'no-sequences': 'error',
    'no-throw-literal': 'error',
    'no-unused-expressions': 'error',
    'no-useless-call': 'error',
    'no-useless-concat': 'error',
    'no-void': 'error',
    'no-with': 'error',
    'wrap-iife': 'error',
    'yoda': 'error'
  },
  settings: {
    'svelte/typescript': () => require('typescript')
  }
};