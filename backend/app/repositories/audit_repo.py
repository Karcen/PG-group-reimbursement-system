"""
审计日志 Repository
审计日志只写不改，查询支持多条件过滤和分页。
"""

from typing import Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, AuditLog)

    async def search(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        target_type: Optional[str] = None,
        is_success: Optional[bool] = None,
        start_date=None,
        end_date=None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[AuditLog], int]:
        """多条件搜索审计日志"""
        filters = []
        if user_id is not None:
            filters.append(AuditLog.user_id == user_id)
        if action:
            filters.append(AuditLog.action.ilike(f"%{action}%"))
        if target_type:
            filters.append(AuditLog.target_type == target_type)
        if is_success is not None:
            filters.append(AuditLog.is_success == is_success)
        if start_date:
            filters.append(AuditLog.created_at >= start_date)
        if end_date:
            filters.append(AuditLog.created_at <= end_date)

        base = and_(*filters) if filters else True

        count_q = select(func.count()).select_from(AuditLog).where(base)
        query = (
            select(AuditLog)
            .where(base)
            .order_by(AuditLog.created_at.desc())
            .options(selectinload(AuditLog.user))
        )

        total = (await self.db.execute(count_q)).scalar_one()
        items = (await self.db.execute(query.offset(offset).limit(limit))).scalars().all()
        return items, total
