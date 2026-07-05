"""
认证相关 API 端点
- POST /auth/login       用户登录
- POST /auth/refresh     刷新 Access Token
- POST /auth/logout      退出登录（前端清除 Token）
- GET  /auth/me          获取当前登录用户信息
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.user import LoginRequest, TokenResponse, UserOut
from app.services.audit_service import AuditAction, AuditService
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=ApiResponse[TokenResponse], summary="用户登录")
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
):
    """
    用户登录接口。
    成功返回 access_token 和 refresh_token。
    """
    auth_svc = AuthService(db)
    audit_svc = AuditService(db)

    user = await auth_svc.authenticate(body.username, body.password)
    tokens = auth_svc.generate_tokens(user)

    await audit_svc.log_from_request(
        request=request,
        action=AuditAction.LOGIN,
        action_desc=f"用户 {user.username} 登录成功",
        user_id=user.id,
        username=user.username,
        target_type="user",
        target_id=user.id,
    )

    return ApiResponse.ok(data=tokens, message="登录成功")


@router.post("/refresh", response_model=ApiResponse[dict], summary="刷新 Token")
async def refresh_token(
    body: dict,
    db: AsyncSession = Depends(get_db_session),
):
    """使用 refresh_token 换取新的 access_token"""
    refresh_token_str = body.get("refresh_token", "")
    auth_svc = AuthService(db)
    new_access_token = await auth_svc.refresh_access_token(refresh_token_str)
    return ApiResponse.ok(
        data={"access_token": new_access_token, "token_type": "bearer"},
        message="Token 刷新成功",
    )


@router.post("/logout", response_model=ApiResponse[None], summary="退出登录")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    退出登录。
    JWT 为无状态 Token，服务端无需操作，前端删除本地 Token 即可。
    此接口主要用于记录审计日志。
    """
    audit_svc = AuditService(db)
    await audit_svc.log_from_request(
        request=request,
        action=AuditAction.LOGOUT,
        action_desc=f"用户 {current_user.username} 退出登录",
        user_id=current_user.id,
        username=current_user.username,
    )
    return ApiResponse.ok(message="已退出登录")


@router.get("/me", response_model=ApiResponse[UserOut], summary="获取当前用户信息")
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """获取当前登录用户的详细信息"""
    return ApiResponse.ok(data=UserOut.model_validate(current_user))
