"""实时消息连接管理器（WebSocket）。

单例化的连接注册表：按 user_id 维护其全部活动 WebSocket 连接
（同一用户多标签页 → 多连接）。提供广播与定向发送能力。

仅依赖 fastapi.WebSocket，不反向依赖任何业务 service，避免循环导入。

资源防护：
- 单用户连接数上限（防止单账号打满 FD/内存）
- 总连接数上限（防止连接洪水）
- 广播对单连接发送限时（防止慢消费者阻塞整个广播循环）
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any

from fastapi import WebSocket
from loguru import logger

# 单连接发送超时（秒）：超时视为慢/死连接，从注册表剔除
SEND_TIMEOUT_SECONDS = 5.0


class ConnectionManager:
    """管理已认证的 WebSocket 连接。"""

    def __init__(self, max_connections_per_user: int = 5, max_total_connections: int = 1000) -> None:
        # user_id -> 该用户的全部活动连接
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)
        self._max_connections_per_user = max_connections_per_user
        self._max_total_connections = max_total_connections

    async def connect(self, user_id: str, websocket: WebSocket) -> bool:
        """登记一条新连接。

        Returns:
            是否登记成功；超过单用户/总连接上限时返回 False，调用方应关闭连接。
        """
        if self.total_connections >= self._max_total_connections:
            logger.warning("WebSocket 总连接数已达上限 %s，拒绝新连接", self._max_total_connections)
            return False
        if len(self._connections[user_id]) >= self._max_connections_per_user:
            logger.warning(
                "用户 %s 的 WebSocket 连接数已达上限 %s，拒绝新连接", user_id, self._max_connections_per_user
            )
            return False
        self._connections[user_id].append(websocket)
        return True

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """移除一条连接；该用户无连接时清理键。"""
        conns = self._connections.get(user_id)
        if conns and websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(user_id, None)

    @property
    def online_users(self) -> int:
        """当前在线用户数。"""
        return len(self._connections)

    @property
    def total_connections(self) -> int:
        """当前活动连接总数（含同一用户多标签页）。"""
        return sum(len(c) for c in self._connections.values())

    @staticmethod
    async def _send_json(ws: WebSocket, payload: str) -> None:
        """带超时的单连接发送；超时抛 TimeoutError 由调用方剔除连接。"""
        await asyncio.wait_for(ws.send_text(payload), timeout=SEND_TIMEOUT_SECONDS)

    async def send_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        """向指定用户的全部连接推送消息（best-effort）。"""
        payload = json.dumps(message, ensure_ascii=False, default=str)
        dead: list[WebSocket] = []
        for ws in list(self._connections.get(user_id, [])):
            try:
                await self._send_json(ws, payload)
            except Exception as exc:  # 单连接异常（含超时）不影响其它连接
                logger.warning("向用户 {} 推送消息失败: {}", user_id, exc)
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """向全部在线连接广播消息（best-effort）。

        单连接发送限时，慢消费者超时后被剔除，不会拖垮整轮广播。
        """
        payload = json.dumps(message, ensure_ascii=False, default=str)
        dead: list[tuple[str, WebSocket]] = []
        for user_id, conns in self._connections.items():
            for ws in list(conns):
                try:
                    await self._send_json(ws, payload)
                except Exception as exc:
                    logger.warning("广播消息失败(用户 {}): {}", user_id, exc)
                    dead.append((user_id, ws))
        for user_id, ws in dead:
            self.disconnect(user_id, ws)


# 进程级单例：service 层与 router 层共享同一实例
ws_manager = ConnectionManager()
