"""应用生命周期（启动 / 关闭）。"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config.settings import settings
from src.core.logger import log_shutdown, log_startup, logger
from src.infrastructure.database import close_db, init_db


@asynccontextmanager
async def application_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """生产/开发环境：日志、建表、关闭连接。"""
    log_startup(app_name=settings.APP_NAME, version=settings.API_VERSION, docs_url=app.docs_url, redoc_url=app.redoc_url)
    await init_db()
    logger.info("数据库初始化完成")
    yield
    logger.info("正在关闭数据库连接...")
    await close_db()
    logger.info("数据库连接已关闭")
    log_shutdown(settings.APP_NAME)


@asynccontextmanager
async def empty_lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """测试用：跳过数据库初始化，避免与内存测试库冲突。"""
    yield
