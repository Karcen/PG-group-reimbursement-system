"""OCR 模块包初始化"""
from app.ocr.pdf_processor import PDFProcessor, PageImage
from app.ocr.paddle_ocr import PaddleOCRWrapper, get_ocr

__all__ = ["PDFProcessor", "PageImage", "PaddleOCRWrapper", "get_ocr"]
