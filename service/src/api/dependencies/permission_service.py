"""权限应用服务工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.services.permission_service import PermissionService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.permission_repository import PermissionRepository


async def get_permission_service(db: AsyncSession = Depends(get_db)) -> PermissionService:
    """获取权限服务实例。

    注入权限仓储依赖。
    """
    perm_repo = PermissionRepository(db)
    return PermissionService(session=db, perm_repo=perm_repo)
