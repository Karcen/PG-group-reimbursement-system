"""
数据库连接与会话管理
使用 SQLAlchemy 2.x async 引擎 + aiosqlite 驱动。
所有数据库操作通过依赖注入获取 AsyncSession。
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """
    所有 ORM 模型的基类。
    通过继承此类，模型自动注册到 metadata，
    供 Alembic 自动生成迁移脚本使用。
    """
    pass


def _build_async_url(url: str) -> str:
    """
    将 SQLite 连接 URL 转换为异步驱动格式。
    sqlite:///xxx  →  sqlite+aiosqlite:///xxx
    """
    if url.startswith("sqlite:///") and "aiosqlite" not in url:
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return url


# 创建异步引擎
_async_url = _build_async_url(settings.DATABASE_URL)
engine = create_async_engine(
    _async_url,
    echo=settings.is_development,   # 开发环境打印 SQL 语句
    connect_args={"check_same_thread": False},  # SQLite 跨线程访问
    pool_pre_ping=True,
)

# 会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不过期，方便在视图中继续访问字段
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 依赖注入函数。
    用法：
        async def some_endpoint(db: AsyncSession = Depends(get_db)):
            ...
    每个请求独享一个 Session，请求结束后自动关闭。
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_all_tables() -> None:
    """
    开发 / 测试时用于快速创建所有表（生产环境改用 Alembic 迁移）。
    调用此函数前需确保所有 model 模块已被导入，否则 metadata 不完整。
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
