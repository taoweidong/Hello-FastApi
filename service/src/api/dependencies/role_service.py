"""角色应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.cache_service import get_cache_service
from src.api.dependencies.repositories import RepoBundle, get_repositories
from src.application.services.role_service import RoleService
from src.domain.services.cache_port import RoleCachePort, UserCachePort


async def get_role_service(
    repos: RepoBundle = Depends(get_repositories),
    cache_service: UserCachePort | None = Depends(get_cache_service),
    options_cache: RoleCachePort | None = Depends(get_cache_service),
) -> RoleService:
    """获取角色服务实例。

    注入角色仓储与缓存端口依赖：用户缓存端口（角色权限变更后失效相关用户的
    权限/路由缓存）与角色选项缓存端口（/list-all-role 读穿透 + 变更后失效）。
    """
    return RoleService(role_repo=repos.role, cache_service=cache_service, options_cache=options_cache)
