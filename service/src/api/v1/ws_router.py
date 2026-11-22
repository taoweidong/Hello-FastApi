"""WebSocket 实时消息路由。

路径: /api/system/ws
协议: 查询参数 ?token=<accessToken> 鉴权，或连接后首条消息 {"type":"auth","token":"..."} 鉴权
（首帧鉴权避免 token 进入代理/服务端访问日志）；文本帧收发 JSON。
"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

from src.api.dependencies.ws_auth import get_ws_user_id
from src.infrastructure.realtime.manager import ws_manager

ws_router = APIRouter()

# 首帧鉴权等待窗口：超时视为未授权关闭，防止客户端挂着不鉴权占用连接
AUTH_MESSAGE_TIMEOUT = 5.0


async def _validate_token(token: str | None) -> str:
    """校验 token 并返回 user_id；非法/异常抛出（含黑名单、Redis 故障）。"""
    return await get_ws_user_id(token)


async def _authenticate_via_query(websocket: WebSocket, token: str) -> str | None:
    """查询参数鉴权：成功返回 user_id；失败接受后以 1008 关闭并返回 None。"""
    try:
        return await _validate_token(token)
    except Exception:
        logger.warning("WebSocket 鉴权异常，拒绝连接: {}", True, exc_info=True)
        await websocket.accept()
        await websocket.close(code=1008, reason="unauthorized")
        return None


async def _authenticate_via_first_frame(websocket: WebSocket) -> str | None:
    """首帧鉴权：已 accept，等待首条 {"type":"auth","token":...}；失败/超时 1008 关闭。"""
    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=AUTH_MESSAGE_TIMEOUT)
        msg = json.loads(raw)
        token = msg.get("token") if isinstance(msg, dict) and msg.get("type") == "auth" else None
        return await _validate_token(token)
    except WebSocketDisconnect:
        return None
    except Exception:
        logger.warning("WebSocket 首帧鉴权失败或异常，拒绝连接", exc_info=True)
        await websocket.close(code=1008, reason="unauthorized")
        return None


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """实时消息 WebSocket 端点。

    - 两种鉴权方式：URL 查询参数（兼容旧行为）或连接后首条 auth 消息（推荐，token 不入日志）；
      鉴权失败（无 token / 非法 / 黑名单 / 首帧超时）：以 1008 关闭，避免浏览器挂起；
      鉴权阶段的内部异常必须记日志——否则 Redis 超时等故障会被静默当成"未授权"。
    - 鉴权成功：登记连接（超上限拒绝）→ 发送 connected 欢迎 → 处理 ping/pong 心跳。
    """
    token = websocket.query_params.get("token")
    if token:
        user_id = await _authenticate_via_query(websocket, token)
        if user_id is None:
            return
        # 查询参数路径：校验通过后再 accept（校验失败由 helper 内 accept+close 处理）
        await websocket.accept()
    else:
        # 首帧鉴权路径：先 accept 才能收首条消息
        await websocket.accept()
        user_id = await _authenticate_via_first_frame(websocket)
    if user_id is None:
        return

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
