"""
审批记录模型
记录每一步审批的动作（通过/驳回）、审批人和意见。
审批记录只增不改，形成完整的审批历史。
"""

import enum

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class ApprovalAction(str, enum.Enum):
    """审批动作"""
    APPROVE = "approve"   # 通过
    REJECT = "reject"     # 驳回
    RECALL = "recall"     # 撤回（申请人操作）


class ApprovalRecord(Base, TimestampMixin):
    """
    审批操作记录表
    每次审批动作（通过/驳回/撤回）均创建一条记录，不可修改。
    """

    __tablename__ = "approval_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="记录ID")
    reimbursement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reimbursements.id", ondelete="CASCADE"), index=True,
        comment="关联报销申请ID"
    )
    operator_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), comment="操作人用户ID"
    )
    action: Mapped[ApprovalAction] = mapped_column(
        Enum(ApprovalAction, native_enum=False),
        comment="审批动作"
    )
    step: Mapped[int] = mapped_column(Integer, default=1, comment="操作发生时的审批步骤号")
    comment: Mapped[str | None] = mapped_column(Text, nullable=True, comment="审批意见/驳回原因")
    from_status: Mapped[str] = mapped_column(String(32), comment="操作前状态")
    to_status: Mapped[str] = mapped_column(String(32), comment="操作后状态")

    # ─── 关联 ──────────────────────────────────────────────────────────────
    reimbursement: Mapped["Reimbursement"] = relationship(  # noqa: F821
        "Reimbursement", back_populates="approval_records"
    )
    operator: Mapped["User"] = relationship("User")  # noqa: F821

    def __repr__(self) -> str:
        return f"<ApprovalRecord id={self.id} action={self.action} step={self.step}>"
