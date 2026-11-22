"""限流模块测试。

覆盖：真实 IP 解析、存储 URI 解析（同步/异步 scheme）、
429 响应形状、RateLimitMiddleware 全局限流行为（异步存储）。
"""

import sys
from unittest.mock import MagicMock

import anyio
import pytest
from limits import parse
from starlette.responses import JSONResponse
from starlette.testclient import TestClient

from src.config.settings import settings
from src.infrastructure.http.limiter import (
    RateLimitMiddleware,
    build_rate_limit_response,
    get_async_storage_uri,
    get_real_ip,
)

_limiter_mod = sys.modules["src.infrastructure.http.limiter"]


class TestGetRealIP:
    """get_real_ip 测试。"""

    def test_get_real_ip_without_proxy(self):
        """测试无代理时获取真实 IP。"""
        request = MagicMock()
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        assert get_real_ip(request) == "127.0.0.1"

    def test_get_real_ip_distrusts_xff_by_default(self, monkeypatch):
        """直连部署（TRUSTED_PROXIES 为空）下必须无视 X-Forwarded-For——否则伪造 XFF 即可绕过限流。"""
        monkeypatch.setattr(_limiter_mod.settings, "TRUSTED_PROXIES", "")
        request = MagicMock()
        request.headers = {"x-forwarded-for": "203.0.113.50, 70.41.3.18"}
        request.client = MagicMock()
        request.client.host = "198.51.100.7"
        assert get_real_ip(request) == "198.51.100.7"

    def test_get_real_ip_trusts_xff_from_trusted_proxy(self, monkeypatch):
        """直连对端位于可信代理列表时采信 X-Forwarded-For 首段。"""
        monkeypatch.setattr(_limiter_mod.settings, "TRUSTED_PROXIES", "127.0.0.1,::1")
        request = MagicMock()
        request.headers = {"x-forwarded-for": "203.0.113.50, 70.41.3.18"}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        assert get_real_ip(request) == "203.0.113.50"

    def test_get_real_ip_trusted_proxy_cidr(self, monkeypatch):
        """可信代理支持 CIDR 网段。"""
        monkeypatch.setattr(_limiter_mod.settings, "TRUSTED_PROXIES", "10.0.0.0/8")
        request = MagicMock()
        request.headers = {"x-forwarded-for": "203.0.113.50"}
        request.client = MagicMock()
        request.client.host = "10.1.2.3"
        assert get_real_ip(request) == "203.0.113.50"

    def test_get_real_ip_invalid_trusted_entry_ignored(self, monkeypatch):
        """无效的 TRUSTED_PROXIES 条目被忽略（不抛异常，回退直连地址）。"""
        monkeypatch.setattr(_limiter_mod.settings, "TRUSTED_PROXIES", "not-an-ip,127.0.0.1")
        request = MagicMock()
        request.headers = {"x-forwarded-for": "203.0.113.50"}
        request.client = MagicMock()
        request.client.host = "10.1.2.3"
        assert get_real_ip(request) == "10.1.2.3"

    def test_get_real_ip_no_client_info(self):
        """request.client 缺失时回退到固定 key（不抛异常）。"""
        request = MagicMock()
        request.headers = {}
        request.client = None
        assert get_real_ip(request) == "127.0.0.1"


class TestStorageURI:
    """存储 URI 解析测试。"""

    def test_storage_uri_returns_memory_when_configured(self):
        """测试配置为 memory 时返回 memory://。"""

        class MockSettings:
            RATE_LIMIT_STORAGE = "memory"
            REDIS_URL = "redis://localhost:6379/0"

        original = _limiter_mod.settings
        _limiter_mod.settings = MockSettings()
        try:
            assert _limiter_mod._get_storage_uri() == "memory://"
        finally:
            _limiter_mod.settings = original

    def test_storage_uri_returns_redis_when_available(self):
        """测试 Redis 可用时返回 redis URL。"""

        class MockSettings:
            RATE_LIMIT_STORAGE = "redis"
            REDIS_URL = "redis://localhost:6379/0"

        original = _limiter_mod.settings
        _limiter_mod.settings = MockSettings()
        try:
            assert _limiter_mod._get_storage_uri() == "redis://localhost:6379/0"
        finally:
            _limiter_mod.settings = original

    def test_storage_uri_fallback_to_memory(self):
        """测试 Redis 不可用时降级为 memory。"""

        class MockSettings:
            RATE_LIMIT_STORAGE = "redis"
            REDIS_URL = ""

        original = _limiter_mod.settings
        _limiter_mod.settings = MockSettings()
        try:
            assert _limiter_mod._get_storage_uri() == "memory://"
        finally:
            _limiter_mod.settings = original

    def test_async_storage_uri_prefixes_async_scheme(self):
        """同步 scheme 转换为 limits.aio 的异步 scheme。"""
        assert get_async_storage_uri("memory://") == "async+memory://"
        assert get_async_storage_uri("redis://localhost:6379/0") == "async+redis://localhost:6379/0"
        assert get_async_storage_uri("rediss://localhost:6379/0") == "async+rediss://localhost:6379/0"

    def test_async_storage_uri_unix_socket(self):
        """unix socket 的异步 scheme 映射为 async+redis+unix。"""
        assert get_async_storage_uri("unix:///tmp/redis.sock") == "async+redis+unix:///tmp/redis.sock"

    def test_async_storage_uri_defaults_from_settings(self):
        """不传参时按 _get_storage_uri 的配置解析结果转换。"""

        class MockSettings:
            RATE_LIMIT_STORAGE = "memory"
            REDIS_URL = "redis://localhost:6379/0"

        original = _limiter_mod.settings
        _limiter_mod.settings = MockSettings()
        try:
            assert get_async_storage_uri() == "async+memory://"
        finally:
            _limiter_mod.settings = original


