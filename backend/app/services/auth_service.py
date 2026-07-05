"""
认证服务
处理登录、Token 刷新、当前用户获取。
"""

from datetime import timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import TokenResponse


class AuthService:
    """认证服务"""

    def __init__(self, db: AsyncSession) -> None:
        self._user_repo = UserRepository(db)

    async def authenticate(self, username: str, password: str) -> User:
        """
        校验用户名/邮箱和密码。
        :raises UnauthorizedException: 用户名不存在、密码错误或账号被禁用
        """
        user = await self._user_repo.get_by_username_or_email(username)
        if not user:
            raise UnauthorizedException("用户名或密码错误")
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedException("用户名或密码错误")
        if not user.is_active:
            raise UnauthorizedException("账号已被禁用，请联系管理员")
        return user

    def generate_tokens(self, user: User) -> TokenResponse:
        """为已认证用户生成 Access Token 和 Refresh Token"""
        extra = {"role": user.role.value, "username": user.username}
        access_token = create_access_token(subject=user.id, extra_claims=extra)
        refresh_token = create_refresh_token(subject=user.id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user,  # type: ignore[arg-type]  # Pydantic 会通过 from_attributes 转换
        )

    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        使用 Refresh Token 换取新的 Access Token。
        :raises UnauthorizedException: Token 无效或已过期
        """
        try:
            payload = decode_token(refresh_token)
        except Exception:
            raise UnauthorizedException("Refresh Token 无效或已过期，请重新登录")

        if payload.get("type") != "refresh":
            raise UnauthorizedException("Token 类型错误")

        user_id = int(payload["sub"])
        user = await self._user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedException("用户不存在或已被禁用")

        extra = {"role": user.role.value, "username": user.username}
        return create_access_token(subject=user.id, extra_claims=extra)

    async def get_user_from_token(self, token: str) -> Optional[User]:
        """从 Token 解析当前用户（用于依赖注入）"""
        try:
            payload = decode_token(token)
        except Exception:
            return None
        user_id = payload.get("sub")
        if not user_id:
            return None
        return await self._user_repo.get_by_id(int(user_id))
