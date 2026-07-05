"""
报销申请相关 Pydantic Schema
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.reimbursement import ReimbursementStatus
from app.schemas.payment_record import PaymentRecordOut
from app.schemas.project import ProjectBrief
from app.schemas.user import UserBrief


class ReimbursementCreate(BaseModel):
    """创建/保存草稿请求"""
    title: str = Field(min_length=1, max_length=256, description="报销标题")
    purpose: Optional[str] = Field(default=None, description="报销事由")
    project_id: Optional[int] = Field(default=None, description="关联经费项目ID")
    funding_source: Optional[str] = Field(default=None, max_length=256, description="经费来源")
    declared_amount: float = Field(default=0.0, ge=0, description="申报报销金额（元）")
    notes: Optional[str] = Field(default=None, description="备注")


class ReimbursementUpdate(BaseModel):
    """更新报销申请（草稿或驳回后可编辑）"""
    title: Optional[str] = Field(default=None, max_length=256)
    purpose: Optional[str] = None
    project_id: Optional[int] = None
    funding_source: Optional[str] = Field(default=None, max_length=256)
    declared_amount: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None


class ReimbursementSubmit(BaseModel):
    """提交审批请求（必填字段校验）"""
    purpose: str = Field(min_length=1, description="报销事由（提交时必填）")
    project_id: int = Field(description="经费项目（提交时必填）")
    declared_amount: float = Field(gt=0, description="报销金额（提交时必填，必须大于0）")


class ApprovalRecordOut(BaseModel):
    """审批记录条目"""
    id: int
    operator: UserBrief
    action: str
    step: int
    comment: Optional[str]
    from_status: str
    to_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReimbursementOut(BaseModel):
    """报销申请详情响应"""
    id: int
    uuid: str
    title: str
    purpose: Optional[str]
    funding_source: Optional[str]
    notes: Optional[str]
    declared_amount: float
    ocr_total_amount: float
    status: ReimbursementStatus
    current_step: int
    applicant: UserBrief
    project: Optional[ProjectBrief]
    approval_records: list[ApprovalRecordOut] = []
    payment_records: list[PaymentRecordOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReimbursementListItem(BaseModel):
    """报销申请列表条目（省略详情，提升列表性能）"""
    id: int
    uuid: str
    title: str
    status: ReimbursementStatus
    declared_amount: float
    applicant: UserBrief
    project: Optional[ProjectBrief]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReimbursementSearchParams(BaseModel):
    """报销申请搜索参数"""
    keyword: Optional[str] = Field(default=None, description="关键字（标题/事由）")
    status: Optional[ReimbursementStatus] = None
    project_id: Optional[int] = None
    applicant_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
