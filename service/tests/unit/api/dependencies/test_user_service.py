"""用户应用服务和仓储工厂测试。"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestGetUserService:
    """get_user_service 函数测试。"""

    @patch("src.api.dependencies.user_service.UserRepository")
    @patch("src.api.dependencies.user_service.RoleRepository")
    async def test_returns_user_service(self, mock_role_repo, mock_user_repo):
        """应返回配置好的 UserService 实例。"""
        mock_user_instance = MagicMock()
        mock_role_instance = MagicMock()
        mock_user_repo.return_value = mock_user_instance
        mock_role_repo.return_value = mock_role_instance

        from src.api.dependencies.user_service import get_user_service

        mock_db = MagicMock()
        mock_pwd = MagicMock()
        mock_cache = MagicMock()
        service = await get_user_service(
            db=mock_db,
            password_service=mock_pwd,
            cache_service=mock_cache,
        )
        from src.application.services.user_service import UserService
        assert isinstance(service, UserService)
        assert service.repo == mock_user_instance
        assert service.role_repo == mock_role_instance
        assert service.password_service == mock_pwd
        assert service.cache_service == mock_cache
        mock_user_repo.assert_called_once_with(mock_db)
        mock_role_repo.assert_called_once_with(mock_db)


@pytest.mark.unit
class TestGetUserRepository:
    """get_user_repository 函数测试。"""

    @patch("src.api.dependencies.user_service.UserRepository")
    async def test_returns_user_repository(self, mock_user_repo):
        """应返回 UserRepository 实例。"""
        mock_repo_instance = MagicMock()
        mock_user_repo.return_value = mock_repo_instance

        from src.api.dependencies.user_service import get_user_repository

        mock_db = MagicMock()
        repo = await get_user_repository(db=mock_db)
        assert repo == mock_repo_instance
        mock_user_repo.assert_called_once_with(mock_db)
