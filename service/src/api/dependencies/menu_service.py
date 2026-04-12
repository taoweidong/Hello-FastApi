"""菜单应用服务和仓储工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.services.menu_service import MenuService
from src.infrastructure.database import get_db
from src.infrastructure.repositories.menu_repository import MenuRepository


async def get_menu_service(db: AsyncSession = Depends(get_db)) -> MenuService:
    """获取菜单服务实例。"""
    menu_repo = MenuRepository(db)
    return MenuService(session=db, menu_repo=menu_repo)


def get_menu_repository(db: AsyncSession = Depends(get_db)) -> MenuRepository:
    """获取菜单仓储实例。"""
    return MenuRepository(db)
