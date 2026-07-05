"""
审计日志服务
封装审计日志的写入逻辑，提供统一的记录接口。
其他服务调用此服务写入操作记录，审计日志一旦写入不可修改。
"""

from typing import Any, Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.audit_repo import AuditLogRepository


class AuditService:
    """审计日志服务"""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = AuditLogRepository(db)

    async def log(
        self,
        action: str,
        action_desc: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        old_data: Optional[Any] = None,
        new_data: Optional[Any] = None,
        is_success: bool = True,
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """
        写入一条审计日志。

        :param action:       操作码，如 LOGIN / UPLOAD_PDF / APPROVE
        :param action_desc:  中文操作描述，如 "用户登录成功"
        """
        log = AuditLog(
            action=action,
            action_desc=action_desc,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            target_type=target_type,
            target_id=target_id,
            old_data=old_data,
            new_data=new_data,
            is_success=is_success,
            error_message=error_message,
        )
        return await self._repo.create(log)

    async def log_from_request(
        self,
        request: Request,
        action: str,
        action_desc: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        **kwargs,
    ) -> AuditLog:
        """从 FastAPI Request 对象中自动提取 IP 和 User-Agent"""
        ip = request.client.host if request.client else None
        ua = request.headers.get("user-agent", "")
        return await self.log(
            action=action,
            action_desc=action_desc,
            user_id=user_id,
            username=username,
            ip_address=ip,
            user_agent=ua[:255] if ua else None,
            **kwargs,
        )

    async def search(self, **kwargs):
        """审计日志搜索（透传给 repository）"""
        return await self._repo.search(**kwargs)


# ─── 操作码常量（避免硬编码字符串） ──────────────────────────────────────────

class AuditAction:
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    UPLOAD_PDF = "UPLOAD_PDF"
    DELETE_FILE = "DELETE_FILE"
    OCR_START = "OCR_START"
    OCR_DONE = "OCR_DONE"
    AI_EXTRACT = "AI_EXTRACT"
    CREATE_REIMBURSEMENT = "CREATE_REIMBURSEMENT"
    UPDATE_REIMBURSEMENT = "UPDATE_REIMBURSEMENT"
    SUBMIT_REIMBURSEMENT = "SUBMIT_REIMBURSEMENT"
    RECALL_REIMBURSEMENT = "RECALL_REIMBURSEMENT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    EDIT_INVOICE = "EDIT_INVOICE"
    CHANGE_PASSWORD = "CHANGE_PASSWORD"
    CREATE_USER = "CREATE_USER"
    UPDATE_USER = "UPDATE_USER"
    RESET_PASSWORD = "RESET_PASSWORD"
    CREATE_PROJECT = "CREATE_PROJECT"
    UPDATE_PROJECT = "UPDATE_PROJECT"
