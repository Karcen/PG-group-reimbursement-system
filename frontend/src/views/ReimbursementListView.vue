<template>
  <div class="page">
    <!-- 页面标题 + 操作栏 -->
    <div class="page-header">
      <h2 class="page-title">报销申请</h2>
      <el-button type="primary" icon="Plus" @click="$router.push('/reimbursements/create')">
        新增报销
      </el-button>
    </div>

    <!-- 搜索过滤栏 -->
    <el-card class="filter-card" shadow="never">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部" clearable style="width:130px">
            <el-option
              v-for="(label, val) in ReimbursementStatusLabel"
              :key="val" :label="label" :value="val"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关键字">
          <el-input v-model="filters.keyword" placeholder="标题/事由" clearable style="width:200px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="loadData(1)">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card shadow="never" style="margin-top:12px">
      <el-table
        v-loading="loading"
        :data="list"
        row-key="id"
        stripe
        @row-click="(row: ReimbursementListItem) => $router.push(`/reimbursements/${row.id}`)"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column label="项目" width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.project?.name || '—' }}</template>
        </el-table-column>
        <el-table-column prop="declared_amount" label="金额（元）" width="120" align="right">
          <template #default="{ row }">¥{{ row.declared_amount.toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag :type="ReimbursementStatusType[row.status]" size="small">
              {{ ReimbursementStatusLabel[row.status] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="申请人" width="110">
          <template #default="{ row }">{{ row.applicant.full_name || row.applicant.username }}</template>
        </el-table-column>
        <el-table-column label="提交时间" width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click.stop="$router.push(`/reimbursements/${row.id}`)">
              查看
            </el-button>
            <el-button
              v-if="row.status === 'draft'"
              link type="danger" size="small"
              @click.stop="deleteDraft(row.id)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="loadData"
          @size-change="() => loadData(1)"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import http from '@/api/index'
import {
  ReimbursementStatusLabel,
  ReimbursementStatusType,
  type ReimbursementListItem,
} from '@/types'

const loading = ref(false)
const list = ref<ReimbursementListItem[]>([])
const filters = reactive({ status: '', keyword: '' })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })

async function loadData(page = pagination.page) {
  loading.value = true
  try {
    const res = await http.get('/reimbursements', {
      params: {
        page,
        page_size: pagination.pageSize,
        status: filters.status || undefined,
        keyword: filters.keyword || undefined,
      },
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
  filters.status = ''
  filters.keyword = ''
  loadData(1)
}

async function deleteDraft(id: number) {
  await ElMessageBox.confirm('确定要删除此草稿吗？', '提示', { type: 'warning' })
  await http.delete(`/reimbursements/${id}`)
  ElMessage.success('已删除')
  loadData()
}

function formatDate(str: string) {
  return dayjs(str).format('YYYY-MM-DD HH:mm')
}

onMounted(() => loadData())
</script>

<style scoped>
.page { max-width: 1200px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; }
.filter-card :deep(.el-card__body) { padding: 16px 20px 4px; }
.filter-form { display: flex; flex-wrap: wrap; gap: 4px; }
.pagination-wrap { display: flex; justify-content: flex-end; padding-top: 16px; }
</style>
