"""授权应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.cache_service import get_cache_service
from src.api.dependencies.repositories import RepoBundle, get_repositories
from src.application.services.authorization_service import AuthorizationService
from src.domain.services.cache_port import UserCachePort


async def get_authorization_service(
    repos: RepoBundle = Depends(get_repositories), cache_service: UserCachePort | None = Depends(get_cache_service)
) -> AuthorizationService:
    """获取授权服务实例。

    与 UserService 共享同一请求级 session（仓储来自同一个束，
    事务约定见 infrastructure/repositories/base.py 模块 docstring）。
    """
    return AuthorizationService(user_repo=repos.user, role_repo=repos.role, cache_service=cache_service)
