"""系统监控路由模块单元测试。"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.entities.user import UserEntity
from src.domain.enums import UserRole
from src.infrastructure.http.exception_handler_registry import register_exception_handlers


@pytest.mark.unit
class TestMonitorRouter:
    """系统监控路由测试类（stub 接口）。"""

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
        from src.api.dependencies.monitor_service import get_redis_or_none

        app.dependency_overrides[get_current_active_user] = lambda: mock_user_entity
        # 禁用 Redis 依赖，缓存监控走降级分支，避免单测依赖真实 Redis
        app.dependency_overrides[get_redis_or_none] = lambda: None
        return TestClient(app, raise_server_exceptions=False)

    auth = {"Authorization": "Bearer test_token"}

    def test_get_online_logs(self, client):
        resp = client.post("/api/system/online-logs", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]["list"]) == 2
        assert data["data"]["total"] == 2

    def test_get_online_logs_filter(self, client):
        resp = client.post("/api/system/online-logs", json={"username": "admin"}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["list"]) == 1
        assert data["data"]["list"][0]["username"] == "admin"

    def test_force_offline(self, client):
        resp = client.post("/api/system/online-logs/force-offline", json={}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "强制下线成功"

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
