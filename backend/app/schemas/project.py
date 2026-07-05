"""
经费项目与审批流 Pydantic Schema
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.user import UserBrief


# ─── 审批流步骤 ────────────────────────────────────────────────────────────

class ApprovalFlowStepOut(BaseModel):
    """审批流单步配置响应"""
    id: int
    step: int
    approver: UserBrief
    is_active: bool

    model_config = {"from_attributes": True}


class ApprovalFlowStepCreate(BaseModel):
    """添加审批流步骤"""
    approver_id: int = Field(description="审批人用户ID（必须为教师或管理员）")
    step: int = Field(ge=1, description="审批顺序（从1开始）")


# ─── 经费项目 ──────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    """创建经费项目请求"""
    name: str = Field(min_length=1, max_length=128, description="项目名称")
    code: str = Field(min_length=1, max_length=64, description="项目编号")
    description: Optional[str] = Field(default=None, description="项目简介")
    budget: Optional[float] = Field(default=None, ge=0, description="项目预算（元），不填表示不限制")
    approval_steps: list[ApprovalFlowStepCreate] = Field(
        default=[], description="审批流配置（按 step 升序）"
    )


class ProjectUpdate(BaseModel):
    """更新经费项目"""
    name: Optional[str] = Field(default=None, max_length=128)
    code: Optional[str] = Field(default=None, max_length=64)
    description: Optional[str] = None
    budget: Optional[float] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class ProjectOut(BaseModel):
    """经费项目响应"""
    id: int
    name: str
    code: str
    description: Optional[str]
    budget: Optional[float]
    used_amount: float
    is_active: bool
    approval_flows: list[ApprovalFlowStepOut]
    created_at: datetime

    model_config = {"from_attributes": True}


class ProjectBrief(BaseModel):
    """项目简要信息（用于下拉选择）"""
    id: int
    name: str
    code: str
    is_active: bool

    model_config = {"from_attributes": True}
