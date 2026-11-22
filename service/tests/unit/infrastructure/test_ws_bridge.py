"""WebSocket Redis 广播桥单元测试。

覆盖：测试环境桥禁用（广播走本地路径且不创建订阅任务）、显式注入 redis_url
启用桥、订阅未就绪时本地直投回退、发布失败 fail-open 降级、桥信封解析投递。
真实 Redis 订阅链路（依赖可用实例）不在此覆盖，由全栈/e2e 验证。
"""

import json
from unittest.mock import AsyncMock

import pytest

from src.infrastructure.realtime.manager import WS_BROADCAST_CHANNEL, ConnectionManager


class _FakeWS:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send_text(self, payload: str) -> None:
        self.sent.append(payload)


@pytest.mark.unit
class TestBridgeDisabledInTesting:
    """测试环境（APP_ENV=testing）桥禁用：广播走本地路径且不启动订阅任务。"""

    async def test_broadcast_uses_local_path_without_subscriber(self):
        mgr = ConnectionManager()
        ws = _FakeWS()
        await mgr.connect("u1", ws)
        await mgr.broadcast({"type": "x"})

        assert len(ws.sent) == 1
        assert mgr._subscriber_task is None  # 未启动订阅任务
        assert mgr._bridge_enabled() is False
        assert mgr._bridge_degraded is False


@pytest.mark.unit
class TestBridgeExplicitUrl:
    """显式注入 redis_url 启用桥（优先于测试环境禁用）。"""

    async def test_falls_back_to_local_before_subscriber_ready(self):
        """订阅未就绪时不得尝试发布，退化为本地直投。"""
        mgr = ConnectionManager(redis_url="redis://127.0.0.1:6390/0")
        ws = _FakeWS()
        await mgr.connect("u1", ws)
        await mgr.broadcast({"type": "y"})

        assert len(ws.sent) == 1
        assert mgr._subscriber_task is not None  # 桥已启动，但尚未就绪
        assert mgr._bridge_degraded is False

    async def test_publish_failure_degrades_to_local(self):
        """发布失败时 fail-open：一次性降级，消息仍本地直投。"""
        mgr = ConnectionManager(redis_url="redis://127.0.0.1:6390/0")
        ws = _FakeWS()
        await mgr.connect("u1", ws)
        mgr._subscriber_ready.set()  # 模拟订阅已就绪
        broken = AsyncMock()
        broken.publish = AsyncMock(side_effect=RuntimeError("redis down"))
        mgr._publish_client = broken

        await mgr.broadcast({"type": "z"})

        assert len(ws.sent) == 1
        assert mgr._bridge_degraded is True

    async def test_degraded_bridge_skips_publish(self):
        """降级后的广播不再尝试发布，直接本地直投。"""
        mgr = ConnectionManager(redis_url="redis://127.0.0.1:6390/0")
        ws = _FakeWS()
        await mgr.connect("u1", ws)
        mgr._bridge_degraded = True
        mgr._subscriber_ready.set()

        await mgr.broadcast({"type": "w"})

        assert len(ws.sent) == 1


@pytest.mark.unit
class TestBridgeDelivery:
    """订阅端收到远端信封后投递给本进程连接。"""

    async def test_deliver_bridge_message(self):
        """合法信封的 payload 被投递给本进程全部连接。"""
        mgr = ConnectionManager()
        ws1, ws2 = _FakeWS(), _FakeWS()
        await mgr.connect("u1", ws1)
        await mgr.connect("u2", ws2)
        envelope = json.dumps({"type": WS_BROADCAST_CHANNEL, "payload": {"type": "notice", "data": 1}})

        await mgr._deliver_bridge_message(envelope)

        assert len(ws1.sent) == 1
        assert len(ws2.sent) == 1

    async def test_deliver_ignores_garbage_and_bad_payload(self):
        """非法 JSON 或 payload 非对象时不投递、不抛异常。"""
        mgr = ConnectionManager()
        ws = _FakeWS()
        await mgr.connect("u1", ws)

        await mgr._deliver_bridge_message("not-json")
        await mgr._deliver_bridge_message(json.dumps({"type": WS_BROADCAST_CHANNEL, "payload": "not-a-dict"}))

        assert ws.sent == []
