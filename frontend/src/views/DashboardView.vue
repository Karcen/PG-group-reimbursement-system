<template>
  <div class="dashboard-page">
    <h2 class="page-title">首页</h2>

    <!-- 学生首页 -->
    <template v-if="authStore.isStudent">
      <el-row :gutter="16" class="stats-row">
        <el-col :xs="12" :sm="8" :md="4" v-for="item in studentStats" :key="item.label">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-value" :style="{ color: item.color }">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 快捷操作 -->
      <el-card class="action-card" style="margin-top:16px">
        <template #header><span>快捷操作</span></template>
        <el-button type="primary" icon="Plus" @click="$router.push('/reimbursements/create')">
          新增报销
        </el-button>
        <el-button icon="Document" @click="$router.push('/reimbursements')">
          我的报销
        </el-button>
      </el-card>
    </template>

    <!-- 教师首页 -->
    <template v-else-if="authStore.isTeacher && !authStore.isAdmin">
      <el-row :gutter="16" class="stats-row">
        <el-col :xs="12" :sm="8" v-for="item in teacherStats" :key="item.label">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-value" :style="{ color: item.color }">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </el-card>
        </el-col>
      </el-row>
      <el-card style="margin-top:16px">
        <template #header><span>快捷操作</span></template>
        <el-button type="primary" icon="Stamp" @click="$router.push('/approvals')">
          待审批列表
        </el-button>
      </el-card>
    </template>

    <!-- 管理员首页 -->
    <template v-else-if="authStore.isAdmin">
      <el-row :gutter="16" class="stats-row">
        <el-col :xs="12" :sm="6" v-for="item in adminStats" :key="item.label">
          <el-card class="stat-card" shadow="hover">
            <div class="stat-value" :style="{ color: item.color }">{{ item.value }}</div>
            <div class="stat-label">{{ item.label }}</div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 发票类型分布 -->
      <el-card style="margin-top:16px" v-if="adminData?.invoice_type_distribution?.length">
        <template #header><span>发票类型分布</span></template>
        <el-table :data="adminData.invoice_type_distribution" size="small">
          <el-table-column prop="type" label="票据类型">
            <template #default="{ row }">
              {{ DocumentTypeLabel[row.type as DocumentType] || row.type }}
            </template>
          </el-table-column>
          <el-table-column prop="count" label="数量" />
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import http from '@/api/index'
import { useAuthStore } from '@/stores/auth'
import { DocumentTypeLabel, type DocumentType } from '@/types'

const authStore = useAuthStore()

// 数据
const studentData = ref<Record<string, number>>({})
const teacherData = ref<Record<string, number>>({})
const adminData = ref<Record<string, any>>({})

// 学生统计卡片
const studentStats = computed(() => [
  { label: '草稿', value: studentData.value.draft ?? 0, color: '#909399' },
  { label: '待审批', value: (studentData.value.submitted ?? 0) + (studentData.value.reviewing ?? 0), color: '#E6A23C' },
  { label: '已通过', value: studentData.value.approved ?? 0, color: '#67C23A' },
  { label: '已驳回', value: studentData.value.rejected ?? 0, color: '#F56C6C' },
  { label: '累计报销（元）', value: `¥${(studentData.value.total_approved_amount ?? 0).toFixed(2)}`, color: '#409EFF' },
  { label: '本月报销（元）', value: `¥${(studentData.value.month_approved_amount ?? 0).toFixed(2)}`, color: '#6366F1' },
])

// 教师统计卡片
const teacherStats = computed(() => [
  { label: '待审批', value: teacherData.value.pending ?? 0, color: '#E6A23C' },
  { label: '本周审批', value: teacherData.value.week_approved ?? 0, color: '#409EFF' },
  { label: '本月审批', value: teacherData.value.month_approved ?? 0, color: '#67C23A' },
])

// 管理员统计卡片
const adminStats = computed(() => [
  { label: '用户总数', value: adminData.value.user_count ?? 0, color: '#409EFF' },
  { label: '本月报销金额（元）', value: `¥${(adminData.value.month_approved_amount ?? 0).toFixed(2)}`, color: '#67C23A' },
  { label: '本月报销次数', value: adminData.value.month_approved_count ?? 0, color: '#E6A23C' },
])

onMounted(async () => {
  try {
    if (authStore.isStudent) {
      const res = await http.get('/dashboard/student')
      studentData.value = res.data.data
    } else if (authStore.isAdmin) {
      const res = await http.get('/dashboard/admin')
      adminData.value = res.data.data
    } else if (authStore.isTeacher) {
      const res = await http.get('/dashboard/teacher')
      teacherData.value = res.data.data
    }
  } catch {
    // 静默失败
  }
})
</script>

<style scoped>
.dashboard-page { max-width: 1200px; }
.page-title { margin: 0 0 20px; font-size: 20px; font-weight: 600; }
.stats-row { margin-bottom: 4px; }
.stat-card { text-align: center; padding: 8px 0; }
.stat-value { font-size: 28px; font-weight: 700; }
.stat-label { font-size: 13px; color: var(--el-text-color-secondary); margin-top: 4px; }
.action-card :deep(.el-card__body) { display: flex; gap: 12px; flex-wrap: wrap; }
</style>
