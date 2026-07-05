/**
 * 通知中心状态管理 Store
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { NotificationOut } from '@/types'
import http from '@/api/index'

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)
  const notifications = ref<NotificationOut[]>([])

  async function fetchUnreadCount() {
    try {
      const res = await http.get('/notifications/unread-count')
      unreadCount.value = res.data.data.count
    } catch {
      // 静默失败，不影响主流程
    }
  }

  async function fetchNotifications(unreadOnly = false) {
    const res = await http.get('/notifications', { params: { unread_only: unreadOnly, page_size: 30 } })
    notifications.value = res.data.data.items
    return res.data.data
  }

  async function markRead(ids: number[] = []) {
    await http.put('/notifications/read', { ids })
    // 本地更新已读状态
    if (ids.length === 0) {
      notifications.value.forEach((n) => (n.is_read = true))
    } else {
      notifications.value.forEach((n) => {
        if (ids.includes(n.id)) n.is_read = true
      })
    }
    await fetchUnreadCount()
  }

  return { unreadCount, notifications, fetchUnreadCount, fetchNotifications, markRead }
})
