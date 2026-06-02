import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-vue':    ['vue', 'vue-router', 'pinia'],
          'vendor-charts': ['apexcharts', 'vue3-apexcharts'],
          'vendor-http':   ['axios'],
          'vendor-utils':  ['date-fns'],
        },
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8888',
        changeOrigin: true,
      },
      '/ws': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8888',
        changeOrigin: true,
        ws: true,
      },
    },
  },
})
