"""FastAPI 应用程序工厂和入口点。"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.v1 import v1_router
from src.config.settings import settings
from src.core.constants import API_PREFIX
from src.core.exceptions import AppException
from src.core.logger import log_shutdown, log_startup, logger
from src.core.middlewares import RequestLoggingMiddleware
from src.infrastructure.database import close_db, init_db


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理器 - 启动和关闭。"""
    # 启动
    log_startup(settings.APP_NAME, settings.API_VERSION)
    await init_db()
    logger.info("数据库初始化完成")
    yield
    # 关闭
    logger.info("正在关闭数据库连接...")
    await close_db()
    logger.info("数据库连接已关闭")
    log_shutdown(settings.APP_NAME)


def create_app() -> FastAPI:
    """应用程序工厂 - 创建并配置 FastAPI 应用。"""
    app = FastAPI(
        title=settings.APP_NAME,
        description="FastAPI + DDD + RBAC API Service",
        version=settings.API_VERSION,
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=f"{API_PREFIX}/redoc",
        openapi_url=f"{API_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Global exception handler
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # 健康检查
    @app.get("/health")
    async def health_check() -> dict:
        return {"status": "healthy", "version": settings.API_VERSION}

    # 注册 API 路由
    app.include_router(v1_router, prefix=API_PREFIX)

    return app


app = create_app()
