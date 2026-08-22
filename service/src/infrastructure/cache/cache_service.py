"""缓存服务。

封装 Token 黑名单和用户权限缓存的 Redis 操作。
所有方法对 Redis 操作做 try/except 降级处理，确保 Redis 异常不阻塞正常请求。
"""

import json
from datetime import datetime, timezone

import redis.asyncio as redis

from src.config.settings import settings
from src.domain.services.cache_port import CachePort
from src.infrastructure.logging.logger import logger


class CacheService(CachePort):
    """缓存服务，封装黑名单与权限缓存的 Redis 操作。"""

    # Key 前缀
    _BLACKLIST_PREFIX = "token:blacklist:"
    _ONLINE_USER_PREFIX = "online:user:"
    _PERMS_PREFIX = "user:perms:"
    _USER_INFO_PREFIX = "user:info:"
    _DICT_PREFIX = "dict:"
    _MENU_ALL_KEY = "menu:all"

    # 缓存 TTL（秒）- 从配置读取
    PERMS_CACHE_TTL = settings.CACHE_PERMISSIONS_TTL
    USER_INFO_CACHE_TTL = settings.CACHE_USER_INFO_TTL
    MENU_ALL_CACHE_TTL = settings.CACHE_MENU_ALL_TTL
    TOKEN_BLACKLIST_TTL = settings.CACHE_TOKEN_BLACKLIST_TTL
    DICT_CACHE_TTL = settings.CACHE_DICT_TTL

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        self._redis = redis_client
        # 在线会话内存镜像存储（Redis 未配置/不可用时降级数据源）
        # key: 会话 Key，value: {"info": 会话信息字典, "expires_at": 过期时间 UTC}
        self._online_memory: dict[str, dict] = {}

    # ---- Token 黑名单 ----

    async def add_token_to_blacklist(self, token: str, expires_at: datetime) -> bool:
        """将 Token 加入黑名单。

        Args:
            token: 原始 JWT Token 字符串
            expires_at: Token 的过期时间

        Returns:
            是否成功加入黑名单
        """
        return await self.blacklist_token_hash(self._token_hash(token), expires_at)

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

    async def blacklist_token_hash(self, token_hash: str, expires_at: datetime) -> bool:
        """将 Token 哈希加入黑名单。

        供强制下线使用：直接以会话哈希作为 Key 后缀写入黑名单，
        与在线会话 Key 保持一致，无需再次对 Token 取哈希。

        Args:
            token_hash: Token 的哈希前缀
            expires_at: Token 的过期时间

        Returns:
            是否成功加入黑名单
        """
        if self._redis is None:
            return True
        key = f"{self._BLACKLIST_PREFIX}{token_hash}"
        ttl = self._remaining_seconds(expires_at)
        if ttl <= 0:
            # Token 已过期，无需加入黑名单
            return True
        try:
            await self._redis.set(key, "1", ex=ttl)
            return True
        except Exception:
            logger.warning("Redis 写入 Token 哈希黑名单失败", exc_info=True)
            return False

    # ---- 在线用户会话 ----

    async def set_online_user(self, session_key: str, info: dict, expires_at: datetime) -> bool:
        """登记在线用户会话（Redis 主存储 + 内存镜像双写）。

        Redis 未配置或不可用时自动降级为内存存储，保证在线用户功能可用；
        内存条目同样遵循 TTL 约束，读取时惰性清理已过期会话。

        Args:
            session_key: 会话 Key（访问令牌哈希前缀）
            info: 会话信息字典
            expires_at: 会话过期时间（TTL 与访问令牌生命周期一致）

        Returns:
            是否成功写入缓存
        """
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        ttl = self._remaining_seconds(expires_at)
        if ttl <= 0:
            # Token 已过期，无需登记
            self._online_memory.pop(session_key, None)
            return True
        # 内存镜像总是写入，Redis 异常时不阻塞在线用户功能
        self._online_memory[session_key] = {"info": info, "expires_at": expires_at}
        if self._redis is None:
            return True
        key = f"{self._ONLINE_USER_PREFIX}{session_key}"
        try:
            await self._redis.set(key, json.dumps(info, ensure_ascii=False), ex=ttl)
            return True
        except Exception:
            logger.warning("Redis 登记在线用户会话失败，已降级为内存存储", exc_info=True)
            return True

    async def get_online_user(self, session_key: str) -> dict | None:
        """获取在线用户会话（Redis 优先，未命中或不可用时读内存镜像）。

        Args:
            session_key: 会话 Key（访问令牌哈希前缀）

        Returns:
            会话信息字典（命中时），None 表示未命中
        """
        if self._redis is not None:
            key = f"{self._ONLINE_USER_PREFIX}{session_key}"
            try:
                data = await self._redis.get(key)
                if data is not None:
                    return json.loads(data)
            except Exception:
                logger.warning("Redis 读取在线用户会话失败，降级读取内存镜像", exc_info=True)
        return self._memory_get_online(session_key)

    async def get_online_users(self) -> list[dict]:
        """获取全部在线用户会话（Redis 优先，不可用时降级内存镜像）。

        Returns:
            会话信息字典列表（每项含 id=session_key 供强制下线使用）；
            Redis 不可用时返回内存镜像中未过期的会话
        """
        if self._redis is not None:
            try:
                sessions: list[dict] = []
                prefix = self._ONLINE_USER_PREFIX
                async for key in self._redis.scan_iter(match=f"{prefix}*", count=100):
                    data = await self._redis.get(key)
                    if data is None:
                        continue
                    item = json.loads(data)
                    item["id"] = key[len(prefix) :]
                    sessions.append(item)
                return sessions
            except Exception:
                logger.warning("Redis 遍历在线用户会话失败，降级读取内存镜像", exc_info=True)
        return self._memory_get_all_online()

    async def delete_online_user(self, session_key: str) -> bool:
        """删除在线用户会话（强制下线），同步清理 Redis 与内存镜像。

        Args:
            session_key: 会话 Key（访问令牌哈希前缀）

        Returns:
            是否成功删除
        """
        self._online_memory.pop(session_key, None)
        if self._redis is None:
            return True
        try:
            await self._redis.delete(f"{self._ONLINE_USER_PREFIX}{session_key}")
            return True
        except Exception:
            logger.warning("Redis 删除在线用户会话失败", exc_info=True)
            return False

    def _memory_get_online(self, session_key: str) -> dict | None:
        """从内存镜像读取在线会话（惰性清理已过期条目）。"""
        entry = self._online_memory.get(session_key)
        if entry is None:
            return None
        if entry["expires_at"] <= datetime.now(timezone.utc):
            self._online_memory.pop(session_key, None)
            return None
        return dict(entry["info"])

    def _memory_get_all_online(self) -> list[dict]:
        """从内存镜像获取全部在线会话（过滤并清理已过期条目）。"""
        now = datetime.now(timezone.utc)
        for key in list(self._online_memory):
            if self._online_memory[key]["expires_at"] <= now:
                self._online_memory.pop(key, None)
        return [{**entry["info"], "id": key} for key, entry in self._online_memory.items()]

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

    # ---- 字典数据缓存 ----

    async def get_dict_items(self, dict_name: str) -> list[dict] | None:
        """从缓存获取字典项列表。

        Args:
            dict_name: 字典类型名称

        Returns:
            字典项列表（缓存命中时），None 表示缓存未命中或 Redis 不可用
        """
        if self._redis is None:
            return None
        key = f"{self._DICT_PREFIX}{dict_name}"
        try:
            data = await self._redis.get(key)
            if data is None:
                return None
            return json.loads(data)
        except Exception:
            logger.warning("Redis 读取字典缓存失败", exc_info=True)
            return None

    async def set_dict_items(self, dict_name: str, items: list[dict]) -> bool:
        """将字典项列表写入缓存。

        Args:
            dict_name: 字典类型名称
            items: 字典项列表

        Returns:
            是否成功写入缓存
        """
        if self._redis is None:
            return False
        key = f"{self._DICT_PREFIX}{dict_name}"
        try:
            await self._redis.set(key, json.dumps(items, ensure_ascii=False), ex=self.DICT_CACHE_TTL)
            return True
        except Exception:
            logger.warning("Redis 写入字典缓存失败", exc_info=True)
            return False

    async def invalidate_dict(self, dict_name: str) -> bool:
        """使指定字典类型的数据缓存失效。

        Args:
            dict_name: 字典类型名称

        Returns:
            是否成功失效
        """
        if self._redis is None:
            return False
        key = f"{self._DICT_PREFIX}{dict_name}"
        try:
            await self._redis.delete(key)
            return True
        except Exception:
            logger.warning("Redis 删除字典缓存失败", exc_info=True)
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
        return f"{self._BLACKLIST_PREFIX}{self._token_hash(token)}"

    @staticmethod
    def _token_hash(token: str) -> str:
        """计算 Token 的 SHA-256 哈希前缀（前 32 位）。"""
        import hashlib

        return hashlib.sha256(token.encode()).hexdigest()[:32]

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
