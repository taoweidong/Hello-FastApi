"""领域层 - 在线用户会话端口。

在线会话不是"读穿透缓存"：它没有回源数据库的语义，登记与查询必须落在同一个
实例上才能读到内存镜像，因此从 ``CachePort`` 中独立出来，由基础设施层的
``RedisOnlineSessionStore`` 实现「Redis 主存储 + 进程内镜像双写」。

消费方：认证服务（登录登记会话）、监控服务（在线列表 / 强制下线）。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class OnlineSessionStore(ABC):
    """在线用户会话的登记与查询端口。

    会话 Key 与 Token 黑名单 Key 共用同一哈希前缀，强制下线才能直接按 Key 拉黑。
    """

    @abstractmethod
    async def set_online_user(self, session_key: str, info: dict[str, Any], expires_at: datetime) -> bool:
        """登记在线用户会话。

        登录成功后调用，将会话信息写入存储，TTL 与访问令牌生命周期一致。

        Args:
            session_key: 会话 Key（访问令牌哈希前缀）
            info: 会话信息字典（userId/username/ip/system/browser/loginTime/expiresAt 等）
            expires_at: 会话过期时间

        Returns:
            是否成功写入（存储不可用时降级为进程内镜像，仍返回 True）
        """
        ...

    @abstractmethod
    async def get_online_user(self, session_key: str) -> dict[str, Any] | None:
        """获取在线用户会话。

        Args:
            session_key: 会话 Key（访问令牌哈希前缀）

        Returns:
            会话信息字典（命中时），None 表示未命中
        """
        ...

    @abstractmethod
    async def get_online_users(self) -> list[dict[str, Any]]:
        """获取全部在线用户会话。

        Returns:
            会话信息字典列表（每项含 id=session_key 供强制下线使用）；
            存储不可用时返回进程内镜像中未过期的会话
        """
        ...

    @abstractmethod
    async def delete_online_user(self, session_key: str) -> bool:
        """删除在线用户会话（强制下线），同步清理 Redis 与进程内镜像。

        Args:
            session_key: 会话 Key（访问令牌哈希前缀）

        Returns:
            是否成功删除
        """
        ...
