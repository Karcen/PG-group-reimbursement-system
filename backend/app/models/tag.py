"""
标签模型
支持给发票打标签（差旅、会议、耗材、办公、出版等），方便检索和统计。
"""

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Tag(Base, TimestampMixin):
    """发票标签表"""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="标签ID")
    name: Mapped[str] = mapped_column(String(32), unique=True, comment="标签名称，如：差旅、会议")
    color: Mapped[str] = mapped_column(String(16), default="#409EFF", comment="标签颜色（十六进制色值）")
    description: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="标签说明")

    # ─── 关联 ──────────────────────────────────────────────────────────────
    invoices: Mapped[list["Invoice"]] = relationship(  # noqa: F821
        "Invoice", secondary="invoice_tags", back_populates="tags"
    )

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name}>"


class InvoiceTag(Base):
    """发票-标签关联表（多对多中间表）"""

    __tablename__ = "invoice_tags"

    invoice_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("invoices.id", ondelete="CASCADE"), primary_key=True, comment="发票ID"
    )
    tag_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True, comment="标签ID"
    )
