"""
审计日志模型
记录系统中所有关键操作，不可修改，管理员可查询和导出。
"""

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class AuditLog(Base, TimestampMixin):
    """
    审计日志表
    每次关键操作（登录、上传、审批、修改等）均写入一条记录。
    记录一旦写入，禁止任何代码对其进行 UPDATE 或 DELETE 操作。
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="日志ID")

    # ─── 操作者信息 ────────────────────────────────────────────────────────
    user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
        index=True, comment="操作用户ID（未登录时为 NULL）"
    )
    username: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="操作用户名（冗余，防止用户删除后丢失）")
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="客户端 IP 地址")
    user_agent: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="浏览器 User-Agent")

    # ─── 操作描述 ──────────────────────────────────────────────────────────
    action: Mapped[str] = mapped_column(String(64), index=True, comment="操作类型，如：LOGIN, UPLOAD_PDF, APPROVE")
    action_desc: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="操作描述（中文）")

    # ─── 操作对象 ──────────────────────────────────────────────────────────
    target_type: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="操作对象类型，如：reimbursement, user")
    target_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="操作对象ID")

    # ─── 操作前后数据 ──────────────────────────────────────────────────────
    old_data: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="操作前数据快照（JSON）")
    new_data: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="操作后数据快照（JSON）")

    # ─── 操作结果 ──────────────────────────────────────────────────────────
    is_success: Mapped[bool] = mapped_column(default=True, comment="操作是否成功")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="失败时的错误信息")

    # ─── 关联 ──────────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User")  # noqa: F821

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action} user={self.username}>"
