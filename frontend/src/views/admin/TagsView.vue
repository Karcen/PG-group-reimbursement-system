<template>
  <div class="page">
    <div class="page-header">
      <h2 class="page-title">标签管理</h2>
      <el-button type="primary" icon="Plus" @click="openDialog()">新增标签</el-button>
    </div>

    <el-card shadow="never">
      <div v-loading="loading" class="tag-grid">
        <div
          v-for="tag in list"
          :key="tag.id"
          class="tag-item"
        >
          <el-tag
            :color="tag.color"
            :style="{ color: getTagTextColor(tag.color), borderColor: tag.color }"
            size="large"
            class="tag-chip"
          >
            {{ tag.name }}
          </el-tag>
          <span class="tag-desc">{{ tag.description || '—' }}</span>
          <div class="tag-actions">
            <el-button link size="small" @click="openDialog(tag)">编辑</el-button>
            <el-button link size="small" type="danger" @click="deleteTag(tag.id)">删除</el-button>
          </div>
        </div>

        <div v-if="list.length === 0" class="empty-tip">
          <el-empty description="暂无标签，点击右上角添加" />
        </div>
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingTag ? '编辑标签' : '新增标签'" width="400px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="标签名称" prop="name">
          <el-input v-model="form.name" placeholder="如：差旅、会议、耗材" />
        </el-form-item>
        <el-form-item label="标签颜色" prop="color">
          <el-color-picker v-model="form.color" />
          <span style="margin-left:8px;font-size:13px;color:var(--el-text-color-secondary)">
            {{ form.color }}
          </span>
        </el-form-item>
        <el-form-item label="说明">
          <el-input v-model="form.description" placeholder="标签用途说明（选填）" />
        </el-form-item>
        <el-form-item label="预览">
          <el-tag
            :color="form.color"
            :style="{ color: getTagTextColor(form.color), borderColor: form.color }"
            size="large"
          >{{ form.name || '预览' }}</el-tag>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveTag">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import http from '@/api/index'
import type { TagOut } from '@/types'
import { getTagTextColor } from '@/utils/color'

const loading = ref(false)
const saving = ref(false)
const list = ref<TagOut[]>([])
const dialogVisible = ref(false)
const editingTag = ref<TagOut | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({ name: '', color: '#409EFF', description: '' })
const rules: FormRules = {
  name: [{ required: true, message: '请输入标签名称', trigger: 'blur' }],
  color: [{ required: true, message: '请选择颜色', trigger: 'change' }],
}

async function loadData() {
  loading.value = true
  try {
    const res = await http.get('/system/tags')
    list.value = res.data.data
  } finally {
    loading.value = false
  }
}

function openDialog(tag?: TagOut) {
  editingTag.value = tag || null
  if (tag) {
    Object.assign(form, { name: tag.name, color: tag.color, description: tag.description || '' })
  } else {
    Object.assign(form, { name: '', color: '#409EFF', description: '' })
  }
  dialogVisible.value = true
}

async function saveTag() {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    if (editingTag.value) {
      // 编辑：先删后建（简化实现）
      await http.delete(`/system/tags/${editingTag.value.id}`)
      await http.post('/system/tags', form)
    } else {
      await http.post('/system/tags', form)
    }
    ElMessage.success(editingTag.value ? '标签已更新' : '标签已创建')
    dialogVisible.value = false
    loadData()
  } finally {
    saving.value = false
  }
}

async function deleteTag(id: number) {
  await ElMessageBox.confirm('确定删除此标签吗？删除后关联发票的标签将同步移除。', '提示', {
    type: 'warning',
  })
  await http.delete(`/system/tags/${id}`)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.page { max-width: 900px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; }

.tag-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  padding: 8px 0;
}

.tag-item {
  border: 1px solid var(--el-border-color);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: box-shadow 0.2s;
}
.tag-item:hover { box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08); }

.tag-chip { align-self: flex-start; font-size: 14px; }
.tag-desc { font-size: 12px; color: var(--el-text-color-secondary); }
.tag-actions { display: flex; gap: 6px; margin-top: 4px; }
.empty-tip { grid-column: 1 / -1; }
</style>
