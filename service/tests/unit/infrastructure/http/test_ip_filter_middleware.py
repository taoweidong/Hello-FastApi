"""IPFilterMiddleware 单元测试。"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.http.ip_filter_middleware import IPFilterMiddleware


@pytest.mark.unit
class TestIPFilterMiddleware:
    """IPFilterMiddleware 测试类。"""

    @pytest.fixture
    def middleware(self):
        return IPFilterMiddleware(MagicMock())

    def _make_request(self, client_ip: str = "192.168.1.1"):
        """构造模拟 Request。"""
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "headers": [],
            "client": (client_ip, 12345),
            "app": MagicMock(),
        }
        request = MagicMock()
        request.client.host = client_ip
        request.app = scope["app"]
        request.app.state.ip_blacklist = set()
        request.app.state.ip_whitelist = set()
        return request

    @pytest.mark.asyncio
    async def test_unknown_client_passes(self, middleware):
        """测试 client 为 None 时放行。"""
        request = MagicMock()
        request.client = None
        request.app.state.ip_blacklist = set()
        request.app.state.ip_whitelist = set()
        call_next = AsyncMock(return_value=MagicMock())

        response = await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)
        assert response is call_next.return_value

    @pytest.mark.asyncio
    async def test_ip_not_in_whitelist_blocked(self, middleware):
        """测试 IP 不在白名单中被拒绝。"""
        request = self._make_request("192.168.1.1")
        request.app.state.ip_blacklist = set()
        request.app.state.ip_whitelist = {"10.0.0.1"}
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 403
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_ip_in_whitelist_passes(self, middleware):
        """测试 IP 在白名单中放行。"""
        request = self._make_request("10.0.0.1")
        request.app.state.ip_blacklist = set()
        request.app.state.ip_whitelist = {"10.0.0.1"}
        call_next = AsyncMock(return_value=MagicMock())

        response = await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)
        assert response is call_next.return_value

    @pytest.mark.asyncio
    async def test_ip_in_blacklist_blocked(self, middleware):
        """测试 IP 在黑名单中被拒绝。"""
        request = self._make_request("192.168.1.1")
        request.app.state.ip_blacklist = {"192.168.1.1"}
        request.app.state.ip_whitelist = set()
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 403
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_ip_not_in_any_list_passes(self, middleware):
        """测试 IP 不在任何名单中时放行。"""
        request = self._make_request("192.168.1.1")
        request.app.state.ip_blacklist = set()
        request.app.state.ip_whitelist = set()
        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_whitelist_does_not_protect_from_blacklist(self, middleware):
        """测试白名单和黑名单同时包含该 IP 时仍被拒绝（黑名单优先）。"""
        request = self._make_request("10.0.0.1")
        request.app.state.ip_blacklist = {"10.0.0.1"}
        request.app.state.ip_whitelist = {"10.0.0.1"}
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 403
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_whitelist_does_not_block(self, middleware):
        """测试白名单为空时不拦截任何 IP。"""
        request = self._make_request("192.168.1.1")
        request.app.state.ip_blacklist = set()
        request.app.state.ip_whitelist = set()
        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_blacklist_and_empty_whitelist(self, middleware):
        """测试黑名单有值且白名单为空时正确拦截。"""
        request = self._make_request("10.0.0.5")
        request.app.state.ip_blacklist = {"10.0.0.5"}
        request.app.state.ip_whitelist = set()
        call_next = AsyncMock()

        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 403
        call_next.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_ip_lists_configured(self, middleware):
        """测试未配置任何名单时放行。"""
        request = self._make_request("10.0.0.1")
        request.app.state = MagicMock(spec=[])
        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_whitelist_empty_blacklist_non_matching(self, middleware):
        """测试白名单空且黑名单不匹配时放行。"""
        request = self._make_request("10.0.0.1")
        request.app.state.ip_whitelist = set()
        request.app.state.ip_blacklist = {"192.168.1.1"}
        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_whitelist_non_empty_but_ip_matches(self, middleware):
        """测试白名单有值且 IP 在白名单中时放行。"""
        request = self._make_request("10.0.0.1")
        request.app.state.ip_whitelist = {"10.0.0.1", "192.168.1.1"}
        request.app.state.ip_blacklist = set()
        call_next = AsyncMock(return_value=MagicMock())

        await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)
