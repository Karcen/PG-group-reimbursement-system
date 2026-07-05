"""
Repository 基类
提供通用的 CRUD 操作，所有具体 Repository 继承此类。
使用泛型确保类型安全，避免子类重复实现基础方法。
"""

from typing import Any, Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """
    通用异步 CRUD Repository 基类。

    用法：
        class UserRepository(BaseRepository[User]):
            def __init__(self, db: AsyncSession):
                super().__init__(db, User)
    """

    def __init__(self, db: AsyncSession, model: Type[ModelT]) -> None:
        self.db = db
        self.model = model

    async def get_by_id(self, record_id: int) -> Optional[ModelT]:
        """根据主键查询单条记录"""
        return await self.db.get(self.model, record_id)

    async def get_all(
        self,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[ModelT]:
        """分页查询所有记录"""
        result = await self.db.execute(
            select(self.model).offset(offset).limit(limit)
        )
        return result.scalars().all()

    async def count(self) -> int:
        """统计总记录数"""
        result = await self.db.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

    async def create(self, obj: ModelT) -> ModelT:
        """
        持久化一个新实体。
        调用方负责构造实体对象，此方法只负责 add + flush（不 commit）。
        commit 由 get_db 依赖中的 session 在请求结束后统一执行。
        """
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: ModelT, data: dict[str, Any]) -> ModelT:
        """
        更新实体字段。
        :param obj:  已从数据库加载的实体对象
        :param data: 要更新的字段字典（仅更新非 None 值）
        """
        for field, value in data.items():
            if value is not None or field in data:
                setattr(obj, field, value)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        """物理删除实体"""
        await self.db.delete(obj)
        await self.db.flush()
