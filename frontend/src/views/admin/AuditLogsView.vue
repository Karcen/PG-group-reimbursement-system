<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">审计日志</h2>
      <el-button icon="Download" @click="exportExcel">导出 Excel</el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card shadow="never" class="filter-card">
      <el-form :model="filters" inline>
        <el-form-item label="操作类型">
          <el-input v-model="filters.action" placeholder="如：LOGIN / APPROVE" clearable style="width:160px" />
        </el-form-item>
        <el-form-item label="用户ID">
          <el-input-number v-model="filters.user_id" :min="1" :controls="false" placeholder="用户ID" style="width:100px" />
        </el-form-item>
        <el-form-item label="结果">
          <el-select v-model="filters.is_success" placeholder="全部" clearable style="width:90px">
            <el-option label="成功" :value="true" />
            <el-option label="失败" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="loadData(1)">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志表格 -->
    <el-card shadow="never" style="margin-top:12px">
      <el-table v-loading="loading" :data="list" stripe size="small">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="时间" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column prop="username" label="用户" width="110" show-overflow-tooltip />
        <el-table-column prop="ip_address" label="IP" width="130" />
        <el-table-column prop="action" label="操作码" width="160" />
        <el-table-column prop="action_desc" label="操作描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="对象" width="130">
          <template #default="{ row }">
            <span v-if="row.target_type">{{ row.target_type }}#{{ row.target_id }}</span>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column label="结果" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_success ? 'success' : 'danger'" size="small">
              {{ row.is_success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="详情" width="60" align="center">
          <template #default="{ row }">
            <el-button
              v-if="row.old_data || row.new_data"
              link size="small"
              @click="showDetail(row)"
            >
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          :total="pagination.total"
          :page-size="pagination.pageSize"
          layout="total, prev, pager, next"
          @current-change="loadData"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="操作前后数据" width="600px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="操作前">
          <pre class="json-pre">{{ formatJson(detailRow?.old_data) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="操作后">
          <pre class="json-pre">{{ formatJson(detailRow?.new_data) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import dayjs from 'dayjs'
import http from '@/api/index'

const loading = ref(false)
const list = ref<any[]>([])
const filters = reactive({ action: '', user_id: undefined as number | undefined, is_success: undefined as boolean | undefined })
const pagination = reactive({ page: 1, pageSize: 50, total: 0 })
const detailVisible = ref(false)
const detailRow = ref<any>(null)

async function loadData(page = pagination.page) {
  loading.value = true
  try {
    const res = await http.get('/audit-logs', {
      params: {
        page, page_size: pagination.pageSize,
        action: filters.action || undefined,
        user_id: filters.user_id || undefined,
        is_success: filters.is_success,
      },
    })
    const data = res.data.data
    list.value = data.items
    pagination.total = data.total
    pagination.page = data.page
  } finally { loading.value = false }
}

function resetFilters() {
  Object.assign(filters, { action: '', user_id: undefined, is_success: undefined })
  loadData(1)
}

function showDetail(row: any) { detailRow.value = row; detailVisible.value = true }

function formatDate(str: string) { return dayjs(str).format('YYYY-MM-DD HH:mm:ss') }
function formatJson(data: any) {
  if (!data) return '—'
  return JSON.stringify(data, null, 2)
}

async function exportExcel() {
  const res = await http.get('/audit-logs/export/excel', { responseType: 'blob' })
  const url = URL.createObjectURL(new Blob([res.data]))
  const a = document.createElement('a')
  a.href = url
  a.download = `audit_logs_${dayjs().format('YYYYMMDD')}.xlsx`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(() => loadData())
</script>

<style scoped>
.page { max-width: 1400px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; }
.filter-card :deep(.el-card__body) { padding: 16px 20px 4px; }
.pagination-wrap { display: flex; justify-content: flex-end; padding-top: 16px; }
.json-pre { font-size: 12px; white-space: pre-wrap; word-break: break-all; margin: 0; max-height: 200px; overflow-y: auto; }
</style>
