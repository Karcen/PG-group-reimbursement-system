<template>
  <!-- 全局应用根组件，通过 ElConfigProvider 设置中文语言 -->
  <el-config-provider :locale="zhCn">
    <router-view />
  </el-config-provider>
</template>

<script setup lang="ts">
import zhCn from 'element-plus/es/locale/lang/zh-cn'
</script>

<style>
/* ─── 全局基础样式 ────────────────────────────────────────────── */
:root {
  --color-primary: #409EFF;
  --color-bg: #f5f7fa;
  --sidebar-width: 220px;
  --header-height: 56px;
}

html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}

/* 深色模式变量覆盖 */
html.dark {
  --color-bg: #141414;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
