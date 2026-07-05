<template>
  <!-- 主布局：顶部导航 + 左侧菜单 + 内容区域 -->
  <div class="layout-wrapper" :class="{ 'is-collapse': isCollapse }">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <!-- Logo 区域 -->
      <div class="sidebar-logo">
        <el-icon class="logo-icon" size="24"><Money /></el-icon>
        <span v-if="!isCollapse" class="logo-text">报销管理系统</span>
      </div>

      <!-- 导航菜单 -->
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :collapse-transition="false"
        background-color="#304156"
        text-color="rgba(255,255,255,0.75)"
        active-text-color="#409EFF"
        class="sidebar-menu"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><Odometer /></el-icon>
          <template #title>首页</template>
        </el-menu-item>

        <el-menu-item index="/reimbursements">
          <el-icon><Document /></el-icon>
          <template #title>报销申请</template>
        </el-menu-item>

        <el-menu-item
          v-if="authStore.isTeacher"
          index="/approvals"
        >
          <el-icon><Stamp /></el-icon>
          <template #title>审批中心</template>
        </el-menu-item>

        <el-menu-item index="/notifications">
          <el-icon><Bell /></el-icon>
          <template #title>
            通知中心
            <el-badge
              v-if="notificationStore.unreadCount > 0"
              :value="notificationStore.unreadCount"
              :max="99"
              class="badge-inline"
            />
          </template>
        </el-menu-item>

        <!-- 系统管理（仅管理员） -->
        <el-sub-menu v-if="authStore.isAdmin" index="admin">
          <template #title>
            <el-icon><Setting /></el-icon>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/admin/users">用户管理</el-menu-item>
          <el-menu-item index="/admin/projects">经费项目</el-menu-item>
          <el-menu-item index="/admin/tags">标签管理</el-menu-item>
          <el-menu-item index="/admin/audit-logs">审计日志</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </aside>

    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 顶部导航栏 -->
      <header class="topbar">
        <!-- 折叠按钮 -->
        <el-button
          link
          class="collapse-btn"
          @click="isCollapse = !isCollapse"
        >
          <el-icon size="20">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
        </el-button>

        <!-- 面包屑 -->
        <el-breadcrumb separator="/" class="breadcrumb">
          <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item v-if="currentTitle">{{ currentTitle }}</el-breadcrumb-item>
        </el-breadcrumb>

        <div class="topbar-right">
          <!-- 深色模式切换 -->
          <el-button link @click="toggleDark">
            <el-icon size="18">
              <Moon v-if="!isDark" />
              <Sunny v-else />
            </el-icon>
          </el-button>

          <!-- 通知铃铛 -->
          <NotificationBell />

          <!-- 用户头像 & 下拉菜单 -->
          <el-dropdown @command="handleCommand">
            <div class="user-avatar">
              <el-avatar :size="32" :src="authStore.user?.avatar_url || undefined">
                {{ authStore.user?.full_name?.charAt(0) || '用' }}
              </el-avatar>
              <span class="user-name">{{ authStore.user?.full_name || authStore.user?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                <el-dropdown-item command="password">修改密码</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 页面内容 -->
      <main class="page-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import NotificationBell from '@/components/NotificationBell.vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

// 侧边栏折叠状态
const isCollapse = ref(false)

// 深色模式
const isDark = ref(false)
function toggleDark() {
  isDark.value = !isDark.value
  if (isDark.value) {
    document.documentElement.classList.add('dark')
    localStorage.setItem('theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    localStorage.setItem('theme', 'light')
  }
}

// 当前激活菜单
const activeMenu = computed(() => route.path)

// 当前页面标题
const currentTitle = computed(() => route.meta.title as string | undefined)

// 顶部操作命令
async function handleCommand(command: string) {
  if (command === 'logout') {
    await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await authStore.logout()
  } else if (command === 'profile') {
    router.push('/users/me/profile')
  } else if (command === 'password') {
    router.push('/users/me/password')
  }
}

onMounted(() => {
  // 恢复深色模式设置
  if (localStorage.getItem('theme') === 'dark') {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
  // 获取未读通知数
  notificationStore.fetchUnreadCount()
  // 每 60 秒轮询一次未读通知数
  setInterval(() => notificationStore.fetchUnreadCount(), 60_000)
})
</script>

<style scoped>
.layout-wrapper {
  display: flex;
  height: 100vh;
  background: var(--el-bg-color-page, #f5f7fa);
}

/* 侧边栏 */
.sidebar {
  width: var(--sidebar-width, 220px);
  height: 100vh;
  background: #304156;            /* 硬编码，不依赖 Element Plus 的 --el-menu-bg-color */
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease;
  flex-shrink: 0;
}
.layout-wrapper.is-collapse .sidebar {
  width: 64px;
}

.sidebar-logo {
  height: 56px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 18px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: #263445;            /* 比侧边栏稍深，形成层次感 */
  overflow: hidden;
  white-space: nowrap;
}
.logo-icon { color: #409EFF; flex-shrink: 0; }
.logo-text { transition: opacity 0.2s; }
.is-collapse .logo-text { opacity: 0; }

.sidebar-menu {
  flex: 1;
  border-right: none !important;
  background: transparent !important;
  overflow-y: auto;
  overflow-x: hidden;
}
/* 覆盖 Element Plus 默认菜单样式，保证深色背景上文字可见 */
:deep(.el-menu) {
  background-color: transparent !important;
}
:deep(.el-menu-item),
:deep(.el-sub-menu__title) {
  color: rgba(255, 255, 255, 0.75) !important;
  background-color: transparent !important;
}
:deep(.el-menu-item:hover),
:deep(.el-sub-menu__title:hover) {
  background-color: rgba(255, 255, 255, 0.08) !important;
  color: #fff !important;
}
:deep(.el-menu-item.is-active) {
  background-color: rgba(64, 158, 255, 0.2) !important;
  color: #409EFF !important;
}
:deep(.el-sub-menu .el-menu) {
  background-color: rgba(0, 0, 0, 0.15) !important;
}
:deep(.el-icon) {
  color: inherit !important;
}

/* 主内容区 */
.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部导航栏 */
.topbar {
  height: 56px;
  background: var(--el-bg-color, #fff);
  border-bottom: 1px solid var(--el-border-color-light);
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 12px;
  flex-shrink: 0;
}
.collapse-btn { padding: 4px; }
.breadcrumb { flex: 1; }
.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-avatar {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.2s;
}
.user-avatar:hover { background: var(--el-fill-color-light); }
.user-name { font-size: 14px; color: var(--el-text-color-primary); }
.badge-inline { margin-left: 4px; }

/* 页面内容 */
.page-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
</style>
