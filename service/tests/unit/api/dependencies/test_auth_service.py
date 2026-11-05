"""认证应用服务工厂测试。"""

from unittest.mock import MagicMock

import pytest


@pytest.mark.unit
class TestGetAuthService:
    """get_auth_service 函数测试。"""

    async def test_returns_auth_service(self):
        """应返回配置好的 AuthService，仓储取自请求级仓储束。"""
        from src.api.dependencies.auth_service import get_auth_service
        from src.api.dependencies.repositories import RepoBundle
        from src.application.services.auth_service import AuthService

        repos = RepoBundle(MagicMock())
        service = await get_auth_service(
            repos=repos,
            token_service=MagicMock(),
            password_service=MagicMock(),
            token_revocation=MagicMock(),
            session_store=MagicMock(),
            menu_cache=MagicMock(),
        )

        assert isinstance(service, AuthService)
        assert service.user_repo is repos.user
        assert service.role_repo is repos.role
        assert service.menu_repo is repos.menu
        assert service.log_repo is repos.log

    async def test_passes_narrow_cache_ports(self):
        """三个缓存窄端口应各自独立注入（在线会话与读穿透缓存分属不同组件）。"""
        from src.api.dependencies.auth_service import get_auth_service
        from src.api.dependencies.repositories import RepoBundle

        mock_token_revocation = MagicMock()
        mock_session_store = MagicMock()
        mock_menu_cache = MagicMock()
        service = await get_auth_service(
            repos=RepoBundle(MagicMock()),
            token_service=MagicMock(),
            password_service=MagicMock(),
            token_revocation=mock_token_revocation,
            session_store=mock_session_store,
            menu_cache=mock_menu_cache,
        )

        assert service.token_revocation is mock_token_revocation
        assert service.session_store is mock_session_store
        assert service.menu_cache is mock_menu_cache
