"""LogService 的单元测试：keyset 深分页游标与 COUNT 缓存策略。

验证 COUNT 策略契约：
- 首页（无游标且 pageNum<=1）：仓储执行精确 COUNT（total=None 透传），结果回填缓存；
- 深页（游标或 pageNum>1）：优先读缓存 total 跳过 COUNT；缓存未命中兜底 COUNT 并回填；
- 游标语义：beforeTime/beforeId 同时提供才走 keyset（before_time/before_id 透传仓储），
  否则 offset 模式（完全向后兼容）。

缓存替身使用内存字典实现真实读写语义（与 fakes.py 的替身思路一致）。
"""

from unittest.mock import AsyncMock

import pytest

from src.application.services.log_service import LogService, _hash_log_filters
from src.domain.services.cache_port import LogCountCachePort


class DictBackedLogCountCache(LogCountCachePort):
    """内存字典实现的日志 count 缓存替身：真实读写语义。"""

    def __init__(self) -> None:
        self.store: dict[str, int] = {}
        self.get_calls: list[str] = []
        self.set_calls: list[tuple[str, int]] = []

    async def get_log_count(self, filters_hash: str) -> int | None:
        self.get_calls.append(filters_hash)
        return self.store.get(filters_hash)

    async def set_log_count(self, filters_hash: str, total: int) -> bool:
        self.set_calls.append((filters_hash, total))
        self.store[filters_hash] = total
        return True


def _make_query_dto(**kw):
    """构造 OperationLogListQueryDTO 实例（camelCase 字段与前端契约一致）。"""
    from src.application.dto.log_dto import OperationLogListQueryDTO

    return OperationLogListQueryDTO(**kw)


def _make_service(total_on_count: int = 42):
    """构造带替身缓存与 mock 仓储的日志服务。

    仓储替身模拟真实语义：total 参数非 None 时原样返回（跳过 COUNT 复用传入值），
    否则返回精确 COUNT 结果 total_on_count。
    """
    repo = AsyncMock()

    async def fake_get_operation_logs(**kwargs):
        passed = kwargs.get("total")
        return [{"id": "log-1"}], (passed if passed is not None else total_on_count)

    repo.get_operation_logs = AsyncMock(side_effect=fake_get_operation_logs)
    return LogService(log_repo=repo, count_cache=DictBackedLogCountCache()), repo


@pytest.mark.unit
class TestLogCountStrategy:
    """日志列表 COUNT 缓存策略。"""

    @pytest.mark.asyncio
    async def test_first_page_counts_and_backfills_cache(self):
        """首页执行精确 COUNT 并回填缓存。"""
        svc, repo = _make_service(total_on_count=42)
        logs, total = await svc.get_operation_logs(_make_query_dto())

        assert total == 42
        repo.get_operation_logs.assert_awaited_once()
        kwargs = repo.get_operation_logs.await_args.kwargs
        assert kwargs["total"] is None  # 首页透传 None → 仓储执行精确 COUNT
        cache: DictBackedLogCountCache = svc.count_cache
        assert cache.set_calls == [(cache.set_calls[0][0], 42)]
        assert cache.set_calls[0][0]  # filters_hash 非空

    @pytest.mark.asyncio
    async def test_deep_offset_page_uses_cached_total(self):
        """offset 深页（pageNum>1）命中缓存时跳过 COUNT（total 透传仓储）。"""
        svc, repo = _make_service(total_on_count=42)
        cache: DictBackedLogCountCache = svc.count_cache
        h = _hash_log_filters(None, None, None, None)
        cache.store[h] = 77

        logs, total = await svc.get_operation_logs(_make_query_dto(pageNum=3))
        assert total == 77
        kwargs = repo.get_operation_logs.await_args.kwargs
        assert kwargs["total"] == 77  # 缓存值透传 → 仓储跳过 COUNT

    @pytest.mark.asyncio
    async def test_deep_page_cache_miss_falls_back_to_count_and_backfills(self):
        """深页缓存未命中时兜底执行 COUNT 并回填缓存。"""
        svc, repo = _make_service(total_on_count=55)
        logs, total = await svc.get_operation_logs(_make_query_dto(pageNum=2))
        assert total == 55
        cache: DictBackedLogCountCache = svc.count_cache
        assert cache.store and list(cache.store.values()) == [55]

    @pytest.mark.asyncio
    async def test_no_cache_port_still_counts_every_page(self):
        """未注入缓存端口时行为与历史一致（每页精确 COUNT）。"""
        repo = AsyncMock()
        repo.get_operation_logs = AsyncMock(return_value=([], 9))
        svc = LogService(log_repo=repo, count_cache=None)

        logs, total = await svc.get_operation_logs(_make_query_dto(pageNum=2))
        assert total == 9
        kwargs = repo.get_operation_logs.await_args.kwargs
        assert kwargs["total"] is None

    @pytest.mark.asyncio
    async def test_filters_hash_changes_with_module(self):
        """筛选条件不同 → 缓存 Key 不同（互不污染）。"""
        h1 = _hash_log_filters("user", None, None, None)
        h2 = _hash_log_filters("role", None, None, None)
        h3 = _hash_log_filters(None, 500, None, None)
        assert len({h1, h2, h3}) == 3


