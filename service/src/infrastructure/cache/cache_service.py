"""缓存服务。

封装 Token 黑名单和用户权限缓存的 Redis 操作。
所有方法对 Redis 操作做 try/except 降级处理，确保 Redis 异常不阻塞正常请求。
"""

import json
from datetime import datetime, timezone

import redis.asyncio as redis

from src.infrastructure.logging.logger import logger


class CacheService:
    """缓存服务，封装黑名单与权限缓存的 Redis 操作。"""

    # Key 前缀
    _BLACKLIST_PREFIX = "token:blacklist:"
    _PERMS_PREFIX = "user:perms:"

    # 权限缓存 TTL（秒）
    PERMS_CACHE_TTL = 300  # 5 分钟

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        self._redis = redis_client

    # ---- Token 黑名单 ----

    async def add_token_to_blacklist(self, token: str, expires_at: datetime) -> bool:
        """将 Token 加入黑名单。

        Args:
            token: 原始 JWT Token 字符串
            expires_at: Token 的过期时间

        Returns:
            是否成功加入黑名单
        """
        if self._redis is None:
            return True
        key = self._blacklist_key(token)
        ttl = self._remaining_seconds(expires_at)
        if ttl <= 0:
            # Token 已过期，无需加入黑名单
            return True
        try:
            await self._redis.set(key, "1", ex=ttl)
            return True
        except Exception:
            logger.warning("Redis 写入 Token 黑名单失败", exc_info=True)
            return False

    async def is_token_blacklisted(self, token: str) -> bool:
        """检查 Token 是否在黑名单中。

        Args:
            token: 原始 JWT Token 字符串

        Returns:
            True 表示已被拉黑，False 表示未拉黑或 Redis 不可用（降级放行）
        """
        if self._redis is None:
            return False
        key = self._blacklist_key(token)
        try:
            result = await self._redis.get(key)
            return result is not None
        except Exception:
            logger.warning("Redis 查询 Token 黑名单失败，降级放行", exc_info=True)
            return False

    # ---- 用户权限缓存 ----

    async def get_user_permissions(self, user_id: str) -> list[dict] | None:
        """从缓存获取用户权限列表。

        Args:
            user_id: 用户 ID

        Returns:
            权限列表（缓存命中时），None 表示缓存未命中或 Redis 不可用
        """
        if self._redis is None:
            return None
        key = self._perms_key(user_id)
        try:
            data = await self._redis.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception:
            logger.warning("Redis 读取用户权限缓存失败", exc_info=True)
            return None

    async def set_user_permissions(self, user_id: str, permissions: list[dict]) -> bool:
        """将用户权限列表写入缓存。

        Args:
            user_id: 用户 ID
            permissions: 权限列表（每个权限为 dict，含 role_name, menu_names 等）

        Returns:
            是否成功写入缓存
        """
        if self._redis is None:
            return False
        key = self._perms_key(user_id)
        try:
            await self._redis.set(key, json.dumps(permissions, ensure_ascii=False), ex=self.PERMS_CACHE_TTL)
            return True
        except Exception:
            logger.warning("Redis 写入用户权限缓存失败", exc_info=True)
            return False

    async def invalidate_user_permissions(self, user_id: str) -> bool:
        """使用户权限缓存失效。

        Args:
            user_id: 用户 ID

        Returns:
            是否成功失效
        """
        if self._redis is None:
            return False
        key = self._perms_key(user_id)
        try:
            await self._redis.delete(key)
            return True
        except Exception:
            logger.warning("Redis 删除用户权限缓存失败", exc_info=True)
            return False

    # ---- 内部方法 ----

    def _blacklist_key(self, token: str) -> str:
        """生成 Token 黑名单的 Redis Key。

        使用 token 的哈希前缀作为标识，避免存储完整 Token。
        """
        import hashlib

        token_hash = hashlib.sha256(token.encode()).hexdigest()[:32]
        return f"{self._BLACKLIST_PREFIX}{token_hash}"

    @staticmethod
    def _remaining_seconds(expires_at: datetime) -> int:
        """计算过期时间距当前时间的剩余秒数。"""
        now = datetime.now(timezone.utc)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        delta = (expires_at - now).total_seconds()
        return max(int(delta), 0)

    def _perms_key(self, user_id: str) -> str:
        """生成用户权限缓存的 Redis Key。"""
        return f"{self._PERMS_PREFIX}{user_id}"
