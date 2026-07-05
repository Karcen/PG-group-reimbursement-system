"""
用户管理 API 端点
- GET    /users          列出所有用户（管理员）
- POST   /users          创建用户（管理员）
- GET    /users/{id}     获取用户详情
- PUT    /users/{id}     管理员更新用户
- DELETE /users/{id}     禁用用户（管理员）
- PUT    /users/me/profile  用户修改自己的资料
- PUT    /users/me/password 用户修改密码
- POST   /users/{id}/reset-password 管理员重置密码
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, require_admin
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedData, PaginationParams
from app.schemas.user import (
    PasswordChange,
    PasswordReset,
    UserAdminUpdate,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.services.audit_service import AuditAction, AuditService
from app.services.user_service import UserService

router = APIRouter()


@router.get("", response_model=ApiResponse[PaginatedData[UserOut]], summary="列出所有用户")
async def list_users(
    pagination: PaginationParams = Depends(),
    keyword: str = None,
    role: str = None,
    is_active: bool = None,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """管理员查看所有用户列表（支持关键字搜索）"""
    from app.models.user import UserRole
    role_enum = UserRole(role) if role else None
    svc = UserService(db)
    items, total = await svc.search(
        keyword=keyword,
        role=role_enum,
        is_active=is_active,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return ApiResponse.ok(
        data=PaginatedData.create(
            items=[UserOut.model_validate(u) for u in items],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    )


@router.post("", response_model=ApiResponse[UserOut], summary="创建用户")
async def create_user(
    body: UserCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """管理员创建新用户"""
    svc = UserService(db)
    user = await svc.create_user(body)
    await AuditService(db).log_from_request(
        request, AuditAction.CREATE_USER,
        f"管理员创建用户：{user.username}",
        user_id=admin.id, username=admin.username,
        target_type="user", target_id=user.id,
        new_data={"username": user.username, "role": user.role.value},
    )
    return ApiResponse.ok(data=UserOut.model_validate(user), message="用户创建成功")


@router.get("/teachers", response_model=ApiResponse[list[UserOut]], summary="获取教师/管理员列表")
async def list_teachers(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取教师和管理员列表（用于审批流配置下拉）"""
    svc = UserService(db)
    teachers = await svc.list_teachers()
    return ApiResponse.ok(data=[UserOut.model_validate(u) for u in teachers])


@router.get("/me/profile", response_model=ApiResponse[UserOut], summary="获取我的资料")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return ApiResponse.ok(data=UserOut.model_validate(current_user))


@router.put("/me/profile", response_model=ApiResponse[UserOut], summary="更新我的资料")
async def update_my_profile(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    svc = UserService(db)
    user = await svc.update_profile(current_user, body)
    return ApiResponse.ok(data=UserOut.model_validate(user), message="资料已更新")


@router.put("/me/password", response_model=ApiResponse[None], summary="修改密码")
async def change_password(
    body: PasswordChange,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    svc = UserService(db)
    await svc.change_password(current_user, body.old_password, body.new_password)
    await AuditService(db).log_from_request(
        request, AuditAction.CHANGE_PASSWORD, "用户修改密码",
        user_id=current_user.id, username=current_user.username,
    )
    return ApiResponse.ok(message="密码已修改，请重新登录")


@router.get("/{user_id}", response_model=ApiResponse[UserOut], summary="获取用户详情")
async def get_user(
    user_id: int,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    svc = UserService(db)
    user = await svc.get_by_id(user_id)
    return ApiResponse.ok(data=UserOut.model_validate(user))


@router.put("/{user_id}", response_model=ApiResponse[UserOut], summary="管理员更新用户")
async def admin_update_user(
    user_id: int,
    body: UserAdminUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    svc = UserService(db)
    old_user = await svc.get_by_id(user_id)
    old_data = {"role": old_user.role.value, "is_active": old_user.is_active}
    user = await svc.admin_update(user_id, body)
    await AuditService(db).log_from_request(
        request, AuditAction.UPDATE_USER, f"管理员更新用户：{user.username}",
        user_id=admin.id, username=admin.username,
        target_type="user", target_id=user_id,
        old_data=old_data,
        new_data=body.model_dump(exclude_none=True),
    )
    return ApiResponse.ok(data=UserOut.model_validate(user), message="用户信息已更新")


@router.post("/{user_id}/reset-password", response_model=ApiResponse[None], summary="管理员重置密码")
async def reset_password(
    user_id: int,
    body: PasswordReset,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    svc = UserService(db)
    await svc.reset_password(user_id, body.new_password)
    await AuditService(db).log_from_request(
        request, AuditAction.RESET_PASSWORD, f"管理员重置用户 ID={user_id} 的密码",
        user_id=admin.id, username=admin.username,
        target_type="user", target_id=user_id,
    )
    return ApiResponse.ok(message="密码已重置")
