"""菜单应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.cache_service import get_cache_service
from src.api.dependencies.repositories import RepoBundle, get_repositories
from src.application.services.menu_service import MenuService
from src.domain.services.cache_port import MenuCachePort


async def get_menu_service(
    repos: RepoBundle = Depends(get_repositories), cache_service: MenuCachePort = Depends(get_cache_service)
) -> MenuService:
    """获取菜单服务实例。

    注入角色仓储：user-menus 接口需要按用户角色过滤菜单（防全量泄露）。
    """
    return MenuService(menu_repo=repos.menu, cache_service=cache_service, role_repo=repos.role)
