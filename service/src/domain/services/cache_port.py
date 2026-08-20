"""领域层 - 缓存抽象端口。

定义缓存服务的抽象接口，遵循依赖倒置原则。
应用层通过此抽象接口访问缓存，不直接依赖基础设施层的具体实现。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class CachePort(ABC):
    """缓存服务的抽象端口。

    封装 Token 黑名单、用户信息缓存、用户权限缓存、菜单缓存等操作。
    所有方法对底层存储做降级处理，确保存储异常不阻塞正常业务。
    """

    # ---- Token 黑名单 ----

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

    # ---- 在线用户会话 ----

    @abstractmethod
    async def set_online_user(self, session_key: str, info: dict[str, Any], expires_at: datetime) -> bool:
        """登记在线用户会话。

        登录成功后调用，将会话信息写入缓存，TTL 与访问令牌生命周期一致。

        Args:
            session_key: 会话 Key（访问令牌哈希前缀）
            info: 会话信息字典（userId/username/ip/system/browser/loginTime/expiresAt 等）
            expires_at: 会话过期时间

        Returns:
            是否成功写入缓存
        """
        ...

    @abstractmethod
    async def get_online_user(self, session_key: str) -> dict[str, Any] | None:
        """获取在线用户会话。

        Args:
            session_key: 会话 Key（访问令牌哈希前缀）

        Returns:
            会话信息字典（命中时），None 表示未命中或存储不可用
        """
        ...

    @abstractmethod
    async def get_online_users(self) -> list[dict[str, Any]]:
        """获取全部在线用户会话。

        Returns:
            会话信息字典列表（每项含 id=session_key 供强制下线使用）；
            存储不可用时返回空列表（降级处理）
        """
        ...

    @abstractmethod
    async def delete_online_user(self, session_key: str) -> bool:
        """删除在线用户会话（强制下线）。

        Args:
            session_key: 会话 Key（访问令牌哈希前缀）

        Returns:
            是否成功删除
        """
        ...

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

    # ---- 菜单全表缓存 ----

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

    # ---- 字典数据缓存 ----

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
