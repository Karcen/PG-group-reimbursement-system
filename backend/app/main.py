"""
FastAPI 应用入口
负责：应用实例化、中间件注册、路由挂载、全局异常处理、生命周期钩子。
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging


# ─── 生命周期钩子 ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动 / 关闭钩子"""
    # 启动时
    setup_logging()
    _ensure_storage_dirs()
    # 启动定时任务调度器（审批超时催办）
    from app.tasks.reminder_tasks import start_scheduler
    start_scheduler()
    logger.info(f"🚀 {settings.APP_NAME} 启动成功，环境：{settings.APP_ENV}")
    yield
    # 关闭时
    from app.tasks.reminder_tasks import stop_scheduler
    stop_scheduler()
    logger.info("👋 应用正在关闭...")


def _ensure_storage_dirs() -> None:
    """确保存储目录存在（容器或首次运行时创建）"""
    for d in [
        settings.storage_original,
        settings.storage_ocr,
        settings.storage_preview,
        settings.storage_thumbnails,
        settings.storage_payment_records,   # 付款凭证目录
    ]:
        d.mkdir(parents=True, exist_ok=True)


# ─── 应用实例 ──────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """工厂函数：创建并配置 FastAPI 应用实例"""

    app = FastAPI(
        title=settings.APP_NAME,
        description="实验室报销管理系统 API 文档",
        version="1.0.0",
        docs_url="/docs" if settings.is_development else None,  # 生产环境关闭 Swagger UI
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    _register_middlewares(app)
    _register_routers(app)
    _register_exception_handlers(app)

    return app


def _register_middlewares(app: FastAPI) -> None:
    """注册中间件"""

    # CORS（允许前端跨域访问）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 请求耗时日志中间件
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = (time.perf_counter() - start) * 1000
        logger.debug(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} ({elapsed:.1f}ms)"
        )
        return response


def _register_routers(app: FastAPI) -> None:
    """挂载所有 API 路由"""
    from app.api.v1.router import api_router

    app.include_router(api_router, prefix="/api/v1")

    # 健康检查（Docker / LB 探针使用，无需认证）
    @app.get("/health", tags=["系统"])
    async def health_check():
        return {"status": "ok", "app": settings.APP_NAME}


def _register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器，统一返回结构化 JSON 错误"""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "code": exc.code,
                "message": exc.message,
                "data": exc.data,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception(f"未处理的异常：{exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误，请联系管理员",
                "data": None,
            },
        )


# 创建全局应用实例（供 uvicorn 直接使用）
app = create_app()
