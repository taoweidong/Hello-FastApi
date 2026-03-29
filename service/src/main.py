"""FastAPI 应用程序工厂和入口点。"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.v1 import system_router
from src.config.settings import settings
from src.core.constants import API_SYSTEM_PREFIX
from src.core.exceptions import AppException
from src.core.logger import log_shutdown, log_startup, logger
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
        docs_url=f"{API_SYSTEM_PREFIX}/docs",
        redoc_url=f"{API_SYSTEM_PREFIX}/redoc",
        openapi_url=f"{API_SYSTEM_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 请求日志中间件
    from src.core.middlewares import RequestLoggingMiddleware

    app.add_middleware(RequestLoggingMiddleware)

    # 全局异常处理
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "message": str(exc.detail)}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """处理参数验证错误"""
        return JSONResponse(
            status_code=422,
            content={"code": 422, "message": "参数验证失败", "errors": exc.errors()}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "Internal server error"}
        )

    # 健康检查
    @app.get("/health")
    async def health_check() -> dict:
        return {"status": "healthy", "version": settings.API_VERSION}

    # 注册 API 路由
    app.include_router(system_router, prefix=API_SYSTEM_PREFIX)

    return app


app = create_app()
