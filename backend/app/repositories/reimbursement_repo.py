"""
报销申请 Repository
"""

from typing import Optional, Sequence

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.reimbursement import Reimbursement, ReimbursementStatus
from app.repositories.base import BaseRepository


class ReimbursementRepository(BaseRepository[Reimbursement]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Reimbursement)

    async def get_with_details(self, record_id: int) -> Optional[Reimbursement]:
        """获取报销申请（含发票、审批记录、申请人、项目、付款凭证）"""
        from app.models.approval_record import ApprovalRecord
        from app.models.invoice import Invoice
        from app.models.payment_record import PaymentRecord

        result = await self.db.execute(
            select(Reimbursement)
            .where(Reimbursement.id == record_id)
            .options(
                selectinload(Reimbursement.applicant),
                selectinload(Reimbursement.project),
                selectinload(Reimbursement.invoices).selectinload(Invoice.tags),
                selectinload(Reimbursement.approval_records).selectinload(
                    ApprovalRecord.operator
                ),
                selectinload(Reimbursement.payment_records),  # 付款凭证预加载
            )
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        applicant_id: Optional[int] = None,
        status: Optional[ReimbursementStatus] = None,
        project_id: Optional[int] = None,
        keyword: Optional[str] = None,
        start_date=None,
        end_date=None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Reimbursement], int]:
        """多条件搜索报销申请，返回 (列表, 总数)"""
        query = select(Reimbursement).options(
            selectinload(Reimbursement.applicant),
            selectinload(Reimbursement.project),
        )
        count_q = select(func.count()).select_from(Reimbursement)

        filters = []
        if applicant_id is not None:
            filters.append(Reimbursement.applicant_id == applicant_id)
        if status is not None:
            filters.append(Reimbursement.status == status)
        if project_id is not None:
            filters.append(Reimbursement.project_id == project_id)
        if keyword:
            like = f"%{keyword}%"
            filters.append(
                or_(
                    Reimbursement.title.ilike(like),
                    Reimbursement.purpose.ilike(like),
                )
            )
        if start_date:
            filters.append(Reimbursement.created_at >= start_date)
        if end_date:
            filters.append(Reimbursement.created_at <= end_date)
        if min_amount is not None:
            filters.append(Reimbursement.declared_amount >= min_amount)
        if max_amount is not None:
            filters.append(Reimbursement.declared_amount <= max_amount)

        if filters:
            query = query.where(and_(*filters))
            count_q = count_q.where(and_(*filters))

        query = query.order_by(Reimbursement.created_at.desc())
        total = (await self.db.execute(count_q)).scalar_one()
        items = (await self.db.execute(query.offset(offset).limit(limit))).scalars().all()
        return items, total

    async def get_pending_for_approver(
        self, approver_id: int, offset: int = 0, limit: int = 20
    ) -> tuple[Sequence[Reimbursement], int]:
        """获取某审批人待审批的报销申请"""
        from app.models.project import ApprovalFlow

        # 找出该审批人负责的项目
        flows = await self.db.execute(
            select(ApprovalFlow.project_id, ApprovalFlow.step)
            .where(ApprovalFlow.approver_id == approver_id, ApprovalFlow.is_active == True)  # noqa
        )
        flow_rows = flows.all()
        if not flow_rows:
            return [], 0

        # 构造条件：项目在列表中 且 处于提交/审批中状态 且当前步骤匹配
        conditions = []
        for project_id, step in flow_rows:
            conditions.append(
                and_(
                    Reimbursement.project_id == project_id,
                    Reimbursement.current_step == step,
                )
            )

        base_filter = and_(
            or_(*conditions),
            Reimbursement.status.in_([ReimbursementStatus.SUBMITTED, ReimbursementStatus.REVIEWING]),
        )

        count_q = select(func.count()).select_from(Reimbursement).where(base_filter)
        query = (
            select(Reimbursement)
            .where(base_filter)
            .options(
                selectinload(Reimbursement.applicant),
                selectinload(Reimbursement.project),
            )
            .order_by(Reimbursement.created_at.asc())
        )

        total = (await self.db.execute(count_q)).scalar_one()
        items = (await self.db.execute(query.offset(offset).limit(limit))).scalars().all()
        return items, total
