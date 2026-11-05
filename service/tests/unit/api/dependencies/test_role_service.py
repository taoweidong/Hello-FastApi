"""角色应用服务工厂测试。"""

from unittest.mock import MagicMock

import pytest


@pytest.mark.unit
class TestGetRoleService:
    """get_role_service 函数测试。"""

    async def test_returns_role_service(self):
        """应返回配置好的 RoleService，角色仓储取自请求级仓储束。"""
        from src.api.dependencies.repositories import RepoBundle
        from src.api.dependencies.role_service import get_role_service
        from src.application.services.role_service import RoleService

        repos = RepoBundle(MagicMock())
        mock_cache = MagicMock()
        service = await get_role_service(repos=repos, cache_service=mock_cache)

        assert isinstance(service, RoleService)
        assert service.role_repo is repos.role
        assert service.cache_service is mock_cache
