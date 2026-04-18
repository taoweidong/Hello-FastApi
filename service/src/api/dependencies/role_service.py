"""角色应用服务和仓储工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.services.role_service import RoleService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.role_repository import RoleRepository


async def get_role_service(db: AsyncSession = Depends(get_db)) -> RoleService:
    """获取角色服务实例。

    注入角色仓储依赖。
    """
    role_repo = RoleRepository(db)
    return RoleService(role_repo=role_repo)


async def get_role_repository(db: AsyncSession = Depends(get_db)) -> RoleRepository:
    """获取角色仓储实例。"""
    return RoleRepository(db)