@pytest.mark.unit
class TestLogKeysetCursor:
    """keyset 游标分页语义。"""

    @pytest.mark.asyncio
    async def test_cursor_page_uses_cached_total_and_skips_offset(self):
        """游标深页：透传 before_time/before_id 与缓存 total。"""
        svc, repo = _make_service()
        cache: DictBackedLogCountCache = svc.count_cache
        cache.store[_hash_log_filters("user", None, None, None)] = 100

        dto = _make_query_dto(module="user", beforeTime="2026-01-01T00:00:00", beforeId="abc")
        logs, total = await svc.get_operation_logs(dto)

        assert total == 100
        kwargs = repo.get_operation_logs.await_args.kwargs
        assert kwargs["before_time"] is not None
        assert kwargs["before_id"] == "abc"
        assert kwargs["total"] == 100

    @pytest.mark.asyncio
    async def test_partial_cursor_falls_back_to_offset_mode(self):
        """游标字段不完整（只有 beforeId）时退回 offset 模式，行为向后兼容。"""
        svc, repo = _make_service(total_on_count=7)
        dto = _make_query_dto(beforeId="abc")
        logs, total = await svc.get_operation_logs(dto)

        assert total == 7
        kwargs = repo.get_operation_logs.await_args.kwargs
        assert kwargs["before_time"] is None
        assert kwargs["before_id"] is None
        assert kwargs["total"] is None  # 首页语义：精确 COUNT

    @pytest.mark.asyncio
    async def test_invalid_before_time_ignored(self):
        """beforeTime 非法（无法解析）时退回 offset 模式。"""
        svc, repo = _make_service(total_on_count=7)
        dto = _make_query_dto(beforeTime="not-a-date", beforeId="abc")
        await svc.get_operation_logs(dto)
        kwargs = repo.get_operation_logs.await_args.kwargs
        assert kwargs["before_time"] is None
        assert kwargs["before_id"] is None

    @pytest.mark.asyncio
    async def test_cursor_page_cache_miss_backfills(self):
        """游标页缓存未命中：兜底 COUNT 并回填（total 语义正确）。"""
        svc, repo = _make_service(total_on_count=88)
        dto = _make_query_dto(beforeTime="2026-01-01T00:00:00", beforeId="abc")
        logs, total = await svc.get_operation_logs(dto)

        assert total == 88
        cache: DictBackedLogCountCache = svc.count_cache
        assert list(cache.store.values()) == [88]


@pytest.mark.unit
class TestLogServiceCompat:
    """既有行为兼容（登录日志不受 COUNT 策略影响）。"""

    @pytest.mark.asyncio
    async def test_login_logs_untouched(self):
        """登录日志不走 count 缓存（keyset 仅针对 sys_logs）。"""
        repo = AsyncMock()
        repo.get_login_logs = AsyncMock(return_value=([{"id": "l1"}], 3))
        svc = LogService(log_repo=repo, count_cache=DictBackedLogCountCache())

        dto = _make_login_query()
        logs, total = await svc.get_login_logs(dto)
        assert total == 3
        assert not svc.count_cache.get_calls
        assert not svc.count_cache.set_calls

    @pytest.mark.asyncio
    async def test_system_logs_share_strategy(self):
        """系统日志与操作日志共享 COUNT 策略（同一张 sys_logs 表）。"""
        repo = AsyncMock()
        repo.get_system_logs = AsyncMock(return_value=([], 5))
        svc = LogService(log_repo=repo, count_cache=DictBackedLogCountCache())

        from src.application.dto.log_dto import SystemLogListQueryDTO

        logs, total = await svc.get_system_logs(SystemLogListQueryDTO())
        assert total == 5
        # 仓储委托到 get_operation_logs 形态（repo mock 已按 get_system_logs 打桩）
        repo.get_system_logs.assert_awaited_once()


def _make_login_query():
    """构造登录日志查询 DTO。"""
    from src.application.dto.log_dto import LoginLogListQueryDTO

    return LoginLogListQueryDTO()
