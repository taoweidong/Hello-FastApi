"""菜单应用服务和仓储工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.api.dependencies.cache_service import get_cache_service
from src.application.services.menu_service import MenuService
from src.domain.repositories.role_repository import RoleRepositoryInterface
from src.domain.services.cache_port import CachePort
from src.infrastructure.database import get_db
from src.infrastructure.repositories.menu_repository import MenuRepository
from src.infrastructure.repositories.role_repository import RoleRepository


async def get_menu_service(
    db: AsyncSession = Depends(get_db), cache_service: CachePort = Depends(get_cache_service)
) -> MenuService:
    """获取菜单服务实例。

    注入角色仓储：user-menus 接口需要按用户角色过滤菜单（防全量泄露）。
    """
    menu_repo = MenuRepository(db)
    role_repo: RoleRepositoryInterface = RoleRepository(db)
    return MenuService(menu_repo=menu_repo, cache_service=cache_service, role_repo=role_repo)


def get_menu_repository(db: AsyncSession = Depends(get_db)) -> MenuRepository:
    """获取菜单仓储实例。"""
    return MenuRepository(db)
