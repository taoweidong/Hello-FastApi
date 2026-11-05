"""领域层 - 缓存抽象端口。

按**消费方**拆成窄接口（接口隔离原则）：每个应用服务只依赖自己真正调用的那一组方法，
新增缓存域时往对应窄端口加方法，而不是继续撑大一个所有服务共享的宽接口。
组合根与完整实现（``CacheService``）使用聚合端口 ``CachePort``，业务服务不应依赖它。

在线会话的登记与查询（Redis 主存储 + 内存镜像双写）语义上不同于"读穿透缓存"，
独立为 ``src.domain.services.online_session_port.OnlineSessionStore``。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class TokenRevocationPort(ABC):
    """Token 吊销端口：黑名单写入与校验。

    消费方：认证服务（刷新/登出）、认证依赖链（每请求校验）、监控服务（强制下线）。
    降级语义：存储不可用时 ``is_token_blacklisted`` 返回 False（放行），
    避免缓存故障阻断全部请求。
    """

    @abstractmethod
    async def add_token_to_blacklist(self, token: str, expires_at: datetime) -> bool:
        """将 Token 加入黑名单。

        Args:
            token: 原始 JWT Token 字符串
            expires_at: Token 的过期时间

        Returns:
            是否成功加入黑名单
        """
        ...

    @abstractmethod
    async def is_token_blacklisted(self, token: str) -> bool:
        """检查 Token 是否在黑名单中。

        Args:
            token: 原始 JWT Token 字符串

        Returns:
            True 表示已被拉黑，False 表示未拉黑或存储不可用（降级放行）
        """
        ...

    @abstractmethod
    async def blacklist_token_hash(self, token_hash: str, expires_at: datetime) -> bool:
        """将 Token 哈希加入黑名单。

        用于强制下线等场景：直接从会话哈希生成黑名单 Key，
        无需再次对 Token 取哈希，保证与在线会话的 Key 一致。

        Args:
            token_hash: Token 的哈希前缀（与在线会话 Key 的后缀一致）
            expires_at: Token 的过期时间

        Returns:
            是否成功加入黑名单
        """
        ...


class UserCachePort(ABC):
    """用户维度缓存端口：基本信息与权限列表的读写、失效。

    消费方：授权服务（每请求热路径读写）、用户服务与角色服务（变更后失效）。
    """

    # ---- 用户权限缓存 ----

    @abstractmethod
    async def get_user_permissions(self, user_id: str) -> list[dict[str, Any]] | None:
        """从缓存获取用户权限列表。

        Args:
            user_id: 用户 ID

        Returns:
            权限列表（缓存命中时），None 表示缓存未命中或存储不可用
        """
        ...

    @abstractmethod
    async def set_user_permissions(self, user_id: str, permissions: list[dict[str, Any]]) -> bool:
        """将用户权限列表写入缓存。

        Args:
            user_id: 用户 ID
            permissions: 权限列表

        Returns:
            是否成功写入缓存
        """
        ...

    @abstractmethod
    async def invalidate_user_permissions(self, user_id: str) -> bool:
        """使用户权限缓存失效。"""
        ...

    # ---- 用户信息缓存 ----

    @abstractmethod
    async def get_user_info(self, user_id: str) -> dict[str, Any] | None:
        """从缓存获取用户基本信息。

        Args:
            user_id: 用户 ID

        Returns:
            用户信息字典（缓存命中时），None 表示缓存未命中或存储不可用
        """
        ...

    @abstractmethod
    async def set_user_info(self, user_id: str, info: dict[str, Any]) -> bool:
        """将用户基本信息写入缓存。"""
        ...

    @abstractmethod
    async def invalidate_user_info(self, user_id: str) -> bool:
        """使用户信息缓存失效。"""
        ...

    async def invalidate_users_batch(self, user_ids: list[str]) -> bool:
        """批量失效多个用户的权限与信息缓存。

        该方法是**性能优化接口**而非抽象契约：默认实现退化为逐条失效，
        具体实现（如 Redis）可重写为一次批量删除，避免 N 次网络往返。

        Args:
            user_ids: 需要失效的用户 ID 列表

        Returns:
            是否全部成功，空列表视为成功
        """
        if not user_ids:
            return True
        results = []
        for uid in user_ids:
            ok_info = await self.invalidate_user_info(uid)
            ok_perms = await self.invalidate_user_permissions(uid)
            results.append(ok_info and ok_perms)
        return all(results)


class MenuCachePort(ABC):
    """菜单全表缓存端口。

    消费方：菜单服务（列表读穿透 + 变更后失效）、认证服务（超管动态路由取数）。
    """

    @abstractmethod
    async def get_all_menus(self) -> list[dict[str, Any]] | None:
        """从缓存获取所有菜单列表。

        Returns:
            菜单字典列表（缓存命中时），None 表示缓存未命中或存储不可用
        """
        ...

    @abstractmethod
    async def set_all_menus(self, menus: list[dict[str, Any]]) -> bool:
        """将所有菜单列表写入缓存。"""
        ...

    @abstractmethod
    async def invalidate_all_menus(self) -> bool:
        """使菜单全量缓存失效。"""
        ...


class DictCachePort(ABC):
    """字典数据缓存端口（按字典类型名分 Key）。

    消费方：字典服务（字典项读穿透 + 变更后失效）。
    """

    @abstractmethod
    async def get_dict_items(self, dict_name: str) -> list[dict[str, Any]] | None:
        """从缓存获取字典项列表。

        Args:
            dict_name: 字典类型名称

        Returns:
            字典项列表（缓存命中时），None 表示缓存未命中或存储不可用
        """
        ...

    @abstractmethod
    async def set_dict_items(self, dict_name: str, items: list[dict[str, Any]]) -> bool:
        """将字典项列表写入缓存。

        Args:
            dict_name: 字典类型名称
            items: 字典项列表

        Returns:
            是否成功写入缓存
        """
        ...

    @abstractmethod
    async def invalidate_dict(self, dict_name: str) -> bool:
        """使指定字典类型的数据缓存失效。"""
        ...


class CachePort(TokenRevocationPort, UserCachePort, MenuCachePort, DictCachePort):
    """读穿透类缓存的聚合端口。

    只作为组合根工厂的返回类型与完整实现（``CacheService``）的基类存在；
    应用服务应按消费方依赖上面四个窄端口，不要注入本聚合类型。
    在线会话不在本聚合内，见 ``OnlineSessionStore``。
    """


class IPFilterPort(ABC):
    """IP 过滤缓存服务的抽象端口。

    封装 IP 过滤规则的刷新操作。
    应用层通过此抽象接口触发 IP 过滤缓存刷新，不直接依赖基础设施层。
    """

    @abstractmethod
    async def refresh(self) -> None:
        """刷新 IP 过滤缓存。

        从数据库重新加载 IP 规则并更新缓存。
        刷新失败时静默处理，不影响正常业务。
        """
        ...
