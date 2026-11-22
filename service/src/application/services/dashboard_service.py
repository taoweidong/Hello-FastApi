"""应用层 - 仪表盘统计聚合服务。

一次聚合出统计卡片（totals/todayStats）、近 7 天登录趋势、操作模块分布
与最近操作日志，供前端仪表盘首屏使用。

聚合策略：
- 日期分桶在 **Python 侧** 完成（仅拉取 created_time/module 等轻量列），
  规避 SQL 日期函数在 SQLite/PG 双方言下的差异（测试跑 SQLite，生产跑 PG）；
- recentLogs 的 creator 经用户仓储批量 IN 查询映射（避免逐条 N+1）；
- 在线会话数复用 ``OnlineSessionStore`` 端口（不可用降级为 0）；
- 整体结果经 ``DashboardCachePort`` 短缓存（TTL 60s 兜底，无主动失效：
  仪表盘统计允许 1 分钟延迟，主动失效要挂钩 6 张表的写路径，得不偿失）。
"""

from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from src.application.dto.dashboard_dto import (
    DashboardRecentLogDTO,
    DashboardStatsDTO,
    DashboardTodayStatsDTO,
    DashboardTotalsDTO,
    LoginTrendPointDTO,
    OpDistributionItemDTO,
)
from src.domain.repositories.department_repository import DepartmentRepositoryInterface
from src.domain.repositories.log_repository import LogRepositoryInterface
from src.domain.repositories.menu_repository import MenuRepositoryInterface
from src.domain.repositories.post_repository import PostRepositoryInterface
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.domain.repositories.user_repository import UserRepositoryInterface
from src.domain.services.cache_port import DashboardCachePort
from src.domain.services.online_session_port import OnlineSessionStore

# 登录日志成功状态（见 LoginLogEntity：0-失败，1-成功）
LOGIN_STATUS_SUCCESS = 1

# 趋势窗口天数（含今日）
TREND_DAYS = 7

# 操作分布取 TOP N
OP_DISTRIBUTION_TOP = 8

# 最近操作日志条数
RECENT_LOGS_LIMIT = 10

# module 为 None 的日志归并展示名
UNKNOWN_MODULE = "未知"


def build_login_trend(login_times: list[datetime], now: datetime) -> list[LoginTrendPointDTO]:
    """近 7 天（含今日）按日成功登录分桶。

    缺失日期补 0、按时间升序、date 为 "MM-DD" 文本；窗口外的
    时间戳（异常未来值等）自然被忽略。
    """
    counts = Counter(ts.date() for ts in login_times)
    start_date = now.date() - timedelta(days=TREND_DAYS - 1)
    return [
        LoginTrendPointDTO(
            date=(start_date + timedelta(days=offset)).strftime("%m-%d"),
            count=counts.get(start_date + timedelta(days=offset), 0),
        )
        for offset in range(TREND_DAYS)
    ]


def build_op_distribution(
    op_stamps: list[tuple[datetime, str | None]], top: int = OP_DISTRIBUTION_TOP
) -> list[OpDistributionItemDTO]:
    """近 7 天操作日志按 module 分组计数，取 TOP 8（count 降序）。

    module 为 None 归入「未知」；并列计数按 module 名升序保证结果稳定。
    """
    counts = Counter(module if module is not None else UNKNOWN_MODULE for _ts, module in op_stamps)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:top]
    return [OpDistributionItemDTO(module=module, count=count) for module, count in ranked]


class DashboardService:
    """仪表盘统计聚合服务（只读聚合，无独立事务边界——读操作随请求会话一致性视图）。"""

    def __init__(
        self,
        *,
        user_repo: UserRepositoryInterface,
        role_repo: RoleRepositoryInterface,
        menu_repo: MenuRepositoryInterface,
        dept_repo: DepartmentRepositoryInterface,
        post_repo: PostRepositoryInterface,
        log_repo: LogRepositoryInterface,
        session_store: OnlineSessionStore | None = None,
        cache: DashboardCachePort | None = None,
    ) -> None:
        """初始化仪表盘服务。

        Args:
            user_repo/role_repo/menu_repo/dept_repo/post_repo: 各资源计数仓储
                （全部来自组合根 RepoBundle，共享请求级会话）
            log_repo: 日志仓储（趋势/分布/最近日志）
            session_store: 在线会话端口，None 时在线数降级为 0
            cache: 仪表盘缓存端口，None 时退化为每次实时聚合
        """
        self._user_repo = user_repo
        self._role_repo = role_repo
        self._menu_repo = menu_repo
        self._dept_repo = dept_repo
        self._post_repo = post_repo
        self._log_repo = log_repo
        self._session_store = session_store
        self._cache = cache

    async def get_dashboard_stats(self) -> dict[str, Any]:
        """返回仪表盘统计聚合数据（JSON 形态 dict，路由直接包装 success_response）。

        读穿透缓存：命中直接返回缓存 dict（``model_dump(mode="json")`` 形态，
        camelCase 键与 DTO 序列化结果一致）；未命中聚合后写回。缓存写入失败
        不影响响应（CachePort 降级语义）。
        """
        if self._cache is not None:
            cached = await self._cache.get_dashboard_stats()
            if cached is not None:
                return cached
        payload = (await self._build_stats()).model_dump(mode="json")
        if self._cache is not None:
            await self._cache.set_dashboard_stats(payload)
        return payload

    async def _build_stats(self) -> DashboardStatsDTO:
        """实时聚合全部统计字段（缓存未命中路径）。"""
        now = datetime.now()
        week_start = (now - timedelta(days=TREND_DAYS - 1)).replace(hour=0, minute=0, second=0, microsecond=0)

        # ---- 趋势与分布：仅拉轻量列，Python 侧分桶 ----
        login_times = await self._log_repo.list_login_log_times(week_start, status=LOGIN_STATUS_SUCCESS)
        op_stamps = await self._log_repo.list_operation_log_stamps(week_start)

        # ---- totals：各资源计数；在线数走会话端口（None 降级为 0） ----
        online = 0
        if self._session_store is not None:
            online = len(await self._session_store.get_online_users())
        totals = DashboardTotalsDTO(
            users=await self._user_repo.count(),
            roles=await self._role_repo.count(),
            menus=await self._menu_repo.count(),
            depts=await self._dept_repo.count(),
            posts=await self._post_repo.count(),
            online=online,
        )

        # ---- 今日业务量：与趋势/分布同源推导，不重复查询 ----
        today = now.date()
        today_login = sum(1 for ts in login_times if ts.date() == today)
        today_op = sum(1 for ts, _ in op_stamps if ts.date() == today)

        # ---- 最近操作日志：creator 批量映射（单次 IN 查询，避免 N+1） ----
        recent_entities, _total = await self._log_repo.get_operation_logs(page_num=1, page_size=RECENT_LOGS_LIMIT)
        username_map = await self._user_repo.get_usernames_by_ids(
            [e.creator_id for e in recent_entities if e.creator_id]
        )
        recent_logs = [
            DashboardRecentLogDTO(
                id=e.id,
                module=e.module,
                method=e.method,
                path=e.path,
                ipaddress=e.ipaddress,
                creator=username_map.get(e.creator_id or "", "") if e.creator_id else "",
                statusCode=e.status_code,
                createdTime=e.created_time,
            )
            for e in recent_entities
        ]

        return DashboardStatsDTO(
            totals=totals,
            todayStats=DashboardTodayStatsDTO(loginCount=today_login, opCount=today_op),
            loginTrend=build_login_trend(login_times, now),
            opDistribution=build_op_distribution(op_stamps),
            recentLogs=recent_logs,
        )
