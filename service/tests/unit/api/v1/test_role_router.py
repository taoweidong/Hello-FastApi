"""角色管理路由模块单元测试。"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

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
    def mock_role_service(self):
        svc = AsyncMock()
        _r1 = MagicMock()
        _r1.model_dump.return_value = {"id": "r1", "name": "管理员", "code": "admin"}
        _r2 = MagicMock()
        _r2.model_dump.return_value = {"id": "r2", "name": "普通用户", "code": "user"}
        svc.get_roles.return_value = ([_r1, _r2], 2)
        svc.create_role.return_value = {"id": "r3", "name": "新角色", "code": "new"}
        svc.get_role.return_value = {"id": "r1", "name": "管理员", "code": "admin"}
        svc.update_role.return_value = {"id": "r1", "name": "更新角色", "code": "admin"}
        svc.delete_role.return_value = None
        svc.assign_menus.return_value = None
        return svc

    @pytest.fixture
    def mock_role_repo(self):
        repo = AsyncMock()
        repo.assign_menus_to_role.return_value = None
        return repo

    @pytest.fixture
    def mock_db_session(self):
        session = AsyncMock()
        session.commit.return_value = None
        return session

    @pytest.fixture
    def client(self, app, mock_user, mock_role_service, mock_role_repo, mock_db_session):
        from src.api.dependencies import get_current_active_user, get_role_repository, get_role_service
        from src.infrastructure.database import get_db
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_role_service] = lambda: mock_role_service
        app.dependency_overrides[get_role_repository] = lambda: mock_role_repo
        app.dependency_overrides[get_db] = lambda: mock_db_session
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
        resp = client.post("/api/system/role/create", json={
            "name": "新角色", "code": "new_role", "isActive": 1,
        }, headers=self.auth)
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

    def test_update_role_status_empty(self, client):
        resp = client.put("/api/system/role/r1/status", json={}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "状态值不能为空"

    def test_assign_menus(self, client):
        resp = client.post("/api/system/role/r1/menus", json={"menuIds": ["m1", "m2"]}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "菜单权限分配成功"

    def test_assign_role_menu(self, client):
        resp = client.post("/api/system/role/r1/menu", json={"menuIds": ["m1"]}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "菜单权限分配成功"
