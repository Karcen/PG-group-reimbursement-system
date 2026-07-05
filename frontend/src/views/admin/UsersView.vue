<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">用户管理</h2>
      <el-button type="primary" icon="Plus" @click="openCreateDialog">新增用户</el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card shadow="never" class="filter-card">
      <el-form :model="filters" inline>
        <el-form-item label="关键字">
          <el-input v-model="filters.keyword" placeholder="用户名/姓名/邮箱" clearable style="width:200px" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="filters.role" placeholder="全部" clearable style="width:110px">
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.is_active" placeholder="全部" clearable style="width:90px">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" icon="Search" @click="loadData(1)">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户表格 -->
    <el-card shadow="never" style="margin-top:12px">
      <el-table v-loading="loading" :data="list" stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="full_name" label="姓名" width="100" />
        <el-table-column prop="email" label="邮箱" min-width="160" show-overflow-tooltip />
        <el-table-column prop="department" label="部门" width="140" show-overflow-tooltip />
        <el-table-column label="角色" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="roleTagType(row.role)" size="small">{{ roleLabel(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="注册时间" width="150">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link size="small" @click="openEditDialog(row as UserOut)">编辑</el-button>
            <el-button link size="small" @click="openResetPwdDialog(row as UserOut)">重置密码</el-button>
            <el-button link :type="(row as UserOut).is_active ? 'danger' : 'success'" size="small" @click="toggleActive(row as UserOut)">
              {{ (row as UserOut).is_active ? '禁用' : '启用' }}
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

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingUser ? '编辑用户' : '新增用户'" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="!!editingUser" />
        </el-form-item>
        <el-form-item v-if="!editingUser" label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" type="email" />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="form.full_name" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width:100%">
            <el-option label="学生" value="student" />
            <el-option label="教师" value="teacher" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门">
          <el-input v-model="form.department" />
        </el-form-item>
        <el-form-item label="学号/工号">
          <el-input v-model="form.student_id" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="resetPwdVisible" title="重置密码" width="400px">
      <el-form label-width="90px">
        <el-form-item label="新密码">
          <el-input v-model="newPassword" type="password" show-password placeholder="至少8位，含大小写字母和数字" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="resetPwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="resetPassword">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import dayjs from 'dayjs'
import http from '@/api/index'
import type { UserOut } from '@/types'

const loading = ref(false)
const saving = ref(false)
const list = ref<UserOut[]>([])
const filters = reactive({ keyword: '', role: '', is_active: undefined as boolean | undefined })
const pagination = reactive({ page: 1, pageSize: 20, total: 0 })
const dialogVisible = ref(false)
const resetPwdVisible = ref(false)
const editingUser = ref<UserOut | null>(null)
const resetingUser = ref<UserOut | null>(null)
const newPassword = ref('')
const formRef = ref<FormInstance>()

const form = reactive({
  username: '', password: '', email: '', full_name: '',
  role: 'student', department: '', student_id: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名' }],
  password: [{ required: true, message: '请输入密码', min: 8 }],
  email: [{ required: true, type: 'email', message: '请输入有效邮箱' }],
  full_name: [{ required: true, message: '请输入姓名' }],
  role: [{ required: true, message: '请选择角色' }],
}

async function loadData(page = pagination.page) {
  loading.value = true
  try {
    const res = await http.get('/users', {
      params: { page, page_size: pagination.pageSize, keyword: filters.keyword || undefined, role: filters.role || undefined, is_active: filters.is_active },
    })
    const data = res.data.data
    list.value = data.items
    pagination.total = data.total
    pagination.page = data.page
  } finally {
    loading.value = false
  }
}

function resetFilters() { Object.assign(filters, { keyword: '', role: '', is_active: undefined }); loadData(1) }

function openCreateDialog() {
  editingUser.value = null
  Object.assign(form, { username: '', password: '', email: '', full_name: '', role: 'student', department: '', student_id: '' })
  dialogVisible.value = true
}

function openEditDialog(user: UserOut) {
  editingUser.value = user
  Object.assign(form, user)
  dialogVisible.value = true
}

function openResetPwdDialog(user: UserOut) {
  resetingUser.value = user
  newPassword.value = ''
  resetPwdVisible.value = true
}

async function saveUser() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editingUser.value) {
      await http.put(`/users/${editingUser.value.id}`, form)
      ElMessage.success('用户信息已更新')
    } else {
      await http.post('/users', form)
      ElMessage.success('用户创建成功')
    }
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

async function resetPassword() {
  if (!resetingUser.value || !newPassword.value) { ElMessage.warning('请输入新密码'); return }
  saving.value = true
  try {
    await http.post(`/users/${resetingUser.value.id}/reset-password`, { new_password: newPassword.value })
    ElMessage.success('密码已重置')
    resetPwdVisible.value = false
  } finally {
    saving.value = false
  }
}

async function toggleActive(user: UserOut) {
  await http.put(`/users/${user.id}`, { is_active: !user.is_active })
  ElMessage.success(user.is_active ? '用户已禁用' : '用户已启用')
  loadData()
}

function formatDate(str: string) { return dayjs(str).format('YYYY-MM-DD') }
const ROLE_LABEL: Record<string, string> = { student: '学生', teacher: '教师', admin: '管理员' }
const ROLE_TAG: Record<string, 'info' | 'warning' | 'danger' | 'success' | 'primary'> = {
  student: 'info', teacher: 'warning', admin: 'danger'
}
function roleLabel(r: string) { return ROLE_LABEL[r] || r }
function roleTagType(r: string): 'info' | 'warning' | 'danger' | 'success' | 'primary' {
  return ROLE_TAG[r] ?? 'info'
}

onMounted(() => loadData())
</script>

<style scoped>
.page { max-width: 1200px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; }
.filter-card :deep(.el-card__body) { padding: 16px 20px 4px; }
.pagination-wrap { display: flex; justify-content: flex-end; padding-top: 16px; }
</style>
