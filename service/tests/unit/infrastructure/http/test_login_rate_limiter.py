"""LoginRateLimitMiddleware（登录/注册专属限流）单元测试。"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.config.settings import settings
from src.infrastructure.http.login_rate_limiter import LoginRateLimitMiddleware


def _build_app(monkeypatch: pytest.MonkeyPatch, limit: str) -> TestClient:
    """挂载中间件的测试应用（memory 存储）。

    用 monkeypatch（测试结束后才恢复）而非 try/finally：
    中间件实例在首个请求时才惰性构造，构造时才读取 LOGIN_RATE_LIMIT。
    """
    from src.api.v1.auth_router import AuthRouter

    monkeypatch.setattr(settings, "LOGIN_RATE_LIMIT", limit)
    app = FastAPI()
    app.include_router(AuthRouter().router, prefix="/api/system")
    app.add_middleware(LoginRateLimitMiddleware, storage_uri="memory://")
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.unit
class TestLoginRateLimitMiddleware:
    def test_non_protected_paths_not_limited(self, monkeypatch: pytest.MonkeyPatch):
        """非 /login、/register 路径不受专属限流影响。"""
        client = _build_app(monkeypatch, "1/minute")
        # 不存在的路径返回 404，而非 429 —— 说明未被限流拦截
        resp = client.post("/api/system/not-exist", json={})
        assert resp.status_code == 404

    def test_limit_triggers_429(self, monkeypatch: pytest.MonkeyPatch):
        """超过限额后返回 429 与 Retry-After。"""
        client = _build_app(monkeypatch, "2/minute")
        # 前两次通过限流检查（业务层因无 DB 会失败，但不返回 429）
        for _ in range(2):
            resp = client.post("/api/system/login", json={"username": "admin", "password": "x"})
            assert resp.status_code != 429, resp.json()
        # 第三次被限流
        resp = client.post("/api/system/login", json={"username": "admin", "password": "x"})
        assert resp.status_code == 429
        body = resp.json()
        assert body["code"] == 429
        assert "Retry-After" in resp.headers
        assert int(resp.headers["Retry-After"]) >= 1

    def test_register_shared_limit(self, monkeypatch: pytest.MonkeyPatch):
        """login 与 register 共享同一名额池（同 IP 同窗口）。"""
        client = _build_app(monkeypatch, "1/minute")
        assert client.post("/api/system/login", json={"username": "a", "password": "x"}).status_code != 429
        resp = client.post("/api/system/register", json={"username": "abcdef", "password": "Pass1234"})
        assert resp.status_code == 429

    def test_get_requests_not_limited(self, monkeypatch: pytest.MonkeyPatch):
        """仅 POST 受限，GET 同路径不受限。"""
        client = _build_app(monkeypatch, "1/minute")
        assert client.post("/api/system/login", json={"username": "a", "password": "x"}).status_code != 429
        resp = client.get("/api/system/login")
        assert resp.status_code == 405  # 方法不允许，而非 429
