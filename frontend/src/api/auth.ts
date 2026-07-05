/**
 * 认证相关 API 调用
 */

import http from './index'
import type { TokenResponse, UserOut } from '@/types'

export interface LoginParams {
  username: string
  password: string
}

export const authApi = {
  /** 用户登录，返回 Token 和用户信息 */
  async login(params: LoginParams): Promise<TokenResponse> {
    const res = await http.post('/auth/login', params)
    return res.data.data
  },

  /** 退出登录（记录审计日志） */
  async logout(): Promise<void> {
    await http.post('/auth/logout')
  },

  /** 使用 Refresh Token 换取新的 Access Token */
  async refresh(refreshToken: string): Promise<string> {
    const res = await http.post('/auth/refresh', { refresh_token: refreshToken })
    return res.data.data.access_token
  },

  /** 获取当前登录用户信息 */
  async getMe(): Promise<UserOut> {
    const res = await http.get('/auth/me')
    return res.data.data
  },
}
