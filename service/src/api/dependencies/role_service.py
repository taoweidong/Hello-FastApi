"""角色应用服务工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.cache_service import get_cache_service
from src.application.services.role_service import RoleService
from src.domain.services.cache_port import CachePort
from src.infrastructure.database import get_db
from src.infrastructure.repositories.role_repository import RoleRepository


async def get_role_service(
    db: AsyncSession = Depends(get_db), cache_service: CachePort | None = Depends(get_cache_service)
) -> RoleService:
    """获取角色服务实例。

    注入角色仓储与缓存端口依赖（角色权限变更后需失效相关用户的权限缓存）。
    """
    role_repo = RoleRepository(db)
    return RoleService(role_repo=role_repo, cache_service=cache_service)
