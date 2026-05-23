"""限流模块测试。"""

import functools
import sys
from unittest.mock import MagicMock

import pytest
from limits import RateLimitItemPerSecond
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.wrappers import Limit
from starlette.requests import Request

from src.infrastructure.http.limiter import (
    _patched_check_limits,
    _patched_check_request_limit,
    _patched_get_route_name,
    _unwrap_partial,
    get_limiter,
    get_real_ip,
    rate_limit_exceeded_handler,
)

_limiter_mod = sys.modules["src.infrastructure.http.limiter"]


class TestLimiterConfig:
    """限流器配置测试。"""

    def test_limiter_instance_exists(self):
        """测试限流器实例已创建。"""
        limiter = get_limiter()
        assert isinstance(limiter, Limiter)

    def test_limiter_has_default_limits(self):
        """测试限流器有默认限制配置。"""
        limiter = get_limiter()
        assert limiter._default_limits is not None
        assert len(limiter._default_limits) > 0

    def test_get_real_ip_without_proxy(self):
        """测试无代理时获取真实 IP。"""
        request = MagicMock()
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        assert get_real_ip(request) == "127.0.0.1"

    def test_get_real_ip_with_x_forwarded_for(self):
        """测试有 X-Forwarded-For 头时获取真实 IP。"""
        request = MagicMock()
        request.headers = {"x-forwarded-for": "203.0.113.50, 70.41.3.18"}
        assert get_real_ip(request) == "203.0.113.50"

    def test_get_real_ip_with_single_forwarded_ip(self):
        """测试单个 X-Forwarded-For IP。"""
        request = MagicMock()
        request.headers = {"x-forwarded-for": "10.0.0.1"}
        assert get_real_ip(request) == "10.0.0.1"


class TestRateLimitStorage:
    """限流存储测试。"""

    def test_storage_uri_returns_memory_when_configured(self):
        """测试配置为 memory 时返回 memory://。"""

        class MockSettings:
            RATE_LIMIT_STORAGE = "memory"
            REDIS_URL = "redis://localhost:6379/0"

        limiter_mod = sys.modules["src.infrastructure.http.limiter"]
        original = limiter_mod.settings
        limiter_mod.settings = MockSettings()
        try:
            assert limiter_mod._get_storage_uri() == "memory://"
        finally:
            limiter_mod.settings = original

    def test_storage_uri_returns_redis_when_available(self):
        """测试 Redis 可用时返回 redis URL。"""

        class MockSettings:
            RATE_LIMIT_STORAGE = "redis"
            REDIS_URL = "redis://localhost:6379/0"

        limiter_mod = sys.modules["src.infrastructure.http.limiter"]
        original = limiter_mod.settings
        limiter_mod.settings = MockSettings()
        try:
            assert limiter_mod._get_storage_uri() == "redis://localhost:6379/0"
        finally:
            limiter_mod.settings = original

    def test_storage_uri_fallback_to_memory(self):
        """测试 Redis 不可用时降级为 memory。"""

        class MockSettings:
            RATE_LIMIT_STORAGE = "redis"
            REDIS_URL = ""

        limiter_mod = sys.modules["src.infrastructure.http.limiter"]
        original = limiter_mod.settings
        limiter_mod.settings = MockSettings()
        try:
            assert limiter_mod._get_storage_uri() == "memory://"
        finally:
            limiter_mod.settings = original


class TestRateLimitExceededHandler:
    """限流异常处理器测试。"""

    @pytest.mark.asyncio
    async def test_handler_returns_429_with_retry_after(self):
        """测试限流异常返回 429 和重试时间。"""
        request = MagicMock(spec=Request)
        mock_exc = MagicMock()
        mock_exc.__str__ = MagicMock(return_value="limit exceeded: 60")
        response = await rate_limit_exceeded_handler(request, mock_exc)
        assert response.status_code == 429
        body = response.body.decode()
        assert "请求过于频繁" in body
        assert "retry_after" in body

    @pytest.mark.asyncio
    async def test_handler_returns_default_retry_when_no_detail(self):
        """测试限流异常无详细信息时返回默认 60 秒重试。"""
        request = MagicMock(spec=Request)
        mock_exc = MagicMock()
        mock_exc.__str__ = MagicMock(return_value="no-colon-here")
        response = await rate_limit_exceeded_handler(request, mock_exc)
        assert response.status_code == 429
        body = response.body.decode()
        assert "retry_after" in body


