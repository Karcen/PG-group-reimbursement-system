/**
 * Vue Router 路由配置
 * 使用 createWebHistory（HTML5 History API），配合 Nginx try_files 使用
 */

import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'
import { useAuthStore } from '@/stores/auth'

// ─── 路由懒加载 ────────────────────────────────────────────────────────────

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '登录', requiresAuth: false },
  },

  // 主布局（带侧边栏和顶部导航）
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard',
      },
      // 首页统计面板
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { title: '首页', icon: 'Odometer' },
      },
      // 报销申请
      {
        path: 'reimbursements',
        name: 'ReimbursementList',
        component: () => import('@/views/ReimbursementListView.vue'),
        meta: { title: '报销申请', icon: 'Document' },
      },
      {
        path: 'reimbursements/create',
        name: 'ReimbursementCreate',
        component: () => import('@/views/ReimbursementCreateView.vue'),
        meta: { title: '新增报销', icon: 'Plus' },
      },
      {
        path: 'reimbursements/:id',
        name: 'ReimbursementDetail',
        component: () => import('@/views/ReimbursementDetailView.vue'),
        meta: { title: '报销详情' },
      },
      // 审批中心（教师/管理员）
      {
        path: 'approvals',
        name: 'ApprovalList',
        component: () => import('@/views/ApprovalListView.vue'),
        meta: { title: '审批中心', icon: 'Stamp', roles: ['teacher', 'admin'] },
      },
      // 通知中心
      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('@/views/NotificationView.vue'),
        meta: { title: '通知中心', icon: 'Bell' },
      },
      // ─── 系统管理（管理员）────────────────────────────────────────
      {
        path: 'admin/users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UsersView.vue'),
        meta: { title: '用户管理', icon: 'User', roles: ['admin'] },
      },
      {
        path: 'admin/projects',
        name: 'AdminProjects',
        component: () => import('@/views/admin/ProjectsView.vue'),
        meta: { title: '经费项目', icon: 'FolderOpened', roles: ['admin'] },
      },
      {
        path: 'admin/audit-logs',
        name: 'AdminAuditLogs',
        component: () => import('@/views/admin/AuditLogsView.vue'),
        meta: { title: '审计日志', icon: 'List', roles: ['admin'] },
      },
      {
        path: 'admin/tags',
        name: 'AdminTags',
        component: () => import('@/views/admin/TagsView.vue'),
        meta: { title: '标签管理', icon: 'PriceTag', roles: ['admin'] },
      },
    ],
  },

  // 404
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

// ─── 全局导航守卫 ──────────────────────────────────────────────────────────

NProgress.configure({ showSpinner: false })

router.beforeEach(async (to) => {
  NProgress.start()

  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth && !authStore.isLoggedIn) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  }

  if (to.name === 'Login' && authStore.isLoggedIn) {
    return { name: 'Dashboard' }
  }

  // 角色权限检查
  const allowedRoles = to.meta.roles as string[] | undefined
  if (allowedRoles && authStore.user && !allowedRoles.includes(authStore.user.role)) {
    return { name: 'Dashboard' }
  }

  document.title = `${to.meta.title ?? '首页'} — 实验室报销管理系统`
  return true
})

router.afterEach(() => {
  NProgress.done()
})

export default router
