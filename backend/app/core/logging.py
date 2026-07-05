"""
日志配置模块
使用 loguru 替代标准库 logging，提供彩色终端输出和按天滚动的文件日志。
"""

import sys
from pathlib import Path

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """
    初始化日志系统。
    - 终端：彩色输出，开发环境显示 DEBUG，生产环境显示 INFO
    - 文件：按天滚动，保留 30 天，ERROR 级别单独写入 error.log
    """
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    # 清除默认 handler
    logger.remove()

    # 终端输出
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
    )

    # 全量日志文件（按天滚动，保留 30 天）
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        level="DEBUG",
        rotation="00:00",      # 每天零点新建文件
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
    )

    # 错误日志单独归档
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        level="ERROR",
        rotation="00:00",
        retention="90 days",
        compression="zip",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}\n{exception}",
    )
