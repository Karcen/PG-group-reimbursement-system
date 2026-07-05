"""
发票/票据模型
一个报销申请可含多张发票，每张发票对应 PDF 中的一页。
同时保留 OCR 原始值和人工修改值，方便后续对比和重新识别。
"""

import enum

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class DocumentType(str, enum.Enum):
    """票据类型枚举（与 AI 提取结果对应）"""
    VAT_ELECTRONIC = "vat_electronic"    # 增值税电子发票
    VAT_PAPER = "vat_paper"              # 增值税纸质发票
    RAILWAY_TICKET = "railway_ticket"    # 铁路电子客票
    AIRLINE = "airline"                  # 航空电子行程单
    HOTEL = "hotel"                      # 酒店发票
    TAXI = "taxi"                        # 出租车发票
    PARKING = "parking"                  # 停车收据
    TOLL = "toll"                        # 过路费收据
    RECEIPT = "receipt"                  # 通用收据
    UNKNOWN = "unknown"                  # 未识别类型


class Invoice(Base, TimestampMixin):
    """
    发票/票据表
    每条记录对应 PDF 的一页或一个独立票据单元。
    """

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="发票ID")
    reimbursement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("reimbursements.id", ondelete="CASCADE"), index=True,
        comment="所属报销申请ID"
    )
    file_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("uploaded_files.id", ondelete="SET NULL"), nullable=True,
        comment="来源文件ID"
    )
    page_number: Mapped[int] = mapped_column(Integer, default=1, comment="在源 PDF 中的页码（从1开始）")

    # ─── 票据类型 ──────────────────────────────────────────────────────────
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, native_enum=False),
        default=DocumentType.UNKNOWN,
        comment="AI 识别的票据类型",
    )

    # ─── OCR / AI 提取字段（人工修改前的原始值） ────────────────────────────
    ocr_invoice_number: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="OCR识别：发票号码")
    ocr_invoice_code: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="OCR识别：发票代码")
    ocr_amount: Mapped[float | None] = mapped_column(Float, nullable=True, comment="OCR识别：金额（元）")
    ocr_tax: Mapped[float | None] = mapped_column(Float, nullable=True, comment="OCR识别：税额（元）")
    ocr_date: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="OCR识别：开票日期")
    ocr_seller: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="OCR识别：销售方名称")
    ocr_buyer: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="OCR识别：购买方名称")
    ocr_passenger: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="OCR识别：乘客姓名（客票）")
    ocr_departure: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="OCR识别：出发地")
    ocr_destination: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="OCR识别：目的地")
    ocr_ticket_number: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="OCR识别：票号")
    ocr_confidence: Mapped[float] = mapped_column(Float, default=0.0, comment="AI识别置信度（0~1）")
    ocr_raw_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="PaddleOCR 原始识别文本")
    ai_raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment="Ollama 返回的原始 JSON")

    # ─── 人工修改后的字段（如与 ocr_* 相同则未修改） ───────────────────────
    invoice_number: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="（人工确认）发票号码")
    invoice_code: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="（人工确认）发票代码")
    amount: Mapped[float | None] = mapped_column(Float, nullable=True, comment="（人工确认）金额（元）")
    tax: Mapped[float | None] = mapped_column(Float, nullable=True, comment="（人工确认）税额（元）")
    date: Mapped[str | None] = mapped_column(String(32), nullable=True, comment="（人工确认）开票日期")
    seller: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="（人工确认）销售方名称")
    buyer: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="（人工确认）购买方名称")
    passenger: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="（人工确认）乘客姓名")
    departure: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="（人工确认）出发地")
    destination: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="（人工确认）目的地")
    ticket_number: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="（人工确认）票号")
    is_manually_edited: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否经过人工修改")

    # ─── 预览图路径 ────────────────────────────────────────────────────────
    preview_image_path: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="页面预览图路径")
    thumbnail_path: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="缩略图路径")

    # ─── 关联 ──────────────────────────────────────────────────────────────
    reimbursement: Mapped["Reimbursement"] = relationship(  # noqa: F821
        "Reimbursement", back_populates="invoices"
    )
    source_file: Mapped["UploadedFile"] = relationship(  # noqa: F821
        "UploadedFile", back_populates="invoices"
    )
    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        "Tag", secondary="invoice_tags", back_populates="invoices"
    )

    def __repr__(self) -> str:
        return f"<Invoice id={self.id} type={self.document_type} amount={self.amount}>"
