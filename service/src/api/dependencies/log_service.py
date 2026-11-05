"""日志应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.repositories import RepoBundle, get_repositories
from src.application.services.log_service import LogService


async def get_log_service(repos: RepoBundle = Depends(get_repositories)) -> LogService:
    """获取日志服务实例。

    注入日志仓储依赖（仓储来自请求级仓储束，事务约定见 repositories.py）。
    """
    return LogService(log_repo=repos.log)
