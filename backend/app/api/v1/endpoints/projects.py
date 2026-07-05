"""
经费项目 API 端点
- GET  /projects          列出项目（支持搜索）
- POST /projects          创建项目（管理员）
- GET  /projects/active   获取启用项目列表（学生提交时使用）
- GET  /projects/{id}     获取项目详情（含审批流）
- PUT  /projects/{id}     更新项目（管理员）
- POST /projects/{id}/flows  更新项目审批流（管理员）
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session, require_admin
from app.models.user import User
from app.schemas.common import ApiResponse, PaginatedData, PaginationParams
from app.schemas.project import (
    ApprovalFlowStepCreate,
    ProjectBrief,
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
)
from app.services.audit_service import AuditAction, AuditService

router = APIRouter()


@router.get("", response_model=ApiResponse[PaginatedData[ProjectOut]], summary="列出经费项目")
async def list_projects(
    pagination: PaginationParams = Depends(),
    keyword: str = None,
    is_active: bool = None,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    from app.repositories.project_repo import ProjectRepository
    repo = ProjectRepository(db)
    items, total = await repo.search(
        keyword=keyword, is_active=is_active,
        offset=pagination.offset, limit=pagination.page_size,
    )
    return ApiResponse.ok(
        data=PaginatedData.create(
            items=[ProjectOut.model_validate(p) for p in items],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    )


@router.get("/active", response_model=ApiResponse[list[ProjectBrief]], summary="获取启用项目（下拉用）")
async def list_active_projects(
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    from app.repositories.project_repo import ProjectRepository
    repo = ProjectRepository(db)
    items = await repo.list_active()
    return ApiResponse.ok(data=[ProjectBrief.model_validate(p) for p in items])


@router.post("", response_model=ApiResponse[ProjectOut], summary="创建经费项目")
async def create_project(
    body: ProjectCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    from app.repositories.project_repo import ProjectRepository
    from app.models.project import ApprovalFlow, Project
    from app.core.exceptions import ConflictException

    repo = ProjectRepository(db)
    if await repo.get_by_code(body.code):
        raise ConflictException(f"项目编号 '{body.code}' 已存在")

    project = Project(
        name=body.name,
        code=body.code,
        description=body.description,
        budget=body.budget,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)

    # 写入审批流
    for step_data in sorted(body.approval_steps, key=lambda s: s.step):
        flow = ApprovalFlow(
            project_id=project.id,
            approver_id=step_data.approver_id,
            step=step_data.step,
        )
        db.add(flow)
    await db.flush()

    await AuditService(db).log_from_request(
        request, AuditAction.CREATE_PROJECT, f"创建项目：{project.name}",
        user_id=admin.id, username=admin.username,
        target_type="project", target_id=project.id,
    )
    fresh = await repo.get_with_flows(project.id)
    return ApiResponse.ok(data=ProjectOut.model_validate(fresh), message="项目创建成功")


@router.get("/{project_id}", response_model=ApiResponse[ProjectOut], summary="项目详情")
async def get_project(
    project_id: int,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    from app.repositories.project_repo import ProjectRepository
    from app.core.exceptions import NotFoundException
    repo = ProjectRepository(db)
    project = await repo.get_with_flows(project_id)
    if not project:
        raise NotFoundException("项目不存在")
    return ApiResponse.ok(data=ProjectOut.model_validate(project))


@router.put("/{project_id}", response_model=ApiResponse[ProjectOut], summary="更新项目")
async def update_project(
    project_id: int,
    body: ProjectUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    from app.repositories.project_repo import ProjectRepository
    from app.core.exceptions import NotFoundException
    repo = ProjectRepository(db)
    project = await repo.get_with_flows(project_id)
    if not project:
        raise NotFoundException("项目不存在")
    await repo.update(project, body.model_dump(exclude_none=True))
    await AuditService(db).log_from_request(
        request, AuditAction.UPDATE_PROJECT, f"更新项目：{project.name}",
        user_id=admin.id, username=admin.username,
        target_type="project", target_id=project_id,
    )
    fresh = await repo.get_with_flows(project_id)
    return ApiResponse.ok(data=ProjectOut.model_validate(fresh), message="项目已更新")


@router.put("/{project_id}/flows", response_model=ApiResponse[ProjectOut], summary="更新项目审批流")
async def update_project_flows(
    project_id: int,
    flows: list[ApprovalFlowStepCreate],
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db_session),
):
    """重新配置项目的审批流（先删除再插入）"""
    from app.repositories.project_repo import ProjectRepository
    from app.models.project import ApprovalFlow
    from app.core.exceptions import NotFoundException
    from sqlalchemy import delete

    repo = ProjectRepository(db)
    project = await repo.get_with_flows(project_id)
    if not project:
        raise NotFoundException("项目不存在")

    # 删除旧审批流
    await db.execute(
        delete(ApprovalFlow).where(ApprovalFlow.project_id == project_id)
    )
    # 插入新审批流
    for step_data in sorted(flows, key=lambda s: s.step):
        flow = ApprovalFlow(
            project_id=project_id,
            approver_id=step_data.approver_id,
            step=step_data.step,
        )
        db.add(flow)
    await db.flush()

    fresh = await repo.get_with_flows(project_id)
    return ApiResponse.ok(data=ProjectOut.model_validate(fresh), message="审批流已更新")
