"""用户应用服务工厂测试。"""

from unittest.mock import MagicMock

import pytest


@pytest.mark.unit
class TestGetUserService:
    """get_user_service 函数测试。"""

    async def test_returns_user_service(self):
        """应返回配置好的 UserService，四个仓储全部取自同一个请求级仓储束。"""
        from src.api.dependencies.repositories import RepoBundle
        from src.api.dependencies.user_service import get_user_service
        from src.application.services.user_service import UserService

        repos = RepoBundle(MagicMock())
        mock_pwd = MagicMock()
        mock_cache = MagicMock()
        service = await get_user_service(repos=repos, password_service=mock_pwd, cache_service=mock_cache)

        assert isinstance(service, UserService)
        assert service.repo is repos.user
        assert service.role_repo is repos.role
        assert service.dept_repo is repos.department
        assert service.post_repo is repos.post
        assert service.password_service is mock_pwd
        assert service.cache_service is mock_cache
