"""缓存服务。

实现读穿透类缓存的四个领域端口（Token 黑名单、用户信息/权限、菜单全表、字典项）
与缓存管理端口 CacheAdminPort（分组清单与清理，供管理员监控页使用）。
所有方法对 Redis 操作做 try/except 降级处理，确保 Redis 异常不阻塞正常请求。

通用 JSON 读写的降级语义由 ``_get_json`` / ``_set_json`` / ``_delete_keys``
统一实现；特殊语义（黑名单降级放行）保留各自实现。
在线会话（Redis + 内存镜像双写）不在本类，见 ``online_session_store.RedisOnlineSessionStore``。
"""

import json
from datetime import datetime
from typing import Any

import redis.asyncio as redis

from src.config.settings import settings
from src.domain.services.cache_admin_port import CacheAdminPort
from src.domain.services.cache_port import CachePort
from src.domain.services.token_service import TokenService
from src.infrastructure.cache.ttl import remaining_seconds
from src.infrastructure.logging.logger import logger


class CacheService(CachePort, CacheAdminPort):
    """缓存服务，封装黑名单与权限缓存的 Redis 操作。"""

    # Key 前缀
    _BLACKLIST_PREFIX = "token:blacklist:"
    _PERMS_PREFIX = "user:perms:"
    _USER_INFO_PREFIX = "user:info:"
    _DICT_PREFIX = "dict:"
    _MENU_ALL_KEY = "menu:all"
    _IP_RULES_KEY = "ip:rules"

    # 缓存 TTL（秒）- 从配置读取
    PERMS_CACHE_TTL = settings.CACHE_PERMISSIONS_TTL
    USER_INFO_CACHE_TTL = settings.CACHE_USER_INFO_TTL
    MENU_ALL_CACHE_TTL = settings.CACHE_MENU_ALL_TTL
    TOKEN_BLACKLIST_TTL = settings.CACHE_TOKEN_BLACKLIST_TTL
    DICT_CACHE_TTL = settings.CACHE_DICT_TTL

    def __init__(self, redis_client: redis.Redis | None = None) -> None:
        self._redis = redis_client

    # ---- 通用 JSON 读写助手（统一降级语义） ----

    async def _get_json(self, key: str) -> tuple[bool, Any]:
        """读取 JSON 缓存。

        Returns:
            (命中, 值)；Redis 未配置、异常或未命中时返回 (False, None)。
        """
        if self._redis is None:
            return False, None
        try:
            data = await self._redis.get(key)
            if data is None:
                return False, None
            return True, json.loads(data)
        except Exception:
            logger.warning(f"Redis 读取缓存失败: {key}", exc_info=True)
            return False, None

    async def _set_json(self, key: str, value: Any, ttl: int) -> bool:
        """写入 JSON 缓存，Redis 未配置或异常时返回 False。"""
        if self._redis is None:
            return False
        try:
            await self._redis.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
            return True
        except Exception:
            logger.warning(f"Redis 写入缓存失败: {key}", exc_info=True)
            return False

    async def _delete_keys(self, *keys: str) -> bool:
        """删除缓存 Key（单次往返），Redis 未配置或异常时返回 False。"""
        if self._redis is None or not keys:
            return False
        try:
            await self._redis.delete(*keys)
            return True
        except Exception:
            logger.warning(f"Redis 删除缓存失败: {keys}", exc_info=True)
            return False

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
        ttl = remaining_seconds(expires_at)
        if ttl <= 0:
            # Token 已过期，无需加入黑名单
            return True
        try:
            await self._redis.set(key, "1", ex=ttl)
            return True
        except Exception:
            logger.warning("Redis 写入 Token 哈希黑名单失败", exc_info=True)
            return False

    # ---- 用户权限缓存 ----

    async def get_user_permissions(self, user_id: str) -> list[dict] | None:
        """从缓存获取用户权限列表。

        Args:
            user_id: 用户 ID

        Returns:
            权限列表（缓存命中时），None 表示缓存未命中或 Redis 不可用
        """
        _, value = await self._get_json(self._perms_key(user_id))
        return value

    async def set_user_permissions(self, user_id: str, permissions: list[dict]) -> bool:
        """将用户权限列表写入缓存。

        Args:
            user_id: 用户 ID
            permissions: 权限列表（每个权限为 dict，含 role_name, menu_names 等）

        Returns:
            是否成功写入缓存
        """
        return await self._set_json(self._perms_key(user_id), permissions, self.PERMS_CACHE_TTL)

    async def invalidate_user_permissions(self, user_id: str) -> bool:
        """使用户权限缓存失效。

        Args:
            user_id: 用户 ID

        Returns:
            是否成功失效
        """
        return await self._delete_keys(self._perms_key(user_id))

    # ---- 用户信息缓存 ----

    async def get_user_info(self, user_id: str) -> dict | None:
        """从缓存获取用户基本信息。

        Args:
            user_id: 用户 ID

        Returns:
            用户信息字典（缓存命中时），None 表示缓存未命中或 Redis 不可用
        """
        _, value = await self._get_json(self._user_info_key(user_id))
        return value

    async def set_user_info(self, user_id: str, info: dict) -> bool:
        """将用户基本信息写入缓存。

        Args:
            user_id: 用户 ID
            info: 用户信息字典

        Returns:
            是否成功写入缓存
        """
        return await self._set_json(self._user_info_key(user_id), info, self.USER_INFO_CACHE_TTL)

    async def invalidate_user_info(self, user_id: str) -> bool:
        """使用户信息缓存失效。

        Args:
            user_id: 用户 ID

        Returns:
            是否成功失效
        """
        return await self._delete_keys(self._user_info_key(user_id))

    async def invalidate_users_batch(self, user_ids: list[str]) -> bool:
        """批量失效多个用户的权限与信息缓存（单次 Redis 往返）。

        将全部 key 的删除合并为一次网络往返，避免批量操作时
        出现 N×2 次 Redis 调用的隐式 N+1 问题。

        Args:
            user_ids: 需要失效的用户 ID 列表

        Returns:
            是否成功失效，Redis 不可用或列表为空时返回 False / True
        """
        if not user_ids:
            return True
        keys = [self._perms_key(uid) for uid in user_ids] + [self._user_info_key(uid) for uid in user_ids]
        return await self._delete_keys(*keys)

    # ---- 菜单全表缓存 ----

    async def get_all_menus(self) -> list[dict] | None:
        """从缓存获取所有菜单列表。

        Returns:
            菜单字典列表（缓存命中时），None 表示缓存未命中或 Redis 不可用
        """
        _, value = await self._get_json(self._MENU_ALL_KEY)
        return value

    async def set_all_menus(self, menus: list[dict]) -> bool:
        """将所有菜单列表写入缓存。

        Args:
            menus: 菜单字典列表

        Returns:
            是否成功写入缓存
        """
        return await self._set_json(self._MENU_ALL_KEY, menus, self.MENU_ALL_CACHE_TTL)

    async def invalidate_all_menus(self) -> bool:
        """使菜单全量缓存失效。

        Returns:
            是否成功失效
        """
        return await self._delete_keys(self._MENU_ALL_KEY)

    # ---- 字典数据缓存 ----

    async def get_dict_items(self, dict_name: str) -> list[dict] | None:
        """从缓存获取字典项列表。

        Args:
            dict_name: 字典类型名称

        Returns:
            字典项列表（缓存命中时），None 表示缓存未命中或 Redis 不可用
        """
        _, value = await self._get_json(f"{self._DICT_PREFIX}{dict_name}")
        return value

    async def set_dict_items(self, dict_name: str, items: list[dict]) -> bool:
        """将字典项列表写入缓存。

        Args:
            dict_name: 字典类型名称
            items: 字典项列表

        Returns:
            是否成功写入缓存
        """
        return await self._set_json(f"{self._DICT_PREFIX}{dict_name}", items, self.DICT_CACHE_TTL)

    async def invalidate_dict(self, dict_name: str) -> bool:
        """使指定字典类型的数据缓存失效。

        Args:
            dict_name: 字典类型名称

        Returns:
            是否成功失效
        """
        return await self._delete_keys(f"{self._DICT_PREFIX}{dict_name}")

    # ---- IP 规则缓存 ----

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
        return await self._delete_keys(self._IP_RULES_KEY)

    # ---- 内部方法 ----

    def _blacklist_key(self, token: str) -> str:
        """生成 Token 黑名单的 Redis Key。

        使用 token 的哈希前缀作为标识，避免存储完整 Token。
        """
        return f"{self._BLACKLIST_PREFIX}{self._token_hash(token)}"

    @staticmethod
    def _token_hash(token: str) -> str:
        """计算 Token 的哈希前缀。

        委托 TokenService.hash_token 单一实现：黑名单 Key 与在线会话 Key
        必须来自同一算法，任一侧独立改动会导致强制下线静默失效。
        """
        return TokenService.hash_token(token)

    def _perms_key(self, user_id: str) -> str:
        """生成用户权限缓存的 Redis Key。"""
        return f"{self._PERMS_PREFIX}{user_id}"

    def _user_info_key(self, user_id: str) -> str:
        """生成用户信息缓存的 Redis Key。"""
        return f"{self._USER_INFO_PREFIX}{user_id}"

    # ---- CacheAdminPort：缓存清单与清理（管理员监控页） ----

    # 分组注册表：(分组标识, 中文名, 键前缀, 是否可清理)。
    # token_blacklist 只读不清理——清除黑名单会使已登出/被强制下线的令牌
    # 复活至自然过期，属安全红线；全量清理也跳过该组与限流计数键。
    _CACHE_GROUPS: tuple[tuple[str, str, str, bool], ...] = (
        ("user_info", "用户信息缓存", _USER_INFO_PREFIX, True),
        ("user_perms", "用户权限缓存", _PERMS_PREFIX, True),
        ("menu_cache", "菜单全量缓存", _MENU_ALL_KEY, True),
        ("dict_cache", "字典缓存", _DICT_PREFIX, True),
        ("ip_rules", "IP 规则缓存", _IP_RULES_KEY, True),
        ("token_blacklist", "令牌黑名单", _BLACKLIST_PREFIX, False),
    )

    async def _count_keys(self, prefix: str) -> int:
        """统计匹配前缀的键数量（SCAN 增量遍历，不阻塞 Redis）。"""
        assert self._redis is not None
        count = 0
        async for _key in self._redis.scan_iter(match=f"{prefix}*"):
            count += 1
        return count

    async def _delete_by_prefix(self, prefix: str) -> int:
        """删除匹配前缀的全部键，返回删除数量。"""
        assert self._redis is not None
        keys = [key async for key in self._redis.scan_iter(match=f"{prefix}*")]
        if not keys:
            return 0
        return int(await self._redis.delete(*keys))

    async def get_cache_groups(self) -> list[dict[str, Any]] | None:
        """返回缓存分组清单（含各分组当前键数量）。

        Redis 未配置/不可用时返回 None，由调用方转为业务错误提示。
        """
        if self._redis is None:
            return None
        try:
            groups = []
            for key, name, prefix, clearable in self._CACHE_GROUPS:
                count = await self._count_keys(prefix)
                groups.append({"key": key, "name": name, "prefix": prefix, "count": count, "clearable": clearable})
            return groups
        except Exception:
            logger.warning("Redis 统计缓存分组失败", exc_info=True)
            return None

    async def clear_cache_group(self, group: str) -> int | None:
        """清理指定分组的全部键，返回删除数量。

        Raises:
            ValueError: 分组不存在，或该组不允许清理（如令牌黑名单）时抛出。
        """
        spec = next((g for g in self._CACHE_GROUPS if g[0] == group), None)
        if spec is None:
            raise ValueError(f"未知的缓存分组: {group}")
        if not spec[3]:
            raise ValueError(f"缓存分组 '{spec[1]}' 不允许清理（清理会带来安全风险）")
        if self._redis is None:
            return None
        try:
            return await self._delete_by_prefix(spec[2])
        except Exception:
            logger.warning(f"Redis 清理缓存分组失败: {group}", exc_info=True)
            return None

    async def clear_all_business_cache(self) -> int | None:
        """清理全部可清理业务组（不含令牌黑名单与限流计数键）。

        逐组执行而非 FLUSHDB：限流计数与令牌黑名单同库，
        整库清空会让已登出令牌复活并重置限流窗口。
        """
        if self._redis is None:
            return None
        deleted = 0
        try:
            for key, _name, _prefix, clearable in self._CACHE_GROUPS:
                if not clearable:
                    continue
                count = await self.clear_cache_group(key)
                if count is None:
                    return None
                deleted += count
            return deleted
        except Exception:
            logger.warning("Redis 清理全部业务缓存失败", exc_info=True)
            return None
