"""角色管理路由模块单元测试。"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.entities.user import UserEntity
from src.domain.enums import UserRole
from src.infrastructure.http.exception_handler_registry import register_exception_handlers


@pytest.mark.unit
class TestRoleRouter:
    """角色管理路由测试类。"""

    @pytest.fixture
    def app(self):
        _app = FastAPI()
        register_exception_handlers(_app)
        from src.api.v1.role_router import RoleRouter

        _app.include_router(RoleRouter().router, prefix="/api/system/role")
        return _app

    @pytest.fixture
    def mock_user(self):
        return {"id": "1", "username": "admin", "is_superuser": True, "is_active": 1}

    @pytest.fixture
    def mock_user_entity(self):
        return UserEntity(id="1", username="admin", password="", is_superuser=UserRole.SUPERUSER)

    @pytest.fixture
    def mock_role_service(self):
        svc = AsyncMock()
        _r1 = MagicMock()
        _r1.model_dump.return_value = {"id": "r1", "name": "管理员", "code": "admin"}
        _r2 = MagicMock()
        _r2.model_dump.return_value = {"id": "r2", "name": "普通用户", "code": "user"}
        svc.get_roles.return_value = ([_r1, _r2], 2)
        _mock_create = MagicMock()
        _mock_create.model_dump.return_value = {"id": "r3", "name": "新角色", "code": "new"}
        _mock_get = MagicMock()
        _mock_get.model_dump.return_value = {"id": "r1", "name": "管理员", "code": "admin"}
        _mock_update = MagicMock()
        _mock_update.model_dump.return_value = {"id": "r1", "name": "更新角色", "code": "admin"}
        svc.create_role.return_value = _mock_create
        svc.get_role.return_value = _mock_get
        svc.update_role.return_value = _mock_update
        svc.delete_role.return_value = None
        svc.assign_menus.return_value = None
        svc.change_data_scope.return_value = None
        return svc

    @pytest.fixture
    def client(self, app, mock_user_entity, mock_role_service):
        from src.api.dependencies import get_current_active_user, get_role_service

        app.dependency_overrides[get_current_active_user] = lambda: mock_user_entity
        app.dependency_overrides[get_role_service] = lambda: mock_role_service
        return TestClient(app, raise_server_exceptions=False)

    auth = {"Authorization": "Bearer test_token"}

    def test_get_role_list(self, client):
        resp = client.post("/api/system/role", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 2
        assert len(data["data"]["list"]) == 2

    def test_create_role_success(self, client):
        resp = client.post(
            "/api/system/role/create", json={"name": "新角色", "code": "new_role", "isActive": 1}, headers=self.auth
        )
        assert resp.status_code == 200
        assert resp.json()["code"] == 201
        assert resp.json()["message"] == "角色创建成功"

    def test_create_role_validation_error(self, client):
        resp = client.post("/api/system/role/create", json={"name": "x"}, headers=self.auth)
        assert resp.status_code == 422

    def test_get_role_detail(self, client):
        resp = client.get("/api/system/role/r1", headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "管理员"

    def test_update_role(self, client):
        resp = client.put("/api/system/role/r1", json={"name": "更新角色"}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "角色更新成功"

    def test_delete_role(self, client):
        resp = client.delete("/api/system/role/r1", headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "角色删除成功"

    def test_update_role_status(self, client):
        resp = client.put("/api/system/role/r1/status", json={"isActive": 0}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "状态更新成功"

    def test_update_role_status_empty_returns_422(self, client):
        resp = client.put("/api/system/role/r1/status", json={}, headers=self.auth)
        assert resp.status_code == 422

    def test_update_role_status_invalid_value_returns_422(self, client):
        resp = client.put("/api/system/role/r1/status", json={"isActive": 5}, headers=self.auth)
        assert resp.status_code == 422

    def test_assign_menus(self, client):
        resp = client.post("/api/system/role/r1/menus", json={"menuIds": ["m1", "m2"]}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "菜单权限分配成功"

    def test_change_data_scope(self, client):
        resp = client.post(
            "/api/system/role/r1/data-scope", json={"dataScope": 2, "deptIds": ["d1", "d2"]}, headers=self.auth
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "数据权限修改成功"

    def test_change_data_scope_invalid_scope_returns_422(self, client):
        resp = client.post("/api/system/role/r1/data-scope", json={"dataScope": 9}, headers=self.auth)
        assert resp.status_code == 422
