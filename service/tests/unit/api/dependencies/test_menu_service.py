"""菜单应用服务和仓储工厂测试。"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestGetMenuService:
    """get_menu_service 函数测试。"""

    @patch("src.api.dependencies.menu_service.MenuRepository")
    async def test_returns_menu_service(self, mock_menu_repo):
        """应返回配置好的 MenuService 实例，包含缓存服务。"""
        mock_repo_instance = MagicMock()
        mock_menu_repo.return_value = mock_repo_instance

        from src.api.dependencies.menu_service import get_menu_service

        mock_db = MagicMock()
        mock_cache = MagicMock()
        service = await get_menu_service(db=mock_db, cache_service=mock_cache)
        from src.application.services.menu_service import MenuService
        assert isinstance(service, MenuService)
        assert service.menu_repo == mock_repo_instance
        assert service.cache_service == mock_cache
        mock_menu_repo.assert_called_once_with(mock_db)


@pytest.mark.unit
class TestGetMenuRepository:
    """get_menu_repository 函数测试。"""

    @patch("src.api.dependencies.menu_service.MenuRepository")
    async def test_returns_menu_repository(self, mock_menu_repo):
        """应返回 MenuRepository 实例。"""
        mock_repo_instance = MagicMock()
        mock_menu_repo.return_value = mock_repo_instance

        from src.api.dependencies.menu_service import get_menu_repository

        mock_db = MagicMock()
        repo = get_menu_repository(db=mock_db)
        assert repo == mock_repo_instance
        mock_menu_repo.assert_called_once_with(mock_db)
