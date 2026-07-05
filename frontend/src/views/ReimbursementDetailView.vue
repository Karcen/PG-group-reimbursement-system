<template>
  <div class="page">
    <!-- 返回 + 标题 -->
    <div class="page-header">
      <el-button icon="ArrowLeft" link @click="$router.back()">返回</el-button>
      <h2 class="page-title">报销申请详情</h2>
      <el-tag v-if="reimb" :type="(ReimbursementStatusType[reimb.status] as any)">
        {{ ReimbursementStatusLabel[reimb.status] }}
      </el-tag>
    </div>

    <el-skeleton v-if="loading" :rows="8" animated />

    <template v-else-if="reimb">
      <!-- 基本信息 -->
      <el-card shadow="never" class="info-card">
        <template #header>
          <span>申请信息</span>
          <div class="card-actions">
            <!-- 草稿/驳回状态：可编辑和提交 -->
            <template v-if="reimb.status === 'draft' || reimb.status === 'rejected'">
              <el-button size="small" icon="Edit" @click="showEditDialog = true">编辑</el-button>
              <el-button size="small" type="primary" icon="Promotion" @click="showSubmitDialog = true">
                提交审批
              </el-button>
            </template>
            <!-- 已提交/审批中：可撤回 -->
            <el-button
              v-if="reimb.status === 'submitted' || reimb.status === 'reviewing'"
              size="small" type="warning" @click="recallApplication"
            >
              撤回申请
            </el-button>
          </div>
        </template>

        <el-descriptions :column="2" border>
          <el-descriptions-item label="标题" :span="2">{{ reimb.title }}</el-descriptions-item>
          <el-descriptions-item label="申请人">
            {{ reimb.applicant.full_name || reimb.applicant.username }}
          </el-descriptions-item>
          <el-descriptions-item label="经费项目">
            {{ reimb.project ? `${reimb.project.name}（${reimb.project.code}）` : '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="报销事由" :span="2">
            {{ reimb.purpose || '—' }}
          </el-descriptions-item>
          <el-descriptions-item label="申报金额">
            <span class="amount">¥{{ reimb.declared_amount.toFixed(2) }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="识别金额">
            <span>¥{{ reimb.ocr_total_amount.toFixed(2) }}</span>
            <el-tag
              v-if="Math.abs(reimb.declared_amount - reimb.ocr_total_amount) > 1"
              type="warning" size="small" style="margin-left:6px"
            >
              差异 ¥{{ Math.abs(reimb.declared_amount - reimb.ocr_total_amount).toFixed(2) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="经费来源">{{ reimb.funding_source || '—' }}</el-descriptions-item>
          <el-descriptions-item label="提交时间">{{ formatDate(reimb.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ reimb.notes || '—' }}</el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 发票列表 -->
      <el-card shadow="never" class="invoice-card" style="margin-top:12px">
        <template #header><span>发票/票据列表</span></template>
        <div v-if="!invoices.length" class="empty-tip">暂无发票，请上传 PDF</div>
        <el-table v-else :data="invoices" border size="small">
          <el-table-column prop="page_number" label="页码" width="60" align="center" />
          <el-table-column label="票据类型" width="140">
            <template #default="{ row }">{{ DocumentTypeLabel[(row as InvoiceListItem).document_type] || (row as InvoiceListItem).document_type }}</template>
          </el-table-column>
          <el-table-column prop="invoice_number" label="发票号码" width="130" show-overflow-tooltip />
          <el-table-column prop="date" label="开票日期" width="110" />
          <el-table-column prop="seller" label="销售方" min-width="140" show-overflow-tooltip />
          <el-table-column prop="amount" label="金额（元）" width="100" align="right">
            <template #default="{ row }">{{ row.amount != null ? `¥${row.amount.toFixed(2)}` : '—' }}</template>
          </el-table-column>
          <el-table-column label="置信度" width="90" align="center">
            <template #default="{ row }">
              <el-progress
                type="dashboard"
                :percentage="Math.round(row.ocr_confidence * 100)"
                :width="40"
                :color="row.ocr_confidence > 0.7 ? '#67C23A' : '#E6A23C'"
              />
            </template>
          </el-table-column>
          <el-table-column label="标签" min-width="120">
            <template #default="{ row }">
              <el-tag
                v-for="tag in row.tags"
                :key="tag.id"
                :color="tag.color"
                :style="{ color: getTagTextColor(tag.color), borderColor: tag.color }"
                size="small"
                style="margin:2px"
              >
                {{ tag.name }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="60" fixed="right">
            <template #default="{ row }">
              <el-button link size="small" @click="previewInvoice(row as InvoiceListItem)">预览</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 付款凭证区块 -->
      <el-card shadow="never" style="margin-top:12px">
        <template #header>
          <span>付款凭证</span>
          <el-text
            v-if="reimb.declared_amount > PAYMENT_THRESHOLD"
            type="warning"
            size="small"
            style="margin-left:8px"
          >
            （金额超过 {{ PAYMENT_THRESHOLD }} 元，提交时须附凭证）
          </el-text>
        </template>
        <PaymentRecordUploader
          :reimbursement-id="reimb.id"
          :declared-amount="reimb.declared_amount"
          :threshold="PAYMENT_THRESHOLD"
          :readonly="reimb.status !== 'draft' && reimb.status !== 'rejected'"
        />
      </el-card>

      <!-- 审批流程 -->
      <el-card shadow="never" style="margin-top:12px" v-if="reimb.approval_records?.length">
        <template #header><span>审批记录</span></template>
        <el-timeline>
          <el-timeline-item
            v-for="record in reimb.approval_records"
            :key="record.id"
            :type="record.action === 'approve' ? 'success' : (record.action === 'reject' ? 'danger' : 'info')"
            :timestamp="formatDate(record.created_at)"
          >
            <div class="timeline-content">
              <span class="actor">{{ record.operator.full_name || record.operator.username }}</span>
              <el-tag :type="record.action === 'approve' ? 'success' : 'danger'" size="small">
                {{ record.action === 'approve' ? '审批通过' : (record.action === 'reject' ? '审批驳回' : '撤回') }}
              </el-tag>
              <p v-if="record.comment" class="comment">{{ record.comment }}</p>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>

      <!-- 教师审批操作 -->
      <el-card
        v-if="canApprove"
        shadow="never"
        style="margin-top:12px"
      >
        <template #header><span>审批操作</span></template>
        <el-form :model="approvalForm" label-width="80px">
          <el-form-item label="审批意见">
            <el-input v-model="approvalForm.comment" type="textarea" :rows="3" placeholder="请填写审批意见（驳回时必填）" />
          </el-form-item>
          <el-form-item>
            <el-button type="success" icon="Check" @click="approve" :loading="approving">审批通过</el-button>
            <el-button type="danger" icon="Close" @click="reject" :loading="approving">审批驳回</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </template>

    <!-- 图片预览对话框 -->
    <el-dialog v-model="previewVisible" title="发票预览" width="70%" :append-to-body="true">
      <img v-if="previewUrl" :src="previewUrl" style="width:100%;border-radius:4px" />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import http from '@/api/index'
import { useAuthStore } from '@/stores/auth'
import {
  DocumentTypeLabel, ReimbursementStatusLabel, ReimbursementStatusType,
  type ReimbursementOut, type InvoiceListItem,
} from '@/types'
import PaymentRecordUploader from '@/components/PaymentRecordUploader.vue'
import { getTagTextColor } from '@/utils/color'

// 与后端配置保持一致的金额阈值
const PAYMENT_THRESHOLD = 200

const route = useRoute()
const authStore = useAuthStore()
const reimb = ref<ReimbursementOut | null>(null)
const invoices = ref<InvoiceListItem[]>([])
const loading = ref(true)
const approving = ref(false)
const approvalForm = ref({ comment: '' })
const previewVisible = ref(false)
const previewUrl = ref('')
const showEditDialog = ref(false)
const showSubmitDialog = ref(false)

const reimb_id = route.params.id as string

// 是否有审批权限
const canApprove = computed(() => {
  if (!reimb.value) return false
  return (
    authStore.isTeacher &&
    (reimb.value.status === 'submitted' || reimb.value.status === 'reviewing')
  )
})

async function loadData() {
  loading.value = true
  try {
    const res = await http.get(`/reimbursements/${reimb_id}`)
    reimb.value = res.data.data
    const invRes = await http.get(`/invoices/reimbursement/${reimb_id}`)
    invoices.value = invRes.data.data
  } finally {
    loading.value = false
  }
}

async function approve() {
  approving.value = true
  try {
    await http.post(`/approvals/${reimb_id}/approve`, { comment: approvalForm.value.comment })
    ElMessage.success('已审批通过')
    await loadData()
  } finally {
    approving.value = false
  }
}

async function reject() {
  if (!approvalForm.value.comment) {
    ElMessage.warning('驳回时请填写审批意见')
    return
  }
  approving.value = true
  try {
    await http.post(`/approvals/${reimb_id}/reject`, { comment: approvalForm.value.comment })
    ElMessage.success('已驳回')
    await loadData()
  } finally {
    approving.value = false
  }
}

async function recallApplication() {
  await ElMessageBox.confirm('确定要撤回此申请吗？', '提示', { type: 'warning' })
  await http.post(`/reimbursements/${reimb_id}/recall`)
  ElMessage.success('已撤回')
  await loadData()
}

function previewInvoice(invoice: InvoiceListItem) {
  previewUrl.value = `/api/v1/invoices/${invoice.id}/preview-image`
  previewVisible.value = true
}

function formatDate(str: string) { return dayjs(str).format('YYYY-MM-DD HH:mm') }

onMounted(loadData)
</script>

<style scoped>
.page { max-width: 1000px; }
.page-header { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.page-title { margin: 0; font-size: 20px; font-weight: 600; flex: 1; }
.card-actions { display: flex; gap: 8px; }
.amount { font-size: 18px; font-weight: 700; color: var(--el-color-primary); }
.empty-tip { text-align: center; padding: 24px; color: var(--el-text-color-secondary); }
.timeline-content { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.actor { font-weight: 600; }
.comment { width: 100%; margin: 4px 0 0; color: var(--el-text-color-secondary); font-size: 13px; }
</style>