class TestUnwrapPartial:
    """_unwrap_partial 测试。"""

    def test_unwrap_single_partial(self):
        """测试单层 partial。"""

        def some_func(a, b):
            return a + b

        p = functools.partial(some_func, 1)
        result = _unwrap_partial(p)
        assert result is some_func

    def test_unwrap_double_nested_partial(self):
        """测试双层 partial → L31-33 (while-loop, nesting >= 2)。"""

        def some_func(a, b, c):
            return a + b + c

        p1 = functools.partial(some_func, 1)
        p2 = functools.partial(p1, 2)
        result = _unwrap_partial(p2)
        assert result is some_func

    def test_unwrap_triple_nested_partial(self):
        """测试三层 partial → L31-33 (while-loop, nesting >= 3)。"""

        def some_func(a, b, c, d):
            return a + b + c + d

        p1 = functools.partial(some_func, 1)
        p2 = functools.partial(p1, 2)
        p3 = functools.partial(p2, 3)
        result = _unwrap_partial(p3)
        assert result is some_func

    def test_unwrap_non_partial(self):
        """测试非 partial 输入直接返回。"""

        def some_func():
            pass

        result = _unwrap_partial(some_func)
        assert result is some_func


class TestPatchedGetRouteName:
    """_patched_get_route_name 测试。"""

    def test_patched_get_route_name_with_partial(self):
        """测试传入 partial-wrapped handler → L45。"""

        def my_endpoint():
            return "ok"

        p = functools.partial(my_endpoint)
        result = _patched_get_route_name(p)
        assert "my_endpoint" in result

    def test_patched_get_route_name_with_regular_func(self):
        """测试传入普通函数。"""

        def regular_handler():
            pass

        result = _patched_get_route_name(regular_handler)
        assert "regular_handler" in result


class TestPatchedCheckRequestLimit:
    """_patched_check_request_limit 测试。"""

    def test_patched_check_request_limit_with_partial(self):
        """测试 partial-wrapped endpoint → L58-59。"""

        def my_endpoint():
            return "ok"

        p = functools.partial(my_endpoint)
        request = MagicMock(spec=Request)
        limiter_instance = get_limiter()

        mock_orig = MagicMock(return_value=None)
        original = _limiter_mod._original_check_request_limit
        _limiter_mod._original_check_request_limit = mock_orig
        try:
            _patched_check_request_limit(limiter_instance, request, p, True)
            call_args = mock_orig.call_args
            assert call_args[0][2] is my_endpoint
        finally:
            _limiter_mod._original_check_request_limit = original


class TestPatchedCheckLimits:
    """_patched_check_limits 测试。"""

    def test_patched_check_limits_auto_check_false(self):
        """测试 _auto_check=False → L90 (short-circuit return)。"""
        limiter_mock = MagicMock()
        limiter_mock._auto_check = False
        request = MagicMock(spec=Request)
        app = MagicMock()

        result = _patched_check_limits(limiter_mock, request, None, app)
        assert result == (None, False, None)

    def test_patched_check_limits_rate_limiting_complete(self):
        """测试 _rate_limiting_complete=True → skip limit check (L76, L90)。"""
        limiter_mock = MagicMock()
        limiter_mock._auto_check = True
        request = MagicMock(spec=Request)
        request.state._rate_limiting_complete = True
        app = MagicMock()

        result = _patched_check_limits(limiter_mock, request, None, app)
        assert result == (None, False, None)

    def test_patched_check_limits_no_exception(self):
        """测试正常路径: _check_request_limit 未抛异常 → 无异常走 L89-L90。"""
        limiter_mock = MagicMock()
        limiter_mock._auto_check = True
        limiter_mock._check_request_limit = MagicMock()
        request = MagicMock(spec=Request)
        request.state._rate_limiting_complete = False
        app = MagicMock()

        result = _patched_check_limits(limiter_mock, request, None, app)
        assert result == (None, False, None)

    def test_patched_check_limits_rate_limit_exceeded(self):
        """测试 RateLimitExceeded 异常 → L79-82。"""
        limit = Limit(
            RateLimitItemPerSecond(10, 1),
            lambda r: "127.0.0.1",
            "test",
            per_method=False,
            methods=None,
            error_message="limit exceeded: 60",
            exempt_when=None,
            cost=1,
            override_defaults=False,
        )

        handler_func = MagicMock()
        limiter_mock = MagicMock()
        limiter_mock._auto_check = True
        limiter_mock._check_request_limit = MagicMock(side_effect=RateLimitExceeded(limit))
        request = MagicMock(spec=Request)
        request.state._rate_limiting_complete = False
        app = MagicMock()
        app.exception_handlers = {RateLimitExceeded: handler_func}

        result = _patched_check_limits(limiter_mock, request, None, app)
        assert result[0] is handler_func
        assert result[1] is False
        assert isinstance(result[2], RateLimitExceeded)

    def test_patched_check_limits_generic_exception(self):
        """测试普通 Exception → L83-88 (logs and returns None, False, None)。"""
        limiter_mock = MagicMock()
        limiter_mock._auto_check = True
        limiter_mock._check_request_limit = MagicMock(side_effect=ValueError("something went wrong"))
        request = MagicMock(spec=Request)
        request.state._rate_limiting_complete = False
        app = MagicMock()

        result = _patched_check_limits(limiter_mock, request, None, app)
        assert result == (None, False, None)
