"""认证应用服务工厂测试。"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.unit
class TestGetAuthService:
    """get_auth_service 函数测试。"""

    @patch("src.api.dependencies.auth_service.UserRepository")
    @patch("src.api.dependencies.auth_service.RoleRepository")
    @patch("src.api.dependencies.auth_service.MenuRepository")
    async def test_returns_auth_service(self, mock_menu_repo, mock_role_repo, mock_user_repo):
        """应返回配置好的 AuthService 实例。"""
        mock_user_repo_instance = MagicMock()
        mock_role_repo_instance = MagicMock()
        mock_menu_repo_instance = MagicMock()
        mock_user_repo.return_value = mock_user_repo_instance
        mock_role_repo.return_value = mock_role_repo_instance
        mock_menu_repo.return_value = mock_menu_repo_instance

        from src.api.dependencies.auth_service import get_auth_service

        service = await get_auth_service(
            db=MagicMock(),
            token_service=MagicMock(),
            password_service=MagicMock(),
            cache_service=MagicMock(),
        )
        from src.application.services.auth_service import AuthService
        assert isinstance(service, AuthService)
        assert service.user_repo == mock_user_repo_instance
        assert service.role_repo == mock_role_repo_instance
        assert service.menu_repo == mock_menu_repo_instance

    @patch("src.api.dependencies.auth_service.UserRepository")
    @patch("src.api.dependencies.auth_service.RoleRepository")
    @patch("src.api.dependencies.auth_service.MenuRepository")
    async def test_passes_dependencies_correctly(self, mock_menu_repo, mock_role_repo, mock_user_repo):
        """应正确传递所有依赖。"""
        mock_db = MagicMock()
        mock_token = MagicMock()
        mock_password = MagicMock()
        mock_cache = MagicMock()

        from src.api.dependencies.auth_service import get_auth_service

        service = await get_auth_service(
            db=mock_db,
            token_service=mock_token,
            password_service=mock_password,
            cache_service=mock_cache,
        )
        assert service.token_service == mock_token
        assert service.password_service == mock_password
        assert service.cache_service == mock_cache
        mock_user_repo.assert_called_once_with(mock_db)
        mock_role_repo.assert_called_once_with(mock_db)
        mock_menu_repo.assert_called_once_with(mock_db)
