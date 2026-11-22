"""应用层 - 仪表盘统计聚合服务。

一次聚合出统计卡片（totals/todayStats）、近 7 天登录趋势、操作模块分布
与最近操作日志，供前端仪表盘首屏使用。

聚合策略：
- 日期分桶在 **Python 侧** 完成（仅拉取 created_time/module 等轻量列），
  规避 SQL 日期函数在 SQLite/PG 双方言下的差异（测试跑 SQLite，生产跑 PG）；
- 时间基归一：SQLite 的 ``func.now()`` 写入 **UTC** naive 值，而"今日"/近 7 日
  分桶基于本地时间，读取后按方言换算（见 ``db_time_to_local``），保证与前端
  "今日"标签语义一致；
- recentLogs 的 creator 经用户仓储批量 IN 查询映射（避免逐条 N+1）；
- 在线会话数复用 ``OnlineSessionStore`` 端口（不可用降级为 0）；
- 整体结果经 ``DashboardCachePort`` 短缓存（TTL 60s 兜底，无主动失效：
  仪表盘统计允许 1 分钟延迟，主动失效要挂钩 6 张表的写路径，得不偿失）。
"""

from collections import Counter
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Any

from src.application.dto.dashboard_dto import (
    DashboardRecentLogDTO,
    DashboardStatsDTO,
    DashboardTodayStatsDTO,
    DashboardTotalsDTO,
    LoginTrendPointDTO,
    OpDistributionItemDTO,
)
from src.config.settings import settings
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


def dialect_of(database_url: str) -> str:
    """从 DATABASE_URL 解析 SQLAlchemy 方言名（``sqlite+aiosqlite://`` → ``sqlite``）。"""
    scheme = database_url.split("://", 1)[0]
    return scheme.split("+", 1)[0]


def _resolve_local_tz(local_tz: tzinfo | None) -> tzinfo:
    """取参数注入的时区；缺省回落到系统本地时区（再兜底 UTC 防极端环境）。"""
    return local_tz or datetime.now().astimezone().tzinfo or timezone.utc


def db_time_to_local(ts: datetime, dialect: str, local_tz: tzinfo | None = None) -> datetime:
    """把仓储读出的 naive ``created_time`` 按方言归一到本地时间（返回 naive 本地值）。

    两种库的时基差异（本模块所有时间换算的依据）：
    - **SQLite**：``func.now()`` 编译为 ``CURRENT_TIMESTAMP``，恒为 **UTC** naive；
      而"今日"判断与趋势分桶用本地 ``datetime.now()``（如 UTC+8），直接比较会
      差出一个时区偏移——刚登录的记录落入"昨天"，前端出现"今日登录 0 次"。
      故 sqlite 方言下把 naive 值视为 UTC，换算成本地时间后再参与分桶；
    - **PostgreSQL**：``now()`` 随会话时区返回（``TIMESTAMP`` 列读出 naive 的
      会话本地时间），与 Python 侧本地时间同基，按原样使用即可。

    Args:
        ts: 仓储读出的 naive 时间戳（见各 ``list_*`` 仓储方法契约）。
        dialect: 数据库方言名（``dialect_of`` 的结果）。
        local_tz: 本地时区；None 用系统本地时区。参数化便于测试注入固定偏移，
            保证单测跨时区稳定。
    """
    if dialect != "sqlite":
        return ts
    tz = _resolve_local_tz(local_tz)
    return ts.replace(tzinfo=timezone.utc).astimezone(tz).replace(tzinfo=None)


def local_time_to_db(ts: datetime, dialect: str, local_tz: tzinfo | None = None) -> datetime:
    """``db_time_to_local`` 的反向换算：本地 naive 边界 → 数据库存储时基。

    用于把"近 7 日本地窗口起点"下推给仓储查询（``created_time >= ?``）：
    sqlite 方言下存储值为 UTC，若直接下发本地 naive 边界，窗口首日的
    前几个小时（本地凌晨 ≈ 前一天 UTC 午后）会被错误排除；故先转为
    UTC naive 再下发。非 sqlite 方言原样返回。
    """
    if dialect != "sqlite":
        return ts
    tz = _resolve_local_tz(local_tz)
    return ts.replace(tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)


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
        dialect: str | None = None,
        local_tz: tzinfo | None = None,
    ) -> None:
        """初始化仪表盘服务。

        Args:
            user_repo/role_repo/menu_repo/dept_repo/post_repo: 各资源计数仓储
                （全部来自组合根 RepoBundle，共享请求级会话）
            log_repo: 日志仓储（趋势/分布/最近日志）
            session_store: 在线会话端口，None 时在线数降级为 0
            cache: 仪表盘缓存端口，None 时退化为每次实时聚合
            dialect: 数据库方言名（sqlite/postgresql/...），None 时从
                ``settings.DATABASE_URL`` 解析
            local_tz: 本地时区（None 用系统本地时区），参数化便于测试注入固定偏移
        """
        self._user_repo = user_repo
        self._role_repo = role_repo
        self._menu_repo = menu_repo
        self._dept_repo = dept_repo
        self._post_repo = post_repo
        self._log_repo = log_repo
        self._session_store = session_store
        self._cache = cache
        self._dialect = dialect or dialect_of(settings.DATABASE_URL)
        self._local_tz = local_tz

    def _now(self) -> datetime:
        """当前本地时间（独立小方法，便于测试注入固定时钟）。"""
        return datetime.now()

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
        now = self._now()
        week_start = (now - timedelta(days=TREND_DAYS - 1)).replace(hour=0, minute=0, second=0, microsecond=0)

        # ---- 趋势与分布：仅拉轻量列，Python 侧分桶 ----
        # 时间基归一（SQLite 存 UTC，见 db_time_to_local 注释）：查询下推的窗口
        # 边界与读出的时间戳统一换算，"今日"桶与近 7 日分桶都基于本地时间，
        # todayStats 与 trend 复用同一份归一结果，避免两套口径。
        db_week_start = local_time_to_db(week_start, self._dialect, self._local_tz)
        login_times = [
            db_time_to_local(ts, self._dialect, self._local_tz)
            for ts in await self._log_repo.list_login_log_times(db_week_start, status=LOGIN_STATUS_SUCCESS)
        ]
        op_stamps = [
            (db_time_to_local(ts, self._dialect, self._local_tz), module)
            for ts, module in await self._log_repo.list_operation_log_stamps(db_week_start)
        ]

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
