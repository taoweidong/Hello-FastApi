"""日志应用服务工厂测试。"""

from unittest.mock import MagicMock

import pytest


@pytest.mark.unit
class TestGetLogService:
    """get_log_service 函数测试。"""

    async def test_returns_log_service(self):
        """应返回配置好的 LogService，日志仓储取自请求级仓储束。"""
        from src.api.dependencies.log_service import get_log_service
        from src.api.dependencies.repositories import RepoBundle
        from src.application.services.log_service import LogService

        repos = RepoBundle(MagicMock())
        service = await get_log_service(repos=repos)

        assert isinstance(service, LogService)
        assert service.log_repo is repos.log
