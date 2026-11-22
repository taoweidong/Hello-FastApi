"""日志应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.cache_service import get_cache_service
from src.api.dependencies.repositories import RepoBundle, get_repositories
from src.application.services.log_service import LogService
from src.domain.services.cache_port import LogCountCachePort


async def get_log_service(
    repos: RepoBundle = Depends(get_repositories), count_cache: LogCountCachePort = Depends(get_cache_service)
) -> LogService:
    """获取日志服务实例。

    注入日志仓储依赖（仓储来自请求级仓储束，事务约定见 repositories.py），
    以及日志列表 count 缓存端口（keyset 深分页的 COUNT 旁路）。
    """
    return LogService(log_repo=repos.log, count_cache=count_cache)
