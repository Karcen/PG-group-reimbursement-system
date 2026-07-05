"""
经费项目模型
管理员预先维护项目信息（如"国家自然科学基金"），
学生提交报销时直接选择，避免手动输入导致名称不一致。
每个项目可指定独立的审批老师（通过 ApprovalFlow 表配置）。
"""

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Project(Base, TimestampMixin):
    """经费项目表"""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="项目ID")
    name: Mapped[str] = mapped_column(String(128), unique=True, comment="项目名称，如：国家自然科学基金")
    code: Mapped[str] = mapped_column(String(64), unique=True, comment="项目编号，如：2024-001")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="项目简介")
    budget: Mapped[float | None] = mapped_column(Float, nullable=True, comment="项目总预算（元），NULL 表示不限制")
    used_amount: Mapped[float] = mapped_column(Float, default=0.0, comment="已报销金额（元）")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")

    # ─── 关联 ──────────────────────────────────────────────────────────────
    # 使用此项目的报销申请
    reimbursements: Mapped[list["Reimbursement"]] = relationship(  # noqa: F821
        "Reimbursement", back_populates="project"
    )
    # 此项目的审批流配置（可配置多个审批人，按顺序审批）
    approval_flows: Mapped[list["ApprovalFlow"]] = relationship(  # noqa: F821
        "ApprovalFlow", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} code={self.code} name={self.name}>"


class ApprovalFlow(Base, TimestampMixin):
    """
    审批流配置表
    每条记录表示"某项目由某老师在第几步进行审批"。
    支持串行多级审批（step=1 → step=2 → ...）。
    """

    __tablename__ = "approval_flows"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="配置ID")
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True, comment="所属项目ID"
    )
    approver_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), comment="审批人用户ID（必须为教师或管理员）"
    )
    step: Mapped[int] = mapped_column(Integer, default=1, comment="审批顺序（从1开始，数字越小越先审批）")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用此审批步骤")

    # ─── 关联 ──────────────────────────────────────────────────────────────
    project: Mapped["Project"] = relationship("Project", back_populates="approval_flows")
    approver: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="approval_flows"
    )

    def __repr__(self) -> str:
        return f"<ApprovalFlow project={self.project_id} step={self.step} approver={self.approver_id}>"
