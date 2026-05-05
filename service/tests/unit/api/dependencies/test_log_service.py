"""日志应用服务工厂测试。"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestGetLogService:
    """get_log_service 函数测试。"""

    @patch("src.api.dependencies.log_service.LogRepository")
    async def test_returns_log_service(self, mock_log_repo):
        """应返回配置好的 LogService 实例。"""
        mock_repo_instance = MagicMock()
        mock_log_repo.return_value = mock_repo_instance

        from src.api.dependencies.log_service import get_log_service

        mock_db = MagicMock()
        service = await get_log_service(db=mock_db)
        from src.application.services.log_service import LogService
        assert isinstance(service, LogService)
        assert service.log_repo == mock_repo_instance
        mock_log_repo.assert_called_once_with(mock_db)
