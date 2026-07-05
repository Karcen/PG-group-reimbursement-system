"""
统一异常定义与 HTTP 错误处理。
所有业务层抛出的异常继承自 AppException，
由 main.py 中注册的 handler 统一转换为标准 JSON 响应。
"""

from typing import Any, Optional

from fastapi import HTTPException, status


class AppException(Exception):
    """
    应用基础异常。
    所有自定义业务异常均继承此类，方便全局捕获。
    """
    def __init__(
        self,
        message: str,
        code: str = "ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        data: Optional[Any] = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.data = data
        super().__init__(message)


# ─── 认证与授权 ───────────────────────────────────────────────────────────

class UnauthorizedException(AppException):
    """未登录或 Token 无效"""
    def __init__(self, message: str = "请先登录"):
        super().__init__(message, "UNAUTHORIZED", status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AppException):
    """已登录但权限不足"""
    def __init__(self, message: str = "权限不足，无法执行此操作"):
        super().__init__(message, "FORBIDDEN", status.HTTP_403_FORBIDDEN)


# ─── 资源操作 ──────────────────────────────────────────────────────────────

class NotFoundException(AppException):
    """资源不存在"""
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, "NOT_FOUND", status.HTTP_404_NOT_FOUND)


class ConflictException(AppException):
    """资源冲突（如用户名重复、发票重复提交）"""
    def __init__(self, message: str = "数据已存在，请勿重复提交"):
        super().__init__(message, "CONFLICT", status.HTTP_409_CONFLICT)


class ValidationException(AppException):
    """业务校验失败（区别于 Pydantic 的数据格式校验）"""
    def __init__(self, message: str, data: Optional[Any] = None):
        super().__init__(message, "VALIDATION_ERROR", status.HTTP_422_UNPROCESSABLE_ENTITY, data)


# ─── 文件操作 ──────────────────────────────────────────────────────────────

class FileTooLargeException(AppException):
    """上传文件超过大小限制"""
    def __init__(self, max_mb: int):
        super().__init__(
            f"文件大小超过限制，最大允许 {max_mb} MB",
            "FILE_TOO_LARGE",
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )


class InvalidFileTypeException(AppException):
    """文件类型不允许"""
    def __init__(self):
        super().__init__(
            "不支持的文件类型，仅允许上传 PDF 和图片文件",
            "INVALID_FILE_TYPE",
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )


# ─── 业务规则 ──────────────────────────────────────────────────────────────

class DuplicateInvoiceException(AppException):
    """重复发票"""
    def __init__(self, existing_id: Optional[int] = None):
        data = {"existing_reimbursement_id": existing_id} if existing_id else None
        super().__init__(
            "该发票疑似已报销，请确认后重新提交。",
            "DUPLICATE_INVOICE",
            status.HTTP_409_CONFLICT,
            data,
        )


class AmountMismatchException(AppException):
    """报销金额与识别金额差异超过阈值"""
    def __init__(self, declared: float, ocr_total: float, threshold: float):
        super().__init__(
            f"报销金额（{declared:.2f} 元）与识别金额（{ocr_total:.2f} 元）差异超过 {threshold:.2f} 元，请确认后重新提交。",
            "AMOUNT_MISMATCH",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {"declared": declared, "ocr_total": ocr_total, "diff": abs(declared - ocr_total)},
        )


class WorkflowException(AppException):
    """审批流状态异常（如重复审批、在非法状态下操作）"""
    def __init__(self, message: str):
        super().__init__(message, "WORKFLOW_ERROR", status.HTTP_400_BAD_REQUEST)


class PaymentRecordRequiredException(AppException):
    """
    报销金额超过阈值但未附付款凭证时抛出。
    提示申请人上传银行卡/支付宝/微信等转账记录截图。
    """
    def __init__(self, threshold: float):
        super().__init__(
            f"报销金额超过 {threshold:.0f} 元，根据实验室报销规定，"
            f"必须附上银行卡、支付宝或微信等转账付款记录截图后方可提交。",
            "PAYMENT_RECORD_REQUIRED",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            {"threshold": threshold},
        )


# ─── 外部服务 ──────────────────────────────────────────────────────────────

class OCRException(AppException):
    """OCR 识别失败"""
    def __init__(self, message: str = "OCR 识别失败，请检查文件是否清晰"):
        super().__init__(message, "OCR_ERROR", status.HTTP_500_INTERNAL_SERVER_ERROR)


class AIException(AppException):
    """Ollama AI 服务调用失败"""
    def __init__(self, message: str = "AI 服务暂不可用，请稍后重试"):
        super().__init__(message, "AI_ERROR", status.HTTP_503_SERVICE_UNAVAILABLE)
