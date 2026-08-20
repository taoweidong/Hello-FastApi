"""角色应用服务工厂测试。"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestGetRoleService:
    """get_role_service 函数测试。"""

    @patch("src.api.dependencies.role_service.RoleRepository")
    async def test_returns_role_service(self, mock_role_repo):
        """应返回配置好的 RoleService 实例。"""
        mock_repo_instance = MagicMock()
        mock_role_repo.return_value = mock_repo_instance

        from src.api.dependencies.role_service import get_role_service

        mock_db = MagicMock()
        service = await get_role_service(db=mock_db)
        from src.application.services.role_service import RoleService

        assert isinstance(service, RoleService)
        assert service.role_repo == mock_repo_instance
        mock_role_repo.assert_called_once_with(mock_db)
