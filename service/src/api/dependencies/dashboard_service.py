"""仪表盘应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.cache_service import get_cache_service, get_online_session_store
from src.api.dependencies.repositories import RepoBundle, get_repositories
from src.application.services.dashboard_service import DashboardService
from src.domain.services.cache_port import DashboardCachePort
from src.domain.services.online_session_port import OnlineSessionStore


async def get_dashboard_service(
    repos: RepoBundle = Depends(get_repositories),
    session_store: OnlineSessionStore = Depends(get_online_session_store),
    cache: DashboardCachePort = Depends(get_cache_service),
) -> DashboardService:
    """获取仪表盘服务实例。

    仓储全部来自请求级仓储束（组合根唯一 Session 入口，事务约定见 repositories.py）；
    在线会话数走 ``OnlineSessionStore``，统计聚合缓存走 ``DashboardCachePort``
    （与 CacheService 的其他窄端口视图同一实例）。
    """
    return DashboardService(
        user_repo=repos.user,
        role_repo=repos.role,
        menu_repo=repos.menu,
        dept_repo=repos.department,
        post_repo=repos.post,
        log_repo=repos.log,
        session_store=session_store,
        cache=cache,
    )
