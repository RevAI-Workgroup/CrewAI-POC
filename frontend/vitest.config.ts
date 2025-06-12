/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: [
      'node_modules',
      'dist',
      'build',
      '.next',
      '.nuxt',
      '.output',
      '.vitepress/cache',
      '.vitepress/dist',
    ],
    // Performance optimizations
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: false,
        useAtomics: true,
        maxThreads: 4,
        minThreads: 1,
      },
    },
    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      reportsDirectory: './coverage',
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/dist/**',
        '**/build/**',
        '**/.vitepress/**',
      ],
      thresholds: {
        global: {
          branches: 80,
          functions: 80,
          lines: 80,
          statements: 80,
        },
      },
    },
    // Test categorization
    testTimeout: 10000,
    hookTimeout: 10000,
    // Reporter configuration
    reporter: ['verbose', 'json'],
    outputFile: {
      json: './test-results/results.json',
    },
    // Watch options for development
    watch: false,
    // Cache configuration for faster subsequent runs
    cache: {
      dir: 'node_modules/.vitest',
    },
    // Mocks configuration
    deps: {
      inline: ['@testing-library/user-event'],
    },
  },
}) 