"""菜单应用服务工厂测试。"""

from unittest.mock import MagicMock

import pytest


@pytest.mark.unit
class TestGetMenuService:
    """get_menu_service 函数测试。"""

    async def test_returns_menu_service(self):
        """应返回配置好的 MenuService，菜单与角色仓储同取自请求级仓储束。"""
        from src.api.dependencies.menu_service import get_menu_service
        from src.api.dependencies.repositories import RepoBundle
        from src.application.services.menu_service import MenuService

        repos = RepoBundle(MagicMock())
        mock_cache = MagicMock()
        service = await get_menu_service(repos=repos, cache_service=mock_cache)

        assert isinstance(service, MenuService)
        assert service.menu_repo is repos.menu
        assert service.role_repo is repos.role
        assert service.cache_service is mock_cache
