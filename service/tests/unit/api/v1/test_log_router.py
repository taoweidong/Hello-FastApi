"""日志管理路由模块单元测试。"""

from datetime import datetime

import pytest
from unittest.mock import AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.infrastructure.http.exception_handler_registry import register_exception_handlers


def _make_log_entity(log_id: str, **kw):
    defaults = {
        "id": log_id, "status": 1, "ipaddress": "127.0.0.1",
        "browser": "Chrome", "system": "Windows", "agent": "",
        "login_type": 0, "creator_id": "1",
        "created_time": datetime(2026, 1, 1),
        "module": "auth", "path": "/login", "body": "{}",
        "method": "POST", "response_code": 200, "response_result": "ok",
        "status_code": 200,
    }
    defaults.update(kw)
    return type("LogEntity", (), defaults)()


@pytest.mark.unit
class TestLogRouter:
    """日志管理路由测试类。"""

    @pytest.fixture
    def app(self):
        _app = FastAPI()
        register_exception_handlers(_app)
        from src.api.v1.log_router import LogRouter
        _app.include_router(LogRouter().router, prefix="/api/system")
        return _app

    @pytest.fixture
    def mock_user(self):
        return {"id": "1", "username": "admin", "is_superuser": True, "is_active": 1}

    @pytest.fixture
    def mock_log_service(self):
        svc = AsyncMock()
        login_log = _make_log_entity("l1")
        opt_log = _make_log_entity("l2", module="dept", path="/dept", method="POST")
        sys_log = _make_log_entity("l3", module="system", path="/config", method="GET")

        svc.get_login_logs.return_value = ([login_log], 1)
        svc.delete_login_logs.return_value = 2
        svc.clear_login_logs.return_value = 5
        svc.get_operation_logs.return_value = ([opt_log], 1)
        svc.delete_operation_logs.return_value = 3
        svc.clear_operation_logs.return_value = 10
        svc.get_system_logs.return_value = ([sys_log], 1)
        svc.get_system_log_detail.return_value = sys_log
        return svc

    @pytest.fixture
    def client(self, app, mock_user, mock_log_service):
        from src.api.dependencies import get_log_service, get_current_active_user
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_log_service] = lambda: mock_log_service
        return TestClient(app, raise_server_exceptions=False)

    auth = {"Authorization": "Bearer test_token"}

    def test_get_login_logs(self, client):
        resp = client.post("/api/system/login-logs", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 1
        assert len(data["data"]["list"]) == 1

    def test_batch_delete_login_logs(self, client):
        resp = client.post("/api/system/login-logs/batch-delete", json={"ids": ["l1", "l2"]}, headers=self.auth)
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

    def test_clear_login_logs(self, client):
        resp = client.post("/api/system/login-logs/clear", headers=self.auth)
        assert resp.status_code == 200
        assert "已清空" in resp.json()["message"]

    def test_get_operation_logs(self, client):
        resp = client.post("/api/system/operation-logs", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total"] == 1
        assert data["data"]["list"][0]["module"] == "dept"

    def test_batch_delete_operation_logs(self, client):
        resp = client.post("/api/system/operation-logs/batch-delete", json={"ids": ["l2"]}, headers=self.auth)
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

    def test_clear_operation_logs(self, client):
        resp = client.post("/api/system/operation-logs/clear", headers=self.auth)
        assert resp.status_code == 200
        assert "已清空" in resp.json()["message"]

    def test_get_system_logs(self, client):
        resp = client.post("/api/system/system-logs", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["total"] == 1

    def test_get_system_log_detail_success(self, client):
        resp = client.post("/api/system/system-logs-detail", json={"id": "l3"}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["data"]["module"] == "system"

    def test_get_system_log_detail_missing_id(self, client):
        resp = client.post("/api/system/system-logs-detail", json={}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["data"] is None

    def test_get_system_log_detail_not_found(self, client, mock_log_service):
        mock_log_service.get_system_log_detail.return_value = None
        resp = client.post("/api/system/system-logs-detail", json={"id": "nonexistent"}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["data"] is None
        assert "不存在" in resp.json()["message"]
