<template>
  <!-- 顶部通知铃铛组件，点击显示通知下拉列表 -->
  <el-popover
    v-model:visible="popoverVisible"
    placement="bottom-end"
    :width="360"
    trigger="click"
    popper-class="notification-popover"
  >
    <template #reference>
      <el-badge
        :value="store.unreadCount"
        :hidden="store.unreadCount === 0"
        :max="99"
        class="notification-badge"
      >
        <el-button link class="bell-btn" @click="onOpen">
          <el-icon size="20"><Bell /></el-icon>
        </el-button>
      </el-badge>
    </template>

    <!-- 通知面板 -->
    <div class="notification-panel">
      <div class="panel-header">
        <span class="panel-title">通知中心</span>
        <el-button
          v-if="store.unreadCount > 0"
          link
          type="primary"
          size="small"
          @click="markAllRead"
        >
          全部已读
        </el-button>
      </div>

      <!-- 通知列表 -->
      <div v-if="store.notifications.length === 0" class="empty-tip">
        暂无通知
      </div>
      <el-scrollbar v-else max-height="360">
        <div
          v-for="item in store.notifications"
          :key="item.id"
          class="notification-item"
          :class="{ unread: !item.is_read }"
          @click="handleItemClick(item)"
        >
          <div class="item-dot" :class="{ 'dot-unread': !item.is_read }" />
          <div class="item-content">
            <div class="item-title">{{ item.title }}</div>
            <div class="item-time">{{ formatTime(item.created_at) }}</div>
          </div>
        </div>
      </el-scrollbar>

      <!-- 查看全部 -->
      <div class="panel-footer">
        <el-button link type="primary" size="small" @click="goToAll">查看全部通知</el-button>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import { useNotificationStore } from '@/stores/notification'
import type { NotificationOut } from '@/types'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const router = useRouter()
const store = useNotificationStore()
const popoverVisible = ref(false)

async function onOpen() {
  // 打开时加载最新通知
  await store.fetchNotifications()
}

async function markAllRead() {
  await store.markRead([])
}

function handleItemClick(item: NotificationOut) {
  // 标记单条已读
  if (!item.is_read) store.markRead([item.id])
  // 跳转到关联资源
  if (item.related_type === 'reimbursement' && item.related_id) {
    router.push(`/reimbursements/${item.related_id}`)
    popoverVisible.value = false
  }
}

function goToAll() {
  popoverVisible.value = false
  router.push('/notifications')
}

function formatTime(dateStr: string): string {
  return dayjs(dateStr).fromNow()
}
</script>

<style scoped>
.bell-btn { padding: 4px; }
.notification-badge { cursor: pointer; }

.notification-panel {
  padding: 0;
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.panel-title { font-size: 15px; font-weight: 600; }

.empty-tip {
  text-align: center;
  padding: 40px 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.15s;
}
.notification-item:hover { background: var(--el-fill-color-light); }
.notification-item.unread { background: var(--el-color-primary-light-9); }

.item-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: transparent;
  margin-top: 6px;
  flex-shrink: 0;
}
.item-dot.dot-unread { background: var(--el-color-primary); }

.item-content { flex: 1; overflow: hidden; }
.item-title {
  font-size: 13px;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.item-time { font-size: 12px; color: var(--el-text-color-secondary); margin-top: 2px; }

.panel-footer {
  text-align: center;
  padding: 8px;
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
