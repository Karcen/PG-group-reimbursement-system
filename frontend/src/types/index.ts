/**
 * 前端全局类型定义
 * 与后端 Pydantic Schema 一一对应
 */

// ─── 通用 ─────────────────────────────────────────────────────────────────

export interface ApiResponse<T> {
  success: boolean
  code: string
  message: string
  data: T
}

export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// ─── 用户 ─────────────────────────────────────────────────────────────────

export type UserRole = 'student' | 'teacher' | 'admin'

export interface UserOut {
  id: number
  username: string
  email: string
  full_name: string
  student_id: string | null
  department: string | null
  role: UserRole
  is_active: boolean
  avatar_url: string | null
  created_at: string
}

export interface UserBrief {
  id: number
  username: string
  full_name: string
  role: UserRole
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserOut
}

// ─── 经费项目 ──────────────────────────────────────────────────────────────

export interface ProjectBrief {
  id: number
  name: string
  code: string
  is_active: boolean
}

export interface ApprovalFlowStep {
  id: number
  step: number
  approver: UserBrief
  is_active: boolean
}

export interface ProjectOut {
  id: number
  name: string
  code: string
  description: string | null
  budget: number | null
  used_amount: number
  is_active: boolean
  approval_flows: ApprovalFlowStep[]
  created_at: string
}

// ─── 报销申请 ──────────────────────────────────────────────────────────────

export type ReimbursementStatus =
  | 'draft'
  | 'submitted'
  | 'reviewing'
  | 'approved'
  | 'rejected'
  | 'ready'

export const ReimbursementStatusLabel: Record<ReimbursementStatus, string> = {
  draft: '草稿',
  submitted: '已提交',
  reviewing: '审批中',
  approved: '已通过',
  rejected: '已驳回',
  ready: '待线下报销',
}

export const ReimbursementStatusType: Record<ReimbursementStatus, string> = {
  draft: 'info',
  submitted: 'warning',
  reviewing: 'warning',
  approved: 'success',
  rejected: 'danger',
  ready: 'success',
}

export interface ApprovalRecord {
  id: number
  operator: UserBrief
  action: string
  step: number
  comment: string | null
  from_status: string
  to_status: string
  created_at: string
}

export interface ReimbursementListItem {
  id: number
  uuid: string
  title: string
  status: ReimbursementStatus
  declared_amount: number
  applicant: UserBrief
  project: ProjectBrief | null
  created_at: string
  updated_at: string
}

export interface ReimbursementOut extends ReimbursementListItem {
  purpose: string | null
  funding_source: string | null
  notes: string | null
  ocr_total_amount: number
  current_step: number
  approval_records: ApprovalRecord[]
  invoices?: InvoiceListItem[]
}

// ─── 发票 ─────────────────────────────────────────────────────────────────

export type DocumentType =
  | 'vat_electronic'
  | 'vat_paper'
  | 'railway_ticket'
  | 'airline'
  | 'hotel'
  | 'taxi'
  | 'parking'
  | 'toll'
  | 'receipt'
  | 'unknown'

export const DocumentTypeLabel: Record<DocumentType, string> = {
  vat_electronic: '增值税电子发票',
  vat_paper: '增值税纸质发票',
  railway_ticket: '铁路电子客票',
  airline: '航空电子行程单',
  hotel: '酒店发票',
  taxi: '出租车发票',
  parking: '停车收据',
  toll: '过路费收据',
  receipt: '通用收据',
  unknown: '未识别',
}

export interface TagOut {
  id: number
  name: string
  color: string
  description: string | null
}

export interface InvoiceListItem {
  id: number
  reimbursement_id: number
  page_number: number
  document_type: DocumentType
  invoice_number: string | null
  amount: number | null
  date: string | null
  seller: string | null
  is_manually_edited: boolean
  tags: TagOut[]
}

export interface InvoiceOut extends InvoiceListItem {
  invoice_code: string | null
  tax: number | null
  buyer: string | null
  passenger: string | null
  departure: string | null
  destination: string | null
  ticket_number: string | null
  ocr_invoice_number: string | null
  ocr_amount: number | null
  ocr_date: string | null
  ocr_confidence: number
  ocr_raw_text: string | null
  ai_raw_json: Record<string, unknown> | null
  preview_image_path: string | null
  thumbnail_path: string | null
}

// ─── 通知 ─────────────────────────────────────────────────────────────────

export type NotificationType =
  | 'submitted'
  | 'approved'
  | 'rejected'
  | 'new_pending'
  | 'ocr_done'
  | 'ai_done'
  | 'reminder'
  | 'announcement'

export interface NotificationOut {
  id: number
  type: NotificationType
  title: string
  content: string | null
  is_read: boolean
  related_type: string | null
  related_id: number | null
  created_at: string
}
