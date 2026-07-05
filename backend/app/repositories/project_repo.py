"""
经费项目 Repository
"""

from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.project import ApprovalFlow, Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, Project)

    async def get_with_flows(self, project_id: int) -> Optional[Project]:
        """获取项目及其审批流配置（含审批人信息）"""
        result = await self.db.execute(
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.approval_flows).selectinload(ApprovalFlow.approver)
            )
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> Sequence[Project]:
        """列出所有启用项目（用于下拉选择）"""
        result = await self.db.execute(
            select(Project)
            .where(Project.is_active == True)  # noqa: E712
            .order_by(Project.name)
            .options(selectinload(Project.approval_flows).selectinload(ApprovalFlow.approver))
        )
        return result.scalars().all()

    async def get_by_code(self, code: str) -> Optional[Project]:
        result = await self.db.execute(select(Project).where(Project.code == code))
        return result.scalar_one_or_none()

    async def search(
        self,
        keyword: Optional[str] = None,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[Project], int]:
        query = select(Project).options(
            selectinload(Project.approval_flows).selectinload(ApprovalFlow.approver)
        )
        count_q = select(func.count()).select_from(Project)
        filters = []
        if keyword:
            like = f"%{keyword}%"
            from sqlalchemy import or_
            filters.append(or_(Project.name.ilike(like), Project.code.ilike(like)))
        if is_active is not None:
            filters.append(Project.is_active == is_active)
        if filters:
            from sqlalchemy import and_
            query = query.where(and_(*filters))
            count_q = count_q.where(and_(*filters))
        total = (await self.db.execute(count_q)).scalar_one()
        items = (await self.db.execute(query.offset(offset).limit(limit))).scalars().all()
        return items, total

    async def get_flows(self, project_id: int) -> Sequence[ApprovalFlow]:
        """获取项目的全部审批步骤，按 step 升序"""
        result = await self.db.execute(
            select(ApprovalFlow)
            .where(ApprovalFlow.project_id == project_id, ApprovalFlow.is_active == True)  # noqa: E712
            .order_by(ApprovalFlow.step)
        )
        return result.scalars().all()
