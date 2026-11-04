"""ConnectionManager 连接管理器单元测试。"""

import asyncio

import pytest

from src.infrastructure.realtime.manager import ConnectionManager


class _FakeWS:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send_text(self, payload: str) -> None:
        self.sent.append(payload)


class _FakeWSBad:
    async def send_text(self, payload: str) -> None:
        raise RuntimeError("连接已断开")


class _FakeWSSlow:
    """发送耗时超过广播超时的慢连接。"""

    async def send_text(self, payload: str) -> None:
        await asyncio.sleep(30)


@pytest.mark.unit
class TestConnectionManager:
    """连接注册、广播、定向发送与异常隔离。"""

    async def test_connect_and_counts(self):
        mgr = ConnectionManager()
        await mgr.connect("u1", _FakeWS())
        await mgr.connect("u1", _FakeWS())
        assert mgr.online_users == 1
        assert mgr.total_connections == 2
        mgr.disconnect("u1", _FakeWS())  # 未登记的实例不影响
        assert mgr.total_connections == 2

    async def test_broadcast_to_all(self):
        mgr = ConnectionManager()
        ws1, ws2 = _FakeWS(), _FakeWS()
        await mgr.connect("a", ws1)
        await mgr.connect("b", ws2)
        await mgr.broadcast({"type": "x"})
        assert len(ws1.sent) == 1
        assert len(ws2.sent) == 1

    async def test_send_to_user_only(self):
        mgr = ConnectionManager()
        a, b = _FakeWS(), _FakeWS()
        await mgr.connect("a", a)
        await mgr.connect("b", b)
        await mgr.send_to_user("a", {"type": "y"})
        assert len(a.sent) == 1
        assert len(b.sent) == 0

    async def test_broadcast_isolates_failing_connection(self):
        mgr = ConnectionManager()
        good, bad = _FakeWS(), _FakeWSBad()
        await mgr.connect("good", good)
        await mgr.connect("bad", bad)
        # 单个连接异常不得扩散，且异常连接应被清理
        await mgr.broadcast({"type": "z"})
        assert len(good.sent) == 1
        assert "bad" not in mgr._connections

    async def test_disconnect_clears_empty_user(self):
        mgr = ConnectionManager()
        ws = _FakeWS()
        await mgr.connect("u", ws)
        mgr.disconnect("u", ws)
        assert mgr.online_users == 0


@pytest.mark.unit
class TestConnectionLimits:
    """连接数上限（DoS 防护）。"""

    async def test_reject_over_per_user_limit(self):
        mgr = ConnectionManager(max_connections_per_user=2)
        assert await mgr.connect("u", _FakeWS()) is True
        assert await mgr.connect("u", _FakeWS()) is True
        assert await mgr.connect("u", _FakeWS()) is False
        assert mgr.total_connections == 2

    async def test_reject_over_total_limit(self):
        mgr = ConnectionManager(max_connections_per_user=10, max_total_connections=3)
        for i in range(3):
            assert await mgr.connect(f"u{i}", _FakeWS()) is True
        assert await mgr.connect("u9", _FakeWS()) is False
        assert mgr.total_connections == 3

    async def test_disconnect_frees_capacity(self):
        mgr = ConnectionManager(max_total_connections=1)
        ws = _FakeWS()
        assert await mgr.connect("a", ws) is True
        assert await mgr.connect("b", _FakeWS()) is False
        mgr.disconnect("a", ws)
        assert await mgr.connect("b", _FakeWS()) is True


@pytest.mark.unit
class TestBroadcastTimeout:
    """广播单连接发送限时：慢消费者被剔除且不阻塞其它连接。"""

    async def test_slow_connection_dropped_without_blocking(self):
        mgr = ConnectionManager()
        good, slow = _FakeWS(), _FakeWSSlow()
        await mgr.connect("good", good)
        await mgr.connect("slow", slow)
        # 若无超时保护，这里会卡 30s（测试全局超时下直接失败）
        await mgr.broadcast({"type": "notice"})
        assert len(good.sent) == 1
        assert "slow" not in mgr._connections

    async def test_send_to_user_timeout_isolated(self):
        mgr = ConnectionManager()
        slow = _FakeWSSlow()
        await mgr.connect("slow", slow)
        # 不抛出超时异常，且慢连接被清理
        await mgr.send_to_user("slow", {"type": "notice"})
        assert "slow" not in mgr._connections
