"""
OCR 后台任务
在 PDF 上传后异步执行 OCR 识别 + AI 信息提取，
完成后更新数据库并发送通知给申请人。
"""

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.invoice_extractor import InvoiceExtractor, result_to_invoice
from app.core.database import AsyncSessionLocal
from app.models.notification import NotificationType
from app.services.notification_service import NotificationService


async def run_ocr_for_file(
    file_id: int,
    reimbursement_id: int,
    applicant_id: int,
) -> None:
    """
    异步 OCR 任务入口。
    对上传文件的每一页执行 OCR + AI 提取，将结果保存为 Invoice 记录。

    :param file_id:          UploadedFile 的数据库 ID
    :param reimbursement_id: 关联的报销申请 ID
    :param applicant_id:     申请人用户 ID（用于发送完成通知）
    """
    async with AsyncSessionLocal() as db:
        try:
            from app.repositories.invoice_repo import InvoiceRepository
            from app.models.uploaded_file import UploadedFile

            # 获取文件记录
            uploaded_file = await db.get(UploadedFile, file_id)
            if not uploaded_file:
                logger.error(f"OCR 任务：文件 ID={file_id} 不存在")
                return

            logger.info(f"OCR 任务启动：file_id={file_id}, reimb_id={reimbursement_id}")

            # 执行 OCR + AI 提取
            extractor = InvoiceExtractor()
            results = await extractor.extract_from_file(uploaded_file)

            if not results:
                logger.warning(f"OCR 任务：文件 ID={file_id} 未提取到任何结果")
                return

            # 保存 Invoice 记录到数据库
            invoice_repo = InvoiceRepository(db)
            for result in results:
                invoice = result_to_invoice(
                    result=result,
                    reimbursement_id=reimbursement_id,
                    file_id=file_id,
                )
                db.add(invoice)

            # 更新文件页数
            uploaded_file.page_count = len(results)
            db.add(uploaded_file)

            await db.commit()
            logger.info(f"OCR 任务完成：file_id={file_id}，识别 {len(results)} 张票据")

            # 发送 OCR 完成通知给申请人
            notification_svc = NotificationService(db)
            await notification_svc.notify_ocr_done(
                user_id=applicant_id,
                reimbursement_id=reimbursement_id,
            )
            await db.commit()

        except Exception as e:
            logger.exception(f"OCR 任务异常：file_id={file_id}，错误：{e}")
            await db.rollback()
