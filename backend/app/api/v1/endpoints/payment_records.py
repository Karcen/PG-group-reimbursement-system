"""
付款凭证 API 端点
当报销金额超过阈值时，学生必须在此上传银行卡/支付宝/微信转账截图。

- POST /payment-records/upload  上传付款凭证（图片或 PDF）
- GET  /payment-records/reimbursement/{id}  获取某报销的全部凭证
- DELETE /payment-records/{id}  删除凭证（仅草稿状态可删）
"""

import uuid as uuid_lib
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_session
from app.core.config import settings
from app.core.exceptions import (
    FileTooLargeException,
    ForbiddenException,
    InvalidFileTypeException,
    NotFoundException,
    WorkflowException,
)
from app.models.payment_record import PaymentRecord, PaymentType
from app.models.reimbursement import ReimbursementStatus
from app.models.user import User, UserRole
from app.schemas.common import ApiResponse
from app.schemas.payment_record import PaymentRecordOut

router = APIRouter()

# 付款凭证允许的 MIME 类型（图片 + PDF）
_ALLOWED_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf",
}


def _validate_file(file: UploadFile) -> None:
    if file.content_type not in _ALLOWED_TYPES:
        raise InvalidFileTypeException()


@router.post(
    "/upload",
    response_model=ApiResponse[PaymentRecordOut],
    summary="上传付款凭证",
)
async def upload_payment_record(
    reimbursement_id: int = Form(..., description="关联报销申请ID"),
    payment_type: PaymentType = Form(default=PaymentType.OTHER, description="付款方式"),
    description: str = Form(default="", description="备注说明"),
    file: UploadFile = File(..., description="转账截图或付款凭证（图片/PDF）"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    上传付款凭证截图。
    金额超过阈值时提交前必须至少上传一条记录。
    凭证文件以 UUID 命名永久保存，不可覆盖。
    """
    _validate_file(file)

    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise FileTooLargeException(settings.MAX_UPLOAD_SIZE_MB)

    # 确保关联的报销申请存在且状态允许
    from app.models.reimbursement import Reimbursement
    reimb = await db.get(Reimbursement, reimbursement_id)
    if not reimb:
        raise NotFoundException("报销申请不存在")
    if reimb.applicant_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise ForbiddenException("只有申请人本人才能上传凭证")
    if reimb.status not in (ReimbursementStatus.DRAFT, ReimbursementStatus.REJECTED):
        raise WorkflowException("只有草稿或驳回状态的申请才能上传付款凭证")

    # 保存文件
    file_uuid = str(uuid_lib.uuid4())
    # 根据 MIME 类型选择扩展名
    ext_map = {
        "image/jpeg": ".jpg", "image/png": ".png",
        "image/gif": ".gif", "image/webp": ".webp",
        "application/pdf": ".pdf",
    }
    ext = ext_map.get(file.content_type or "", ".bin")
    save_path = settings.storage_payment_records / f"{file_uuid}{ext}"
    settings.storage_payment_records.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(content)

    record = PaymentRecord(
        uuid=file_uuid,
        reimbursement_id=reimbursement_id,
        original_filename=file.filename or f"payment{ext}",
        file_path=str(save_path),
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        payment_type=payment_type,
        description=description or None,
        uploader_id=current_user.id,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)

    return ApiResponse.ok(
        data=PaymentRecordOut.model_validate(record),
        message="付款凭证上传成功",
    )


@router.get(
    "/reimbursement/{reimbursement_id}",
    response_model=ApiResponse[list[PaymentRecordOut]],
    summary="获取某报销申请的付款凭证列表",
)
async def list_payment_records(
    reimbursement_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(PaymentRecord)
        .where(PaymentRecord.reimbursement_id == reimbursement_id)
        .order_by(PaymentRecord.created_at)
    )
    records = result.scalars().all()
    return ApiResponse.ok(data=[PaymentRecordOut.model_validate(r) for r in records])


@router.get(
    "/{record_id}/file",
    summary="预览/下载付款凭证文件",
)
async def get_payment_record_file(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    record = await db.get(PaymentRecord, record_id)
    if not record:
        raise NotFoundException("付款凭证不存在")
    path = Path(record.file_path)
    if not path.exists():
        raise NotFoundException("凭证文件已丢失，请重新上传")
    return FileResponse(path, media_type=record.mime_type)


@router.delete(
    "/{record_id}",
    response_model=ApiResponse[None],
    summary="删除付款凭证",
)
async def delete_payment_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """只有草稿/驳回状态的申请才允许删除凭证"""
    record = await db.get(PaymentRecord, record_id)
    if not record:
        raise NotFoundException("付款凭证不存在")

    # 鉴权
    from app.models.reimbursement import Reimbursement
    reimb = await db.get(Reimbursement, record.reimbursement_id)
    if reimb and reimb.applicant_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise ForbiddenException("无权删除此凭证")
    if reimb and reimb.status not in (ReimbursementStatus.DRAFT, ReimbursementStatus.REJECTED):
        raise WorkflowException("只有草稿或驳回状态的申请才能删除凭证")

    await db.delete(record)
    await db.flush()
    return ApiResponse.ok(message="凭证已删除")
