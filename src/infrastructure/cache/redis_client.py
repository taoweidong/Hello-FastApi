"""Redis 缓存连接管理。"""

import redis.asyncio as redis
from config.settings import settings

_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """获取或创建 Redis 客户端实例。"""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """关闭 Redis 连接。"""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
