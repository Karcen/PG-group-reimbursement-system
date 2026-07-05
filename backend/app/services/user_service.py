"""
用户管理服务
"""

from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserAdminUpdate, UserCreate, UserUpdate


class UserService:
    """用户管理服务"""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = UserRepository(db)

    async def create_user(self, data: UserCreate) -> User:
        """
        创建新用户（管理员调用）。
        :raises ConflictException: 用户名或邮箱已存在
        """
        if await self._repo.get_by_username(data.username):
            raise ConflictException(f"用户名 '{data.username}' 已存在")
        if await self._repo.get_by_email(data.email):
            raise ConflictException(f"邮箱 '{data.email}' 已被注册")

        user = User(
            username=data.username,
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            student_id=data.student_id,
            department=data.department,
            role=data.role,
        )
        return await self._repo.create(user)

    async def get_by_id(self, user_id: int) -> User:
        """获取用户（不存在时抛出 NotFoundException）"""
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(f"用户 ID={user_id} 不存在")
        return user

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        """用户更新自己的个人资料"""
        update_dict = data.model_dump(exclude_none=True)
        return await self._repo.update(user, update_dict)

    async def admin_update(self, user_id: int, data: UserAdminUpdate) -> User:
        """管理员更新任意用户信息"""
        user = await self.get_by_id(user_id)
        update_dict = data.model_dump(exclude_none=True)

        # 如果更新了邮箱，需要检查唯一性
        if "email" in update_dict and update_dict["email"] != user.email:
            existing = await self._repo.get_by_email(update_dict["email"])
            if existing:
                raise ConflictException(f"邮箱 '{update_dict['email']}' 已被其他用户使用")

        return await self._repo.update(user, update_dict)

    async def change_password(self, user: User, old_password: str, new_password: str) -> None:
        """用户自主修改密码"""
        from app.core.security import verify_password
        if not verify_password(old_password, user.hashed_password):
            from app.core.exceptions import ValidationException
            raise ValidationException("当前密码不正确")
        await self._repo.update(user, {"hashed_password": hash_password(new_password)})

    async def reset_password(self, user_id: int, new_password: str) -> None:
        """管理员重置任意用户密码"""
        user = await self.get_by_id(user_id)
        await self._repo.update(user, {"hashed_password": hash_password(new_password)})

    async def list_teachers(self) -> Sequence[User]:
        """列出所有教师（用于审批流配置下拉）"""
        teachers = await self._repo.list_by_role(UserRole.TEACHER)
        admins = await self._repo.list_by_role(UserRole.ADMIN)
        return list(teachers) + list(admins)

    async def search(self, **kwargs):
        return await self._repo.search(**kwargs)
