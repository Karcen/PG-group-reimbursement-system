"""
用户模型
角色分为：学生（student）、教师（teacher）、管理员（admin）。
密码字段存储 bcrypt 哈希值，永远不存明文。
"""

import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    STUDENT = "student"   # 学生：提交报销
    TEACHER = "teacher"   # 教师：审批报销
    ADMIN = "admin"       # 管理员：系统管理


class User(Base, TimestampMixin):
    """用户表"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="用户ID")
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, comment="用户名（登录用）")
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True, comment="邮箱")
    hashed_password: Mapped[str] = mapped_column(String(128), comment="bcrypt 哈希密码")
    full_name: Mapped[str] = mapped_column(String(64), default="", comment="真实姓名")
    student_id: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="学号/工号")
    department: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="所属部门/课题组")
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False),
        default=UserRole.STUDENT,
        comment="用户角色",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    avatar_url: Mapped[str | None] = mapped_column(String(256), nullable=True, comment="头像 URL")

    # ─── 关联 ──────────────────────────────────────────────────────────────
    # 该用户提交的报销申请
    reimbursements: Mapped[list["Reimbursement"]] = relationship(  # noqa: F821
        "Reimbursement", back_populates="applicant", foreign_keys="Reimbursement.applicant_id"
    )
    # 该用户收到的通知
    notifications: Mapped[list["Notification"]] = relationship(  # noqa: F821
        "Notification", back_populates="user"
    )
    # 该用户（教师）负责审批的审批流配置
    approval_flows: Mapped[list["ApprovalFlow"]] = relationship(  # noqa: F821
        "ApprovalFlow", back_populates="approver"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} role={self.role}>"
