/**
 * 认证状态管理 Store
 * 管理登录状态、当前用户信息和 Token
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserOut } from '@/types'
import { authApi } from '@/api/auth'
import router from '@/router'

export const useAuthStore = defineStore(
  'auth',
  () => {
    // ─── 状态 ───────────────────────────────────────────────────────
    const accessToken = ref<string | null>(null)
    const refreshToken = ref<string | null>(null)
    const user = ref<UserOut | null>(null)

    // ─── 计算属性 ────────────────────────────────────────────────────
    const isLoggedIn = computed(() => !!accessToken.value && !!user.value)
    const isAdmin = computed(() => user.value?.role === 'admin')
    const isTeacher = computed(() => user.value?.role === 'teacher' || user.value?.role === 'admin')
    const isStudent = computed(() => user.value?.role === 'student')

    // ─── 操作 ────────────────────────────────────────────────────────

    /**
     * 登录：调用 API → 保存 Token 和用户信息
     */
    async function login(username: string, password: string): Promise<void> {
      const data = await authApi.login({ username, password })
      accessToken.value = data.access_token
      refreshToken.value = data.refresh_token
      user.value = data.user
    }

    /**
     * 退出登录：清除本地状态，跳转到登录页
     */
    async function logout(): Promise<void> {
      try {
        await authApi.logout()
      } catch {
        // 忽略退出登录的 API 错误
      } finally {
        _clearState()
        await router.push({ name: 'Login' })
      }
    }

    /**
     * 刷新 Access Token（Token 过期时自动调用）
     */
    async function refreshAccessToken(): Promise<boolean> {
      if (!refreshToken.value) return false
      try {
        const newToken = await authApi.refresh(refreshToken.value)
        accessToken.value = newToken
        return true
      } catch {
        _clearState()
        return false
      }
    }

    /**
     * 更新本地用户信息（修改资料后调用）
     */
    function updateUser(updated: Partial<UserOut>): void {
      if (user.value) {
        user.value = { ...user.value, ...updated }
      }
    }

    function _clearState(): void {
      accessToken.value = null
      refreshToken.value = null
      user.value = null
    }

    return {
      accessToken,
      refreshToken,
      user,
      isLoggedIn,
      isAdmin,
      isTeacher,
      isStudent,
      login,
      logout,
      refreshAccessToken,
      updateUser,
    }
  },
  {
    // 持久化到 localStorage（页面刷新后保持登录状态）
    persist: {
      key: 'reimbursement-auth',
      storage: localStorage,
      pick: ['accessToken', 'refreshToken', 'user'],
    },
  },
)
