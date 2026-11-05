"""监控应用服务工厂。"""

import redis.asyncio as redis_async
from fastapi import Depends
from loguru import logger

from src.api.dependencies.cache_service import get_cache_service, get_online_session_store
from src.application.services.monitor_service import MonitorService
from src.domain.services.cache_port import TokenRevocationPort
from src.domain.services.online_session_port import OnlineSessionStore
from src.infrastructure.cache.redis_manager import get_redis


async def get_redis_or_none() -> redis_async.Redis | None:
    """获取 Redis 客户端，获取失败时返回 None（触发缓存监控降级响应）。"""
    try:
        return await get_redis()
    except Exception as exc:  # noqa: BLE001 —— Redis 不可用时降级而非报错
        logger.warning(f"缓存监控获取 Redis 客户端失败：{exc}")
        return None


async def get_monitor_service(
    session_store: OnlineSessionStore = Depends(get_online_session_store),
    token_revocation: TokenRevocationPort = Depends(get_cache_service),
) -> MonitorService:
    """获取监控服务实例。

    在线用户会话查询走 ``OnlineSessionStore``，强制下线时拉黑令牌走 ``TokenRevocationPort``。
    """
    return MonitorService(session_store=session_store, token_revocation=token_revocation)
