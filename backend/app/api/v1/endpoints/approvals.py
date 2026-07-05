"""
审批操作 API 端点
- POST /approvals/{reimb_id}/approve   审批通过
- POST /approvals/{reimb_id}/reject    审批驳回
"""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, require_teacher
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.reimbursement import ReimbursementOut
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditAction, AuditService
from app.services.reimbursement_service import ReimbursementService

router = APIRouter()


class ApproveBody(BaseModel):
    comment: str = ""


class RejectBody(BaseModel):
    comment: str


@router.post("/{reimb_id}/approve", response_model=ApiResponse[ReimbursementOut], summary="审批通过")
async def approve(
    reimb_id: int,
    body: ApproveBody,
    request: Request,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db_session),
):
    """教师/管理员审批通过报销申请"""
    reimb_svc = ReimbursementService(db)
    approval_svc = ApprovalService(db)

    reimb = await reimb_svc.get_or_raise(reimb_id)
    reimb = await approval_svc.approve(reimb, current_user, body.comment)
    await AuditService(db).log_from_request(
        request, AuditAction.APPROVE, f"审批通过报销申请 ID={reimb_id}",
        user_id=current_user.id, username=current_user.username,
        target_type="reimbursement", target_id=reimb_id,
        new_data={"comment": body.comment},
    )
    fresh = await reimb_svc.get_or_raise(reimb.id)
    return ApiResponse.ok(data=ReimbursementOut.model_validate(fresh), message="已审批通过")


@router.post("/{reimb_id}/reject", response_model=ApiResponse[ReimbursementOut], summary="审批驳回")
async def reject(
    reimb_id: int,
    body: RejectBody,
    request: Request,
    current_user: User = Depends(require_teacher),
    db: AsyncSession = Depends(get_db_session),
):
    """教师/管理员驳回报销申请，需填写驳回原因"""
    reimb_svc = ReimbursementService(db)
    approval_svc = ApprovalService(db)

    reimb = await reimb_svc.get_or_raise(reimb_id)
    reimb = await approval_svc.reject(reimb, current_user, body.comment)
    await AuditService(db).log_from_request(
        request, AuditAction.REJECT, f"驳回报销申请 ID={reimb_id}",
        user_id=current_user.id, username=current_user.username,
        target_type="reimbursement", target_id=reimb_id,
        new_data={"comment": body.comment},
    )
    fresh = await reimb_svc.get_or_raise(reimb.id)
    return ApiResponse.ok(data=ReimbursementOut.model_validate(fresh), message="已驳回")
