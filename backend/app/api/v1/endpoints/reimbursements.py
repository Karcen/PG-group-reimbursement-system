"""
报销申请 API 端点
- GET    /reimbursements                    搜索报销申请列表
- POST   /reimbursements                    创建草稿
- GET    /reimbursements/{id}               获取详情
- PUT    /reimbursements/{id}               更新草稿
- DELETE /reimbursements/{id}               删除草稿
- POST   /reimbursements/{id}/submit        提交审批
- POST   /reimbursements/{id}/recall        撤回申请
- GET    /reimbursements/export/excel       导出 Excel
- GET    /reimbursements/export/csv         导出 CSV
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedData, PaginationParams
from app.schemas.reimbursement import (
    ReimbursementCreate,
    ReimbursementListItem,
    ReimbursementOut,
    ReimbursementSubmit,
    ReimbursementUpdate,
)
from app.services.approval_service import ApprovalService
from app.services.audit_service import AuditAction, AuditService
from app.services.export_service import ExportService
from app.services.reimbursement_service import ReimbursementService

router = APIRouter()


@router.get("", response_model=ApiResponse[PaginatedData[ReimbursementListItem]], summary="搜索报销申请")
async def list_reimbursements(
    pagination: PaginationParams = Depends(),
    keyword: str = None,
    status: str = None,
    project_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """列出报销申请（学生只看自己，教师/管理员可看全部）"""
    from app.models.reimbursement import ReimbursementStatus
    status_enum = ReimbursementStatus(status) if status else None
    svc = ReimbursementService(db)
    items, total = await svc.search(
        operator=current_user,
        keyword=keyword,
        status=status_enum,
        project_id=project_id,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    return ApiResponse.ok(
        data=PaginatedData.create(
            items=[ReimbursementListItem.model_validate(r) for r in items],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    )


@router.post("", response_model=ApiResponse[ReimbursementOut], summary="创建报销草稿")
async def create_reimbursement(
    body: ReimbursementCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ReimbursementService(db)
    reimb = await svc.create_draft(body, current_user)
    await AuditService(db).log_from_request(
        request, AuditAction.CREATE_REIMBURSEMENT, "创建报销草稿",
        user_id=current_user.id, username=current_user.username,
        target_type="reimbursement", target_id=reimb.id,
    )
    fresh = await svc.get_or_raise(reimb.id)
    return ApiResponse.ok(data=ReimbursementOut.model_validate(fresh), message="草稿已保存")


@router.get("/pending", response_model=ApiResponse[PaginatedData[ReimbursementListItem]], summary="待审批列表")
async def list_pending(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取审批人的待审批列表"""
    svc = ReimbursementService(db)
    items, total = await svc.get_pending_for_approver(
        approver=current_user, offset=pagination.offset, limit=pagination.page_size
    )
    return ApiResponse.ok(
        data=PaginatedData.create(
            items=[ReimbursementListItem.model_validate(r) for r in items],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    )


@router.get("/export/excel", summary="导出 Excel")
async def export_excel(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """将当前用户可见的报销申请导出为 Excel"""
    svc = ReimbursementService(db)
    items, _ = await svc.search(operator=current_user, limit=10000)
    export_svc = ExportService(db)
    content = await export_svc.export_excel(items)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=reimbursements.xlsx"},
    )


@router.get("/export/csv", summary="导出 CSV")
async def export_csv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ReimbursementService(db)
    items, _ = await svc.search(operator=current_user, limit=10000)
    export_svc = ExportService(db)
    content = await export_svc.export_csv(items)
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=reimbursements.csv"},
    )


@router.get("/{reimb_id}", response_model=ApiResponse[ReimbursementOut], summary="报销申请详情")
async def get_reimbursement(
    reimb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ReimbursementService(db)
    reimb = await svc.get_or_raise(reimb_id)
    # 权限检查：学生只能查看自己的申请
    from app.models.user import UserRole
    if current_user.role == UserRole.STUDENT and reimb.applicant_id != current_user.id:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException("无权查看该报销申请")
    return ApiResponse.ok(data=ReimbursementOut.model_validate(reimb))


@router.put("/{reimb_id}", response_model=ApiResponse[ReimbursementOut], summary="更新草稿")
async def update_reimbursement(
    reimb_id: int,
    body: ReimbursementUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ReimbursementService(db)
    reimb = await svc.get_or_raise(reimb_id)
    updated = await svc.update_draft(reimb, body, current_user)
    await AuditService(db).log_from_request(
        request, AuditAction.UPDATE_REIMBURSEMENT, "更新报销草稿",
        user_id=current_user.id, username=current_user.username,
        target_type="reimbursement", target_id=reimb_id,
    )
    fresh = await svc.get_or_raise(updated.id)
    return ApiResponse.ok(data=ReimbursementOut.model_validate(fresh), message="已保存")


@router.delete("/{reimb_id}", response_model=ApiResponse[None], summary="删除草稿")
async def delete_reimbursement(
    reimb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    svc = ReimbursementService(db)
    reimb = await svc.get_or_raise(reimb_id)
    await svc.delete_draft(reimb, current_user)
    return ApiResponse.ok(message="已删除")


@router.post("/{reimb_id}/submit", response_model=ApiResponse[ReimbursementOut], summary="提交申请")
async def submit_reimbursement(
    reimb_id: int,
    body: ReimbursementSubmit,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """提交报销申请进入审批流"""
    reimb_svc = ReimbursementService(db)
    approval_svc = ApprovalService(db)
    reimb = await reimb_svc.get_or_raise(reimb_id)
    # 金额校验 + 字段补充
    reimb = await reimb_svc.prepare_submit(reimb, body, current_user)
    # 状态推进
    reimb = await approval_svc.submit(reimb, current_user)
    await AuditService(db).log_from_request(
        request, AuditAction.SUBMIT_REIMBURSEMENT, "提交报销申请",
        user_id=current_user.id, username=current_user.username,
        target_type="reimbursement", target_id=reimb_id,
    )
    fresh = await reimb_svc.get_or_raise(reimb.id)
    return ApiResponse.ok(data=ReimbursementOut.model_validate(fresh), message="申请已提交")


@router.post("/{reimb_id}/recall", response_model=ApiResponse[ReimbursementOut], summary="撤回申请")
async def recall_reimbursement(
    reimb_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """申请人撤回已提交的报销申请"""
    reimb_svc = ReimbursementService(db)
    approval_svc = ApprovalService(db)
    reimb = await reimb_svc.get_or_raise(reimb_id)
    reimb = await approval_svc.recall(reimb, current_user)
    await AuditService(db).log_from_request(
        request, AuditAction.RECALL_REIMBURSEMENT, "撤回报销申请",
        user_id=current_user.id, username=current_user.username,
        target_type="reimbursement", target_id=reimb_id,
    )
    fresh = await reimb_svc.get_or_raise(reimb.id)
    return ApiResponse.ok(data=ReimbursementOut.model_validate(fresh), message="申请已撤回")
