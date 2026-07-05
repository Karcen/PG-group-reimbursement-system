"""
Models 包初始化
导入所有模型，确保 Alembic 能发现完整的 metadata。
所有新增模型都需要在此处导入。
"""

from app.models.approval_record import ApprovalAction, ApprovalRecord
from app.models.audit_log import AuditLog
from app.models.base import TimestampMixin
from app.models.invoice import DocumentType, Invoice
from app.models.notification import Notification, NotificationType
from app.models.payment_record import PaymentRecord, PaymentType
from app.models.project import ApprovalFlow, Project
from app.models.reimbursement import Reimbursement, ReimbursementStatus
from app.models.tag import InvoiceTag, Tag
from app.models.uploaded_file import UploadedFile
from app.models.user import User, UserRole

__all__ = [
    "User", "UserRole",
    "Project", "ApprovalFlow",
    "UploadedFile",
    "Reimbursement", "ReimbursementStatus",
    "Invoice", "DocumentType",
    "Tag", "InvoiceTag",
    "ApprovalRecord", "ApprovalAction",
    "Notification", "NotificationType",
    "AuditLog",
    "PaymentRecord", "PaymentType",
    "TimestampMixin",
]
