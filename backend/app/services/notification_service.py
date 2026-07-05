"""
通知服务
负责创建和发送站内通知，其他服务调用此服务发送通知。
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.repositories.notification_repo import NotificationRepository


class NotificationService:
    """站内通知服务"""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = NotificationRepository(db)

    async def send(
        self,
        user_id: int,
        type_: NotificationType,
        title: str,
        content: str = "",
        related_type: str = None,
        related_id: int = None,
    ) -> Notification:
        """创建并保存一条通知"""
        notification = Notification(
            user_id=user_id,
            type=type_,
            title=title,
            content=content,
            related_type=related_type,
            related_id=related_id,
        )
        return await self._repo.create(notification)

    # ─── 场景化快捷方法 ────────────────────────────────────────────────────

    async def notify_submitted(self, applicant_id: int, reimbursement_id: int, title: str) -> None:
        """报销提交成功 → 通知申请人"""
        await self.send(
            user_id=applicant_id,
            type_=NotificationType.SUBMITTED,
            title=f"报销申请提交成功：{title}",
            content="您的报销申请已成功提交，请等待审批人审核。",
            related_type="reimbursement",
            related_id=reimbursement_id,
        )

    async def notify_new_pending(self, approver_id: int, reimbursement_id: int, applicant_name: str) -> None:
        """新报销待审批 → 通知审批人"""
        await self.send(
            user_id=approver_id,
            type_=NotificationType.NEW_PENDING,
            title=f"新报销申请待审批（{applicant_name}）",
            content=f"{applicant_name} 提交了一笔报销申请，请及时审批。",
            related_type="reimbursement",
            related_id=reimbursement_id,
        )

    async def notify_approved(self, applicant_id: int, reimbursement_id: int, title: str) -> None:
        """审批通过 → 通知申请人"""
        await self.send(
            user_id=applicant_id,
            type_=NotificationType.APPROVED,
            title=f"报销申请已通过：{title}",
            content="您的报销申请已审批通过，请按学校规定完成线下报销流程。",
            related_type="reimbursement",
            related_id=reimbursement_id,
        )

    async def notify_rejected(self, applicant_id: int, reimbursement_id: int, title: str, reason: str = "") -> None:
        """审批驳回 → 通知申请人"""
        content = f"驳回原因：{reason}" if reason else "请查看审批意见后修改并重新提交。"
        await self.send(
            user_id=applicant_id,
            type_=NotificationType.REJECTED,
            title=f"报销申请已被驳回：{title}",
            content=content,
            related_type="reimbursement",
            related_id=reimbursement_id,
        )

    async def notify_ocr_done(self, user_id: int, reimbursement_id: int) -> None:
        """OCR 识别完成 → 通知申请人"""
        await self.send(
            user_id=user_id,
            type_=NotificationType.OCR_DONE,
            title="发票识别完成",
            content="系统已完成 OCR 识别，请检查识别结果并确认后提交报销申请。",
            related_type="reimbursement",
            related_id=reimbursement_id,
        )

    async def notify_approval_reminder(self, approver_id: int, reimbursement_id: int, hours: int) -> None:
        """超时催办提醒 → 通知审批人"""
        await self.send(
            user_id=approver_id,
            type_=NotificationType.REMINDER,
            title=f"报销申请待审批已超 {hours} 小时",
            content=f"有一笔报销申请等待您审批已超过 {hours} 小时，请及时处理。",
            related_type="reimbursement",
            related_id=reimbursement_id,
        )

    async def count_unread(self, user_id: int) -> int:
        return await self._repo.count_unread(user_id)

    async def list_for_user(self, user_id: int, unread_only: bool = False, offset: int = 0, limit: int = 30):
        return await self._repo.list_for_user(user_id, unread_only, offset, limit)

    async def mark_read(self, user_id: int, ids: list[int]) -> None:
        await self._repo.mark_read(user_id, ids)
