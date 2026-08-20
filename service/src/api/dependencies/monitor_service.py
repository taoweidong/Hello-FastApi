"""监控应用服务工厂。"""

import redis.asyncio as redis_async
from loguru import logger

from src.application.services.monitor_service import MonitorService
from src.infrastructure.cache.redis_manager import get_redis


async def get_redis_or_none() -> redis_async.Redis | None:
    """获取 Redis 客户端，获取失败时返回 None（触发缓存监控降级响应）。"""
    try:
        return await get_redis()
    except Exception as exc:  # noqa: BLE001 —— Redis 不可用时降级而非报错
        logger.warning(f"缓存监控获取 Redis 客户端失败：{exc}")
        return None


def get_monitor_service() -> MonitorService:
    """获取监控服务实例（无状态，无需数据库会话）。"""
    return MonitorService()
