<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">通知中心</h2>
      <el-button
        v-if="store.unreadCount > 0"
        type="primary" plain size="small"
        @click="markAllRead"
      >
        全部标记已读
      </el-button>
    </div>

    <el-card shadow="never">
      <div class="filter-bar">
        <el-radio-group v-model="unreadOnly" @change="loadData">
          <el-radio-button :value="false">全部</el-radio-button>
          <el-radio-button :value="true">
            未读
            <el-badge v-if="store.unreadCount > 0" :value="store.unreadCount" :max="99" />
          </el-radio-button>
        </el-radio-group>
      </div>

      <div v-if="loading" class="loading-area">
        <el-skeleton :rows="5" animated />
      </div>
      <div v-else-if="list.length === 0" class="empty-area">
        <el-empty description="暂无通知" />
      </div>
      <div v-else class="notification-list">
        <div
          v-for="item in list"
          :key="item.id"
          class="notification-item"
          :class="{ unread: !item.is_read }"
          @click="handleClick(item)"
        >
          <!-- 未读指示点 -->
          <div class="unread-dot" :class="{ visible: !item.is_read }" />

          <!-- 内容 -->
          <div class="item-body">
            <div class="item-header">
              <el-tag :type="typeTagType(item.type)" size="small">
                {{ typeLabel(item.type) }}
              </el-tag>
              <span class="item-title">{{ item.title }}</span>
            </div>
            <p v-if="item.content" class="item-content">{{ item.content }}</p>
            <div class="item-time">{{ formatTime(item.created_at) }}</div>
          </div>

          <!-- 已读标记 -->
          <el-button
            v-if="!item.is_read"
            link size="small"
            @click.stop="markRead(item.id)"
          >
            标为已读
          </el-button>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="loadData"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import { useNotificationStore } from '@/stores/notification'
import type { NotificationOut, NotificationType } from '@/types'
import http from '@/api/index'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const router = useRouter()
const store = useNotificationStore()
const loading = ref(false)
const list = ref<NotificationOut[]>([])
const unreadOnly = ref(false)
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

async function loadData() {
  loading.value = true
  try {
    const res = await http.get('/notifications', {
      params: {
        page: pagination.page,
        page_size: pagination.pageSize,
        unread_only: unreadOnly.value,
      },
    })
    const data = res.data.data
    list.value = data.items
    pagination.total = data.total
    await store.fetchUnreadCount()
  } finally {
    loading.value = false
  }
}

async function markRead(id: number) {
  await store.markRead([id])
  const item = list.value.find((n) => n.id === id)
  if (item) item.is_read = true
}

async function markAllRead() {
  await store.markRead([])
  list.value.forEach((n) => (n.is_read = true))
}

function handleClick(item: NotificationOut) {
  if (!item.is_read) markRead(item.id)
  if (item.related_type === 'reimbursement' && item.related_id) {
    router.push(`/reimbursements/${item.related_id}`)
  }
}

function formatTime(str: string) { return dayjs(str).fromNow() }

const TYPE_LABEL: Record<string, string> = {
  submitted: '已提交', approved: '审批通过', rejected: '审批驳回',
  new_pending: '待审批', ocr_done: 'OCR完成', ai_done: 'AI完成',
  reminder: '催办提醒', announcement: '系统公告',
}
const TYPE_TAG: Record<string, string> = {
  approved: 'success', rejected: 'danger', new_pending: 'warning',
  reminder: 'warning', announcement: 'info',
}
function typeLabel(t: string) { return TYPE_LABEL[t] || t }
function typeTagType(t: string) { return TYPE_TAG[t] || '' }

onMounted(() => loadData())
</script>

<style scoped>
.page { max-width: 800px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; }
.filter-bar { margin-bottom: 16px; }
.loading-area, .empty-area { padding: 24px 0; }

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: background 0.15s;
  border-radius: 4px;
}
.notification-item:hover { background: var(--el-fill-color-lighter); }
.notification-item.unread { background: var(--el-color-primary-light-9); }
.notification-item:last-child { border-bottom: none; }

.unread-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  margin-top: 8px;
  flex-shrink: 0;
  background: transparent;
}
.unread-dot.visible { background: var(--el-color-primary); }

.item-body { flex: 1; overflow: hidden; }
.item-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.item-title { font-size: 14px; font-weight: 500; }
.item-content { font-size: 13px; color: var(--el-text-color-secondary); margin: 4px 0; }
.item-time { font-size: 12px; color: var(--el-text-color-placeholder); }
.pagination-wrap { display: flex; justify-content: flex-end; padding-top: 16px; }
</style>
