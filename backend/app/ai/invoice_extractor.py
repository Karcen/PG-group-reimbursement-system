"""
发票信息提取器
整合 PDF 处理 → PaddleOCR → Ollama AI，实现完整的发票识别流水线。
每个 PDF 页面独立处理，支持一个 PDF 包含多张不同类型票据。
"""

import json
from pathlib import Path
from typing import NamedTuple, Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ollama_client import get_ollama_client
from app.ai.prompts import build_extraction_prompt
from app.core.config import settings
from app.models.invoice import DocumentType, Invoice
from app.models.uploaded_file import UploadedFile
from app.ocr.paddle_ocr import get_ocr
from app.ocr.pdf_processor import PDFProcessor, PageImage


class ExtractionResult(NamedTuple):
    """单页票据提取结果"""
    page_number: int
    ocr_text: str
    ocr_confidence: float
    ai_result: dict          # Ollama 返回的原始 JSON
    document_type: DocumentType
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
    confidence: float
    preview_image_path: Optional[str]
    thumbnail_path: Optional[str]


class InvoiceExtractor:
    """
    发票信息提取器
    对外提供 extract_from_file() 方法，内部协调 PDF → OCR → AI 的完整流程。
    """

    def __init__(self) -> None:
        self._pdf_processor = PDFProcessor(
            preview_dir=settings.storage_preview,
            thumbnail_dir=settings.storage_thumbnails,
        )
        self._ocr = get_ocr()
        self._ai = get_ollama_client()

    async def extract_from_file(
        self, uploaded_file: UploadedFile
    ) -> list[ExtractionResult]:
        """
        处理一个上传文件，返回每页的提取结果列表。

        :param uploaded_file: 数据库中的 UploadedFile 记录
        :return: 按页码排序的提取结果列表
        """
        pdf_path = Path(uploaded_file.file_path)
        if not pdf_path.exists():
            logger.error(f"PDF 文件不存在：{pdf_path}")
            return []

        logger.info(f"开始处理文件：{uploaded_file.original_filename}（UUID: {uploaded_file.uuid}）")

        # Step 1: 将 PDF 每页转换为图像
        pages: list[PageImage] = self._pdf_processor.extract_all_pages(
            pdf_path=pdf_path, file_uuid=uploaded_file.uuid
        )
        logger.info(f"PDF 页数：{len(pages)}")

        results: list[ExtractionResult] = []

        for page in pages:
            result = await self._process_page(page)
            if result:
                results.append(result)

        return results

    async def _process_page(self, page: PageImage) -> Optional[ExtractionResult]:
        """处理单页：OCR 识别 + AI 提取"""
        # Step 2: PaddleOCR 识别
        try:
            ocr_text, ocr_confidence = self._ocr.recognize(page.preview_path)
        except Exception as e:
            logger.error(f"第 {page.page_number} 页 OCR 识别失败：{e}")
            ocr_text = page.text  # 回退到 PyMuPDF 提取的纯文本
            ocr_confidence = 0.0

        # 如果 OCR 结果为空，尝试使用 PyMuPDF 的文本
        if not ocr_text.strip() and page.text:
            ocr_text = page.text
            logger.debug(f"第 {page.page_number} 页 OCR 无结果，使用 PyMuPDF 文本")

        if not ocr_text.strip():
            logger.warning(f"第 {page.page_number} 页无法提取文字（可能是图片或空白页）")
            return ExtractionResult(
                page_number=page.page_number,
                ocr_text="",
                ocr_confidence=0.0,
                ai_result={},
                document_type=DocumentType.UNKNOWN,
                invoice_number=None,
                invoice_code=None,
                amount=None,
                tax=None,
                date=None,
                seller=None,
                buyer=None,
                passenger=None,
                departure=None,
                destination=None,
                ticket_number=None,
                confidence=0.0,
                preview_image_path=str(page.preview_path),
                thumbnail_path=str(page.thumbnail_path),
            )

        # Step 3: Ollama AI 信息提取
        try:
            prompt = build_extraction_prompt(ocr_text)
            ai_result = await self._ai.extract_json(prompt)
        except Exception as e:
            logger.error(f"第 {page.page_number} 页 AI 提取失败：{e}")
            ai_result = {"document_type": "unknown", "confidence": 0.0}

        # 解析 AI 返回字段
        doc_type_str = ai_result.get("document_type", "unknown")
        try:
            document_type = DocumentType(doc_type_str)
        except ValueError:
            document_type = DocumentType.UNKNOWN

        def _to_float(val) -> Optional[float]:
            try:
                return float(val) if val is not None else None
            except (ValueError, TypeError):
                return None

        return ExtractionResult(
            page_number=page.page_number,
            ocr_text=ocr_text,
            ocr_confidence=ocr_confidence,
            ai_result=ai_result,
            document_type=document_type,
            invoice_number=ai_result.get("invoice_number"),
            invoice_code=ai_result.get("invoice_code"),
            amount=_to_float(ai_result.get("amount")),
            tax=_to_float(ai_result.get("tax")),
            date=ai_result.get("date"),
            seller=ai_result.get("seller"),
            buyer=ai_result.get("buyer"),
            passenger=ai_result.get("passenger"),
            departure=ai_result.get("departure"),
            destination=ai_result.get("destination"),
            ticket_number=ai_result.get("ticket_number"),
            confidence=float(ai_result.get("confidence", 0.0) or 0.0),
            preview_image_path=str(page.preview_path),
            thumbnail_path=str(page.thumbnail_path),
        )


def result_to_invoice(result: ExtractionResult, reimbursement_id: int, file_id: int) -> Invoice:
    """
    将提取结果转换为 Invoice ORM 对象（未持久化，由调用方负责 add + flush）。
    OCR 原始值和人工确认值初始相同，人工修改后通过 is_manually_edited 区分。
    """
    invoice = Invoice(
        reimbursement_id=reimbursement_id,
        file_id=file_id,
        page_number=result.page_number,
        document_type=result.document_type,
        # OCR 原始值
        ocr_invoice_number=result.invoice_number,
        ocr_invoice_code=result.invoice_code,
        ocr_amount=result.amount,
        ocr_tax=result.tax,
        ocr_date=result.date,
        ocr_seller=result.seller,
        ocr_buyer=result.buyer,
        ocr_passenger=result.passenger,
        ocr_departure=result.departure,
        ocr_destination=result.destination,
        ocr_ticket_number=result.ticket_number,
        ocr_confidence=result.ocr_confidence,
        ocr_raw_text=result.ocr_text,
        ai_raw_json=result.ai_result,
        # 人工确认值（初始与 OCR 值相同）
        invoice_number=result.invoice_number,
        invoice_code=result.invoice_code,
        amount=result.amount,
        tax=result.tax,
        date=result.date,
        seller=result.seller,
        buyer=result.buyer,
        passenger=result.passenger,
        departure=result.departure,
        destination=result.destination,
        ticket_number=result.ticket_number,
        is_manually_edited=False,
        preview_image_path=result.preview_image_path,
        thumbnail_path=result.thumbnail_path,
    )
    return invoice
