"""
智能提醒服务
定时检测超时未审批的报销申请，向审批人发送催办通知。
由 APScheduler 定时任务调用，也可通过管理界面手动触发。
"""

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.models.reimbursement import Reimbursement, ReimbursementStatus
from app.services.notification_service import NotificationService
from app.repositories.project_repo import ProjectRepository


class ReminderService:
    """审批超时催办服务"""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._notification_svc = NotificationService(db)
        self._project_repo = ProjectRepository(db)

    async def send_overdue_reminders(self) -> int:
        """
        检查所有超时未审批的报销申请，向当前步骤审批人发送提醒。
        :return: 发送提醒的数量
        """
        timeout_hours = settings.APPROVAL_TIMEOUT_HOURS
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=timeout_hours)

        # 查找所有处于提交/审批中状态且更新时间超过阈值的申请
        result = await self._db.execute(
            select(Reimbursement).where(
                and_(
                    Reimbursement.status.in_([
                        ReimbursementStatus.SUBMITTED,
                        ReimbursementStatus.REVIEWING,
                    ]),
                    Reimbursement.updated_at <= cutoff_time,
                    Reimbursement.project_id.is_not(None),
                )
            )
        )
        overdue_list = result.scalars().all()

        sent_count = 0
        for reimb in overdue_list:
            try:
                approver_id = await self._get_current_approver_id(reimb)
                if approver_id:
                    await self._notification_svc.notify_approval_reminder(
                        approver_id=approver_id,
                        reimbursement_id=reimb.id,
                        hours=timeout_hours,
                    )
                    sent_count += 1
            except Exception as e:
                logger.error(f"发送催办提醒失败，报销ID={reimb.id}：{e}")

        if sent_count:
            logger.info(f"已发送 {sent_count} 条审批催办提醒")
        return sent_count

    async def _get_current_approver_id(self, reimbursement: Reimbursement) -> int | None:
        """获取当前审批步骤的审批人 ID"""
        flows = await self._project_repo.get_flows(reimbursement.project_id)
        current_flow = next(
            (f for f in flows if f.step == reimbursement.current_step and f.is_active),
            None,
        )
        return current_flow.approver_id if current_flow else None
