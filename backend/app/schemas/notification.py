"""
通知 & 审计日志相关 Pydantic Schema
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.notification import NotificationType


# ─── 通知 ──────────────────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    """通知响应"""
    id: int
    type: NotificationType
    title: str
    content: Optional[str]
    is_read: bool
    related_type: Optional[str]
    related_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationMarkRead(BaseModel):
    """标记通知已读请求"""
    ids: list[int] = Field(description="要标记已读的通知ID列表，空列表表示全部标记已读")


class UnreadCountOut(BaseModel):
    """未读通知数量"""
    count: int


# ─── 审计日志 ──────────────────────────────────────────────────────────────

class AuditLogOut(BaseModel):
    """审计日志响应"""
    id: int
    user_id: Optional[int]
    username: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    action: str
    action_desc: Optional[str]
    target_type: Optional[str]
    target_id: Optional[int]
    old_data: Optional[Any]
    new_data: Optional[Any]
    is_success: bool
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogSearchParams(BaseModel):
    """审计日志搜索参数"""
    user_id: Optional[int] = None
    action: Optional[str] = None
    target_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_success: Optional[bool] = None
