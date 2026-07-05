"""
通知中心 API 端点
- GET  /notifications         获取当前用户的通知列表
- GET  /notifications/unread  获取未读通知数量
- PUT  /notifications/read    批量标记已读
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedData, PaginationParams
from app.schemas.notification import NotificationMarkRead, NotificationOut, UnreadCountOut
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get("", response_model=ApiResponse[PaginatedData[NotificationOut]], summary="通知列表")
async def list_notifications(
    pagination: PaginationParams = Depends(),
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取当前用户的通知列表"""
    svc = NotificationService(db)
    items, total = await svc.list_for_user(
        user_id=current_user.id,
        unread_only=unread_only,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return ApiResponse.ok(
        data=PaginatedData.create(
            items=[NotificationOut.model_validate(n) for n in items],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    )


@router.get("/unread-count", response_model=ApiResponse[UnreadCountOut], summary="未读通知数量")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    svc = NotificationService(db)
    count = await svc.count_unread(current_user.id)
    return ApiResponse.ok(data=UnreadCountOut(count=count))


@router.put("/read", response_model=ApiResponse[None], summary="批量标记已读")
async def mark_as_read(
    body: NotificationMarkRead,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """将指定通知（或全部通知）标记为已读。ids 为空列表时标记全部。"""
    svc = NotificationService(db)
    await svc.mark_read(current_user.id, body.ids)
    return ApiResponse.ok(message="已标记为已读")
