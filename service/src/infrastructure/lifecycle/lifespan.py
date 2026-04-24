"""应用生命周期（启动 / 关闭）。"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config.settings import settings
from src.infrastructure.cache.redis_manager import close_redis, get_redis
from src.infrastructure.database import close_db, init_db
from src.infrastructure.logging.logger import log_shutdown, log_startup, logger


@asynccontextmanager
async def application_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """生产/开发环境：日志、建表、Redis初始化、关闭连接。"""
    log_startup(
        app_name=settings.APP_NAME, version=settings.API_VERSION, docs_url=app.docs_url, redoc_url=app.redoc_url
    )
    await init_db()
    logger.info("数据库初始化完成")

    # 初始化 Redis 连接
    try:
        redis_client = await get_redis()
        await redis_client.ping()
        logger.info("Redis 连接初始化完成")
    except Exception:
        logger.warning("Redis 连接初始化失败，缓存功能将降级为直接查库", exc_info=True)

    # 加载 IP 黑白名单规则到 app.state
    try:
        from src.infrastructure.http.ip_filter_cache import get_ip_filter_cache

        ip_filter_cache = get_ip_filter_cache()
        await ip_filter_cache.load_to_app_state(app)
        logger.info("IP 黑白名单规则加载完成")
    except Exception:
        logger.warning("IP 黑白名单规则加载失败，IP 过滤将以空规则运行", exc_info=True)

    yield

    # 关闭 Redis 连接
    logger.info("正在关闭 Redis 连接...")
    await close_redis()
    logger.info("Redis 连接已关闭")

    # 关闭数据库连接
    logger.info("正在关闭数据库连接...")
    await close_db()
    logger.info("数据库连接已关闭")
    log_shutdown(settings.APP_NAME)


@asynccontextmanager
async def empty_lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """测试用：跳过数据库和 Redis 初始化，避免与内存测试库冲突。"""
    yield
