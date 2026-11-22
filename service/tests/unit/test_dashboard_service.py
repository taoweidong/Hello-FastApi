"""仪表盘统计聚合服务的单元测试（fakes + 字典背板缓存替身）。

覆盖：趋势按日分桶补零 / 操作分布 TOP8 截断与 None 归并 / creator 批量映射 /
在线数降级 / 读穿透缓存命中不重算 / SQLite UTC 时基按方言归一（参考
test_highfreq_cache.py 的替身模式）。

时区稳定性：替身仓储里的 naive 时间戳按 sqlite 语义视作 UTC；make_service
默认注入 local_tz=timezone.utc 使换算为恒等映射，断言与运行机器的本地时区
解耦。需要验证真实换算的用例显式注入固定偏移（如 UTC+8）并 monkeypatch
``DashboardService._now`` 固定时钟。
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from src.application.services.dashboard_service import (
    OP_DISTRIBUTION_TOP,
    DashboardService,
    build_login_trend,
    build_op_distribution,
    db_time_to_local,
    dialect_of,
    local_time_to_db,
)
from src.domain.entities.log import LoginLogEntity, OperationLogEntity
from src.domain.entities.user import UserEntity
from tests.unit.fakes import InMemoryLogRepository, InMemoryRoleRepository, InMemoryUserRepository

NOW = datetime(2026, 11, 23, 15, 30, 45)


class DictBackedDashboardCache:
    """内存字典实现的仪表盘缓存替身：真实读写语义（与真实 CacheService 的
    JSON dict 读写降级行为一致，写入失败场景由 CacheService 单测覆盖）。"""

    def __init__(self) -> None:
        self.store: dict[str, dict] = {}

    async def get_dashboard_stats(self):
        return self.store.get("dashboard:stats")

    async def set_dashboard_stats(self, data: dict) -> bool:
        self.store["dashboard:stats"] = data
        return True


def make_service(
    log_repo, user_repo=None, role_repo=None, session_store=None, cache=None, dialect="sqlite", local_tz=timezone.utc
) -> DashboardService:
    """组装被测服务（menu/dept/post 计数用 AsyncMock 桩，计数与本测试无关）。

    dialect 默认 sqlite + local_tz 默认注入 UTC：替身仓储的 naive 时间戳按
    sqlite 语义视作 UTC，归一换算为恒等映射，使断言与运行机器的本地时区解耦。
    """
    menu_repo = AsyncMock()
    menu_repo.count.return_value = 3
    dept_repo = AsyncMock()
    dept_repo.count.return_value = 4
    post_repo = AsyncMock()
    post_repo.count.return_value = 5
    return DashboardService(
        user_repo=user_repo or InMemoryUserRepository(),
        role_repo=role_repo or InMemoryRoleRepository(),
        menu_repo=menu_repo,
        dept_repo=dept_repo,
        post_repo=post_repo,
        log_repo=log_repo,
        session_store=session_store,
        cache=cache,
        dialect=dialect,
        local_tz=local_tz,
    )


@pytest.mark.unit
class TestBuildLoginTrend:
    """登录趋势纯函数：分桶 / 补零 / 窗口裁剪 / 升序。"""

    def test_fills_missing_days_with_zero_and_sorted_ascending(self):
        times = [NOW - timedelta(days=6), NOW - timedelta(days=2), NOW]
        points = build_login_trend(times, NOW)

        assert len(points) == 7
        assert [p.count for p in points] == [1, 0, 0, 0, 1, 0, 1]
        # date 为 "MM-DD" 文本且按时间升序（首项 = 6 天前，末项 = 今天）
        assert points[-1].date == "11-23"
        assert points[0].date == "11-17"

    def test_out_of_window_timestamps_ignored(self):
        times = [NOW - timedelta(days=8), NOW + timedelta(days=1)]
        points = build_login_trend(times, NOW)
        assert all(p.count == 0 for p in points)


@pytest.mark.unit
class TestBuildOpDistribution:
    """操作分布纯函数：None 归并 / TOP8 截断 / 计数降序。"""

    def test_none_module_merged_into_unknown(self):
        stamps = [(NOW, "user"), (NOW, None), (NOW, None)]
        result = build_op_distribution(stamps)
        assert [(item.module, item.count) for item in result] == [("未知", 2), ("user", 1)]

    def test_top8_truncation_and_descending_order(self):
        stamps = [(NOW, f"mod{i}") for i in range(12)]
        # 让 mod11 计数最高（重复多次），验证截断后保留计数最多的前 8 个
        stamps.extend((NOW, "mod11") for _ in range(9))
        result = build_op_distribution(stamps)

        assert len(result) == OP_DISTRIBUTION_TOP
        counts = [item.count for item in result]
        assert counts == sorted(counts, reverse=True)
        assert result[0].module == "mod11" and result[0].count == 10


@pytest.mark.unit
class TestDbTimeNormalization:
    """方言感知的时间基归一纯函数：SQLite UTC → 本地，PG 原样。"""

    def test_dialect_of_parses_sqlalchemy_url(self):
        assert dialect_of("sqlite+aiosqlite:///./sql/test.db") == "sqlite"
        assert dialect_of("postgresql+asyncpg://u:p@h/db") == "postgresql"
        assert dialect_of("mysql://u:p@h/db") == "mysql"

    def test_sqlite_utc_naive_converts_to_local(self):
        """sqlite 方言：UTC naive 视为 UTC，换算本地（+8）——跨日边界落对桶。"""
        tz_plus8 = timezone(timedelta(hours=8))
        # 11-23 16:00 UTC == 本地 11-24 00:00（跨日临界点）
        assert db_time_to_local(datetime(2026, 11, 23, 16, 0, 0), "sqlite", tz_plus8) == datetime(2026, 11, 24, 0, 0)
        # 11-23 15:59 UTC == 本地 11-23 23:59（尚在本日）
        assert db_time_to_local(datetime(2026, 11, 23, 15, 59, 0), "sqlite", tz_plus8) == datetime(2026, 11, 23, 23, 59)

    def test_postgres_passthrough(self):
        """PG 方言：now() 随会话时区返回，与 Python 本地同基，原样使用。"""
        ts = datetime(2026, 11, 23, 16, 0, 0)
        assert db_time_to_local(ts, "postgresql", timezone(timedelta(hours=8))) is ts

    def test_local_time_to_db_is_inverse(self):
        """本地 naive 边界 → UTC naive（查询下推），与 db_time_to_local 互逆。"""
        tz_plus8 = timezone(timedelta(hours=8))
        utc = local_time_to_db(datetime(2026, 11, 24, 4, 0, 0), "sqlite", tz_plus8)
        assert utc == datetime(2026, 11, 23, 20, 0, 0)
        assert db_time_to_local(utc, "sqlite", tz_plus8) == datetime(2026, 11, 24, 4, 0, 0)
        # 非 sqlite 方言恒等
        ts = datetime(2026, 11, 24, 4, 0, 0)
        assert local_time_to_db(ts, "postgresql", tz_plus8) is ts


@pytest.mark.unit
class TestDashboardSqliteTimeBase:
    """服务级时基归一：SQLite UTC naive 时间戳落入正确的本地日桶。

    注入固定时区（UTC+8）与固定时钟（本地 11-24 正午），跨时区/跨日稳定。
    """

    async def test_sqlite_utc_stamps_bucket_into_local_day(self, monkeypatch):
        local_tz = timezone(timedelta(hours=8))
        fixed_now = datetime(2026, 11, 24, 12, 0, 0)  # 本地（+8）正午，"今日" = 11-24

        log_repo = InMemoryLogRepository()
        # 11-23 20:00 UTC == 本地 11-24 04:00 → 今日桶（修正前会落入 11-23）
        login_today = LoginLogEntity.create_new(status=1)
        login_today.created_time = datetime(2026, 11, 23, 20, 0, 0)
        await log_repo.create_login_log(login_today)
        # 11-23 15:59 UTC == 本地 11-23 23:59 → 昨日桶
        login_yesterday = LoginLogEntity.create_new(status=1)
        login_yesterday.created_time = datetime(2026, 11, 23, 15, 59, 0)
        await log_repo.create_login_log(login_yesterday)
        # 操作日志：11-23 20:00 UTC → 本地 11-24 → 今日操作数
        op_today = OperationLogEntity.create_new(module="user")
        op_today.created_time = datetime(2026, 11, 23, 20, 0, 0)
        await log_repo.create_operation_log(op_today)

        service = make_service(log_repo, dialect="sqlite", local_tz=local_tz)
        monkeypatch.setattr(service, "_now", lambda: fixed_now)
        data = await service.get_dashboard_stats()

        # todayStats 与 trend 复用同一份归一结果：今日登录 1、今日操作 1
        assert data["todayStats"] == {"loginCount": 1, "opCount": 1}
        assert data["loginTrend"][-1]["date"] == "11-24"
        assert data["loginTrend"][-1]["count"] == 1
        assert data["loginTrend"][-2]["date"] == "11-23"
        assert data["loginTrend"][-2]["count"] == 1


@pytest.mark.unit
class TestDashboardServiceAggregation:
    """服务聚合：totals / todayStats / creator 批量映射 / 在线数。"""

    async def test_aggregates_from_fakes(self):
        log_repo = InMemoryLogRepository()
        # 近 7 天成功登录 3 条 + 失败 1 条（不计入）+ 窗口外 1 条
        for offset, status in ((0, 1), (0, 1), (2, 1), (0, 0), (8, 1)):
            entity = LoginLogEntity.create_new(status=status)
            entity.created_time = NOW - timedelta(days=offset)
            await log_repo.create_login_log(entity)

        # 操作日志：user 模块 2 条（1 条今日）+ None 模块 1 条
        for module, created_time, creator_id in (
            ("user", NOW, "u1"),
            ("user", NOW - timedelta(days=3), "u2"),
            (None, NOW - timedelta(days=1), None),
        ):
            entity = OperationLogEntity.create_new(module=module)
            entity.creator_id = creator_id
            entity.created_time = created_time
            await log_repo.create_operation_log(entity)

        user_repo = InMemoryUserRepository()
        await user_repo.create(UserEntity(id="u1", username="alice", password="x"))
        # u2 无对应用户 → creator 回填空串
        role_repo = InMemoryRoleRepository()

        service = make_service(log_repo, user_repo=user_repo, role_repo=role_repo)
        data = await service.get_dashboard_stats()

        # totals：菜单/部门/岗位来自 AsyncMock 桩；用户/角色来自内存仓储
        assert data["totals"] == {"users": 1, "roles": 0, "menus": 3, "depts": 4, "posts": 5, "online": 0}
        # todayStats：仅今日成功登录与今日操作日志
        assert data["todayStats"] == {"loginCount": 2, "opCount": 1}
        # 趋势：7 项、补零、升序（day-2 为 1）、今日为 2
        assert [p["count"] for p in data["loginTrend"]] == [0, 0, 0, 0, 1, 0, 2]
        assert data["loginTrend"][-1]["date"] == "11-23"
        # 分布：None 归入「未知」，count 降序
        assert data["opDistribution"] == [{"module": "user", "count": 2}, {"module": "未知", "count": 1}]
        # 最近日志：creator 批量映射（u1→alice，u2 缺失→空串），camelCase 字段
        assert len(data["recentLogs"]) == 3
        assert {log["creator"] for log in data["recentLogs"]} == {"alice", ""}
        recent = next(log for log in data["recentLogs"] if log["creator"] == "alice")
        assert set(recent.keys()) == {
            "id",
            "module",
            "method",
            "path",
            "ipaddress",
            "creator",
            "statusCode",
            "createdTime",
        }

    async def test_online_count_from_session_store(self):
        class FakeSessionStore:
            async def get_online_users(self):
                return [{"username": "a"}, {"username": "b"}]

        service = make_service(InMemoryLogRepository(), session_store=FakeSessionStore())
        data = await service.get_dashboard_stats()
        assert data["totals"]["online"] == 2


@pytest.mark.unit
class TestDashboardCache:
    """读穿透缓存：命中不重算，未命中聚合并写回。"""

    async def test_cache_hit_skips_all_repos(self):
        cache = DictBackedDashboardCache()
        cached_payload = {"totals": {"users": 99}, "hit": True}
        await cache.set_dashboard_stats(cached_payload)

        log_repo = InMemoryLogRepository()
        # 全部仓储方法替换为 AsyncMock：命中缓存时一次都不应被调用
        log_repo.list_login_log_times = AsyncMock()
        log_repo.list_operation_log_stamps = AsyncMock()
        log_repo.get_operation_logs = AsyncMock()
        user_repo = InMemoryUserRepository()
        user_repo.count = AsyncMock()
        service = make_service(log_repo, user_repo=user_repo, cache=cache)

        data = await service.get_dashboard_stats()

        assert data == cached_payload
        log_repo.list_login_log_times.assert_not_called()
        log_repo.list_operation_log_stamps.assert_not_called()
        log_repo.get_operation_logs.assert_not_called()
        user_repo.count.assert_not_called()

    async def test_cache_miss_computes_and_writes_back(self):
        cache = DictBackedDashboardCache()
        log_repo = InMemoryLogRepository()
        entity = LoginLogEntity.create_new(status=1)
        entity.created_time = NOW
        await log_repo.create_login_log(entity)

        service = make_service(log_repo, cache=cache)
        data = await service.get_dashboard_stats()

        cached = await cache.get_dashboard_stats()
        assert cached == data  # 写回的是 model_dump(mode="json") 形态
        assert data["todayStats"]["loginCount"] == 1

    async def test_second_call_served_from_cache_without_recompute(self):
        """首次调用写缓存后，第二次调用即使日志翻倍也返回缓存值。"""
        cache = DictBackedDashboardCache()
        log_repo = InMemoryLogRepository()
        service = make_service(log_repo, cache=cache)

        first = await service.get_dashboard_stats()

        entity = LoginLogEntity.create_new(status=1)
        entity.created_time = NOW
        await log_repo.create_login_log(entity)
        second = await service.get_dashboard_stats()

        assert second == first
        assert second["todayStats"]["loginCount"] == 0  # 60s TTL 内不重算
