"""实时消息连接管理器（WebSocket）。

单例化的连接注册表：按 user_id 维护其全部活动 WebSocket 连接
（同一用户多标签页 → 多连接）。提供广播与定向发送能力。

仅依赖 fastapi.WebSocket 与 Redis 广播桥，不反向依赖任何业务 service，避免循环导入。

资源防护：
- 单用户连接数上限（防止单账号打满 FD/内存）
- 总连接数上限（防止连接洪水）
- 广播对单连接发送限时（防止慢消费者阻塞整轮广播）
- Redis pub/sub 广播桥：多 worker 部署时跨进程投递（详见 broadcast）
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from collections import defaultdict
from typing import Any

import redis.asyncio as redis_async
from fastapi import WebSocket
from loguru import logger

from src.config.settings import settings

# 单连接发送超时（秒）：超时视为慢/死连接，从注册表剔除
SEND_TIMEOUT_SECONDS = 5.0

# Redis 广播桥频道；消息信封格式：{"type": "ws:broadcast", "payload": 原始消息}
WS_BROADCAST_CHANNEL = "ws:broadcast"

# 订阅任务异常自动重启：有限次数 + 指数退避，耗尽后降级为本地直投（避免静默死亡）
_WS_SUBSCRIBER_MAX_RESTARTS = 5
_WS_SUBSCRIBER_BACKOFF_SECONDS = 1.0


class ConnectionManager:
    """管理已认证的 WebSocket 连接。"""

    def __init__(
        self, max_connections_per_user: int = 5, max_total_connections: int = 1000, redis_url: str | None = None
    ) -> None:
        # user_id -> 该用户的全部活动连接
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)
        self._max_connections_per_user = max_connections_per_user
        self._max_total_connections = max_total_connections
        # ---- Redis 广播桥状态（多 worker 支持；显式注入 redis_url 优先于全局配置）----
        self._redis_url_override = redis_url
        # 发布客户端：读写超时取全局配置，发布失败快速降级（不拖慢广播调用方）
        self._publish_client: redis_async.Redis | None = None
        # 订阅客户端：socket_timeout 必须为 None（长阻塞读，见 _get_subscribe_client）
        self._subscribe_client: redis_async.Redis | None = None
        self._subscriber_task: asyncio.Task[None] | None = None
        # 订阅命令已确认：桥可用，广播走"发布"路径；未就绪/失败时走本地直投
        self._subscriber_ready = asyncio.Event()
        self._subscriber_failures = 0
        # 桥永久降级：发布失败或订阅重启耗尽后置位，广播只走本地直投
        self._bridge_degraded = False

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
        # 首次有连接注册时惰性启动 Redis 广播订阅（幂等；不进 lifespan）
        self._ensure_subscriber()
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
        """向指定用户的全部连接推送消息（best-effort，仅本进程连接）。"""
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

        多 worker 支持：桥可用（配置了 Redis 且订阅就绪）时，本进程只把消息
        发布到 ``ws:broadcast`` 频道，由各 worker 的订阅端（含本进程回环）统一
        投递给本地连接——广播只走"发布"一条路径，避免双发。
        Redis 未配置 / 测试环境 / 订阅未就绪 / 发布失败（fail-open 一次性告警
        并降级）时，退化为本地直投。单连接发送限时，慢消费者超时后被剔除。
        """
        self._ensure_subscriber()
        if await self._publish_to_bridge(message):
            return
        await self._broadcast_local(message)

    # ==================== Redis 广播桥（多 worker 支持） ====================

    def _bridge_enabled(self) -> bool:
        """广播桥是否启用。

        显式注入 redis_url 时无条件启用（供桥本身的功能验证）；
        否则要求配置了 REDIS_URL，且测试环境（APP_ENV=testing）强制禁用——
        测试必须走本地路径保证确定性（订阅回环是异步投递，会破坏同步断言）。
        """
        if self._redis_url_override is not None:
            return True
        if settings.APP_ENV == "testing":
            return False
        return bool(settings.REDIS_URL)

    def _resolve_redis_url(self) -> str:
        """解析桥使用的 Redis 连接地址（显式注入优先）。"""
        if self._redis_url_override is not None:
            return self._redis_url_override
        return settings.REDIS_URL

    def _ensure_subscriber(self) -> None:
        """惰性启动 Redis 广播订阅后台任务（幂等；首次有连接注册时触发）。

        守护任务：不进 lifespan，进程退出随事件循环终止；
        订阅未就绪期间广播自动走本地直投（见 broadcast）。
        """
        if self._subscriber_task is not None or self._bridge_degraded or not self._bridge_enabled():
            return
        self._subscriber_task = asyncio.create_task(self._subscriber_loop())
        logger.debug("WebSocket 广播桥订阅任务已启动（频道 {}）", WS_BROADCAST_CHANNEL)

    async def _get_publish_client(self) -> redis_async.Redis:
        """获取桥发布专用 Redis 客户端（与缓存客户端隔离，独立生命周期）。"""
        if self._publish_client is None:
            self._publish_client = redis_async.Redis.from_url(
                self._resolve_redis_url(),
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                # 显式 RESP2 协议，兼容 Redis 6.0 以下（与 redis_manager 一致）
                protocol=2,
            )
        return self._publish_client

    async def _get_subscribe_client(self) -> redis_async.Redis:
        """获取桥订阅专用 Redis 客户端。

        订阅是长阻塞读：沿用全局读超时（1s）会让空闲连接每秒抛超时异常，
        触发无意义重连直至误判降级，因此订阅连接禁用读超时。
        """
        if self._subscribe_client is None:
            self._subscribe_client = redis_async.Redis.from_url(
                self._resolve_redis_url(),
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
                # 订阅长连接禁用读超时；连接断开由订阅循环捕获并退避重连
                socket_timeout=None,
                protocol=2,
            )
        return self._subscribe_client

    async def _publish_to_bridge(self, message: dict[str, Any]) -> bool:
        """尝试把广播消息发布到 Redis 频道；成功返回 True（投递交给订阅端）。

        返回 False 表示应走本地直投：桥未启用 / 订阅未就绪 / 发布失败
        （fail-open：一次性告警并永久降级，避免每次广播都付出连接超时代价）。
        """
        if self._bridge_degraded or not self._bridge_enabled() or not self._subscriber_ready.is_set():
            return False
        try:
            client = await self._get_publish_client()
            envelope = json.dumps({"type": WS_BROADCAST_CHANNEL, "payload": message}, ensure_ascii=False, default=str)
            await client.publish(WS_BROADCAST_CHANNEL, envelope)
            return True
        except Exception as exc:  # noqa: BLE001 —— 广播不允许因 Redis 故障而报错
            self._bridge_degraded = True
            logger.warning("WebSocket 广播桥发布失败，降级为本地直投: {}", exc)
            return False

    async def _subscriber_loop(self) -> None:
        """订阅广播频道并把远端消息投递给本进程连接（含本进程发布者的回环）。

        异常自动重启（有限次 + 指数退避）；重启耗尽后标记降级——广播退回
        本地直投，避免订阅静默死亡后远端广播丢失。
        """
        backoff = _WS_SUBSCRIBER_BACKOFF_SECONDS
        while self._subscriber_failures < _WS_SUBSCRIBER_MAX_RESTARTS:
            pubsub = None
            try:
                client = await self._get_subscribe_client()
                pubsub = client.pubsub(ignore_subscribe_messages=True)
                await pubsub.subscribe(WS_BROADCAST_CHANNEL)
                # 订阅成功：重置失败计数与退避（只有连续失败才计入重启预算）
                backoff = _WS_SUBSCRIBER_BACKOFF_SECONDS
                self._subscriber_failures = 0
                self._subscriber_ready.set()
                logger.debug("WebSocket 广播桥已订阅频道 {}", WS_BROADCAST_CHANNEL)
                async for msg in pubsub.listen():
                    if not isinstance(msg, dict) or msg.get("type") != "message":
                        continue
                    await self._deliver_bridge_message(msg.get("data"))
                # listen 正常返回（理论少见）：按当前退避重订阅，避免紧密循环
                await asyncio.sleep(backoff)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._subscriber_failures += 1
                self._subscriber_ready.clear()
                logger.warning(
                    "WebSocket 广播桥订阅异常（第 {}/{} 次，{}s 后重试）: {}",
                    self._subscriber_failures,
                    _WS_SUBSCRIBER_MAX_RESTARTS,
                    backoff,
                    exc,
                )
                if self._subscriber_failures >= _WS_SUBSCRIBER_MAX_RESTARTS:
                    break
                await asyncio.sleep(backoff)
                backoff *= 2
            finally:
                # 释放本次订阅占用的连接（失败重连前清理现场）
                if pubsub is not None:
                    with contextlib.suppress(Exception):
                        await pubsub.aclose()
        # 重启次数耗尽：永久降级，广播退回本地直投
        self._bridge_degraded = True
        self._subscriber_ready.clear()
        if self._subscribe_client is not None:
            with contextlib.suppress(Exception):
                await self._subscribe_client.aclose()
        logger.error("WebSocket 广播桥订阅任务重启次数耗尽，本实例广播降级为本地直投")

    async def _deliver_bridge_message(self, raw: Any) -> None:
        """解析桥信封并把消息投递给本进程连接（解析失败仅告警，不中断订阅）。"""
        try:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", "replace")
            envelope = json.loads(str(raw))
            payload = envelope.get("payload")
            if isinstance(payload, dict):
                await self._broadcast_local(payload)
        except (json.JSONDecodeError, TypeError, ValueError, AttributeError) as exc:
            logger.warning("忽略无法解析的 WebSocket 广播桥消息: {}", exc)

    # ==================== 本地并发广播 ====================

    async def _broadcast_local(self, message: dict[str, Any]) -> None:
        """本地直投：并发发送给本进程全部连接，慢/死连接剔除。

        asyncio.gather 并发发送：慢消费者只阻塞自己一路（超时上限 5s），
        不再串行拖慢整轮广播；单连接异常经 return_exceptions 隔离，不影响其它连接。
        """
        payload = json.dumps(message, ensure_ascii=False, default=str)
        targets = [(user_id, ws) for user_id, conns in self._connections.items() for ws in list(conns)]
        if not targets:
            return
        await asyncio.gather(*(self._send_one(user_id, ws, payload) for user_id, ws in targets), return_exceptions=True)

    async def _send_one(self, user_id: str, ws: WebSocket, payload: str) -> None:
        """单连接广播发送：超时/异常时告警并剔除，不影响其它连接。"""
        try:
            await self._send_json(ws, payload)
        except Exception as exc:
            logger.warning("广播消息失败(用户 {}): {}", user_id, exc)
            self.disconnect(user_id, ws)


# 进程级单例：service 层与 router 层共享同一实例
ws_manager = ConnectionManager()
