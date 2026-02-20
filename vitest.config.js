import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'happy-dom',
    globals: true,
    include: [
      'src/**/*.test.{js,ts}',
      'src/**/*.spec.{js,ts}'
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.js', 'src/**/*.vue'],
      exclude: ['src/**/*.test.{js,ts}', 'src/**/*.spec.{js,ts}']
    },
    setupFiles: ['./vitest.setup.js'],
    deps: {
      optimizer: {
        web: {
          include: ['quasar']
        }
      }
    }
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      'stores': fileURLToPath(new URL('./src/stores', import.meta.url)),
      'boot': fileURLToPath(new URL('./src/boot', import.meta.url)),
      'components': fileURLToPath(new URL('./src/components', import.meta.url))
    }
  }
})
