"""
FastAPI 依赖注入函数
通过 Depends() 注入到路由处理函数中，实现当前用户认证和角色鉴权。
"""

from typing import Optional

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

# HTTPBearer 自动从 Authorization: Bearer <token> 提取 token
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    获取当前登录用户（必须已登录）。
    Token 无效或未传时抛出 UnauthorizedException。
    """
    if not credentials:
        raise UnauthorizedException()
    auth_svc = AuthService(db)
    user = await auth_svc.get_user_from_token(credentials.credentials)
    if not user or not user.is_active:
        raise UnauthorizedException()
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前已激活用户（封装 get_current_user，方便后续扩展）"""
    return current_user


async def require_teacher(
    current_user: User = Depends(get_current_user),
) -> User:
    """要求当前用户为教师或管理员（审批操作使用）"""
    if current_user.role not in (UserRole.TEACHER, UserRole.ADMIN):
        raise ForbiddenException("该操作仅教师或管理员可执行")
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """要求当前用户为管理员"""
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException("该操作仅管理员可执行")
    return current_user


async def get_db_session(
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    """数据库会话依赖（直接暴露给需要手动控制事务的端点）"""
    return db
