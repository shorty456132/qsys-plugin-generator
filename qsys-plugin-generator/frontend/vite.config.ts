import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/generate': 'http://localhost:5000',
      '/reply': 'http://localhost:5000',
      '/download': 'http://localhost:5000',
      '/complete': 'http://localhost:5000',
      '/delete-conversation': 'http://localhost:5000',
    }
  },
  build: {
    outDir: '../static/dist',
    emptyOutDir: true
  }
})
