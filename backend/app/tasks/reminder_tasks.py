"""
定时提醒任务
使用 APScheduler 定期检查审批超时，发送催办通知。
在应用启动时由 main.py 中的 lifespan 钩子注册。
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

from app.core.config import settings

# 全局调度器实例
_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler:
    """获取全局调度器（懒加载单例）"""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
    return _scheduler


async def _send_overdue_reminders_job() -> None:
    """定时任务：检查超时审批并发送催办通知"""
    from app.core.database import AsyncSessionLocal
    from app.services.reminder_service import ReminderService

    async with AsyncSessionLocal() as db:
        try:
            svc = ReminderService(db)
            count = await svc.send_overdue_reminders()
            if count > 0:
                logger.info(f"[定时催办] 发送了 {count} 条催办提醒")
            await db.commit()
        except Exception as e:
            logger.error(f"[定时催办] 执行失败：{e}")
            await db.rollback()


def start_scheduler() -> None:
    """
    启动调度器并注册所有定时任务。
    在 FastAPI lifespan 的启动阶段调用。
    """
    scheduler = get_scheduler()

    # 每隔 N 小时检查一次超时审批
    interval_hours = settings.APPROVAL_REMINDER_INTERVAL_HOURS
    scheduler.add_job(
        _send_overdue_reminders_job,
        trigger="interval",
        hours=interval_hours,
        id="overdue_reminder",
        replace_existing=True,
        misfire_grace_time=300,  # 最多允许延迟 5 分钟执行
    )

    scheduler.start()
    logger.info(f"定时任务调度器已启动（催办检查间隔：{interval_hours} 小时）")


def stop_scheduler() -> None:
    """关闭调度器（在 FastAPI lifespan 的关闭阶段调用）"""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已关闭")
