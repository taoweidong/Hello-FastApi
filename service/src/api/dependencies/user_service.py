"""用户应用服务和仓储工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.cache_service import get_cache_service
from src.api.dependencies.domain_services import get_password_service
from src.application.services.user_service import UserService
from src.domain.services.cache_port import CachePort
from src.domain.services.password_service import PasswordService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.role_repository import RoleRepository
from src.infrastructure.repositories.user_repository import UserRepository


async def get_user_service(
    db: AsyncSession = Depends(get_db),
    password_service: PasswordService = Depends(get_password_service),
    cache_service: CachePort = Depends(get_cache_service),
) -> UserService:
    """获取用户服务实例。

    注入用户仓储、角色仓储、密码服务和缓存服务依赖。
    """
    user_repo = UserRepository(db)
    role_repo = RoleRepository(db)
    return UserService(
        repo=user_repo, password_service=password_service, role_repo=role_repo, cache_service=cache_service
    )


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """获取用户仓储实例。"""
    return UserRepository(db)
