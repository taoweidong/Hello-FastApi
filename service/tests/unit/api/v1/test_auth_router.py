"""认证路由模块单元测试。"""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.entities.menu import MenuEntity
from src.domain.entities.menu_meta import MenuMetaEntity
from src.domain.entities.user import UserEntity
from src.infrastructure.http.exception_handler_registry import register_exception_handlers


@pytest.mark.unit
class TestAuthRouter:
    """认证管理路由测试类。"""

    @pytest.fixture
    def app(self):
        _app = FastAPI()
        register_exception_handlers(_app)
        from src.api.v1.auth_router import AuthRouter
        _app.include_router(AuthRouter().router, prefix="/api/system")
        return _app

    @pytest.fixture
    def mock_user(self):
        return {"id": "1", "username": "admin", "email": "admin@test.com", "is_superuser": True, "is_active": 1}

    @pytest.fixture
    def mock_user_entity(self):
        return UserEntity(
            id="1", username="admin", password="hashed", avatar="av.png",
            nickname="管理员", email="admin@test.com", phone="13800000000",
            description="管理员账号", is_active=1, is_superuser=1,
        )

    @pytest.fixture
    def mock_auth_service(self):
        svc = AsyncMock()
        svc.login.return_value = {
            "accessToken": "access_token", "expires": 1800,
            "refreshToken": "refresh_token",
            "userInfo": {"id": "1", "username": "admin"}, "roles": ["admin"],
        }
        svc.register.return_value = {"id": "2", "username": "newuser"}
        svc.logout.return_value = None
        svc.refresh_token.return_value = {
            "accessToken": "new_access", "expires": 1800, "refreshToken": "new_refresh",
        }
        svc.get_async_routes.return_value = [
            {"name": "sys", "path": "/sys", "component": None, "meta": {"title": "系统管理", "icon": "setting"}},
        ]
        svc.get_user_role_ids.return_value = ["r1"]
        svc.get_role_menu_ids.return_value = ["1", "2"]
        return svc

    @pytest.fixture
    def mock_menu_service(self):
        svc = AsyncMock()
        meta1 = MenuMetaEntity(id="m1", title="系统管理", icon="setting")
        menu1 = MenuEntity(id="1", name="sys", menu_type=0, path="/sys", rank=1, meta=meta1)
        menu2 = MenuEntity(id="2", name="users", menu_type=1, path="/sys/users",
                           component="sys/users.vue", parent_id="1", rank=2,
                           meta=MenuMetaEntity(id="m2", title="用户管理"))
        svc.get_all_menus_raw.return_value = [menu1, menu2]
        return svc

    @pytest.fixture
    def mock_role_service(self):
        svc = AsyncMock()
        svc.get_all_simple_roles.return_value = [
            {"id": "r1", "name": "管理员"},
            {"id": "r2", "name": "普通用户"},
        ]
        return svc

    @pytest.fixture
    def mock_user_service(self, mock_user_entity):
        svc = AsyncMock()
        svc.get_user_by_id.return_value = mock_user_entity
        return svc

    @pytest.fixture
    def client(self, app, mock_user, mock_user_entity, mock_auth_service, mock_menu_service, mock_role_service, mock_user_service):
        from src.api.dependencies import (
            get_auth_service,
            get_current_active_user,
            get_menu_service,
            get_role_service,
            get_user_service,
        )
        app.dependency_overrides[get_current_active_user] = lambda: mock_user_entity
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
        app.dependency_overrides[get_menu_service] = lambda: mock_menu_service
        app.dependency_overrides[get_role_service] = lambda: mock_role_service
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        return TestClient(app, raise_server_exceptions=False)

    def test_login_success(self, client, mock_auth_service):
        resp = client.post("/api/system/login", json={"username": "admin", "password": "admin123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["message"] == "登录成功"
        assert data["data"]["accessToken"] == "access_token"

    def test_login_validation_error(self, client):
        resp = client.post("/api/system/login", json={})
        assert resp.status_code == 422

    def test_register_success(self, client):
        resp = client.post("/api/system/register", json={"username": "newuser", "password": "Pass1234"})
        assert resp.status_code == 200
        assert resp.json()["message"] == "注册成功"

    def test_register_validation_error(self, client):
        resp = client.post("/api/system/register", json={"username": "ab"})
        assert resp.status_code == 422

    def test_logout_success(self, client):
        resp = client.post("/api/system/logout", headers={"Authorization": "Bearer test_token"})
        assert resp.status_code == 200
        assert resp.json()["message"] == "登出成功"

    def test_refresh_token_success(self, client):
        resp = client.post("/api/system/refresh-token", json={"refreshToken": "some_refresh"})
        assert resp.status_code == 200
        assert resp.json()["message"] == "刷新成功"

    def test_get_mine_success(self, client, mock_user_entity):
        resp = client.get("/api/system/mine", headers={"Authorization": "Bearer test_token"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["username"] == "admin"
        assert data["data"]["nickname"] == "管理员"

    def test_get_mine_missing_user(self, client, mock_user_service):
        mock_user_service.get_user_by_id.return_value = None
        resp = client.get("/api/system/mine", headers={"Authorization": "Bearer test_token"})
        assert resp.status_code == 401

    def test_get_mine_logs(self, client):
        resp = client.get("/api/system/mine-logs", headers={"Authorization": "Bearer test_token"})
        assert resp.status_code == 200
        assert resp.json()["data"]["list"] == []

    def test_get_async_routes(self, client):
        resp = client.get("/api/system/get-async-routes", headers={"Authorization": "Bearer test_token"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) > 0
        assert data["data"][0]["name"] == "sys"

    def test_list_all_roles(self, client):
        resp = client.get("/api/system/list-all-role", headers={"Authorization": "Bearer test_token"})
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    def test_list_role_ids_success(self, client):
        resp = client.post(
            "/api/system/list-role-ids",
            json={"userId": "1"},
            headers={"Authorization": "Bearer test_token"},
        )
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_list_role_ids_missing_param(self, client):
        resp = client.post("/api/system/list-role-ids", json={}, headers={"Authorization": "Bearer test_token"})
        assert resp.status_code == 200
        assert resp.json()["code"] == 10001

    def test_get_role_menu(self, client):
        resp = client.post("/api/system/role-menu", headers={"Authorization": "Bearer test_token"})
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    def test_get_role_menu_ids_success(self, client):
        resp = client.post(
            "/api/system/role-menu-ids",
            json={"id": "r1"},
            headers={"Authorization": "Bearer test_token"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "1" in data

    def test_get_role_menu_ids_empty_id(self, client):
        resp = client.post("/api/system/role-menu-ids", json={}, headers={"Authorization": "Bearer test_token"})
        assert resp.status_code == 200
        assert resp.json()["data"] == []
