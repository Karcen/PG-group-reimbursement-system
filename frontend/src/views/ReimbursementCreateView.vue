<template>
  <div class="page">
    <div class="page-header">
      <el-button icon="ArrowLeft" link @click="$router.back()">返回</el-button>
      <h2 class="page-title">新增报销申请</h2>
    </div>

    <el-steps :active="currentStep" align-center class="steps-bar" finish-status="success">
      <el-step title="上传发票" description="上传 PDF 文件" />
      <el-step title="确认信息" description="核对识别结果" />
      <el-step title="填写申请" description="完善报销信息" />
      <el-step title="提交审批" description="发送给审批老师" />
    </el-steps>

    <!-- Step 1: 上传 PDF -->
    <el-card v-if="currentStep === 0" shadow="never" class="step-card">
      <template #header>
        <span>上传发票 PDF</span>
        <el-text type="info" size="small" style="margin-left:8px">支持同时上传多页发票</el-text>
      </template>

      <el-upload
        v-model:file-list="fileList"
        drag
        :action="uploadUrl"
        :headers="uploadHeaders"
        :data="uploadData"
        :before-upload="beforeUpload"
        :on-success="onUploadSuccess"
        :on-error="onUploadError"
        accept=".pdf,image/jpeg,image/png"
        :limit="5"
        multiple
      >
        <el-icon class="el-icon--upload" size="48"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处，或 <em>点击选择文件</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 PDF、JPG、PNG，单文件最大 {{ maxUploadMB }} MB
          </div>
        </template>
      </el-upload>

      <div v-if="uploadedFileIds.length > 0" class="upload-result">
        <el-alert type="success" :closable="false">
          已上传 {{ uploadedFileIds.length }} 个文件，正在识别中...
        </el-alert>
        <el-button type="primary" style="margin-top:12px" @click="goToStep(1)">
          查看识别结果
        </el-button>
      </div>
    </el-card>

    <!-- Step 2: 确认发票信息 -->
    <el-card v-if="currentStep === 1" shadow="never" class="step-card">
      <template #header>
        <span>确认识别结果</span>
        <el-text type="info" size="small" style="margin-left:8px">
          OCR 识别完成，请核实以下信息并修正错误
        </el-text>
      </template>

      <div v-if="invoices.length === 0" class="empty-tip">
        <el-icon class="is-loading" size="20"><Loading /></el-icon>
        &nbsp; 正在识别中，请稍候...
      </div>
      <div v-else>
        <InvoiceEditCard
          v-for="inv in invoices"
          :key="inv.id"
          :invoice="inv"
          @update="refreshInvoice"
        />
      </div>

      <div class="step-footer">
        <el-button @click="currentStep = 0">上一步</el-button>
        <el-button type="primary" :disabled="invoices.length === 0" @click="goToStep(2)">
          确认，填写申请
        </el-button>
      </div>
    </el-card>

    <!-- Step 3: 填写报销信息 -->
    <el-card v-if="currentStep === 2" shadow="never" class="step-card">
      <template #header><span>填写报销申请</span></template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" style="max-width:600px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入报销标题" />
        </el-form-item>
        <el-form-item label="经费项目" prop="project_id">
          <el-select v-model="form.project_id" placeholder="请选择经费项目" style="width:100%">
            <el-option
              v-for="p in projects"
              :key="p.id" :label="`${p.name}（${p.code}）`" :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="报销事由" prop="purpose">
          <el-input v-model="form.purpose" type="textarea" :rows="3" placeholder="请描述报销事由" />
        </el-form-item>
        <el-form-item label="经费来源">
          <el-input v-model="form.funding_source" placeholder="如：国家自然科学基金" />
        </el-form-item>
        <el-form-item label="申报金额（元）" prop="declared_amount">
          <el-input-number
            v-model="form.declared_amount"
            :precision="2" :min="0" style="width:200px"
          />
          <el-text type="info" size="small" style="margin-left:8px">
            识别总金额：¥{{ ocrTotalAmount.toFixed(2) }}
          </el-text>
        </el-form-item>
        <el-form-item v-if="amountWarning" label=" ">
          <el-alert type="warning" :closable="false">{{ amountWarning }}</el-alert>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>

      <!-- 付款凭证上传区：金额超过阈值时强制显示 -->
      <el-divider v-if="form.declared_amount > PAYMENT_THRESHOLD" />
      <PaymentRecordUploader
        ref="paymentUploaderRef"
        :reimbursement-id="reimbursementId"
        :declared-amount="form.declared_amount"
        :threshold="PAYMENT_THRESHOLD"
      />

      <div class="step-footer">
        <el-button @click="currentStep = 1">上一步</el-button>
        <el-button @click="saveDraft" :loading="saving">保存草稿</el-button>
        <el-button type="primary" @click="submitApplication" :loading="submitting">
          提交审批
        </el-button>
      </div>
    </el-card>

    <!-- Step 4: 提交成功 -->
    <el-card v-if="currentStep === 3" shadow="never" class="step-card">
      <el-result icon="success" title="报销申请已提交" sub-title="您的申请已进入审批流程，请等待审批人审核。">
        <template #extra>
          <el-button type="primary" @click="$router.push('/reimbursements')">查看列表</el-button>
          <el-button @click="$router.push('/reimbursements/create')">继续新增</el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import http from '@/api/index'
