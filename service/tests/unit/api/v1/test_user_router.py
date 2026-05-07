"""用户管理路由模块单元测试。"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.infrastructure.http.exception_handler_registry import register_exception_handlers


@pytest.mark.unit
class TestUserRouter:
    """用户管理路由测试类。"""

    @pytest.fixture
    def app(self):
        _app = FastAPI()
        register_exception_handlers(_app)
        from src.api.v1.user_router import UserRouter
        _app.include_router(UserRouter().router, prefix="/api/system/user")
        return _app

    @pytest.fixture
    def mock_user(self):
        return {"id": "1", "username": "admin", "is_superuser": True, "is_active": 1}

    @pytest.fixture
    def mock_user_service(self):
        svc = AsyncMock()
        _mock_user_obj = MagicMock()
        _mock_user_obj.model_dump.return_value = {
            "id": "1",
            "username": "admin",
            "nickname": "",
            "email": "",
            "phone": "",
            "avatar": "",
            "description": "",
            "dept_id": None,
        }
        svc.get_users.return_value = ([_mock_user_obj], 1)
        svc.create_user.return_value = {"id": "2", "username": "newuser"}
        svc.get_user.return_value = {"id": "1", "username": "admin", "email": "admin@test.com"}
        svc.update_user.return_value = {"id": "1", "username": "updated"}
        svc.delete_user.return_value = None
        svc.batch_delete_users.return_value = {"deleted": 2}
        svc.reset_password.return_value = None
        svc.update_status.return_value = None
        svc.change_password.return_value = None
        svc.assign_roles.return_value = None
        return svc

    @pytest.fixture
    def client(self, app, mock_user, mock_user_service):
        from src.api.dependencies import get_current_active_user, get_current_user_id, get_user_service
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_current_user_id] = lambda: "1"
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        return TestClient(app, raise_server_exceptions=False)

    auth = {"Authorization": "Bearer test_token"}

    def test_get_user_list(self, client):
        resp = client.post("/api/system/user", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]["list"]) == 1

    def test_create_user_success(self, client):
        resp = client.post("/api/system/user/create", json={
            "username": "newuser", "password": "Pass1234", "isActive": 1,
        }, headers=self.auth)
        assert resp.status_code == 201
        assert resp.json()["message"] == "创建成功"

    def test_create_user_validation_error(self, client):
        resp = client.post("/api/system/user/create", json={"username": "ab"}, headers=self.auth)
        assert resp.status_code == 422

    def test_get_current_user_info(self, client):
        resp = client.get("/api/system/user/info", headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["data"]["username"] == "admin"

    def test_get_user_detail(self, client):
        resp = client.get("/api/system/user/1", headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["data"]["username"] == "admin"

    def test_update_user(self, client):
        resp = client.put("/api/system/user/1", json={"nickname": "new_nick"}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "更新成功"

    def test_delete_user(self, client):
        resp = client.delete("/api/system/user/1", headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"

    def test_batch_delete_users(self, client):
        resp = client.post("/api/system/user/batch-delete", json={"ids": ["1", "2"]}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "批量删除成功"

    def test_reset_password(self, client):
        resp = client.put("/api/system/user/1/reset-password", json={"newPassword": "NewPass123"}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "密码重置成功"

    def test_update_user_status(self, client):
        resp = client.put("/api/system/user/1/status", json={"isActive": 0}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "状态更新成功"

    def test_change_password(self, client):
        resp = client.post("/api/system/user/change-password", json={
            "oldPassword": "old123", "newPassword": "NewPass123",
        }, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "密码修改成功"

    def test_assign_role(self, client):
        resp = client.post("/api/system/user/assign-role", json={
            "userId": "1", "roleIds": ["r1", "r2"],
        }, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "角色分配成功"
