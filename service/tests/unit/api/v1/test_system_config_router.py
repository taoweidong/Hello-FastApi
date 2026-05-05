"""系统配置路由模块单元测试。"""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.infrastructure.http.exception_handler_registry import register_exception_handlers


@pytest.mark.unit
class TestSystemConfigRouter:
    """系统配置路由测试类。"""

    @pytest.fixture
    def app(self):
        _app = FastAPI()
        register_exception_handlers(_app)
        from src.api.v1.system_config_router import SystemConfigRouter
        _app.include_router(SystemConfigRouter().router, prefix="/api/system/config")
        return _app

    @pytest.fixture
    def mock_user(self):
        return {"id": "1", "username": "admin", "is_superuser": True, "is_active": 1}

    @pytest.fixture
    def mock_config_service(self):
        svc = AsyncMock()
        configs = [
            {"id": "c1", "key": "site_name", "value": '"Hello-FastApi"', "isActive": 1, "access": 0},
            {"id": "c2", "key": "site_desc", "value": '"A FastAPI project"', "isActive": 1, "access": 0},
        ]
        svc.get_configs.return_value = (
            [type("Config", (), {"model_dump": lambda self: c})() for c in configs], 2)
        svc.create_config.return_value = {"id": "c3", "key": "new_key", "value": '"new_val"'}
        svc.get_config.return_value = {"id": "c1", "key": "site_name", "value": '"Hello-FastApi"'}
        svc.update_config.return_value = {"id": "c1", "key": "site_name", "value": '"Updated"'}
        svc.delete_config.return_value = None
        return svc

    @pytest.fixture
    def client(self, app, mock_user, mock_config_service):
        from src.api.dependencies import get_current_active_user, get_system_config_service
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_system_config_service] = lambda: mock_config_service
        return TestClient(app, raise_server_exceptions=False)

    auth = {"Authorization": "Bearer test_token"}

    def test_get_config_list(self, client):
        resp = client.post("/api/system/config", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 2
        assert len(data["data"]["list"]) == 2

    def test_create_config_success(self, client):
        resp = client.post("/api/system/config/create", json={
            "key": "new_key", "value": '"new_val"', "isActive": 1,
        }, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["code"] == 201
        assert resp.json()["message"] == "创建成功"

    def test_create_config_validation_error(self, client):
        resp = client.post("/api/system/config/create", json={}, headers=self.auth)
        assert resp.status_code == 422

    def test_get_config_detail(self, client):
        resp = client.get("/api/system/config/c1", headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["data"]["key"] == "site_name"

    def test_update_config(self, client):
        resp = client.put("/api/system/config/c1", json={"value": '"Updated"'}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "更新成功"

    def test_delete_config(self, client):
        resp = client.delete("/api/system/config/c1", headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"
