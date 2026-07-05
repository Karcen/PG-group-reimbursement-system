"""
Alembic 迁移环境配置
支持 async 引擎（aiosqlite），并从应用配置中读取数据库 URL。
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

# 导入应用配置和所有 ORM 模型（确保 metadata 完整）
from app.core.config import settings
from app.core.database import Base

# 导入所有模型，使其注册到 Base.metadata
import app.models  # noqa: F401

# Alembic Config 对象（提供对 alembic.ini 的访问）
config = context.config

# 设置 Python 日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标 metadata（用于自动生成迁移脚本）
target_metadata = Base.metadata


def _get_async_url() -> str:
    """从应用配置获取异步数据库 URL"""
    url = settings.DATABASE_URL
    if url.startswith("sqlite:///") and "aiosqlite" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return url


def run_migrations_offline() -> None:
    """离线模式：不连接数据库，直接生成 SQL 脚本"""
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # SQLite 需要 batch 模式以支持 ALTER TABLE
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在线模式：使用 async 引擎连接数据库执行迁移"""
    engine = create_async_engine(_get_async_url())
    async with engine.connect() as conn:
        await conn.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
