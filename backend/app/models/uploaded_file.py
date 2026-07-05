"""
上传文件模型
用户每次上传 PDF 均生成一条记录，以 UUID 作为唯一标识。
原始文件路径永久不变，OCR/预览图单独存储，不影响原文件。
"""

import uuid as uuid_lib

from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class UploadedFile(Base, TimestampMixin):
    """
    上传文件表
    每次上传保存一条记录，文件以 UUID 命名存入 storage/original/。
    系统永远不修改此目录下的文件。
    """

    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="文件ID")
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid_lib.uuid4()),
        comment="文件唯一标识（UUID4），用于构造存储路径",
    )
    original_filename: Mapped[str] = mapped_column(String(256), comment="用户上传时的原始文件名（仅用于展示）")
    file_path: Mapped[str] = mapped_column(String(512), comment="原始文件在服务器上的绝对路径")
    file_size: Mapped[int] = mapped_column(BigInteger, comment="文件大小（字节）")
    mime_type: Mapped[str] = mapped_column(String(64), comment="MIME 类型，如 application/pdf")
    page_count: Mapped[int] = mapped_column(Integer, default=0, comment="PDF 页数（上传后异步填充）")
    uploader_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="上传用户ID"
    )

    # ─── 关联 ──────────────────────────────────────────────────────────────
    uploader: Mapped["User"] = relationship("User")  # noqa: F821
    invoices: Mapped[list["Invoice"]] = relationship(  # noqa: F821
        "Invoice", back_populates="source_file"
    )

    def __repr__(self) -> str:
        return f"<UploadedFile uuid={self.uuid} name={self.original_filename}>"
