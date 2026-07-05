"""
PaddleOCR 封装模块
对 PaddleOCR 进行单例封装，避免每次识别都重新初始化模型（耗时较长）。
提供对图像文件路径和 numpy 数组两种输入方式的识别接口。
"""

import json
from pathlib import Path
from typing import Optional

from loguru import logger

from app.core.config import settings


class PaddleOCRWrapper:
    """
    PaddleOCR 单例封装。
    OCR 模型只在第一次调用时初始化，后续复用同一实例。
    """

    _instance: Optional["PaddleOCRWrapper"] = None
    _ocr = None  # PaddleOCR 实例

    def __new__(cls) -> "PaddleOCRWrapper":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _ensure_initialized(self) -> None:
        """懒加载：首次调用时初始化 PaddleOCR"""
        if self._ocr is not None:
            return
        try:
            from paddleocr import PaddleOCR
            logger.info(f"正在初始化 PaddleOCR（语言：{settings.OCR_LANG}）...")
            self._ocr = PaddleOCR(
                use_angle_cls=True,   # 开启方向分类（处理倒置文字）
                lang=settings.OCR_LANG,
                show_log=False,       # 关闭 PaddleOCR 内部日志
            )
            logger.info("PaddleOCR 初始化完成")
        except ImportError:
            logger.warning("PaddleOCR 未安装，OCR 功能不可用。请执行 pip install paddleocr")
            raise

    def recognize(self, image_path: Path) -> tuple[str, float]:
        """
        识别图像中的文字。

        :param image_path: 图像文件路径（JPEG / PNG）
        :return: (识别出的纯文本, 平均置信度)
        """
        self._ensure_initialized()

        try:
            result = self._ocr.ocr(str(image_path), cls=True)
        except Exception as e:
            logger.error(f"OCR 识别失败（{image_path}）：{e}")
            return "", 0.0

        if not result or result[0] is None:
            return "", 0.0

        lines: list[str] = []
        confidences: list[float] = []

        for line in result[0]:
            if not line:
                continue
            # PaddleOCR 返回格式：[[box坐标], [文字, 置信度]]
            text_info = line[1]
            if text_info and len(text_info) >= 2:
                text = str(text_info[0]).strip()
                conf = float(text_info[1])
                if text:
                    lines.append(text)
                    confidences.append(conf)

        full_text = "\n".join(lines)
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        logger.debug(
            f"OCR 完成：{image_path.name}，"
            f"识别 {len(lines)} 行，平均置信度 {avg_conf:.2f}"
        )
        return full_text, avg_conf


def get_ocr() -> PaddleOCRWrapper:
    """获取 OCR 单例（全局快捷访问）"""
    return PaddleOCRWrapper()
