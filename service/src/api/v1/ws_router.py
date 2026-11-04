"""WebSocket 实时消息路由。

路径: /api/system/ws
协议: 查询参数 ?token=<accessToken> 鉴权；文本帧收发 JSON。
"""

from __future__ import annotations

import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from src.api.dependencies.ws_auth import get_ws_user_id
from src.infrastructure.realtime.manager import ws_manager

ws_router = APIRouter()


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """实时消息 WebSocket 端点。

    - 鉴权失败（无 token / 非法 / 黑名单）：接受后以 1008 关闭，避免浏览器挂起；
      鉴权阶段的内部异常必须记日志——否则 Redis 超时等故障会被静默当成"未授权"。
    - 鉴权成功：登记连接（超上限拒绝）→ 发送 connected 欢迎 → 处理 ping/pong 心跳。
    """
    token = websocket.query_params.get("token")
    try:
        user_id = await get_ws_user_id(token)
    except Exception:
        logger.warning("WebSocket 鉴权异常，拒绝连接: {}", token is not None, exc_info=True)
        await websocket.accept()
        await websocket.close(code=1008, reason="unauthorized")
        return

    await websocket.accept()
    if not await ws_manager.connect(user_id, websocket):
        await websocket.close(code=1013, reason="connection limit exceeded")
        return
    try:
        await websocket.send_json({"type": "connected", "data": {"user_id": user_id}})
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            # 客户端可能发送合法 JSON 非对象（如 123、[1]），直接 .get 会抛 AttributeError
            if isinstance(msg, dict) and msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(user_id, websocket)
