<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">审批中心</h2>
    </div>

    <!-- 搜索过滤 -->
    <el-card shadow="never" class="filter-card">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="关键字">
          <el-input v-model="filters.keyword" placeholder="标题/申请人" clearable style="width:200px" @keyup.enter="loadData(1)" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="loadData(1)">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 待审批列表 -->
    <el-card shadow="never" style="margin-top:12px">
      <template #header>
        <span>待审批列表</span>
        <el-badge :value="pagination.total" :max="99" type="warning" style="margin-left:8px" />
      </template>

      <el-table
        v-loading="loading"
        :data="list"
        stripe
        @row-click="(row) => $router.push(`/reimbursements/${row.id}`)"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
        <el-table-column label="申请人" width="110">
          <template #default="{ row }">
            {{ row.applicant.full_name || row.applicant.username }}
          </template>
        </el-table-column>
        <el-table-column label="经费项目" width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.project?.name || '—' }}</template>
        </el-table-column>
        <el-table-column prop="declared_amount" label="金额（元）" width="120" align="right">
          <template #default="{ row }">¥{{ row.declared_amount.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="(ReimbursementStatusType[(row as ReimbursementListItem).status] as any)" size="small">
              {{ ReimbursementStatusLabel[(row as ReimbursementListItem).status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="提交时间" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="等待时长" width="100" align="center">
          <template #default="{ row }">
            <el-text :type="isLongWait(row.created_at) ? 'danger' : 'info'" size="small">
              {{ waitDuration(row.created_at) }}
            </el-text>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="$router.push(`/reimbursements/${row.id}`)">
              审批
            </el-button>
          </template>
        </el-table-column>
      </el-table>

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
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'
import http from '@/api/index'
import { ReimbursementStatusLabel, ReimbursementStatusType, type ReimbursementListItem } from '@/types'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const loading = ref(false)
const list = ref<ReimbursementListItem[]>([])
const filters = reactive({ keyword: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

async function loadData(page = pagination.page) {
  loading.value = true
  try {
    const res = await http.get('/reimbursements/pending', {
      params: { page, page_size: pagination.pageSize, keyword: filters.keyword || undefined },
    })
    const data = res.data.data
    list.value = data.items
    pagination.total = data.total
    pagination.page = data.page
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.keyword = ''
  loadData(1)
}

function formatDate(str: string) { return dayjs(str).format('YYYY-MM-DD HH:mm') }
function waitDuration(str: string) { return dayjs(str).fromNow(true) }
function isLongWait(str: string) {
  return dayjs().diff(dayjs(str), 'hour') >= 72
}

onMounted(() => loadData())
</script>

<style scoped>
.page { max-width: 1200px; }
.page-header { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; }
.filter-card :deep(.el-card__body) { padding: 16px 20px 4px; }
.pagination-wrap { display: flex; justify-content: flex-end; padding-top: 16px; }
</style>
