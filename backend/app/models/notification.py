"""
通知模型
站内通知，支持已读/未读状态，点击可跳转到关联资源。
"""

import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class NotificationType(str, enum.Enum):
    """通知类型"""
    SUBMITTED = "submitted"         # 提交成功（发给申请人）
    APPROVED = "approved"           # 审批通过（发给申请人）
    REJECTED = "rejected"           # 审批驳回（发给申请人）
    NEW_PENDING = "new_pending"     # 新待审批（发给审批人）
    OCR_DONE = "ocr_done"           # OCR 识别完成（发给申请人）
    AI_DONE = "ai_done"             # AI 提取完成（发给申请人）
    REMINDER = "reminder"           # 超时催办提醒（发给审批人）
    ANNOUNCEMENT = "announcement"   # 系统公告（全员）


class Notification(Base, TimestampMixin):
    """通知表"""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="通知ID")
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, comment="接收用户ID"
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, native_enum=False),
        comment="通知类型"
    )
    title: Mapped[str] = mapped_column(String(128), comment="通知标题")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="通知正文")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True, comment="是否已读")

    # 点击跳转目标
    related_type: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="关联资源类型，如 reimbursement")
    related_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="关联资源ID")

    # ─── 关联 ──────────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="notifications")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Notification id={self.id} type={self.type} user={self.user_id} read={self.is_read}>"
