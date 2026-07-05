"""
发票 Repository
"""

from typing import Optional, Sequence

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.invoice import DocumentType, Invoice
from app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Invoice)

    async def get_with_tags(self, invoice_id: int) -> Optional[Invoice]:
        """获取发票（含标签）"""
        result = await self.db.execute(
            select(Invoice)
            .where(Invoice.id == invoice_id)
            .options(selectinload(Invoice.tags))
        )
        return result.scalar_one_or_none()

    async def list_by_reimbursement(self, reimbursement_id: int) -> Sequence[Invoice]:
        """获取某报销申请的所有发票，按页码排序"""
        result = await self.db.execute(
            select(Invoice)
            .where(Invoice.reimbursement_id == reimbursement_id)
            .order_by(Invoice.page_number)
            .options(selectinload(Invoice.tags))
        )
        return result.scalars().all()

    async def find_duplicate(
        self,
        invoice_number: Optional[str],
        invoice_code: Optional[str],
        ticket_number: Optional[str],
        exclude_reimbursement_id: Optional[int] = None,
    ) -> Optional[Invoice]:
        """
        查重：根据发票号码 / 票号检测重复。
        规则1：发票号码 + 发票代码 相同
        规则2：票号相同（客票类）
        """
        if not invoice_number and not ticket_number:
            return None

        conditions = []
        if invoice_number and invoice_code:
            conditions.append(
                and_(
                    Invoice.invoice_number == invoice_number,
                    Invoice.invoice_code == invoice_code,
                )
            )
        elif invoice_number:
            conditions.append(Invoice.invoice_number == invoice_number)
        if ticket_number:
            conditions.append(Invoice.ticket_number == ticket_number)

        if not conditions:
            return None

        from sqlalchemy import or_
        query = select(Invoice).where(or_(*conditions))
        if exclude_reimbursement_id:
            query = query.where(Invoice.reimbursement_id != exclude_reimbursement_id)

        result = await self.db.execute(query.limit(1))
        return result.scalar_one_or_none()

    async def sum_amount_by_reimbursement(self, reimbursement_id: int) -> float:
        """计算某报销申请下所有发票金额总和"""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.coalesce(func.sum(Invoice.amount), 0.0))
            .where(Invoice.reimbursement_id == reimbursement_id)
        )
        return result.scalar_one()
