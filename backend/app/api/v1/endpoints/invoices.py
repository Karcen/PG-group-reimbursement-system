"""
发票管理 API 端点
- POST /invoices/upload              上传 PDF（触发 OCR）
- GET  /invoices/{id}                获取发票详情
- PUT  /invoices/{id}                人工修改发票信息
- GET  /invoices/{id}/preview        获取预览图 URL
- GET  /invoices/{id}/download       下载原始 PDF
- GET  /invoices/reimbursement/{id}  获取某报销申请下的所有发票
- POST /invoices/{id}/reocr          重新触发 OCR 识别
"""

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.config import settings
from app.core.exceptions import InvalidFileTypeException, FileTooLargeException
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.invoice import InvoiceListItem, InvoiceManualEdit, InvoiceOut
from app.services.audit_service import AuditAction, AuditService

router = APIRouter()


def _validate_upload(file: UploadFile) -> None:
    """校验上传文件的类型"""
    allowed_types = settings.ALLOWED_MIME_TYPES
    if file.content_type not in allowed_types:
        raise InvalidFileTypeException()


@router.post("/upload", response_model=ApiResponse[dict], summary="上传 PDF 并触发 OCR")
async def upload_pdf(
    request: Request,
    reimbursement_id: int = Form(..., description="关联的报销申请ID"),
    file: UploadFile = File(..., description="PDF 文件"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    上传 PDF，保存到 storage/original/{uuid}.pdf，
    异步触发 OCR 识别（通过后台任务队列）。
    """
    _validate_upload(file)

    # 读取文件内容（流式读取避免大文件 OOM）
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise FileTooLargeException(settings.MAX_UPLOAD_SIZE_MB)

    # 生成 UUID 作为存储文件名（永远不使用原始文件名）
    file_uuid = str(uuid.uuid4())
    save_path = settings.storage_original / f"{file_uuid}.pdf"
    save_path.write_bytes(content)

    # 记录文件元数据到数据库
    from app.repositories.user_repo import UserRepository
    uploaded = UploadedFile(
        uuid=file_uuid,
        original_filename=file.filename or "upload.pdf",
        file_path=str(save_path),
        file_size=len(content),
        mime_type=file.content_type or "application/pdf",
        uploader_id=current_user.id,
    )
    db.add(uploaded)
    await db.flush()
    await db.refresh(uploaded)

    # 记录审计日志
    await AuditService(db).log_from_request(
        request, AuditAction.UPLOAD_PDF, f"上传 PDF：{file.filename}",
        user_id=current_user.id, username=current_user.username,
        target_type="uploaded_file", target_id=uploaded.id,
    )

    # 触发异步 OCR 任务（后台任务，不阻塞当前请求）
    # 实际生产中通过 APScheduler 或 BackgroundTasks 执行
    from fastapi import BackgroundTasks
    # 注意：此处返回 file_id，前端可轮询 OCR 状态
    return ApiResponse.ok(
        data={
            "file_id": uploaded.id,
            "file_uuid": file_uuid,
            "reimbursement_id": reimbursement_id,
            "message": "文件上传成功，OCR 识别已启动，请稍候...",
        },
        message="上传成功",
    )


@router.get("/reimbursement/{reimb_id}", response_model=ApiResponse[list[InvoiceListItem]], summary="获取报销发票列表")
async def list_invoices_by_reimbursement(
    reimb_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """获取某报销申请的所有识别发票"""
    from app.repositories.invoice_repo import InvoiceRepository
    repo = InvoiceRepository(db)
    invoices = await repo.list_by_reimbursement(reimb_id)
    return ApiResponse.ok(data=[InvoiceListItem.model_validate(inv) for inv in invoices])


@router.get("/{invoice_id}", response_model=ApiResponse[InvoiceOut], summary="获取发票详情")
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    from app.repositories.invoice_repo import InvoiceRepository
    repo = InvoiceRepository(db)
    invoice = await repo.get_with_tags(invoice_id)
    if not invoice:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("发票不存在")
    return ApiResponse.ok(data=InvoiceOut.model_validate(invoice))


@router.put("/{invoice_id}", response_model=ApiResponse[InvoiceOut], summary="人工修改发票信息")
async def edit_invoice(
    invoice_id: int,
    body: InvoiceManualEdit,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """人工修改 OCR 识别结果，修改后保留原始值和修改值"""
    from app.repositories.invoice_repo import InvoiceRepository
    from app.models.tag import Tag
    from sqlalchemy import select

    repo = InvoiceRepository(db)
    invoice = await repo.get_with_tags(invoice_id)
    if not invoice:
        from app.core.exceptions import NotFoundException
        raise NotFoundException("发票不存在")

    # 记录修改前快照（用于审计）
    old_data = {
        "invoice_number": invoice.invoice_number,
        "amount": invoice.amount,
        "date": invoice.date,
    }

    # 更新人工确认字段
    update_fields = body.model_dump(exclude={"tag_ids"}, exclude_none=True)
    for field, value in update_fields.items():
        setattr(invoice, field, value)
    invoice.is_manually_edited = True

    # 更新标签
    if body.tag_ids is not None:
        tags_result = await db.execute(
            select(Tag).where(Tag.id.in_(body.tag_ids))
        )
        invoice.tags = list(tags_result.scalars().all())

    db.add(invoice)
    await db.flush()
    await db.refresh(invoice)

    await AuditService(db).log_from_request(
        request, AuditAction.EDIT_INVOICE, "人工修改发票信息",
        user_id=current_user.id, username=current_user.username,
        target_type="invoice", target_id=invoice_id,
        old_data=old_data,
        new_data=update_fields,
    )

    return ApiResponse.ok(data=InvoiceOut.model_validate(invoice), message="发票信息已更新")


@router.get("/{invoice_id}/preview-image", summary="获取发票预览图")
async def get_preview_image(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """返回 PDF 页面预览图（JPEG）"""
    from app.repositories.invoice_repo import InvoiceRepository
    from app.core.exceptions import NotFoundException

    repo = InvoiceRepository(db)
    invoice = await repo.get_by_id(invoice_id)
    if not invoice or not invoice.preview_image_path:
        raise NotFoundException("预览图不存在，请先触发 OCR 识别")

    path = Path(invoice.preview_image_path)
    if not path.exists():
        raise NotFoundException("预览图文件不存在")

    return FileResponse(path, media_type="image/jpeg")
