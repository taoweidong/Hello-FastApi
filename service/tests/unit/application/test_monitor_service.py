"""监控应用服务单元测试。

覆盖 MonitorService：
- 格式化工具函数（GB/时长）
- get_server_info 真实采集结构完整性
- get_cache_info 降级（None 客户端/连接异常）与 Redis info 解析（命中率/命令统计 Top10）
"""

from datetime import datetime, timezone

import pytest

from src.application.dto.monitor_dto import CacheInfoDTO, OnlineLogsQueryDTO, ServerInfoDTO
from src.application.services.monitor_service import MonitorService, _format_duration, _format_gb


class _FakeRedis:
    """Redis 客户端替身：可预置 info/dbsize 返回值或抛出异常。"""

    def __init__(self, info: dict | None = None, dbsize: int = 0, error: Exception | None = None):
        self._info = info or {}
        self._dbsize = dbsize
        self._error = error

    async def info(self) -> dict:
        if self._error:
            raise self._error
        return self._info

    async def dbsize(self) -> int:
        return self._dbsize


@pytest.mark.unit
class TestFormatHelpers:
    """格式化工具函数测试。"""

    def test_format_gb(self):
        assert _format_gb(1024**3) == "1.00 GB"
        assert _format_gb(1.5 * 1024**3) == "1.50 GB"
        assert _format_gb(0) == "0.00 GB"

    def test_format_duration(self):
        assert _format_duration(5) == "5秒"
        assert _format_duration(3661) == "1小时1分钟1秒"
        assert _format_duration(90061) == "1天1小时1分钟1秒"
        assert _format_duration(-5) == "0秒"


@pytest.mark.unit
class TestGetServerInfo:
    """服务器信息采集测试（真实调用 psutil）。"""

    async def test_returns_full_structure(self):
        service = MonitorService()
        result = await service.get_server_info()

        assert isinstance(result, ServerInfoDTO)
        assert result.cpu.coreCount >= 1
        assert 0 <= result.cpu.usedPercent <= 100
        assert result.memory.total.endswith(" GB")
        assert result.memory.usedPercent >= 0
        assert result.disk.total.endswith(" GB")
        assert result.system.hostname
        assert result.system.pythonVersion
        assert result.system.workDir
        assert result.process.pid > 0
        assert result.process.memoryUsed.endswith(" GB")
        assert result.process.runningTime


@pytest.mark.unit
class TestGetCacheInfo:
    """缓存信息采集测试。"""

    async def test_none_client_returns_degraded(self):
        """客户端为 None 时返回降级结构，不抛异常。"""
        result = await MonitorService().get_cache_info(None)
        assert isinstance(result, CacheInfoDTO)
        assert result.connected is False
        assert result.message

    async def test_parse_redis_info(self):
        """正常解析 Redis info 各字段与命中率。"""
        fake = _FakeRedis(
            info={
                "redis_version": "7.2.4",
                "redis_mode": "standalone",
                "uptime_in_seconds": 3600,
                "used_memory_human": "1.20M",
                "used_memory_peak_human": "2.00M",
                "connected_clients": 3,
                "keyspace_hits": 80,
                "keyspace_misses": 20,
                "cmdstat_get": {"calls": 100, "usec": 500},
                "cmdstat_set": {"calls": 50, "usec": 300},
            },
            dbsize=12,
        )
        result = await MonitorService().get_cache_info(fake)
        assert result.connected is True
        assert result.version == "7.2.4"
        assert result.mode == "standalone"
        assert result.uptimeSeconds == 3600
        assert result.usedMemory == "1.20M"
        assert result.usedMemoryPeak == "2.00M"
        assert result.keyCount == 12
        assert result.hitRate == 80.0
        assert result.clients == 3
        # 命令统计按调用次数降序
        assert [item.name for item in result.commandStats] == ["get", "set"]

    async def test_hit_rate_none_without_keyspace_stats(self):
        """无命中统计时 hitRate 为 None。"""
        fake = _FakeRedis(info={}, dbsize=0)
        result = await MonitorService().get_cache_info(fake)
        assert result.connected is True
        assert result.hitRate is None
        assert result.commandStats == []

    async def test_connection_error_returns_degraded(self):
        """Redis 命令执行失败时降级返回并携带错误说明。"""
        fake = _FakeRedis(error=ConnectionError("connection refused"))
        result = await MonitorService().get_cache_info(fake)
        assert result.connected is False
        assert "connection refused" in result.message

    async def test_command_stats_sorted_top10(self):
        """命令统计超过 10 条时按调用次数取 Top10。"""
        info = {f"cmdstat_cmd{i}": {"calls": i, "usec": i * 10} for i in range(1, 16)}
        fake = _FakeRedis(info=info, dbsize=0)
        result = await MonitorService().get_cache_info(fake)
        assert len(result.commandStats) == 10
        assert result.commandStats[0].name == "cmd15"
        assert result.commandStats[0].calls == 15