import { useAuthStore } from '@/stores/auth'
import type { ProjectBrief, InvoiceListItem } from '@/types'
import PaymentRecordUploader from '@/components/PaymentRecordUploader.vue'
import { defineComponent, h } from 'vue'

// 付款凭证金额门槛（与后端配置保持一致，默认200元）
const PAYMENT_THRESHOLD = 200

const authStore = useAuthStore()
const currentStep = ref(0)
const fileList = ref([])
const uploadedFileIds = ref<number[]>([])
const reimbursementId = ref<number | null>(null)
const invoices = ref<InvoiceListItem[]>([])
const projects = ref<ProjectBrief[]>([])
const saving = ref(false)
const submitting = ref(false)
const formRef = ref<FormInstance>()
const paymentUploaderRef = ref<InstanceType<typeof PaymentRecordUploader> | null>(null)
const maxUploadMB = 50

const form = reactive({
  title: '',
  project_id: null as number | null,
  purpose: '',
  funding_source: '',
  declared_amount: 0,
  notes: '',
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  project_id: [{ required: true, message: '请选择经费项目', trigger: 'change' }],
  purpose: [{ required: true, message: '请填写报销事由', trigger: 'blur' }],
  declared_amount: [{ required: true, type: 'number', min: 0.01, message: '请填写大于0的金额', trigger: 'blur' }],
}

// OCR 发票金额总计
const ocrTotalAmount = computed(() =>
  invoices.value.reduce((sum, inv) => sum + (inv.amount ?? 0), 0)
)

// 金额差值警告
const amountWarning = computed(() => {
  const diff = Math.abs(form.declared_amount - ocrTotalAmount.value)
  if (ocrTotalAmount.value > 0 && diff > 0.01) {
    return `报销金额与识别金额相差 ¥${diff.toFixed(2)}，请确认后提交。`
  }
  return ''
})

const uploadUrl = computed(() => `/api/v1/invoices/upload`)
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${authStore.accessToken}`,
}))
const uploadData = computed(() => ({
  reimbursement_id: reimbursementId.value ?? 0,
}))

function beforeUpload(file: File) {
  const isOk = ['application/pdf', 'image/jpeg', 'image/png'].includes(file.type)
  if (!isOk) { ElMessage.error('只支持 PDF 和图片文件'); return false }
  if (file.size > maxUploadMB * 1024 * 1024) {
    ElMessage.error(`文件大小不能超过 ${maxUploadMB} MB`)
    return false
  }
  return true
}

async function onUploadSuccess(res: any) {
  if (res.success) {
    uploadedFileIds.value.push(res.data.file_id)
    // 首次上传时先创建草稿报销申请
    if (!reimbursementId.value) {
      const r = await http.post('/reimbursements', {
        title: '新报销申请（待完善）',
        declared_amount: 0,
      })
      reimbursementId.value = r.data.data.id
    }
  }
}

function onUploadError() {
  ElMessage.error('上传失败，请重试')
}

async function goToStep(step: number) {
  if (step === 1 && reimbursementId.value) {
    const res = await http.get(`/invoices/reimbursement/${reimbursementId.value}`)
    invoices.value = res.data.data
  }
  if (step === 2) {
    await loadProjects()
    form.declared_amount = ocrTotalAmount.value
    form.title = `报销申请 ${new Date().toLocaleDateString()}`
  }
  currentStep.value = step
}

async function loadProjects() {
  const res = await http.get('/projects/active')
  projects.value = res.data.data
}

async function refreshInvoice() {
  if (reimbursementId.value) {
    const res = await http.get(`/invoices/reimbursement/${reimbursementId.value}`)
    invoices.value = res.data.data
  }
}

async function saveDraft() {
  if (!reimbursementId.value) return
  saving.value = true
  try {
    await http.put(`/reimbursements/${reimbursementId.value}`, {
      title: form.title,
      purpose: form.purpose,
      project_id: form.project_id,
      funding_source: form.funding_source,
      declared_amount: form.declared_amount,
      notes: form.notes,
    })
    ElMessage.success('草稿已保存')
  } finally {
    saving.value = false
  }
}

async function submitApplication() {
  if (!formRef.value || !reimbursementId.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  // 付款凭证校验：金额超过阈值时必须已上传凭证
  if (form.declared_amount > PAYMENT_THRESHOLD) {
    const uploaderValid = paymentUploaderRef.value?.isValid
    if (!uploaderValid) {
      ElMessage.warning(
        `报销金额超过 ${PAYMENT_THRESHOLD} 元，请先上传银行卡、支付宝或微信等转账付款截图后再提交。`
      )
      return
    }
  }

  submitting.value = true
  try {
    await http.post(`/reimbursements/${reimbursementId.value}/submit`, {
      purpose: form.purpose,
      project_id: form.project_id,
      declared_amount: form.declared_amount,
    })
    currentStep.value = 3
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.page { max-width: 900px; }
.page-header { display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; }
.steps-bar { margin-bottom: 24px; }
.step-card { margin-bottom: 16px; }
.step-footer { display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; }
.empty-tip { text-align: center; padding: 40px; color: var(--el-text-color-secondary); }
.upload-result { margin-top: 16px; }
.invoice-edit-card { border: 1px solid var(--el-border-color); border-radius: 8px; padding: 12px; margin-bottom: 10px; }
</style>
