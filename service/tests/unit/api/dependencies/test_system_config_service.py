"""系统配置应用服务工厂测试。"""

from unittest.mock import MagicMock

import pytest


@pytest.mark.unit
class TestGetSystemConfigService:
    """get_system_config_service 函数测试。"""

    async def test_returns_system_config_service(self):
        """应返回配置好的 SystemConfigService，配置仓储取自请求级仓储束。"""
        from src.api.dependencies.repositories import RepoBundle
        from src.api.dependencies.system_config_service import get_system_config_service
        from src.application.services.system_config_service import SystemConfigService

        repos = RepoBundle(MagicMock())
        service = await get_system_config_service(repos=repos)

        assert isinstance(service, SystemConfigService)
        assert service.config_repo is repos.system_config
