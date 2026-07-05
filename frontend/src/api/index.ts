/**
 * Axios HTTP 客户端
 * 统一配置请求拦截（注入 Token）和响应拦截（统一错误处理、Token 刷新）
 */

import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

// 创建 Axios 实例
const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─── 请求拦截器：注入 Authorization Token ─────────────────────────────────
http.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 从 localStorage 读取 auth store（避免循环依赖）
    try {
      const raw = localStorage.getItem('reimbursement-auth')
      if (raw) {
        const auth = JSON.parse(raw)
        const token = auth?.accessToken
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
      }
    } catch {
      // 忽略解析错误
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ─── 响应拦截器：统一错误处理 ────────────────────────────────────────────
let isRefreshing = false
let failedQueue: Array<{ resolve: (v: string) => void; reject: (e: unknown) => void }> = []

function processQueue(error: unknown, token: string | null = null) {
  failedQueue.forEach((prom) => {
    if (error) prom.reject(error)
    else prom.resolve(token!)
  })
  failedQueue = []
}

http.interceptors.response.use(
  (response) => {
    // 统一返回 data 层
    const data = response.data
    if (data && !data.success) {
      // 业务层失败（HTTP 200 但 success=false）
      const msg = data.message || '操作失败'
      ElMessage.error(msg)
      return Promise.reject(new Error(msg))
    }
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // 401：Token 过期，尝试刷新
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return http(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const raw = localStorage.getItem('reimbursement-auth')
        const refreshToken = raw ? JSON.parse(raw)?.refreshToken : null

        if (!refreshToken) throw new Error('无 Refresh Token')

        const { useAuthStore } = await import('@/stores/auth')
        const authStore = useAuthStore()
        const success = await authStore.refreshAccessToken()

        if (success && authStore.accessToken) {
          processQueue(null, authStore.accessToken)
          originalRequest.headers.Authorization = `Bearer ${authStore.accessToken}`
          return http(originalRequest)
        } else {
          throw new Error('刷新 Token 失败')
        }
      } catch (refreshError) {
        processQueue(refreshError, null)
        const { useAuthStore } = await import('@/stores/auth')
        const store = useAuthStore()
        // 强制清除 Token（不走 API logout，直接跳转登录页）
        store.accessToken = null
        store.refreshToken = null
        store.user = null
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // 显示错误提示
    const message =
      (error.response?.data as { message?: string })?.message ||
      getErrorMessage(error.response?.status)
    ElMessage.error(message)
    return Promise.reject(error)
  },
)

function getErrorMessage(status?: number): string {
  const messages: Record<number, string> = {
    400: '请求参数错误',
    401: '请先登录',
    403: '权限不足',
    404: '资源不存在',
    409: '数据冲突',
    413: '文件过大',
    422: '数据校验失败',
    500: '服务器内部错误',
    503: '服务暂不可用',
  }
  return status ? (messages[status] ?? `请求失败（${status}）`) : '网络连接失败'
}

export default http
