"""Redis 缓存连接管理器。"""

import redis.asyncio as redis

from src.config.settings import settings


class RedisManager:
    """Redis 管理器，封装客户端生命周期。"""

    def __init__(self, redis_url: str | None = None, encoding: str = "utf-8", decode_responses: bool = True) -> None:
        self._url = redis_url or settings.REDIS_URL
        self._encoding = encoding
        self._decode_responses = decode_responses
        self._client: redis.Redis | None = None

    async def get_client(self) -> redis.Redis:
        """获取或创建 Redis 客户端实例。"""
        if self._client is None:
            self._client = redis.from_url(self._url, encoding=self._encoding, decode_responses=self._decode_responses)
        return self._client

    async def close(self) -> None:
        """关闭 Redis 连接。"""
        if self._client is not None:
            await self._client.close()
            self._client = None


# ── 模块级单例 & 兼容函数 ──────────────────────────────────────────

_redis_manager: RedisManager | None = None


def _get_redis_manager() -> RedisManager:
    """获取或创建 RedisManager 单例。"""
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager


async def get_redis() -> redis.Redis:
    """获取或创建 Redis 客户端实例（兼容旧接口）。"""
    return await _get_redis_manager().get_client()


async def close_redis() -> None:
    """关闭 Redis 连接（兼容旧接口）。"""
    global _redis_manager
    if _redis_manager is not None:
        await _redis_manager.close()
        _redis_manager = None
