import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // 自动导入 Vue / Vue Router / Pinia 组合式 API，无需手动 import
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: ['vue', 'vue-router', 'pinia'],
      dts: 'src/auto-imports.d.ts',
    }),
    // 自动导入 Element Plus 组件，无需手动注册
    Components({
      resolvers: [ElementPlusResolver()],
      dts: 'src/components.d.ts',
    }),
  ],
  resolve: {
    alias: {
      // @/ 映射到 src/ 目录，方便绝对路径导入
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      // 开发环境代理：/api 请求转发到后端
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path,
      },
    },
  },
  build: {
    // 输出目录
    outDir: 'dist',
    // 启用 CSS 代码分割
    cssCodeSplit: true,
    rollupOptions: {
      output: {
        // 代码分包：将大库单独打包，减少主包体积
        manualChunks: {
          'element-plus': ['element-plus'],
          'vendor': ['vue', 'vue-router', 'pinia', 'axios'],
        },
      },
    },
  },
})
