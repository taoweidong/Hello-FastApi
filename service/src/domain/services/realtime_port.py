"""领域层 - 实时消息推送抽象端口。

定义实时推送的抽象接口，遵循依赖倒置原则。
应用层（如公告服务）通过此端口发送实时消息，不直接依赖
infrastructure 层的 WebSocket 连接管理器实现。
"""

from abc import ABC, abstractmethod
from typing import Any


class RealtimePort(ABC):
    """实时消息推送的抽象端口。"""

    @abstractmethod
    async def broadcast(self, message: dict[str, Any]) -> None:
        """向全部在线连接广播消息（best-effort，失败不抛出）。"""
        ...

    @abstractmethod
    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        """向指定用户的全部连接推送消息（best-effort，失败不抛出）。"""
        ...
