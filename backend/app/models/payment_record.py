"""
付款凭证模型
当报销金额超过阈值（默认200元）时，申请人必须上传银行卡/支付宝/
微信等转账付款截图或记录。
一个报销申请可以附多条付款凭证（如分多次转账）。
"""

import enum
import uuid as uuid_lib

from sqlalchemy import BigInteger, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class PaymentType(str, enum.Enum):
    """付款方式枚举"""
    BANK = "bank"         # 银行卡转账
    ALIPAY = "alipay"     # 支付宝
    WECHAT = "wechat"     # 微信支付
    CASH = "cash"         # 现金（附收据）
    OTHER = "other"       # 其他


PAYMENT_TYPE_LABEL = {
    PaymentType.BANK: "银行卡转账",
    PaymentType.ALIPAY: "支付宝",
    PaymentType.WECHAT: "微信支付",
    PaymentType.CASH: "现金",
    PaymentType.OTHER: "其他",
}


class PaymentRecord(Base, TimestampMixin):
    """
    付款凭证表
    存储转账截图或付款记录文件，绑定到报销申请。
    文件以 UUID 命名保存到 storage/payment_records/，永不覆盖。
    """

    __tablename__ = "payment_records"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment="凭证ID"
    )
    uuid: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        default=lambda: str(uuid_lib.uuid4()),
        comment="文件唯一标识（UUID4）",
    )
    reimbursement_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("reimbursements.id", ondelete="CASCADE"),
        index=True,
        comment="关联报销申请ID",
    )
    original_filename: Mapped[str] = mapped_column(
        String(256), comment="用户上传时的原始文件名（仅展示用）"
    )
    file_path: Mapped[str] = mapped_column(
        String(512), comment="凭证文件在服务器上的绝对路径"
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger, comment="文件大小（字节）"
    )
    mime_type: Mapped[str] = mapped_column(
        String(64), comment="MIME 类型，如 image/jpeg、application/pdf"
    )
    payment_type: Mapped[PaymentType] = mapped_column(
        Enum(PaymentType, native_enum=False),
        default=PaymentType.OTHER,
        comment="付款方式",
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="凭证备注（如转账流水号、备注说明）"
    )
    uploader_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="上传人用户ID",
    )

    # ─── 关联 ──────────────────────────────────────────────────────────────
    reimbursement: Mapped["Reimbursement"] = relationship(  # noqa: F821
        "Reimbursement", back_populates="payment_records"
    )
    uploader: Mapped["User"] = relationship("User")  # noqa: F821

    def __repr__(self) -> str:
        return (
            f"<PaymentRecord id={self.id} type={self.payment_type} "
            f"reimb={self.reimbursement_id}>"
        )
