"""
统计面板 API 端点
- GET /dashboard/student   学生首页统计
- GET /dashboard/teacher   教师首页统计
- GET /dashboard/admin     管理员首页统计
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.reimbursement import Reimbursement, ReimbursementStatus
from app.models.user import User, UserRole
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/student", response_model=ApiResponse[dict], summary="学生首页统计")
async def student_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """学生首页：统计自己的报销申请各状态数量和金额"""
    from datetime import datetime, timezone
    from calendar import monthrange

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 各状态计数
    counts_result = await db.execute(
        select(Reimbursement.status, func.count().label("cnt"))
        .where(Reimbursement.applicant_id == current_user.id)
        .group_by(Reimbursement.status)
    )
    counts = {row.status: row.cnt for row in counts_result}

    # 已通过总金额
    total_amt = await db.execute(
        select(func.coalesce(func.sum(Reimbursement.declared_amount), 0.0))
        .where(
            Reimbursement.applicant_id == current_user.id,
            Reimbursement.status == ReimbursementStatus.APPROVED,
        )
    )
    # 本月报销金额
    month_amt = await db.execute(
        select(func.coalesce(func.sum(Reimbursement.declared_amount), 0.0))
        .where(
            Reimbursement.applicant_id == current_user.id,
            Reimbursement.status == ReimbursementStatus.APPROVED,
            Reimbursement.updated_at >= month_start,
        )
    )

    return ApiResponse.ok(data={
        "draft": counts.get(ReimbursementStatus.DRAFT, 0),
        "submitted": counts.get(ReimbursementStatus.SUBMITTED, 0),
        "reviewing": counts.get(ReimbursementStatus.REVIEWING, 0),
        "approved": counts.get(ReimbursementStatus.APPROVED, 0),
        "rejected": counts.get(ReimbursementStatus.REJECTED, 0),
        "total_approved_amount": float(total_amt.scalar_one()),
        "month_approved_amount": float(month_amt.scalar_one()),
    })


@router.get("/teacher", response_model=ApiResponse[dict], summary="教师首页统计")
async def teacher_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """教师首页：待审批数量、本周/本月审批统计"""
    from datetime import datetime, timedelta, timezone
    from app.models.approval_record import ApprovalRecord, ApprovalAction

    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 待审批（通过审批流查找该教师负责的申请）
    from app.repositories.reimbursement_repo import ReimbursementRepository
    repo = ReimbursementRepository(db)
    _, pending_total = await repo.get_pending_for_approver(
        approver_id=current_user.id, offset=0, limit=1
    )

    # 本周/本月审批通过数量
    week_approved = await db.execute(
        select(func.count())
        .select_from(ApprovalRecord)
        .where(
            ApprovalRecord.operator_id == current_user.id,
            ApprovalRecord.action == ApprovalAction.APPROVE,
            ApprovalRecord.created_at >= week_start,
        )
    )
    month_approved = await db.execute(
        select(func.count())
        .select_from(ApprovalRecord)
        .where(
            ApprovalRecord.operator_id == current_user.id,
            ApprovalRecord.action == ApprovalAction.APPROVE,
            ApprovalRecord.created_at >= month_start,
        )
    )

    return ApiResponse.ok(data={
        "pending": pending_total,
        "week_approved": week_approved.scalar_one(),
        "month_approved": month_approved.scalar_one(),
    })


@router.get("/admin", response_model=ApiResponse[dict], summary="管理员首页统计")
async def admin_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """管理员首页：用户总数、本月报销、发票类型统计"""
    from datetime import datetime, timezone
    from app.models.invoice import Invoice, DocumentType

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 用户总数
    user_count = await db.execute(select(func.count()).select_from(User))

    # 本月总报销金额
    month_amt = await db.execute(
        select(func.coalesce(func.sum(Reimbursement.declared_amount), 0.0))
        .where(
            Reimbursement.status == ReimbursementStatus.APPROVED,
            Reimbursement.updated_at >= month_start,
        )
    )

    # 本月报销次数
    month_count = await db.execute(
        select(func.count())
        .select_from(Reimbursement)
        .where(
            Reimbursement.status == ReimbursementStatus.APPROVED,
            Reimbursement.updated_at >= month_start,
        )
    )

    # 发票类型分布（全量）
    type_dist = await db.execute(
        select(Invoice.document_type, func.count().label("cnt"))
        .group_by(Invoice.document_type)
    )

    return ApiResponse.ok(data={
        "user_count": user_count.scalar_one(),
        "month_approved_amount": float(month_amt.scalar_one()),
        "month_approved_count": month_count.scalar_one(),
        "invoice_type_distribution": [
            {"type": row.document_type, "count": row.cnt}
            for row in type_dist
        ],
    })
