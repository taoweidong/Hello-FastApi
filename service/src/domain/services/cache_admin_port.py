"""领域层 - 缓存管理端口（管理员运维能力）。

面向监控页面的缓存清单与清理能力。与读穿透类窄端口不同，
本端口是**运维操作面**，路由层必须以管理员权限守护。

安全语义：
- ``token_blacklist`` 组**只读不清理**（clearable=False）——清除黑名单会使
  已登出/被强制下线的令牌复活至自然过期，属安全红线；
- 全量清理 = 逐个清理全部可清理业务组，不触碰限流计数键。
"""

from abc import ABC, abstractmethod
from typing import Any


class CacheAdminPort(ABC):
    """缓存清单与清理的管理端口。"""

    @abstractmethod
    async def get_cache_groups(self) -> list[dict[str, Any]] | None:
        """返回缓存分组清单。

        每组包含 key（分组标识）/ name（中文名）/ prefix（键前缀）/
        count（当前键数量）/ clearable（是否允许清理）。

        Returns:
            分组列表；缓存存储不可用时返回 None（调用方转为业务错误）。
        """
        ...

    @abstractmethod
    async def clear_cache_group(self, group: str) -> int | None:
        """清理指定分组的全部键。

        Args:
            group: 分组标识（须为 get_cache_groups 中 clearable=True 的组）

        Returns:
            删除的键数量；缓存存储不可用时返回 None。

        Raises:
            ValueError: 分组不存在或该组不允许清理时抛出。
        """
        ...

    @abstractmethod
    async def clear_all_business_cache(self) -> int | None:
        """清理全部可清理业务组的缓存（不含令牌黑名单与限流计数键）。

        Returns:
            删除的键总数；缓存存储不可用时返回 None。
        """
        ...
