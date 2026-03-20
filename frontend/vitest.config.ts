import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    include: ['**/*.test.tsx', '**/*.test.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'tests/'],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
      '@/shared': path.resolve(__dirname, './shared'),
      '@/app': path.resolve(__dirname, './app'),
      '@/features': path.resolve(__dirname, './features'),
      '@/components': path.resolve(__dirname, './components'),
    },
  },
});
