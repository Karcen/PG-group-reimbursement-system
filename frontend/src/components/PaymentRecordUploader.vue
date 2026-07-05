<template>
  <!--
    付款凭证上传/展示组件
    金额超过阈值时显示，强制要求上传至少一条付款截图。
    Props:
      reimbursement-id  - 关联报销申请的 ID
      declared-amount   - 当前填写的报销金额
      threshold         - 触发强制的金额门槛（默认 200 元）
      readonly          - 详情页只读模式，不显示上传按钮
  -->
  <div class="payment-uploader">
    <!-- 金额超过阈值时的提示横幅 -->
    <el-alert
      v-if="isRequired && !readonly"
      type="warning"
      :closable="false"
      class="threshold-alert"
    >
      <template #title>
        <el-icon style="margin-right:4px"><Warning /></el-icon>
        报销金额超过 {{ threshold }} 元，须附上付款凭证
      </template>
      <div>
        根据实验室报销规定，报销金额超过 <b>{{ threshold }} 元</b> 时，
        必须上传银行卡、支付宝或微信等转账记录截图。
        提交前请确保至少上传一条付款凭证。
      </div>
    </el-alert>

    <!-- 只读模式标题 / 上传区域标题 -->
    <div class="section-header" v-if="records.length > 0 || (isRequired && !readonly)">
      <span class="section-title">
        付款凭证
        <el-badge
          v-if="records.length > 0"
          :value="records.length"
          type="primary"
          class="count-badge"
        />
      </span>
      <el-button
        v-if="!readonly && isRequired"
        type="primary"
        size="small"
        icon="Plus"
        @click="triggerUpload"
      >
        上传凭证
      </el-button>
    </div>

    <!-- 隐藏的文件选择 input -->
    <input
      v-if="!readonly"
      ref="fileInput"
      type="file"
      accept="image/jpeg,image/png,image/gif,image/webp,application/pdf"
      style="display:none"
      @change="handleFileChange"
    />

    <!-- 已上传凭证列表 -->
    <div v-if="records.length > 0" class="records-list">
      <div
        v-for="record in records"
        :key="record.id"
        class="record-item"
      >
        <!-- 预览图或文件图标 -->
        <div class="record-preview" @click="previewRecord(record)">
          <img
            v-if="isImage(record.mime_type)"
            :src="`/api/v1/payment-records/${record.id}/file`"
            class="preview-img"
            :alt="record.original_filename"
          />
          <el-icon v-else class="file-icon" size="32"><Document /></el-icon>
        </div>

        <!-- 凭证信息 -->
        <div class="record-info">
          <div class="record-type">
            <el-tag size="small" :type="typeTagColor(record.payment_type)">
              {{ record.payment_type_label || paymentTypeLabel(record.payment_type) }}
            </el-tag>
          </div>
          <div class="record-name">{{ record.original_filename }}</div>
          <div v-if="record.description" class="record-desc">{{ record.description }}</div>
          <div class="record-size">{{ formatSize(record.file_size) }}</div>
        </div>

        <!-- 删除按钮（非只读） -->
        <el-button
          v-if="!readonly"
          link
          type="danger"
          size="small"
          icon="Delete"
          :loading="deleting === record.id"
          @click="deleteRecord(record.id)"
        />
      </div>
    </div>

    <!-- 空状态提示（金额超阈值但还没上传） -->
    <div
      v-else-if="isRequired && !readonly"
      class="empty-required"
    >
      <el-icon class="empty-icon" size="36"><Upload /></el-icon>
      <p>请点击"上传凭证"按钮添加转账截图</p>
    </div>

    <!-- 上传类型选择对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传付款凭证"
      width="400px"
      :append-to-body="true"
    >
      <el-form label-width="90px">
        <el-form-item label="付款方式">
          <el-select v-model="uploadForm.payment_type" style="width:100%">
            <el-option label="银行卡转账" value="bank" />
            <el-option label="支付宝" value="alipay" />
            <el-option label="微信支付" value="wechat" />
            <el-option label="现金" value="cash" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注说明">
          <el-input
            v-model="uploadForm.description"
            placeholder="如：流水号、交易说明等（选填）"
            maxlength="200"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="doUpload">
          确认上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 图片预览 -->
    <el-dialog
      v-model="previewVisible"
      title="凭证预览"
      width="70%"
      :append-to-body="true"
    >
      <img
        v-if="previewUrl"
        :src="previewUrl"
        style="width:100%;border-radius:6px"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/index'
import { useAuthStore } from '@/stores/auth'

// ─── Props ────────────────────────────────────────────────────────────────

const props = withDefaults(defineProps<{
  reimbursementId: number | null
  declaredAmount: number
  threshold?: number
  readonly?: boolean
}>(), {
  threshold: 200,
  readonly: false,
})

const emit = defineEmits<{
  (e: 'update:records', records: PaymentRecordItem[]): void
}>()

// ─── 类型定义 ──────────────────────────────────────────────────────────────

interface PaymentRecordItem {
  id: number
  uuid: string
  reimbursement_id: number
  original_filename: string
  file_size: number
  mime_type: string
  payment_type: string
  payment_type_label: string
  description: string | null
  created_at: string
}

// ─── 状态 ─────────────────────────────────────────────────────────────────

