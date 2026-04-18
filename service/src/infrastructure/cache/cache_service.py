"""缓存服务。

封装 Token 黑名单和用户权限缓存的 Redis 操作。
所有方法对 Redis 操作做 try/except 降级处理，确保 Redis 异常不阻塞正常请求。
"""

import json
from datetime import datetime, timezone

import redis.asyncio as redis

from src.domain.services.cache_port import CachePort
from src.infrastructure.logging.logger import logger


class CacheService(CachePort):
    """缓存服务，封装黑名单与权限缓存的 Redis 操作。"""

    # Key 前缀
    _BLACKLIST_PREFIX = "token:blacklist:"
    _PERMS_PREFIX = "user:perms:"
    _USER_INFO_PREFIX = "user:info:"
    _MENU_ALL_KEY = "menu:all"

    # 缓存 TTL（秒）
    PERMS_CACHE_TTL = 300  # 5 分钟
    USER_INFO_CACHE_TTL = 300  # 5 分钟
    MENU_ALL_CACHE_TTL = 600  # 10 分钟

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

    # ---- 用户信息缓存 ----

    async def get_user_info(self, user_id: str) -> dict | None:
        """从缓存获取用户基本信息。

        Args:
            user_id: 用户 ID

        Returns:
            用户信息字典（缓存命中时），None 表示缓存未命中或 Redis 不可用
        """
        if self._redis is None:
            return None
        key = f"{self._USER_INFO_PREFIX}{user_id}"
        try:
            data = await self._redis.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception:
            logger.warning("Redis 读取用户信息缓存失败", exc_info=True)
            return None

    async def set_user_info(self, user_id: str, info: dict) -> bool:
        """将用户基本信息写入缓存。

        Args:
            user_id: 用户 ID
            info: 用户信息字典

        Returns:
            是否成功写入缓存
        """
        if self._redis is None:
            return False
        key = f"{self._USER_INFO_PREFIX}{user_id}"
        try:
            await self._redis.set(key, json.dumps(info, ensure_ascii=False), ex=self.USER_INFO_CACHE_TTL)
            return True
        except Exception:
            logger.warning("Redis 写入用户信息缓存失败", exc_info=True)
            return False

    async def invalidate_user_info(self, user_id: str) -> bool:
        """使用户信息缓存失效。

        Args:
            user_id: 用户 ID

        Returns:
            是否成功失效
        """
        if self._redis is None:
            return False
        key = f"{self._USER_INFO_PREFIX}{user_id}"
        try:
            await self._redis.delete(key)
            return True
        except Exception:
            logger.warning("Redis 删除用户信息缓存失败", exc_info=True)
            return False

    # ---- 菜单全表缓存 ----

    async def get_all_menus(self) -> list[dict] | None:
        """从缓存获取所有菜单列表。

        Returns:
            菜单字典列表（缓存命中时），None 表示缓存未命中或 Redis 不可用
        """
        if self._redis is None:
            return None
        try:
            data = await self._redis.get(self._MENU_ALL_KEY)
            if data is None:
                return None
            return json.loads(data)
        except Exception:
            logger.warning("Redis 读取菜单缓存失败", exc_info=True)
            return None

    async def set_all_menus(self, menus: list[dict]) -> bool:
        """将所有菜单列表写入缓存。

        Args:
            menus: 菜单字典列表

        Returns:
            是否成功写入缓存
        """
        if self._redis is None:
            return False
        try:
            await self._redis.set(self._MENU_ALL_KEY, json.dumps(menus, ensure_ascii=False), ex=self.MENU_ALL_CACHE_TTL)
            return True
        except Exception:
            logger.warning("Redis 写入菜单缓存失败", exc_info=True)
            return False

    async def invalidate_all_menus(self) -> bool:
        """使菜单全量缓存失效。

        Returns:
            是否成功失效
        """
        if self._redis is None:
            return False
        try:
            await self._redis.delete(self._MENU_ALL_KEY)
            return True
        except Exception:
            logger.warning("Redis 删除菜单缓存失败", exc_info=True)
            return False

    # ---- IP 规则缓存 ----

    _IP_RULES_KEY = "ip:rules"

    async def set_ip_rules(self, blacklist: set[str], whitelist: set[str]) -> bool:
        """将 IP 黑白名单写入 Redis 缓存。

        Args:
            blacklist: 黑名单 IP 集合
            whitelist: 白名单 IP 集合

        Returns:
            是否成功写入缓存
        """
        if self._redis is None:
            return False
        try:
            # 使用 pipeline 逐字段写入，兼容 Redis 3.x（不支持 HSET mapping 语法）
            async with self._redis.pipeline() as pipe:
                pipe.hset(self._IP_RULES_KEY, "blacklist", json.dumps(sorted(blacklist), ensure_ascii=False))
                pipe.hset(self._IP_RULES_KEY, "whitelist", json.dumps(sorted(whitelist), ensure_ascii=False))
                await pipe.execute()
            return True
        except Exception:
            logger.warning("Redis 写入 IP 规则缓存失败", exc_info=True)
            return False

    async def get_ip_rules(self) -> tuple[set[str], set[str]] | None:
        """从 Redis 缓存获取 IP 黑白名单。

        Returns:
            (blacklist, whitelist) 元组（缓存命中时），None 表示缓存未命中或 Redis 不可用
        """
        if self._redis is None:
            return None
        try:
            data = await self._redis.hgetall(self._IP_RULES_KEY)
            if not data:
                return None
            blacklist = set(json.loads(data.get("blacklist", "[]")))
            whitelist = set(json.loads(data.get("whitelist", "[]")))
            return blacklist, whitelist
        except Exception:
            logger.warning("Redis 读取 IP 规则缓存失败", exc_info=True)
            return None

    async def invalidate_ip_rules(self) -> bool:
        """使 IP 规则缓存失效。

        Returns:
            是否成功失效
        """
        if self._redis is None:
            return False
        try:
            await self._redis.delete(self._IP_RULES_KEY)
            return True
        except Exception:
            logger.warning("Redis 删除 IP 规则缓存失败", exc_info=True)
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

    def _user_info_key(self, user_id: str) -> str:
        """生成用户信息缓存的 Redis Key。"""
        return f"{self._USER_INFO_PREFIX}{user_id}"
