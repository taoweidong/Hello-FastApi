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
    """用户维度缓存端口：基本信息、完整信息（/user/info）、权限列表与路由树的读写、失效。

    消费方：授权服务（每请求热路径读写）、认证服务（动态路由读写）、
    用户服务与角色服务（变更后失效）。
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
        """使用户信息缓存失效。

        同时失效基础信息（user:info:{id}）与完整信息（user:info:full:{id}）：
        完整信息是基础信息的超集（含角色列表），基础信息变化时必然连带失效。
        """
        ...

    # ---- 用户完整信息缓存（/user/info 响应）----

    @abstractmethod
    async def get_user_info_full(self, user_id: str) -> dict[str, Any] | None:
        """从缓存获取用户完整信息（/user/info 响应形态，含角色列表）。

        Args:
            user_id: 用户 ID

        Returns:
            用户完整信息字典（缓存命中时），None 表示缓存未命中或存储不可用
        """
        ...

    @abstractmethod
    async def set_user_info_full(self, user_id: str, info: dict[str, Any]) -> bool:
        """将用户完整信息（/user/info 响应形态）写入缓存。"""
        ...

    # ---- 用户路由树缓存 ----

    @abstractmethod
    async def get_user_routes(self, user_id: str) -> list[dict[str, Any]] | None:
        """从缓存获取用户动态路由树。

        Args:
            user_id: 用户 ID

        Returns:
            路由树列表（缓存命中时），None 表示缓存未命中或存储不可用
        """
        ...

    @abstractmethod
    async def set_user_routes(self, user_id: str, routes: list[dict[str, Any]]) -> bool:
        """将用户动态路由树写入缓存。"""
        ...

    @abstractmethod
    async def invalidate_user_routes(self, user_id: str) -> bool:
        """使用户路由树缓存失效。"""
        ...

    async def invalidate_users_batch(self, user_ids: list[str]) -> bool:
        """批量失效多个用户的权限、信息与路由树缓存。

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
            ok_routes = await self.invalidate_user_routes(uid)
            results.append(ok_info and ok_perms and ok_routes)
        return all(results)

    # ---- 用户数据权限范围缓存（user:scope:{id}）----

    async def get_user_scope(self, user_id: str) -> dict[str, Any] | None:
        """从缓存获取用户数据权限范围的解析结果。

        该方法是**性能优化接口**而非抽象契约：默认实现返回 None（视为未命中，
        消费方退化为查库），具体实现（如 Redis）可重写以提供真实缓存。

        Args:
            user_id: 操作人用户 ID

        Returns:
            解析结果字典（命中时），形如
            ``{"deptIds": [...] | None, "userId": str | None}``；
            None 表示缓存未命中或存储不可用
        """
        return None

    async def set_user_scope(self, user_id: str, scope: dict[str, Any]) -> bool:
        """将用户数据权限范围的解析结果写入缓存。

        默认实现为不存储（返回 False），具体实现可重写。

        Args:
            user_id: 操作人用户 ID
            scope: 解析结果 ``{"deptIds": [...] | None, "userId": str | None}``

        Returns:
            是否成功写入缓存
        """
        return False


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


class RoleCachePort(ABC):
    """角色选项缓存端口（/list-all-role 全量角色简单列表）。

    消费方：角色服务（选项读穿透 + 变更后失效）。
    """

    @abstractmethod
    async def get_role_options(self) -> list[dict[str, Any]] | None:
        """从缓存获取角色选项列表。

        Returns:
            角色选项列表（缓存命中时），None 表示缓存未命中或存储不可用
        """
        ...

    @abstractmethod
    async def set_role_options(self, options: list[dict[str, Any]]) -> bool:
        """将角色选项列表写入缓存。

        Args:
            options: 角色选项列表（``[{"id": ..., "name": ...}]``）

        Returns:
            是否成功写入缓存
        """
        ...

    @abstractmethod
    async def invalidate_role_options(self) -> bool:
        """使角色选项缓存失效。"""
        ...


class LogCountCachePort(ABC):
    """日志列表总数缓存端口（keyset 深分页的 COUNT 旁路）。

    消费方：日志服务（操作/系统日志列表的 total 缓存）。
    Key 形如 ``logs:count:{filters_hash}``（哈希覆盖筛选条件、不含分页/游标）；
    写入发生在首页精确 count 与深页兜底 count 之后；审计日志批量落库的
    worker 在 flush 后按前缀统一失效（见 audit_log_queue），TTL 60s 兜底。
    """

    @abstractmethod
    async def get_log_count(self, filters_hash: str) -> int | None:
        """从缓存获取日志列表总数。

        Args:
            filters_hash: 筛选条件哈希（稳定序列化后哈希，不含分页/游标）

        Returns:
            缓存的总数（命中时），None 表示未命中或存储不可用
        """
        ...

    @abstractmethod
    async def set_log_count(self, filters_hash: str, total: int) -> bool:
        """将日志列表总数写入缓存。

        Args:
            filters_hash: 筛选条件哈希
            total: 列表总数

        Returns:
            是否成功写入缓存
        """
        ...


class DashboardCachePort(ABC):
    """仪表盘统计聚合缓存端口（key ``dashboard:stats``，整体 data dict 读写）。

    消费方：仪表盘服务（统计聚合读穿透）。聚合跨 6 张表与日志明细，
    结果 60s 短缓存即可显著降低重复请求的聚合开销；
    失效策略仅依赖 TTL 兜底（统计允许 1 分钟延迟，无需主动失效）。
    """

    @abstractmethod
    async def get_dashboard_stats(self) -> dict[str, Any] | None:
        """从缓存获取仪表盘统计聚合结果。

        Returns:
            统计数据字典（DTO model_dump(mode="json") 形态，缓存命中时），
            None 表示缓存未命中或存储不可用
        """
        ...

    @abstractmethod
    async def set_dashboard_stats(self, data: dict[str, Any]) -> bool:
        """将仪表盘统计聚合结果写入缓存（TTL 取 settings.CACHE_DASHBOARD_TTL）。

        Args:
            data: 统计数据字典（DTO model_dump(mode="json") 后的整体 data dict）

        Returns:
            是否成功写入缓存
        """
        ...


class CachePort(
    TokenRevocationPort,
    UserCachePort,
    MenuCachePort,
    DictCachePort,
    RoleCachePort,
    LogCountCachePort,
    DashboardCachePort,
):
    """读穿透类缓存的聚合端口。

    只作为组合根工厂的返回类型与完整实现（``CacheService``）的基类存在；
    应用服务应按消费方依赖上面各窄端口，不要注入本聚合类型。
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
