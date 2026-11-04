"""实时消息推送的基础设施适配器。

将 WebSocket 连接管理器适配为领域层的 RealtimePort 端口，
供应用层依赖注入使用（对齐 ip_filter_port_adapter 的模式）。
"""

from __future__ import annotations

from typing import Any

from src.domain.services.realtime_port import RealtimePort
from src.infrastructure.realtime.manager import ConnectionManager


class WSManagerRealtimeAdapter(RealtimePort):
    """基于 ConnectionManager 的 RealtimePort 实现。"""

    def __init__(self, manager: ConnectionManager) -> None:
        self._manager = manager

    async def broadcast(self, message: dict[str, Any]) -> None:
        await self._manager.broadcast(message)

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        await self._manager.send_to_user(user_id, message)


def get_realtime_port() -> RealtimePort:
    """获取进程级 RealtimePort 实例（构建于 ws_manager 单例之上）。"""
    from src.infrastructure.realtime.manager import ws_manager

    return WSManagerRealtimeAdapter(ws_manager)
