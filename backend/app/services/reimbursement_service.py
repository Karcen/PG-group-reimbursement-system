"""
报销申请服务
整合发票查重、金额校验、OCR 汇总、CRUD 操作。
是报销业务的核心服务，由 API 层调用。
"""

from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AmountMismatchException,
    ForbiddenException,
    NotFoundException,
    PaymentRecordRequiredException,
    ValidationException,
    WorkflowException,
)
from app.models.reimbursement import Reimbursement, ReimbursementStatus
from app.models.user import User, UserRole
from app.repositories.invoice_repo import InvoiceRepository
from app.repositories.reimbursement_repo import ReimbursementRepository
from app.schemas.reimbursement import ReimbursementCreate, ReimbursementSubmit, ReimbursementUpdate
from app.services.duplicate_check_service import DuplicateCheckService


class ReimbursementService:
    """报销申请服务"""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = ReimbursementRepository(db)
        self._invoice_repo = InvoiceRepository(db)
        self._dup_svc = DuplicateCheckService(db)
        self._db = db

    async def create_draft(self, data: ReimbursementCreate, applicant: User) -> Reimbursement:
        """创建草稿报销申请"""
        reimb = Reimbursement(
            applicant_id=applicant.id,
            title=data.title,
            purpose=data.purpose,
            project_id=data.project_id,
            funding_source=data.funding_source,
            declared_amount=data.declared_amount,
            notes=data.notes,
            status=ReimbursementStatus.DRAFT,
        )
        return await self._repo.create(reimb)

    async def update_draft(
        self,
        reimbursement: Reimbursement,
        data: ReimbursementUpdate,
        operator: User,
    ) -> Reimbursement:
        """更新草稿（只有申请人且处于草稿/驳回状态时可编辑）"""
        self._check_editable(reimbursement, operator)
        update_dict = data.model_dump(exclude_none=True)
        return await self._repo.update(reimbursement, update_dict)

    async def prepare_submit(
        self,
        reimbursement: Reimbursement,
        data: ReimbursementSubmit,
        operator: User,
    ) -> Reimbursement:
        """
        预提交校验：必填字段补充 + 金额校验。
        通过后不改变状态，由 ApprovalService.submit() 完成状态转换。
        """
        self._check_editable(reimbursement, operator)

        # 写入提交时补充的字段
        reimbursement.purpose = data.purpose
        reimbursement.project_id = data.project_id
        reimbursement.declared_amount = data.declared_amount
        self._db.add(reimbursement)

        # 汇总 OCR 发票金额
        ocr_total = await self._invoice_repo.sum_amount_by_reimbursement(reimbursement.id)
        reimbursement.ocr_total_amount = ocr_total
        self._db.add(reimbursement)

        # 金额差值校验
        diff = abs(data.declared_amount - ocr_total)
        amount_threshold = settings.AMOUNT_DIFF_THRESHOLD
        if diff > amount_threshold and ocr_total > 0:
            raise AmountMismatchException(
                declared=data.declared_amount,
                ocr_total=ocr_total,
                threshold=amount_threshold,
            )

        # 付款凭证校验：金额超过阈值时必须附上转账截图
        payment_threshold = settings.PAYMENT_RECORD_THRESHOLD
        if data.declared_amount > payment_threshold:
            from sqlalchemy import select, func
            from app.models.payment_record import PaymentRecord
            count_result = await self._db.execute(
                select(func.count())
                .select_from(PaymentRecord)
                .where(PaymentRecord.reimbursement_id == reimbursement.id)
            )
            payment_count = count_result.scalar_one()
            if payment_count == 0:
                raise PaymentRecordRequiredException(threshold=payment_threshold)

        await self._db.flush()
        return reimbursement

    async def get_or_raise(self, record_id: int) -> Reimbursement:
        """获取报销申请，不存在时抛出 NotFoundException"""
        reimb = await self._repo.get_with_details(record_id)
        if not reimb:
            raise NotFoundException(f"报销申请 ID={record_id} 不存在")
        return reimb

    async def search(self, operator: User, **kwargs) -> tuple:
        """
        搜索报销申请。
        学生只能看到自己的申请，教师和管理员可以看到所有申请。
        """
        if operator.role == UserRole.STUDENT:
            kwargs["applicant_id"] = operator.id
        return await self._repo.search(**kwargs)

    async def get_pending_for_approver(self, approver: User, offset: int = 0, limit: int = 20):
        """获取审批人的待审批列表"""
        return await self._repo.get_pending_for_approver(
            approver_id=approver.id, offset=offset, limit=limit
        )

    async def delete_draft(self, reimbursement: Reimbursement, operator: User) -> None:
        """删除草稿（只允许删除草稿状态）"""
        if reimbursement.applicant_id != operator.id and operator.role != UserRole.ADMIN:
            raise ForbiddenException("无权删除此报销申请")
        if reimbursement.status != ReimbursementStatus.DRAFT:
            raise WorkflowException("只有草稿状态的申请才能删除")
        await self._repo.delete(reimbursement)

    @staticmethod
    def _check_editable(reimbursement: Reimbursement, operator: User) -> None:
        """校验报销申请是否可编辑"""
        if reimbursement.applicant_id != operator.id:
            raise ForbiddenException("只有申请人本人才能修改报销申请")
        if reimbursement.status not in (ReimbursementStatus.DRAFT, ReimbursementStatus.REJECTED):
            raise WorkflowException(
                f"当前状态 '{reimbursement.status.value}' 不允许修改，只有草稿或驳回状态可编辑"
            )
