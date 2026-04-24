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
