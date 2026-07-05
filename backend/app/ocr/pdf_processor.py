"""
PDF 处理模块
使用 PyMuPDF（fitz）完成：
  1. PDF 按页拆分，生成每页的预览图和缩略图
  2. 提取每页的纯文本（辅助 OCR）
  3. 统计页数

原始 PDF 始终保持不变，本模块只读取，不修改。
"""

from pathlib import Path
from typing import NamedTuple

import fitz  # PyMuPDF


class PageImage(NamedTuple):
    """单页处理结果"""
    page_number: int      # 页码（从1开始）
    preview_path: Path    # 预览图路径（高分辨率，用于 PDF 预览）
    thumbnail_path: Path  # 缩略图路径（低分辨率，用于列表展示）
    text: str             # 该页提取的纯文本（可为空）


class PDFProcessor:
    """
    PDF 处理器
    将 PDF 每页渲染成图像并保存，供 OCR 识别和前端预览使用。
    """

    # 预览图 DPI（越高图像越清晰，但文件越大）
    PREVIEW_DPI = 150
    # 缩略图 DPI
    THUMBNAIL_DPI = 72

    def __init__(self, preview_dir: Path, thumbnail_dir: Path) -> None:
        self.preview_dir = preview_dir
        self.thumbnail_dir = thumbnail_dir
        preview_dir.mkdir(parents=True, exist_ok=True)
        thumbnail_dir.mkdir(parents=True, exist_ok=True)

    def get_page_count(self, pdf_path: Path) -> int:
        """获取 PDF 页数"""
        with fitz.open(str(pdf_path)) as doc:
            return doc.page_count

    def extract_all_pages(self, pdf_path: Path, file_uuid: str) -> list[PageImage]:
        """
        将 PDF 每页渲染为图像，返回所有页的 PageImage 列表。

        :param pdf_path:   原始 PDF 路径
        :param file_uuid:  文件 UUID，用于构造唯一图像文件名
        :return:           按页码排序的 PageImage 列表
        """
        results: list[PageImage] = []

        with fitz.open(str(pdf_path)) as doc:
            for page_idx in range(doc.page_count):
                page = doc[page_idx]
                page_num = page_idx + 1

                # 渲染预览图
                mat_preview = fitz.Matrix(self.PREVIEW_DPI / 72, self.PREVIEW_DPI / 72)
                pix_preview = page.get_pixmap(matrix=mat_preview, alpha=False)
                preview_path = self.preview_dir / f"{file_uuid}_page{page_num}.jpg"
                pix_preview.save(str(preview_path), jpg_quality=90)

                # 渲染缩略图
                mat_thumb = fitz.Matrix(self.THUMBNAIL_DPI / 72, self.THUMBNAIL_DPI / 72)
                pix_thumb = page.get_pixmap(matrix=mat_thumb, alpha=False)
                thumb_path = self.thumbnail_dir / f"{file_uuid}_thumb{page_num}.jpg"
                pix_thumb.save(str(thumb_path), jpg_quality=70)

                # 提取纯文本（辅助信息，可能为空）
                text = page.get_text("text") or ""

                results.append(PageImage(
                    page_number=page_num,
                    preview_path=preview_path,
                    thumbnail_path=thumb_path,
                    text=text.strip(),
                ))

        return results

    def extract_page_image(self, pdf_path: Path, page_number: int, file_uuid: str) -> PageImage:
        """提取单页图像（用于重新识别单页时）"""
        with fitz.open(str(pdf_path)) as doc:
            if page_number < 1 or page_number > doc.page_count:
                raise ValueError(f"页码 {page_number} 超出范围（共 {doc.page_count} 页）")
            page = doc[page_number - 1]

            mat = fitz.Matrix(self.PREVIEW_DPI / 72, self.PREVIEW_DPI / 72)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            preview_path = self.preview_dir / f"{file_uuid}_page{page_number}.jpg"
            pix.save(str(preview_path), jpg_quality=90)

            mat_thumb = fitz.Matrix(self.THUMBNAIL_DPI / 72, self.THUMBNAIL_DPI / 72)
            pix_thumb = page.get_pixmap(matrix=mat_thumb, alpha=False)
            thumb_path = self.thumbnail_dir / f"{file_uuid}_thumb{page_number}.jpg"
            pix_thumb.save(str(thumb_path), jpg_quality=70)

            text = page.get_text("text") or ""
            return PageImage(
                page_number=page_number,
                preview_path=preview_path,
                thumbnail_path=thumb_path,
                text=text.strip(),
            )
