<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">经费项目管理</h2>
      <el-button type="primary" icon="Plus" @click="openCreateDialog">新增项目</el-button>
    </div>

    <!-- 项目卡片列表 -->
    <div v-loading="loading" class="project-grid">
      <el-card
        v-for="proj in list"
        :key="proj.id"
        class="project-card"
        shadow="hover"
      >
        <template #header>
          <div class="card-header">
            <span class="proj-name">{{ proj.name }}</span>
            <el-tag :type="proj.is_active ? 'success' : 'info'" size="small">
              {{ proj.is_active ? '启用' : '禁用' }}
            </el-tag>
          </div>
        </template>

        <el-descriptions :column="1" size="small">
          <el-descriptions-item label="项目编号">{{ proj.code }}</el-descriptions-item>
          <el-descriptions-item label="预算（元）">
            {{ proj.budget != null ? `¥${proj.budget.toFixed(2)}` : '不限' }}
          </el-descriptions-item>
          <el-descriptions-item label="已使用">
            ¥{{ proj.used_amount.toFixed(2) }}
            <el-progress
              v-if="proj.budget"
              :percentage="Math.min(100, Math.round((proj.used_amount / proj.budget) * 100))"
              :status="proj.used_amount / (proj.budget || 1) > 0.9 ? 'exception' : undefined"
              :stroke-width="4"
              style="margin-top:4px"
            />
          </el-descriptions-item>
          <el-descriptions-item label="简介">
            {{ proj.description || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="审批流">
            <div v-if="proj.approval_flows.length === 0" class="tip-text">未配置</div>
            <div v-else>
              <el-tag
                v-for="flow in proj.approval_flows"
                :key="flow.id"
                size="small"
                style="margin:2px"
              >
                第{{ flow.step }}步：{{ flow.approver.full_name || flow.approver.username }}
              </el-tag>
            </div>
          </el-descriptions-item>
        </el-descriptions>

        <div class="card-actions">
          <el-button size="small" @click="openEditDialog(proj)">编辑</el-button>
          <el-button size="small" @click="openFlowDialog(proj)">配置审批流</el-button>
          <el-button
            size="small"
            :type="proj.is_active ? 'danger' : 'success'"
            @click="toggleActive(proj)"
          >
            {{ proj.is_active ? '禁用' : '启用' }}
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingProject ? '编辑项目' : '新增项目'" width="500px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="项目编号" prop="code">
          <el-input v-model="form.code" />
        </el-form-item>
        <el-form-item label="预算（元）">
          <el-input-number v-model="form.budget" :min="0" :precision="2" placeholder="不填表示不限" />
        </el-form-item>
        <el-form-item label="项目简介">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveProject">保存</el-button>
      </template>
    </el-dialog>

    <!-- 审批流配置对话框 -->
    <el-dialog v-model="flowDialogVisible" title="配置审批流" width="500px">
      <el-alert type="info" :closable="false" style="margin-bottom:12px">
        配置此项目的审批步骤顺序，保存后生效。
      </el-alert>
      <div v-for="(step, idx) in flowSteps" :key="idx" class="flow-row">
        <span class="step-label">第 {{ idx + 1 }} 步</span>
        <el-select v-model="step.approver_id" placeholder="选择审批人" style="flex:1">
          <el-option
            v-for="t in teachers"
            :key="t.id" :label="t.full_name || t.username" :value="t.id"
          />
        </el-select>
        <el-button icon="Delete" link type="danger" @click="flowSteps.splice(idx, 1)" />
      </div>
      <el-button style="margin-top:8px" icon="Plus" @click="flowSteps.push({ approver_id: null, step: flowSteps.length + 1 })">
        添加审批步骤
      </el-button>
      <template #footer>
        <el-button @click="flowDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveFlows">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import http from '@/api/index'
import type { ProjectOut, UserBrief } from '@/types'

const loading = ref(false)
const saving = ref(false)
const list = ref<ProjectOut[]>([])
const teachers = ref<UserBrief[]>([])
const dialogVisible = ref(false)
const flowDialogVisible = ref(false)
const editingProject = ref<ProjectOut | null>(null)
const flowProject = ref<ProjectOut | null>(null)
const flowSteps = ref<{ approver_id: number | null; step: number }[]>([])
const formRef = ref<FormInstance>()

const form = reactive({ name: '', code: '', budget: undefined as number | undefined, description: '' })
const rules: FormRules = {
  name: [{ required: true, message: '请输入项目名称' }],
  code: [{ required: true, message: '请输入项目编号' }],
}

async function loadData() {
  loading.value = true
  try {
    const res = await http.get('/projects', { params: { page_size: 100 } })
    list.value = res.data.data.items
  } finally { loading.value = false }
}

async function loadTeachers() {
  if (teachers.value.length) return
  const res = await http.get('/users/teachers')
  teachers.value = res.data.data
}

function openCreateDialog() {
  editingProject.value = null
  Object.assign(form, { name: '', code: '', budget: undefined, description: '' })
  dialogVisible.value = true
}

function openEditDialog(proj: ProjectOut) {
  editingProject.value = proj
  Object.assign(form, { name: proj.name, code: proj.code, budget: proj.budget, description: proj.description })
  dialogVisible.value = true
}

async function openFlowDialog(proj: ProjectOut) {
  flowProject.value = proj
  await loadTeachers()
  flowSteps.value = proj.approval_flows.map((f) => ({ approver_id: f.approver.id, step: f.step }))
  flowDialogVisible.value = true
}

async function saveProject() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editingProject.value) {
      await http.put(`/projects/${editingProject.value.id}`, form)
    } else {
      await http.post('/projects', { ...form, approval_steps: [] })
    }
    ElMessage.success('已保存')
    dialogVisible.value = false
    loadData()
  } finally { saving.value = false }
}

async function saveFlows() {
  if (!flowProject.value) return
  saving.value = true
  try {
    const steps = flowSteps.value
      .filter((s) => s.approver_id)
      .map((s, idx) => ({ approver_id: s.approver_id as number, step: idx + 1 }))
    await http.put(`/projects/${flowProject.value.id}/flows`, steps)
    ElMessage.success('审批流已更新')
    flowDialogVisible.value = false
    loadData()
  } finally { saving.value = false }
}

async function toggleActive(proj: ProjectOut) {
  await http.put(`/projects/${proj.id}`, { is_active: !proj.is_active })
  ElMessage.success(proj.is_active ? '已禁用' : '已启用')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.page { max-width: 1200px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; }
.project-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.project-card :deep(.el-card__body) { padding: 14px 16px 8px; }
.card-header { display: flex; align-items: center; justify-content: space-between; }
.proj-name { font-weight: 600; font-size: 15px; }
.card-actions { display: flex; gap: 6px; justify-content: flex-end; margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--el-border-color-lighter); }
.tip-text { color: var(--el-text-color-secondary); font-size: 13px; }
.flow-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.step-label { flex-shrink: 0; font-size: 13px; width: 50px; }
</style>
