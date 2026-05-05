"""系统配置应用服务工厂测试。"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestGetSystemConfigService:
    """get_system_config_service 函数测试。"""

    @patch("src.api.dependencies.system_config_service.SystemConfigRepository")
    async def test_returns_system_config_service(self, mock_config_repo):
        """应返回配置好的 SystemConfigService 实例。"""
        mock_repo_instance = MagicMock()
        mock_config_repo.return_value = mock_repo_instance

        from src.api.dependencies.system_config_service import get_system_config_service

        mock_db = MagicMock()
        service = await get_system_config_service(db=mock_db)
        from src.application.services.system_config_service import SystemConfigService
        assert isinstance(service, SystemConfigService)
        assert service.config_repo == mock_repo_instance
        mock_config_repo.assert_called_once_with(mock_db)