const authStore = useAuthStore()
const records = ref<PaymentRecordItem[]>([])
const uploading = ref(false)
const deleting = ref<number | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const pendingFile = ref<File | null>(null)
const uploadDialogVisible = ref(false)
const previewVisible = ref(false)
const previewUrl = ref('')

const uploadForm = ref({
  payment_type: 'other',
  description: '',
})

// 是否需要付款凭证
const isRequired = computed(() => props.declaredAmount > props.threshold)

// ─── 数据加载 ──────────────────────────────────────────────────────────────

async function loadRecords() {
  if (!props.reimbursementId) return
  try {
    const res = await http.get(`/payment-records/reimbursement/${props.reimbursementId}`)
    records.value = res.data.data
    emit('update:records', records.value)
  } catch {
    records.value = []
  }
}

// 当 reimbursementId 变化时重新加载
watch(() => props.reimbursementId, (newId) => {
  if (newId) loadRecords()
})

onMounted(() => {
  if (props.reimbursementId) loadRecords()
})

// ─── 上传逻辑 ──────────────────────────────────────────────────────────────

function triggerUpload() {
  fileInput.value?.click()
}

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || input.files.length === 0) return
  pendingFile.value = input.files[0]
  uploadForm.value.payment_type = 'other'
  uploadForm.value.description = ''
  uploadDialogVisible.value = true
  // 清空 input 以便再次选同一文件
  input.value = ''
}

async function doUpload() {
  if (!pendingFile.value || !props.reimbursementId) return
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('reimbursement_id', String(props.reimbursementId))
    formData.append('payment_type', uploadForm.value.payment_type)
    formData.append('description', uploadForm.value.description)
    formData.append('file', pendingFile.value)

    await http.post('/payment-records/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    ElMessage.success('付款凭证上传成功')
    uploadDialogVisible.value = false
    pendingFile.value = null
    await loadRecords()
  } finally {
    uploading.value = false
  }
}

// ─── 删除逻辑 ──────────────────────────────────────────────────────────────

async function deleteRecord(id: number) {
  await ElMessageBox.confirm('确定删除此付款凭证吗？', '提示', { type: 'warning' })
  deleting.value = id
  try {
    await http.delete(`/payment-records/${id}`)
    records.value = records.value.filter((r) => r.id !== id)
    emit('update:records', records.value)
    ElMessage.success('凭证已删除')
  } finally {
    deleting.value = null
  }
}

// ─── 预览 ─────────────────────────────────────────────────────────────────

function previewRecord(record: PaymentRecordItem) {
  if (isImage(record.mime_type)) {
    previewUrl.value = `/api/v1/payment-records/${record.id}/file`
    previewVisible.value = true
  } else {
    // PDF 在新标签页打开
    window.open(`/api/v1/payment-records/${record.id}/file`, '_blank')
  }
}

// ─── 工具函数 ──────────────────────────────────────────────────────────────

function isImage(mimeType: string): boolean {
  return mimeType.startsWith('image/')
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

const PAYMENT_TYPE_LABELS: Record<string, string> = {
  bank: '银行卡转账',
  alipay: '支付宝',
  wechat: '微信支付',
  cash: '现金',
  other: '其他',
}
function paymentTypeLabel(type: string): string {
  return PAYMENT_TYPE_LABELS[type] || type
}
function typeTagColor(type: string): 'success' | 'primary' | 'warning' | 'info' | 'danger' {
  const map: Record<string, 'success' | 'primary' | 'warning' | 'info' | 'danger'> = {
    bank: 'success',
    alipay: 'primary',
    wechat: 'success',
    cash: 'warning',
    other: 'info',
  }
  return map[type] || 'info'
}

// 暴露校验方法给父组件使用
defineExpose({
  /** 返回是否满足上传要求（金额未超阈值 或 已有凭证） */
  isValid: computed(() => !isRequired.value || records.value.length > 0),
  recordCount: computed(() => records.value.length),
  reload: loadRecords,
})
</script>

<style scoped>
.payment-uploader { margin-top: 8px; }

.threshold-alert { margin-bottom: 14px; }
.threshold-alert :deep(.el-alert__title) {
  display: flex; align-items: center; font-size: 14px; font-weight: 600;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 12px 0 10px;
}
.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}
.count-badge { margin-left: 4px; }

/* 凭证列表 */
.records-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.record-item {
  width: 160px;
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color);
  transition: box-shadow 0.2s;
  position: relative;
}
.record-item:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.1); }

.record-preview {
  width: 100%;
  height: 100px;
  background: var(--el-fill-color-light);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
}
.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.file-icon { color: var(--el-text-color-secondary); }

.record-info { padding: 8px; }
.record-type { margin-bottom: 4px; }
.record-name {
  font-size: 12px;
  color: var(--el-text-color-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.record-desc {
  font-size: 11px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.record-size {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-top: 2px;
}

.record-item :deep(.el-button) {
  position: absolute;
  top: 4px;
  right: 4px;
  background: rgba(0,0,0,0.4);
  color: white;
  border-radius: 50%;
  padding: 4px;
}

/* 空状态 */
.empty-required {
  border: 2px dashed var(--el-color-warning);
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  color: var(--el-color-warning);
  background: var(--el-color-warning-light-9);
}
.empty-icon { margin-bottom: 8px; }
.empty-required p { margin: 0; font-size: 13px; }
</style>
