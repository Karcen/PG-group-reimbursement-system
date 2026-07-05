"""
通知 Repository
"""

from typing import Sequence

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from app.models.notification import Notification, NotificationType
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Notification)

    async def list_for_user(
        self,
        user_id: int,
        unread_only: bool = False,
        offset: int = 0,
        limit: int = 30,
    ) -> tuple[Sequence[Notification], int]:
        """查询用户通知列表，按创建时间倒序"""
        filters = [Notification.user_id == user_id]
        if unread_only:
            filters.append(Notification.is_read == False)  # noqa: E712

        count_q = select(func.count()).select_from(Notification).where(and_(*filters))
        query = (
            select(Notification)
            .where(and_(*filters))
            .order_by(Notification.created_at.desc())
        )

        total = (await self.db.execute(count_q)).scalar_one()
        items = (await self.db.execute(query.offset(offset).limit(limit))).scalars().all()
        return items, total

    async def count_unread(self, user_id: int) -> int:
        """统计用户未读通知数量"""
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa
        )
        return result.scalar_one()

    async def mark_read(self, user_id: int, ids: list[int]) -> None:
        """批量标记已读，ids 为空则标记该用户所有通知"""
        stmt = update(Notification).where(Notification.user_id == user_id)
        if ids:
            stmt = stmt.where(Notification.id.in_(ids))
        await self.db.execute(stmt.values(is_read=True))
        await self.db.flush()
