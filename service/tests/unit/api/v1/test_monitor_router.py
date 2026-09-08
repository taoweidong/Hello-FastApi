"""系统监控路由模块单元测试。"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.entities.user import UserEntity
from src.domain.enums import UserRole
from src.infrastructure.http.exception_handler_registry import register_exception_handlers


class _FakeCache:
    """缓存服务替身：预置在线会话列表并记录删除/拉黑调用。"""

    def __init__(self, sessions: list[dict] | None = None):
        self._sessions = list(sessions or [])
        self.deleted: list[str] = []
        self.blacklisted: list[str] = []

    async def get_online_users(self) -> list[dict]:
        return [dict(item) for item in self._sessions]

    async def get_online_user(self, session_key: str) -> dict | None:
        for item in self._sessions:
            if item.get("id") == session_key:
                return dict(item)
        return None

    async def delete_online_user(self, session_key: str) -> bool:
        self.deleted.append(session_key)
        return True

    async def blacklist_token_hash(self, token_hash: str, expires_at) -> bool:
        self.blacklisted.append(token_hash)
        return True


def _make_session(session_id: str, username: str, login_time: str) -> dict:
    """构造一条在线会话记录（含 id=session_key）。"""
    return {
        "id": session_id,
        "userId": f"u-{session_id}",
        "username": username,
        "ip": "127.0.0.1",
        "system": "Windows",
        "browser": "Chrome",
        "loginTime": login_time,
        "expiresAt": "2099-01-01T00:00:00+00:00",
    }


@pytest.mark.unit
class TestMonitorRouter:
    """系统监控路由测试类。"""

    @pytest.fixture
    def app(self):
        _app = FastAPI()
        register_exception_handlers(_app)
        from src.api.v1.monitor_router import MonitorRouter

        _app.include_router(MonitorRouter().router, prefix="/api/system")
        return _app

    @pytest.fixture
    def mock_user(self):
        return {"id": "1", "username": "admin", "is_superuser": True, "is_active": 1}

    @pytest.fixture
    def mock_user_entity(self):
        return UserEntity(id="1", username="admin", password="", is_superuser=UserRole.SUPERUSER)

    @pytest.fixture
    def client(self, app, mock_user_entity):
        from src.api.dependencies import get_current_active_user
        from src.api.dependencies.monitor_service import get_monitor_service, get_redis_or_none
        from src.application.services.monitor_service import MonitorService

        app.dependency_overrides[get_current_active_user] = lambda: mock_user_entity
        # 禁用 Redis 依赖，缓存监控走降级分支，避免单测依赖真实 Redis
        app.dependency_overrides[get_redis_or_none] = lambda: None
        # 在线用户接口注入内存替身缓存
        fake_cache = _FakeCache(
            sessions=[
                _make_session("hash1", "admin", "2026-03-29T10:00:00"),
                _make_session("hash2", "common", "2026-03-29T09:30:00"),
            ]
        )
        self._fake_cache = fake_cache
        app.dependency_overrides[get_monitor_service] = lambda: MonitorService(cache_service=fake_cache)
        return TestClient(app, raise_server_exceptions=False)

    auth = {"Authorization": "Bearer test_token"}

    def test_get_online_logs(self, client):
        resp = client.post("/api/system/online-logs", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]["list"]) == 2
        assert data["data"]["total"] == 2
        first = data["data"]["list"][0]
        for key in ("id", "username", "ip", "system", "browser", "loginTime"):
            assert key in first

    def test_get_online_logs_filter(self, client):
        resp = client.post("/api/system/online-logs", json={"username": "admin"}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["list"]) == 1
        assert data["data"]["list"][0]["username"] == "admin"

    def test_force_offline(self, client):
        resp = client.post("/api/system/online-logs/force-offline", json={"id": "hash1"}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "强制下线成功"
        assert self._fake_cache.deleted == ["hash1"]
        assert self._fake_cache.blacklisted == ["hash1"]

    def test_force_offline_without_cache_degraded(self, app, mock_user_entity):
        """缓存服务未注入时强制下线返回 500 失败提示。"""
        from src.api.dependencies import get_current_active_user
        from src.api.dependencies.monitor_service import get_monitor_service
        from src.application.services.monitor_service import MonitorService

        app.dependency_overrides[get_current_active_user] = lambda: mock_user_entity
        app.dependency_overrides[get_monitor_service] = lambda: MonitorService()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/system/online-logs/force-offline", json={"id": "hash1"}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["code"] == 500
        assert "缓存服务不可用" in resp.json()["message"]

    def test_get_map_info(self, client):
        resp = client.get("/api/system/get-map-info", headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]) == 50

    def test_get_card_list(self, client):
        resp = client.post("/api/system/get-card-list", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]["list"]) == 48

    def test_get_server_info(self, client):
        resp = client.get("/api/system/server-info", headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        payload = data["data"]
        for key in ("cpu", "memory", "disk", "system", "process"):
            assert key in payload
        assert payload["cpu"]["coreCount"] >= 1

    def test_get_cache_info_degraded(self, client):
        """Redis 依赖被覆写为 None 时返回降级结构。"""
        resp = client.get("/api/system/cache-info", headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["connected"] is False
        assert data["data"]["message"]
