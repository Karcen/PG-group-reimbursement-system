"""
数据库初始化脚本
创建默认管理员账号、默认发票标签和示例经费项目。
首次部署时运行：python -m app.scripts.init_db
"""

import asyncio
import sys
from pathlib import Path

# 确保能找到项目根目录
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from loguru import logger
from app.core.security import hash_password


async def main() -> None:
    """执行数据库初始化"""
    from app.core.config import settings
    from app.core.database import AsyncSessionLocal, Base, engine
    from app.core.security import hash_password
    from app.models import User, UserRole, Tag, Project, ApprovalFlow  # 触发所有模型注册

    # 1. 创建所有表
    logger.info("正在创建数据库表...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表创建完成")

    async with AsyncSessionLocal() as db:
        await _create_admin(db, settings)
        await _create_default_tags(db)
        await _create_sample_project(db)
        await db.commit()

    logger.info("✅ 数据库初始化完成！")
    logger.info(f"  管理员用户名：{settings.INIT_ADMIN_USERNAME}")
    logger.info(f"  管理员密码：{settings.INIT_ADMIN_PASSWORD}")
    logger.info("  ⚠️  请立即修改默认密码！")


async def _create_admin(db, settings) -> None:
    """创建默认管理员账号（已存在则跳过）"""
    from app.models import User, UserRole
    from sqlalchemy import select

    existing = await db.execute(
        select(User).where(User.username == settings.INIT_ADMIN_USERNAME)
    )
    if existing.scalar_one_or_none():
        logger.info(f"管理员账号 '{settings.INIT_ADMIN_USERNAME}' 已存在，跳过")
        return

    admin = User(
        username=settings.INIT_ADMIN_USERNAME,
        email=settings.INIT_ADMIN_EMAIL,
        hashed_password=hash_password(settings.INIT_ADMIN_PASSWORD),
        full_name="系统管理员",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    logger.info(f"已创建管理员账号：{admin.username}")

    # 同时创建一个示例教师和学生账号（方便演示）
    teacher = User(
        username="teacher1",
        email="teacher1@lab.edu.cn",
        hashed_password=hash_password("Teacher@123456"),
        full_name="示例教师",
        role=UserRole.TEACHER,
        department="计算机科学与技术系",
        is_active=True,
    )
    student = User(
        username="student1",
        email="student1@lab.edu.cn",
        hashed_password=hash_password("Student@123456"),
        full_name="示例学生",
        role=UserRole.STUDENT,
        student_id="2021000001",
        department="计算机科学与技术系",
        is_active=True,
    )
    db.add(teacher)
    db.add(student)
    await db.flush()
    logger.info("已创建示例教师和学生账号")


async def _create_default_tags(db) -> None:
    """创建默认发票标签（已存在则跳过）"""
    from app.models import Tag
    from sqlalchemy import select

    existing = await db.execute(select(Tag))
    if existing.scalars().first():
        logger.info("标签已存在，跳过")
        return

    default_tags = [
        Tag(name="差旅", color="#FF6B6B", description="出差交通、住宿等费用"),
        Tag(name="会议", color="#4ECDC4", description="会议注册费、会议材料等"),
        Tag(name="耗材", color="#45B7D1", description="实验室耗材、试剂等"),
        Tag(name="办公", color="#96CEB4", description="办公用品、打印等"),
        Tag(name="出版", color="#FFEAA7", description="论文版面费、图书资料等"),
        Tag(name="设备", color="#DDA0DD", description="设备购置、维修等"),
        Tag(name="劳务", color="#98D8C8", description="劳务报酬等"),
    ]
    for tag in default_tags:
        db.add(tag)
    await db.flush()
    logger.info(f"已创建 {len(default_tags)} 个默认标签")


async def _create_sample_project(db) -> None:
    """创建示例经费项目（已存在则跳过）"""
    from app.models import Project, ApprovalFlow, User, UserRole
    from sqlalchemy import select

    existing = await db.execute(select(Project))
    if existing.scalars().first():
        logger.info("经费项目已存在，跳过")
        return

    # 获取第一个教师作为审批人
    teacher = (
        await db.execute(select(User).where(User.role == UserRole.TEACHER).limit(1))
    ).scalar_one_or_none()

    if not teacher:
        logger.warning("未找到教师账号，跳过示例项目创建")
        return

    project = Project(
        name="国家自然科学基金（示例）",
        code="NSFC-2024-001",
        description="示例经费项目，可在系统管理中修改",
        budget=100000.0,
    )
    db.add(project)
    await db.flush()

    # 配置审批流：由 teacher1 负责审批
    flow = ApprovalFlow(
        project_id=project.id,
        approver_id=teacher.id,
        step=1,
    )
    db.add(flow)
    await db.flush()
    logger.info(f"已创建示例项目：{project.name}，审批人：{teacher.full_name}")


if __name__ == "__main__":
    asyncio.run(main())
