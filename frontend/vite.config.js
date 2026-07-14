import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api/notifications': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        ws: false,
        headers: { 'Connection': 'keep-alive' },
      },
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
