"""
审批工作流服务
驱动报销申请的状态机，处理提交、审批、驳回、撤回操作。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, NotFoundException, WorkflowException
from app.models.approval_record import ApprovalAction, ApprovalRecord
from app.models.reimbursement import Reimbursement, ReimbursementStatus
from app.models.user import User, UserRole
from app.repositories.project_repo import ProjectRepository
from app.repositories.reimbursement_repo import ReimbursementRepository
from app.services.notification_service import NotificationService


class ApprovalService:
    """报销审批工作流服务"""

    def __init__(self, db: AsyncSession) -> None:
        self._reimb_repo = ReimbursementRepository(db)
        self._project_repo = ProjectRepository(db)
        self._notification_svc = NotificationService(db)
        self._db = db

    async def submit(self, reimbursement: Reimbursement, operator: User) -> Reimbursement:
        """
        提交报销申请（草稿 / 驳回 → 已提交）。
        只有申请人本人可以提交。
        """
        if reimbursement.applicant_id != operator.id:
            raise ForbiddenException("只有申请人本人才能提交报销申请")
        if reimbursement.status not in (ReimbursementStatus.DRAFT, ReimbursementStatus.REJECTED):
            raise WorkflowException(f"当前状态 '{reimbursement.status.value}' 无法提交，只有草稿或驳回状态可提交")

        # 获取项目的第一步审批人
        first_approver_id = await self._get_first_approver_id(reimbursement.project_id)

        # 更新申请状态
        reimbursement.status = ReimbursementStatus.SUBMITTED
        reimbursement.current_step = 1
        self._db.add(reimbursement)

        # 记录操作
        record = ApprovalRecord(
            reimbursement_id=reimbursement.id,
            operator_id=operator.id,
            action=ApprovalAction.RECALL,  # 实际上是"提交"，但使用 recall 的反方向
            step=0,
            comment="",
            from_status=ReimbursementStatus.DRAFT.value,
            to_status=ReimbursementStatus.SUBMITTED.value,
        )
        # 覆盖：提交是独立操作，用 APPROVE 语义
        record.action = ApprovalAction.APPROVE
        record.from_status = "draft"
        record.to_status = "submitted"
        self._db.add(record)

        # 通知申请人和第一步审批人
        await self._notification_svc.notify_submitted(
            applicant_id=operator.id,
            reimbursement_id=reimbursement.id,
            title=reimbursement.title,
        )
        if first_approver_id:
            await self._notification_svc.notify_new_pending(
                approver_id=first_approver_id,
                reimbursement_id=reimbursement.id,
                applicant_name=operator.full_name or operator.username,
            )

        await self._db.flush()
        return reimbursement

    async def approve(
        self,
        reimbursement: Reimbursement,
        operator: User,
        comment: str = "",
    ) -> Reimbursement:
        """
        审批通过。
        检查操作人是否为当前步骤的审批人，若多步审批则进入下一步，否则标记为已审批。
        """
        await self._check_approver_permission(reimbursement, operator)

        flows = await self._project_repo.get_flows(reimbursement.project_id)
        active_flows = [f for f in flows if f.is_active]
        total_steps = len(active_flows)

        from_status = reimbursement.status.value
        if reimbursement.current_step >= total_steps:
            # 最后一步：审批完成
            reimbursement.status = ReimbursementStatus.APPROVED
        else:
            # 进入下一步
            reimbursement.status = ReimbursementStatus.REVIEWING
            reimbursement.current_step += 1
            # 通知下一步审批人
            next_flow = next(
                (f for f in active_flows if f.step == reimbursement.current_step), None
            )
            if next_flow:
                await self._notification_svc.notify_new_pending(
                    approver_id=next_flow.approver_id,
                    reimbursement_id=reimbursement.id,
                    applicant_name="",
                )

        record = ApprovalRecord(
            reimbursement_id=reimbursement.id,
            operator_id=operator.id,
            action=ApprovalAction.APPROVE,
            step=reimbursement.current_step,
            comment=comment,
            from_status=from_status,
            to_status=reimbursement.status.value,
        )
        self._db.add(record)
        self._db.add(reimbursement)

        if reimbursement.status == ReimbursementStatus.APPROVED:
            await self._notification_svc.notify_approved(
                applicant_id=reimbursement.applicant_id,
                reimbursement_id=reimbursement.id,
                title=reimbursement.title,
            )

        await self._db.flush()
        return reimbursement

    async def reject(
        self,
        reimbursement: Reimbursement,
        operator: User,
        comment: str,
    ) -> Reimbursement:
        """审批驳回，申请退回到驳回状态，申请人可修改后重新提交"""
        await self._check_approver_permission(reimbursement, operator)

        from_status = reimbursement.status.value
        reimbursement.status = ReimbursementStatus.REJECTED
        reimbursement.current_step = 0

        record = ApprovalRecord(
            reimbursement_id=reimbursement.id,
            operator_id=operator.id,
            action=ApprovalAction.REJECT,
            step=reimbursement.current_step,
            comment=comment,
            from_status=from_status,
            to_status=ReimbursementStatus.REJECTED.value,
        )
        self._db.add(record)
        self._db.add(reimbursement)

        await self._notification_svc.notify_rejected(
            applicant_id=reimbursement.applicant_id,
            reimbursement_id=reimbursement.id,
            title=reimbursement.title,
            reason=comment,
        )

        await self._db.flush()
        return reimbursement

    async def recall(self, reimbursement: Reimbursement, operator: User) -> Reimbursement:
        """申请人撤回（已提交 / 审批中 → 草稿）"""
        if reimbursement.applicant_id != operator.id:
            raise ForbiddenException("只有申请人本人才能撤回申请")
        if reimbursement.status not in (ReimbursementStatus.SUBMITTED, ReimbursementStatus.REVIEWING):
            raise WorkflowException("只有已提交或审批中的申请才能撤回")

        from_status = reimbursement.status.value
        reimbursement.status = ReimbursementStatus.DRAFT
        reimbursement.current_step = 0

        record = ApprovalRecord(
            reimbursement_id=reimbursement.id,
            operator_id=operator.id,
            action=ApprovalAction.RECALL,
            step=0,
            comment="申请人主动撤回",
            from_status=from_status,
            to_status=ReimbursementStatus.DRAFT.value,
        )
        self._db.add(record)
        self._db.add(reimbursement)
        await self._db.flush()
        return reimbursement

    # ─── 内部辅助方法 ──────────────────────────────────────────────────────

    async def _get_first_approver_id(self, project_id: int) -> int | None:
        """获取项目第一步审批人 ID"""
        if not project_id:
            return None
        flows = await self._project_repo.get_flows(project_id)
        if flows:
            return flows[0].approver_id
        return None

    async def _check_approver_permission(
        self, reimbursement: Reimbursement, operator: User
    ) -> None:
        """
        校验当前操作人是否有权限对此报销的当前步骤进行审批。
        管理员可审批任意步骤。
        """
        if operator.role == UserRole.ADMIN:
            return  # 管理员拥有所有审批权限

        if reimbursement.status not in (
            ReimbursementStatus.SUBMITTED, ReimbursementStatus.REVIEWING
        ):
            raise WorkflowException("该报销申请当前状态不允许审批操作")

        # 检查操作人是否为当前步骤的审批人
        flows = await self._project_repo.get_flows(reimbursement.project_id)
        current_flow = next(
            (f for f in flows if f.step == reimbursement.current_step and f.is_active),
            None,
        )
        if not current_flow or current_flow.approver_id != operator.id:
            raise ForbiddenException("您不是当前审批步骤的审批人，无权操作")
