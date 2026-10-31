import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // 指向你的 FastAPI 后端
        changeOrigin: true,
      },
      // 👇 新增下面这段关于 WebSocket 的代理
      '/ws': {
        target: 'ws://127.0.0.1:8000',
        ws: true,
      }
    }
  },
})