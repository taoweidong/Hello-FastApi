"""用户应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.cache_service import get_cache_service
from src.api.dependencies.domain_services import get_password_service
from src.api.dependencies.repositories import RepoBundle, get_repositories
from src.application.services.user_service import UserService
from src.domain.services.cache_port import UserCachePort
from src.domain.services.password_service import PasswordService


async def get_user_service(
    repos: RepoBundle = Depends(get_repositories),
    password_service: PasswordService = Depends(get_password_service),
    cache_service: UserCachePort = Depends(get_cache_service),
) -> UserService:
    """获取用户服务实例。

    注入用户/角色/部门/岗位仓储、密码服务和用户缓存端口依赖。
    四个仓储同来自请求级仓储束，共享同一 Session（事务约定见 repositories.py）。
    """
    return UserService(
        repo=repos.user,
        password_service=password_service,
        role_repo=repos.role,
        cache_service=cache_service,
        dept_repo=repos.department,
        post_repo=repos.post,
    )