class _FakeCache:
    """缓存服务替身：预置在线会话列表并记录删除/拉黑调用。"""

    def __init__(self, sessions: list[dict] | None = None):
        self._sessions = list(sessions or [])
        self.deleted: list[str] = []
        self.blacklisted: list[str] = []
        self.blacklist_ttl: int = 0

    async def get_online_users(self) -> list[dict]:
        return [dict(item) for item in self._sessions]

    async def get_online_user(self, session_key: str) -> dict | None:
        for item in self._sessions:
            if item.get("id") == session_key:
                return dict(item)
        return None

    async def delete_online_user(self, session_key: str) -> bool:
        self.deleted.append(session_key)
        return True

    async def blacklist_token_hash(self, token_hash: str, expires_at: datetime) -> bool:
        self.blacklisted.append(token_hash)
        now = datetime.now(timezone.utc)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        self.blacklist_ttl = max(int((expires_at - now).total_seconds()), 0)
        return True


def _make_session(
    session_id: str, username: str, login_time: str, expires_at: str = "2099-01-01T00:00:00+00:00"
) -> dict:
    """构造一条在线会话记录（含 id=session_key）。"""
    return {
        "id": session_id,
        "userId": f"u-{session_id}",
        "username": username,
        "ip": "127.0.0.1",
        "system": "Windows",
        "browser": "Chrome",
        "loginTime": login_time,
        "expiresAt": expires_at,
    }


@pytest.mark.unit
class TestGetOnlineLogs:
    """在线用户会话查询测试（get_online_logs）。"""

    async def test_without_cache_service_returns_empty(self):
        """未注入缓存服务时降级返回空列表与 0 总数。"""
        query = OnlineLogsQueryDTO()
        result = await MonitorService().get_online_logs(query)
        assert result == ([], 0)

    async def test_filter_sort_and_paginate(self):
        """支持用户名过滤、loginTime 倒序与分页。"""
        cache = _FakeCache(
            sessions=[
                _make_session("h1", "admin", "2026-03-29T10:00:00"),
                _make_session("h2", "common", "2026-03-29T11:00:00"),
                _make_session("h3", "Admin", "2026-03-29T09:00:00"),
            ]
        )
        service = MonitorService(cache_service=cache)

        # 无过滤：按登录时间倒序
        items, total = await service.get_online_logs(OnlineLogsQueryDTO(page_size=2))
        assert total == 3
        assert [item["id"] for item in items] == ["h2", "h1"]

        # 用户名过滤（忽略大小写）、分页取第二页
        items, total = await service.get_online_logs(OnlineLogsQueryDTO(username="admin", page_num=1, page_size=10))
        assert total == 2
        assert sorted(item["username"] for item in items) == ["Admin", "admin"]


@pytest.mark.unit
class TestForceOffline:
    """强制下线测试（force_offline）。"""

    async def test_without_cache_service_returns_false(self):
        """未注入缓存服务时返回 False（调用方应提示失败）。"""
        assert await MonitorService().force_offline("h1") is False

    async def test_force_offline_deletes_session_and_blacklists_token(self):
        """强退删除会话并将会话哈希加入黑名单，TTL 取会话过期时间。"""
        cache = _FakeCache(sessions=[_make_session("h1", "admin", "2026-03-29T10:00:00", "2099-01-01T00:00:00+00:00")])
        service = MonitorService(cache_service=cache)

        result = await service.force_offline("h1")
        assert result is True
        assert cache.deleted == ["h1"]
        assert cache.blacklisted == ["h1"]
        assert cache.blacklist_ttl > 0

    async def test_force_offline_missing_session_is_idempotent(self):
        """会话不存在时同样删除并拉黑（幂等，不抛异常）。"""
        cache = _FakeCache(sessions=[])
        service = MonitorService(cache_service=cache)

        result = await service.force_offline("unknown-hash")
        assert result is True
        assert cache.deleted == ["unknown-hash"]
        assert cache.blacklisted == ["unknown-hash"]
        # 无会话过期时间：兜底使用默认黑名单保留时长
        assert cache.blacklist_ttl == 86400

    async def test_force_offline_invalid_expires_at_uses_fallback(self):
        """会话过期时间无法解析时兜底使用默认黑名单保留时长。"""
        cache = _FakeCache(
            sessions=[{"id": "h1", "username": "admin", "loginTime": "2026-03-29T10:00:00", "expiresAt": "bad-value"}]
        )
        service = MonitorService(cache_service=cache)

        result = await service.force_offline("h1")
        assert result is True
        assert cache.blacklist_ttl == 86400
