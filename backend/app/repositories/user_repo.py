"""
用户 Repository
封装所有用户相关的数据库操作。
"""

from typing import Optional, Sequence

from sqlalchemy import or_, select

from app.models.user import User, UserRole
from app.repositories.base import BaseRepository
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository(BaseRepository[User]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db, User)

    async def get_by_username(self, username: str) -> Optional[User]:
        """根据用户名查询"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """根据邮箱查询"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username_or_email(self, identity: str) -> Optional[User]:
        """根据用户名或邮箱查询（用于登录）"""
        result = await self.db.execute(
            select(User).where(
                or_(User.username == identity, User.email == identity)
            )
        )
        return result.scalar_one_or_none()

    async def list_by_role(
        self,
        role: UserRole,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[User]:
        """按角色列出用户"""
        result = await self.db.execute(
            select(User)
            .where(User.role == role, User.is_active == True)  # noqa: E712
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def search(
        self,
        keyword: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[User], int]:
        """搜索用户，返回 (列表, 总数) 元组"""
        from sqlalchemy import func

        query = select(User)
        count_query = select(func.count()).select_from(User)

        filters = []
        if keyword:
            like = f"%{keyword}%"
            filters.append(
                or_(
                    User.username.ilike(like),
                    User.full_name.ilike(like),
                    User.email.ilike(like),
                    User.student_id.ilike(like),
                )
            )
        if role is not None:
            filters.append(User.role == role)
        if is_active is not None:
            filters.append(User.is_active == is_active)

        if filters:
            from sqlalchemy import and_
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        total = (await self.db.execute(count_query)).scalar_one()
        items = (
            await self.db.execute(query.offset(offset).limit(limit))
        ).scalars().all()
        return items, total
