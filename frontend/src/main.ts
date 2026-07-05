/**
 * 前端应用入口
 * 初始化 Vue 应用、注册全局插件和 Element Plus
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'

import App from './App.vue'
import router from './router'

// 创建 Vue 应用实例
const app = createApp(App)

// 注册 Pinia 状态管理（含持久化插件）
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
app.use(pinia)

// 注册路由
app.use(router)

// 注册 Element Plus
app.use(ElementPlus, {
  // 设置中文语言
  locale: undefined, // 将在 App.vue 中通过 ElConfigProvider 动态设置
})

// 批量注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.mount('#app')
