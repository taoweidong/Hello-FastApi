"""授权应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.cache_service import get_cache_service
from src.application.services.authorization_service import AuthorizationService
from src.domain.services.cache_port import CachePort
from src.infrastructure.database import get_db
from src.infrastructure.repositories.role_repository import RoleRepository
from src.infrastructure.repositories.user_repository import UserRepository


async def get_authorization_service(
    db=Depends(get_db), cache_service: CachePort | None = Depends(get_cache_service)
) -> AuthorizationService:
    """获取授权服务实例。

    与 UserService 共享同一请求级 session（事务约定见
    infrastructure/repositories/base.py 模块 docstring）。
    """
    return AuthorizationService(user_repo=UserRepository(db), role_repo=RoleRepository(db), cache_service=cache_service)
