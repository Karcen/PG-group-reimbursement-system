"""
pytest 测试配置与 Fixture 定义
提供：
  - 异步测试引擎配置
  - 内存 SQLite 测试数据库
  - 测试客户端（TestClient）
  - 默认测试用户 Fixture
"""

import asyncio
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import hash_password
from app.main import app
from app.models import User, UserRole

# 使用内存 SQLite 作为测试数据库，每次测试套件独立
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ─── 会话级别 Fixture ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    """覆盖默认 event_loop，使用 session 级别"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """创建所有测试表（会话开始时执行一次）"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ─── 函数级别 Fixture ──────────────────────────────────────────────────────

@pytest.fixture
async def db() -> AsyncSession:
    """每个测试函数获得独立的数据库会话，测试结束后回滚"""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db: AsyncSession) -> AsyncClient:
    """注入测试数据库的 HTTP 测试客户端"""
    app.dependency_overrides[get_db] = lambda: db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ─── 测试用户 Fixture ──────────────────────────────────────────────────────

@pytest.fixture
async def admin_user(db: AsyncSession) -> User:
    """创建测试管理员用户"""
    user = User(
        username="test_admin",
        email="admin@test.com",
        hashed_password=hash_password("Admin@123456"),
        full_name="测试管理员",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest.fixture
async def teacher_user(db: AsyncSession) -> User:
    """创建测试教师用户"""
    user = User(
        username="test_teacher",
        email="teacher@test.com",
        hashed_password=hash_password("Teacher@123456"),
        full_name="测试教师",
        role=UserRole.TEACHER,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest.fixture
async def student_user(db: AsyncSession) -> User:
    """创建测试学生用户"""
    user = User(
        username="test_student",
        email="student@test.com",
        hashed_password=hash_password("Student@123456"),
        full_name="测试学生",
        role=UserRole.STUDENT,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    """获取管理员 Access Token"""
    res = await client.post("/api/v1/auth/login", json={
        "username": "test_admin",
        "password": "Admin@123456",
    })
    return res.json()["data"]["access_token"]


@pytest.fixture
async def student_token(client: AsyncClient, student_user: User) -> str:
    """获取学生 Access Token"""
    res = await client.post("/api/v1/auth/login", json={
        "username": "test_student",
        "password": "Student@123456",
    })
    return res.json()["data"]["access_token"]
