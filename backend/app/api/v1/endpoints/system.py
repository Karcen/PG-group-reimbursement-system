"""
系统设置 API 端点
- GET /system/config       获取系统配置（仅管理员）
- PUT /system/config       更新可调整配置（仅管理员）
- GET /system/tags         获取所有标签
- POST /system/tags        创建标签（管理员）
- DELETE /system/tags/{id} 删除标签（管理员）
- POST /system/reminders/trigger  手动触发超时催办检查
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, require_admin
from app.core.config import settings
from app.models.tag import Tag
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.invoice import TagOut

router = APIRouter()


@router.get("/config", response_model=ApiResponse[dict], summary="获取系统配置")
async def get_config(
    _: User = Depends(require_admin),
):
    """返回当前可调整的系统配置项（不包含密钥等敏感信息）"""
    return ApiResponse.ok(data={
        "app_name": settings.APP_NAME,
        "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
        "amount_diff_threshold": settings.AMOUNT_DIFF_THRESHOLD,
        "approval_timeout_hours": settings.APPROVAL_TIMEOUT_HOURS,
        "approval_reminder_interval_hours": settings.APPROVAL_REMINDER_INTERVAL_HOURS,
        "ollama_model": settings.OLLAMA_MODEL,
        "ollama_base_url": settings.OLLAMA_BASE_URL,
    })


# ─── 标签管理 ──────────────────────────────────────────────────────────────

class TagCreate(BaseModel):
    name: str
    color: str = "#409EFF"
    description: str | None = None


@router.get("/tags", response_model=ApiResponse[list[TagOut]], summary="获取所有标签")
async def list_tags(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(select(Tag).order_by(Tag.name))
    tags = result.scalars().all()
    return ApiResponse.ok(data=[TagOut.model_validate(t) for t in tags])


@router.post("/tags", response_model=ApiResponse[TagOut], summary="创建标签")
async def create_tag(
    body: TagCreate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    tag = Tag(name=body.name, color=body.color, description=body.description)
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return ApiResponse.ok(data=TagOut.model_validate(tag), message="标签已创建")


@router.delete("/tags/{tag_id}", response_model=ApiResponse[None], summary="删除标签")
async def delete_tag(
    tag_id: int,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    from app.core.exceptions import NotFoundException
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise NotFoundException("标签不存在")
    await db.delete(tag)
    await db.flush()
    return ApiResponse.ok(message="标签已删除")


# ─── 提醒管理 ──────────────────────────────────────────────────────────────

@router.post("/reminders/trigger", response_model=ApiResponse[dict], summary="手动触发催办检查")
async def trigger_reminders(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """管理员手动触发一次审批超时催办检查"""
    from app.services.reminder_service import ReminderService
    svc = ReminderService(db)
    count = await svc.send_overdue_reminders()
    return ApiResponse.ok(
        data={"sent_count": count},
        message=f"已发送 {count} 条催办提醒",
    )