class TestBuildRateLimitResponse:
    """429 限流响应测试。"""

    def test_response_shape_matches_legacy_handler(self):
        """响应形状与原 rate_limit_exceeded_handler 保持一致。"""
        response = build_rate_limit_response(30)
        assert response.status_code == 429
        body = response.body.decode()
        assert '"code":429' in body.replace(" ", "")
        assert "请求过于频繁" in body
        assert "retry_after" in body
        assert response.headers["Retry-After"] == "30"

    def test_retry_after_header_is_integer_string(self):
        """Retry-After 头为整数字符串。"""
        response = build_rate_limit_response(7)
        assert int(response.headers["Retry-After"]) == 7


async def _inner_app(scope, receive, send):
    """透传型内层应用：固定返回 {"ok": True}。"""
    await JSONResponse({"ok": True})(scope, receive, send)


def _build_client(times: int = 2) -> TestClient:
    """构建挂载全局限流中间件的测试应用（memory 存储，限定 times 次）。"""
    middleware = RateLimitMiddleware(_inner_app, storage_uri="memory://")
    # 覆盖默认限额（settings.RATE_LIMIT_TIMES=1000，测试用小限额加速）
    middleware._item = parse(f"{times} per 60 seconds")
    return TestClient(middleware)


@pytest.mark.unit
class TestRateLimitMiddleware:
    """RateLimitMiddleware 行为测试。"""

    def test_under_limit_passes(self):
        """限额内请求正常放行。"""
        client = _build_client(times=3)
        for _ in range(3):
            resp = client.get("/api/system/user")
            assert resp.status_code == 200
            assert resp.json() == {"ok": True}

    def test_over_limit_returns_429(self):
        """超过限额后返回 429 与 Retry-After。"""
        client = _build_client(times=2)
        assert client.get("/api/system/user").status_code == 200
        assert client.get("/api/system/user").status_code == 200
        resp = client.get("/api/system/user")
        assert resp.status_code == 429
        body = resp.json()
        assert body["code"] == 429
        assert "请求过于频繁" in body["msg"]
        assert "Retry-After" in resp.headers
        assert int(resp.headers["Retry-After"]) >= 1

    def test_per_path_isolation(self):
        """不同路径各自独立计数（与原 SlowAPI key_style="url" 语义一致）。"""
        client = _build_client(times=1)
        assert client.get("/api/system/user").status_code == 200
        # 同一路径第二次被限流
        assert client.get("/api/system/user").status_code == 429
        # 其他路径不受影响
        assert client.get("/api/system/role").status_code == 200

    def test_storage_error_fail_open(self, monkeypatch):
        """存储异常时 fail-open 放行（与登录限流语义一致）。"""
        client = _build_client(times=1)

        async def _raise(*args, **kwargs):
            raise RuntimeError("storage down")

        monkeypatch.setattr(client.app._strategy, "hit", _raise)
        resp = client.get("/api/system/user")
        assert resp.status_code == 200

    def test_non_http_scope_passes_through(self):
        """非 http 作用域（websocket 等）直接透传，不限流。"""
        called = []

        async def recorder(scope, receive, send):
            called.append(scope["type"])

        middleware = RateLimitMiddleware(recorder, storage_uri="memory://")
        anyio.run(middleware.__call__, {"type": "websocket", "path": "/api/system/ws"}, None, None)
        assert called == ["websocket"]

    def test_default_limit_from_settings(self):
        """默认限额取自 settings.RATE_LIMIT_TIMES / RATE_LIMIT_SECONDS。"""
        middleware = RateLimitMiddleware(_inner_app, storage_uri="memory://")
        assert middleware._item.amount == settings.RATE_LIMIT_TIMES
