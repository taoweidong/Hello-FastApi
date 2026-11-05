"""IP 规则应用服务工厂测试。"""

from unittest.mock import MagicMock

import pytest


@pytest.mark.unit
class TestGetIpRuleService:
    """get_ip_rule_service 函数测试。"""

    async def test_returns_ip_rule_service(self):
        """应返回配置好的 IPRuleService，规则仓储取自请求级仓储束。"""
        from src.api.dependencies.ip_rule_service import get_ip_rule_service
        from src.api.dependencies.repositories import RepoBundle
        from src.application.services.ip_rule_service import IPRuleService

        repos = RepoBundle(MagicMock())
        mock_filter_port = MagicMock()
        mock_logging_port = MagicMock()
        service = await get_ip_rule_service(
            repos=repos, ip_filter_port=mock_filter_port, logging_port=mock_logging_port
        )

        assert isinstance(service, IPRuleService)
        assert service.ip_rule_repo is repos.ip_rule
        assert service.ip_filter_port is mock_filter_port
        assert service.logging_port is mock_logging_port


@pytest.mark.unit
class TestFactoryFunctions:
    """内部工厂函数测试。"""

    def test_get_ip_filter_port(self):
        """_get_ip_filter_port 应返回 IPFilterPortAdapter 实例。"""
        from src.api.dependencies.ip_rule_service import _get_ip_filter_port
        from src.infrastructure.http.ip_filter_port_adapter import IPFilterPortAdapter

        result = _get_ip_filter_port()
        assert isinstance(result, IPFilterPortAdapter)

    def test_get_logging_port(self):
        """_get_logging_port 应返回 logging_adapter 实例。"""
        from src.api.dependencies.ip_rule_service import _get_logging_port
        from src.domain.services.logging_port import LoggingPort

        result = _get_logging_port()
        assert isinstance(result, LoggingPort)
