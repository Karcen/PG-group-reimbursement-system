"""
重复发票查重服务
检测规则：
  1. 发票号码 + 发票代码相同
  2. 仅发票号码相同（无代码时）
  3. 铁路电子客票票号相同
  4. 航空行程单票号相同
检测到重复时抛出 DuplicateInvoiceException。
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateInvoiceException
from app.repositories.invoice_repo import InvoiceRepository


class DuplicateCheckService:
    """发票重复检测服务"""

    def __init__(self, db: AsyncSession) -> None:
        self._invoice_repo = InvoiceRepository(db)

    async def check(
        self,
        invoice_number: Optional[str],
        invoice_code: Optional[str],
        ticket_number: Optional[str],
        exclude_reimbursement_id: Optional[int] = None,
    ) -> None:
        """
        执行查重。若检测到重复发票，抛出 DuplicateInvoiceException。

        :param invoice_number:         发票号码（增值税发票）
        :param invoice_code:           发票代码（增值税发票）
        :param ticket_number:          票号（客票 / 行程单）
        :param exclude_reimbursement_id: 排除自身所在报销申请（编辑时使用）
        """
        # 仅当有有效字段时才查重
        if not invoice_number and not ticket_number:
            return

        duplicate = await self._invoice_repo.find_duplicate(
            invoice_number=invoice_number,
            invoice_code=invoice_code,
            ticket_number=ticket_number,
            exclude_reimbursement_id=exclude_reimbursement_id,
        )
        if duplicate:
            raise DuplicateInvoiceException(
                existing_id=duplicate.reimbursement_id
            )

    async def check_invoice(
        self,
        invoice_number: Optional[str] = None,
        invoice_code: Optional[str] = None,
        ticket_number: Optional[str] = None,
        exclude_reimbursement_id: Optional[int] = None,
    ) -> bool:
        """
        静默版查重（不抛异常，返回 True 表示有重复）。
        适用于管理员查询重复记录页面。
        """
        if not invoice_number and not ticket_number:
            return False
        duplicate = await self._invoice_repo.find_duplicate(
            invoice_number=invoice_number,
            invoice_code=invoice_code,
            ticket_number=ticket_number,
            exclude_reimbursement_id=exclude_reimbursement_id,
        )
        return duplicate is not None
