"""
发票/票据相关 Pydantic Schema
"""

from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.invoice import DocumentType


class InvoiceOcrResult(BaseModel):
    """AI/OCR 提取结果（对应 Ollama 返回的 JSON 结构）"""
    document_type: str = Field(default="unknown")
    invoice_number: Optional[str] = None
    invoice_code: Optional[str] = None
    amount: Optional[float] = None
    tax: Optional[float] = None
    date: Optional[str] = None
    seller: Optional[str] = None
    buyer: Optional[str] = None
    passenger: Optional[str] = None
    departure: Optional[str] = None
    destination: Optional[str] = None
    ticket_number: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0, le=1)


class InvoiceManualEdit(BaseModel):
    """人工修改发票信息请求"""
    document_type: Optional[DocumentType] = None
    invoice_number: Optional[str] = Field(default=None, max_length=64)
    invoice_code: Optional[str] = Field(default=None, max_length=32)
    amount: Optional[float] = Field(default=None, ge=0)
    tax: Optional[float] = Field(default=None, ge=0)
    date: Optional[str] = Field(default=None, max_length=32)
    seller: Optional[str] = Field(default=None, max_length=128)
    buyer: Optional[str] = Field(default=None, max_length=128)
    passenger: Optional[str] = Field(default=None, max_length=64)
    departure: Optional[str] = Field(default=None, max_length=64)
    destination: Optional[str] = Field(default=None, max_length=64)
    ticket_number: Optional[str] = Field(default=None, max_length=64)
    tag_ids: Optional[list[int]] = Field(default=None, description="标签ID列表")


class TagOut(BaseModel):
    """标签响应"""
    id: int
    name: str
    color: str
    description: Optional[str]

    model_config = {"from_attributes": True}


class InvoiceOut(BaseModel):
    """发票详情响应（包含 OCR 原始值和人工确认值）"""
    id: int
    reimbursement_id: int
    page_number: int
    document_type: DocumentType
    # 人工确认字段
    invoice_number: Optional[str]
    invoice_code: Optional[str]
    amount: Optional[float]
    tax: Optional[float]
    date: Optional[str]
    seller: Optional[str]
    buyer: Optional[str]
    passenger: Optional[str]
    departure: Optional[str]
    destination: Optional[str]
    ticket_number: Optional[str]
    is_manually_edited: bool
    # OCR 原始字段
    ocr_invoice_number: Optional[str]
    ocr_amount: Optional[float]
    ocr_date: Optional[str]
    ocr_confidence: float
    ocr_raw_text: Optional[str]
    ai_raw_json: Optional[Any]
    # 预览图
    preview_image_path: Optional[str]
    thumbnail_path: Optional[str]
    # 标签
    tags: list[TagOut] = []

    model_config = {"from_attributes": True}


class InvoiceListItem(BaseModel):
    """发票列表条目（省略原始 OCR 数据）"""
    id: int
    reimbursement_id: int
    page_number: int
    document_type: DocumentType
    invoice_number: Optional[str]
    amount: Optional[float]
    date: Optional[str]
    seller: Optional[str]
    is_manually_edited: bool
    tags: list[TagOut] = []

    model_config = {"from_attributes": True}
