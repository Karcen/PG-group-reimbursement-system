"""
报销申请模型
一个申请对应一批发票（一对多），状态机驱动审批流。
"""

import enum
import uuid as uuid_lib

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class ReimbursementStatus(str, enum.Enum):
    """报销申请状态"""
    DRAFT = "draft"             # 草稿（未提交）
    SUBMITTED = "submitted"     # 已提交，等待审批
    REVIEWING = "reviewing"     # 审批中
    APPROVED = "approved"       # 已批准
    REJECTED = "rejected"       # 已驳回
    READY = "ready"             # 已批准，待线下报销


class Reimbursement(Base, TimestampMixin):
    """报销申请表"""

    __tablename__ = "reimbursements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="申请ID")
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid_lib.uuid4()),
        comment="申请唯一标识（UUID4）",
    )
    applicant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), index=True, comment="申请人用户ID"
    )
    project_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True,
        comment="关联经费项目ID"
    )
    title: Mapped[str] = mapped_column(String(256), comment="报销标题（自动生成或用户填写）")
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True, comment="报销事由（用户填写）")
    funding_source: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="经费来源（用户填写）")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True, comment="备注")

    # ─── 金额 ───────────────────────────────────────────────────────────────
    declared_amount: Mapped[float] = mapped_column(Float, default=0.0, comment="用户填写的报销金额（元）")
    ocr_total_amount: Mapped[float] = mapped_column(Float, default=0.0, comment="OCR 识别发票金额总和（元）")

    # ─── 状态 ───────────────────────────────────────────────────────────────
    status: Mapped[ReimbursementStatus] = mapped_column(
        Enum(ReimbursementStatus, native_enum=False),
        default=ReimbursementStatus.DRAFT,
        index=True,
        comment="当前审批状态",
    )
    current_step: Mapped[int] = mapped_column(Integer, default=0, comment="当前处于第几步审批（0=未提交）")

    # ─── 关联 ───────────────────────────────────────────────────────────────
    applicant: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="reimbursements", foreign_keys=[applicant_id]
    )
    project: Mapped["Project"] = relationship("Project", back_populates="reimbursements")  # noqa: F821
    invoices: Mapped[list["Invoice"]] = relationship(  # noqa: F821
        "Invoice", back_populates="reimbursement", cascade="all, delete-orphan"
    )
    approval_records: Mapped[list["ApprovalRecord"]] = relationship(  # noqa: F821
        "ApprovalRecord", back_populates="reimbursement", cascade="all, delete-orphan"
    )
    payment_records: Mapped[list["PaymentRecord"]] = relationship(  # noqa: F821
        "PaymentRecord", back_populates="reimbursement", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Reimbursement id={self.id} status={self.status} amount={self.declared_amount}>"
