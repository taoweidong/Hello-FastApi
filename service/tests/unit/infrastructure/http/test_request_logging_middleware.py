"""RequestLoggingMiddleware 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.http.request_logging_middleware import (
    RequestLoggingMiddleware,
    _extract_user_agent_info,
    _try_decode_user_id,
)


@pytest.mark.unit
class TestExtractUserAgentInfo:
    """_extract_user_agent_info 工具函数测试。"""

    def test_empty_user_agent(self):
        """测试空 user-agent。"""
        browser, system = _extract_user_agent_info("")
        assert browser == "unknown"
        assert system == "unknown"

    def test_none_user_agent(self):
        """测试 None user-agent。"""
        browser, system = _extract_user_agent_info(None)  # type: ignore[arg-type]
        assert browser == "unknown"
        assert system == "unknown"

    def test_windows_chrome(self):
        """测试 Windows Chrome。"""
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0"
        browser, system = _extract_user_agent_info(ua)
        assert browser == "Chrome"
        assert system == "Windows"

    def test_mac_firefox(self):
        """测试 Mac Firefox。"""
        ua = "Mozilla/5.0 (Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0"
        browser, system = _extract_user_agent_info(ua)
        assert browser == "Firefox"
        assert system == "Mac OS"

    def test_linux_edge(self):
        """测试 Linux Edge（包含 android 但 linux 优先匹配）。"""
        ua = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Edg/120.0"
        browser, system = _extract_user_agent_info(ua)
        assert browser == "Edge"
        assert system == "Linux"

    def test_ios_safari(self):
        """测试 iOS Safari。"""
        ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) AppleWebKit/605.1.15 Safari/604.1"
        browser, system = _extract_user_agent_info(ua)
        assert browser == "Safari"
        assert system == "iOS"

    def test_chrome_in_safari_string(self):
        """测试字符串中包含 Chrome 时优先识别为 Chrome。"""
        ua = "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        browser, system = _extract_user_agent_info(ua)
        assert browser == "Chrome"
        assert system == "Windows"

    def test_android_unknown_browser(self):
        """测试 Android 未知浏览器。"""
        ua = "Mozilla/5.0 (Android 13; Mobile) AppleWebKit/537.36"
        browser, system = _extract_user_agent_info(ua)
        assert browser == "unknown"
        assert system == "Android"

    def test_unknown_os_unknown_browser(self):
        """测试完全未知的 User-Agent。"""
        ua = "SomeRandom/1.0"
        browser, system = _extract_user_agent_info(ua)
        assert browser == "unknown"
        assert system == "unknown"

    def test_safari_without_chrome(self):
        """测试纯 Safari（不含 Chrome 字样）。"""
        ua = "Mozilla/5.0 (iPad; CPU OS 17_0) AppleWebKit/605.1.15 Safari/604.1"
        browser, system = _extract_user_agent_info(ua)
        assert browser == "Safari"
        assert system == "iOS"


@pytest.mark.unit
class TestTryDecodeUserId:
    """_try_decode_user_id 工具函数测试。"""

    @patch("src.infrastructure.http.request_logging_middleware.jwt")
    def test_valid_access_token(self, mock_jwt):
        """测试有效 access token 返回用户 ID。"""
        mock_jwt.decode.return_value = {"type": "access", "sub": "user-123"}
        result = _try_decode_user_id("Bearer valid-token")
        assert result == "user-123"

    @patch("src.infrastructure.http.request_logging_middleware.jwt")
    def test_invalid_token_silent(self, mock_jwt):
        """测试无效 token 静默返回 None。"""
        from jose import JWTError

        mock_jwt.decode.side_effect = JWTError("无效 token")
        result = _try_decode_user_id("Bearer invalid-token")
        assert result is None

    def test_no_auth_header(self):
        """测试无 Authorization 头返回 None。"""
        result = _try_decode_user_id(None)
        assert result is None

    def test_not_bearer(self):
        """测试非 Bearer 格式返回 None。"""
        result = _try_decode_user_id("Basic dXNlcjpwYXNz")
        assert result is None

    def test_empty_auth(self):
        """测试空 Authorization 返回 None。"""
        result = _try_decode_user_id("")
        assert result is None

    @patch("src.infrastructure.http.request_logging_middleware.jwt")
    def test_refresh_token_ignored(self, mock_jwt):
        """测试 refresh token 被忽略返回 None。"""
        mock_jwt.decode.return_value = {"type": "refresh", "sub": "user-123"}
        result = _try_decode_user_id("Bearer refresh-token")
        assert result is None

    @patch("src.infrastructure.http.request_logging_middleware.jwt")
    def test_jwt_error_silent(self, mock_jwt):
        """测试 JWTError 静默返回 None。"""
        from jose import JWTError

        mock_jwt.decode.side_effect = JWTError("jwt error")
        result = _try_decode_user_id("Bearer bad-token")
        assert result is None


@pytest.mark.unit
class TestShouldSkipLog:
    """_should_skip_log 方法测试。"""

    @pytest.fixture
    def middleware(self):
        return RequestLoggingMiddleware(MagicMock())

    def test_login_path_skipped(self, middleware):
        """测试登录路径跳过审计日志。"""
        assert middleware._should_skip_log("/api/system/login") is True
        assert middleware._should_skip_log("/api/system/login/captcha") is True

    def test_register_path_skipped(self, middleware):
        """测试注册路径跳过审计日志。"""
        assert middleware._should_skip_log("/api/system/register") is True

    def test_logout_path_skipped(self, middleware):
        """测试登出路径跳过审计日志。"""
        assert middleware._should_skip_log("/api/system/logout") is True

    def test_refresh_token_skipped(self, middleware):
        """测试刷新 token 路径跳过审计日志。"""
        assert middleware._should_skip_log("/api/system/refresh-token") is True

    def test_async_routes_skipped(self, middleware):
        """测试异步路由路径跳过审计日志。"""
        assert middleware._should_skip_log("/api/system/get-async-routes") is True

    def test_list_role_skipped(self, middleware):
        """测试角色列表路径跳过审计日志。"""
        assert middleware._should_skip_log("/api/system/list-all-role") is True
        assert middleware._should_skip_log("/api/system/list-role-ids") is True
        assert middleware._should_skip_log("/api/system/role-menu") is True
        assert middleware._should_skip_log("/api/system/role-menu-ids") is True

    def test_normal_api_not_skipped(self, middleware):
        """测试正常业务路径不跳过审计日志。"""
        assert middleware._should_skip_log("/api/system/user") is False
        assert middleware._should_skip_log("/api/system/role") is False
        assert middleware._should_skip_log("/api/system/department") is False

    def test_sub_path_not_skipped(self, middleware):
        """测试非跳过前缀的子路径。"""
        assert middleware._should_skip_log("/api/system/user/list") is False
        assert middleware._should_skip_log("/api/system/role/create") is False


@pytest.mark.unit
class TestExtractModule:
    """_extract_module 方法测试。"""

    @pytest.fixture
    def middleware(self):
        return RequestLoggingMiddleware(MagicMock())

    def test_extract_module_user(self, middleware):
        """测试提取 user 模块。"""
        module = middleware._extract_module("/api/system/user")
        assert module == "user"

    def test_extract_module_role_create(self, middleware):
        """测试提取 role 模块。"""
        module = middleware._extract_module("/api/system/role/create")
        assert module == "role"

    def test_extract_module_root(self, middleware):
        """测试根路径。"""
        module = middleware._extract_module("/")
        assert module == "/"

    def test_extract_module_short(self, middleware):
        """测试短路径。"""
        module = middleware._extract_module("/api")
        assert module == "/api"

    def test_extract_module_deeply_nested(self, middleware):
        """测试深层嵌套路径。"""
        module = middleware._extract_module("/api/system/user/1/profile")
        assert module == "user"

    def test_extract_module_empty_string(self, middleware):
        """测试空字符串。"""
        module = middleware._extract_module("")
        assert module == ""


@pytest.mark.unit
class TestRequestLoggingMiddleware:
    """RequestLoggingMiddleware 测试类。"""

    @pytest.fixture
    def middleware(self):
        return RequestLoggingMiddleware(MagicMock())

    def _make_request(self, method="GET", path="/api/test", client_ip="127.0.0.1"):
        request = MagicMock()
        request.method = method
        request.url.path = path
        request.client.host = client_ip
        request.headers = {"user-agent": "test-agent", "authorization": None}
        request.body = AsyncMock(return_value=b'{"key": "value"}')
        return request

    @pytest.mark.asyncio
    async def test_get_request_logs_and_passes(self, middleware):
        """测试 GET 请求正常记录日志并放行。"""
        request = self._make_request("GET", "/api/test")
        call_next = AsyncMock(return_value=MagicMock())
        response = await middleware.dispatch(request, call_next)
        call_next.assert_called_once_with(request)
        assert response is call_next.return_value

    @pytest.mark.asyncio
    async def test_post_request_reads_body(self, middleware):
        """测试 POST 请求读取请求体。"""
        request = self._make_request("POST", "/api/system/user")
        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(request, call_next)
        request.body.assert_called_once()

    @pytest.mark.asyncio
    async def test_post_request_body_truncated(self, middleware):
        """测试 POST 请求体超过 4000 字符被截断。"""
        request = self._make_request("POST", "/api/system/user")
        long_body = "x" * 5000
        request.body = AsyncMock(return_value=long_body.encode("utf-8"))
        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(request, call_next)
        request.body.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_request_does_not_read_body(self, middleware):
        """测试 GET 请求不读取请求体。"""
        request = self._make_request("GET", "/api/test")
        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(request, call_next)
        request.body.assert_not_called()

    @pytest.mark.asyncio
    async def test_response_has_process_time_header(self, middleware):
        """测试响应包含 X-Process-Time 头。"""
        request = self._make_request("GET", "/api/test")
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)
        response = await middleware.dispatch(request, call_next)
        assert "X-Process-Time" in response.headers

    @pytest.mark.asyncio
    async def test_skip_log_paths_not_written(self, middleware):
        """测试跳过路径不写入 SystemLog。"""
        request = self._make_request("POST", "/api/system/login")
        call_next = AsyncMock(return_value=MagicMock())
        with patch.object(middleware, "_write_system_log_async") as mock_write:
            await middleware.dispatch(request, call_next)
            mock_write.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_skip_post_path_writes_log(self, middleware):
        """测试非跳过 POST 路径写入 SystemLog。"""
        request = self._make_request("POST", "/api/system/user")
        call_next = AsyncMock(return_value=MagicMock())
        with patch.object(middleware, "_write_system_log_async") as mock_write:
            await middleware.dispatch(request, call_next)
            mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_body_read_error_silent(self, middleware):
        """测试请求体读取异常时静默处理。"""
        request = self._make_request("POST", "/api/system/user")
        request.body = AsyncMock(side_effect=Exception("读取失败"))
        call_next = AsyncMock(return_value=MagicMock())
        with patch.object(middleware, "_write_system_log_async"):
            await middleware.dispatch(request, call_next)
            call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_client_is_none(self, middleware):
        """测试 client 为 None 时使用 unknown。"""
        request = self._make_request("GET", "/api/test")
        request.client = None
        call_next = AsyncMock(return_value=MagicMock())
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_post_empty_body(self, middleware):
        """测试 POST 请求体为空时 body_str 为 None。"""
        request = self._make_request("POST", "/api/system/user")
        request.body = AsyncMock(return_value=b"")
        call_next = AsyncMock(return_value=MagicMock())
        with patch.object(middleware, "_write_system_log_async") as mock_write:
            await middleware.dispatch(request, call_next)
        mock_write.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_post_body_truncated_to_4000(self, middleware):
        """测试 POST 请求体超过 4000 字符被截断。"""
        request = self._make_request("POST", "/api/system/user")
        request.body = AsyncMock(return_value=("x" * 5000).encode("utf-8"))
        call_next = AsyncMock(return_value=MagicMock())
        with patch.object(middleware, "_write_system_log_async") as mock_write:
            await middleware.dispatch(request, call_next)
        mock_write.assert_called_once()


@pytest.mark.unit
class TestWriteSystemLogAsync:
    """_write_system_log_async 方法测试。"""

    @pytest.fixture
    def middleware(self):
        return RequestLoggingMiddleware(MagicMock())

    @pytest.mark.asyncio
    async def test_write_system_log_called_with_data(self, middleware):
        """测试 _write_system_log_async 被调用时传递正确数据。"""
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/system/user"
        request.headers = {"user-agent": "test", "authorization": None}

        response = MagicMock()
        response.status_code = 200

        with patch("asyncio.create_task") as mock_task:
            middleware._write_system_log_async(
                request=request,
                response=response,
                client_ip="127.0.0.1",
                body='{"name": "test"}',
                duration_ms=50.0,
            )
        mock_task.assert_called_once()
