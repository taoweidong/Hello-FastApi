"""IP 规则应用服务工厂测试。"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.mark.unit
class TestGetIpRuleService:
    """get_ip_rule_service 函数测试。"""

    @patch("src.api.dependencies.ip_rule_service.IPRuleRepository")
    @patch("src.api.dependencies.ip_rule_service.IPFilterPortAdapter")
    async def test_returns_ip_rule_service(self, mock_filter_adapter, mock_ip_repo):
        """应返回配置好的 IPRuleService 实例。"""
        mock_repo_instance = MagicMock()
        mock_ip_repo.return_value = mock_repo_instance
        mock_filter_instance = MagicMock()
        mock_filter_adapter.return_value = mock_filter_instance

        from src.api.dependencies.ip_rule_service import get_ip_rule_service

        mock_db = MagicMock()
        service = await get_ip_rule_service(
            db=mock_db,
            ip_filter_port=mock_filter_instance,
            logging_port=MagicMock(),
        )
        from src.application.services.ip_rule_service import IPRuleService
        assert isinstance(service, IPRuleService)
        assert service.ip_rule_repo == mock_repo_instance
        mock_ip_repo.assert_called_once_with(mock_db)

    @patch("src.api.dependencies.ip_rule_service.IPRuleRepository")
    async def test_passes_ports_correctly(self, mock_ip_repo):
        """应正确传递 IP 过滤端口和日志端口。"""
        mock_ip_repo.return_value = MagicMock()
        mock_filter_port = MagicMock()
        mock_logging_port = MagicMock()

        from src.api.dependencies.ip_rule_service import get_ip_rule_service

        service = await get_ip_rule_service(
            db=MagicMock(),
            ip_filter_port=mock_filter_port,
            logging_port=mock_logging_port,
        )
        assert service.ip_filter_port == mock_filter_port
        assert service.logging_port == mock_logging_port
