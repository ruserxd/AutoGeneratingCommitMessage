import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  base: './',
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, '../../out'), // 打包到專案的 out/
    emptyOutDir: true,
    rollupOptions: {
      input: {
        webview: resolve(__dirname, 'index.html') // 入口是 index.html
      }
    }
  }
})
