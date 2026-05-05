"""菜单管理路由模块单元测试。"""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.infrastructure.http.exception_handler_registry import register_exception_handlers


@pytest.mark.unit
class TestMenuRouter:
    """菜单管理路由测试类。"""

    @pytest.fixture
    def app(self):
        _app = FastAPI()
        register_exception_handlers(_app)
        from src.api.v1.menu_router import MenuRouter
        _app.include_router(MenuRouter().router, prefix="/api/system/menu")
        return _app

    @pytest.fixture
    def mock_user(self):
        return {"id": "1", "username": "admin", "is_superuser": True, "is_active": 1}

    @pytest.fixture
    def mock_menu_service(self):
        svc = AsyncMock()
        svc.get_menu_list.return_value = [
            {"id": "1", "name": "系统管理", "menuType": 0, "children": [
                {"id": "2", "name": "用户管理", "menuType": 1},
            ]},
        ]
        svc.get_menu_tree.return_value = {"id": None, "children": [
            {"id": "1", "name": "系统管理", "children": [
                {"id": "2", "name": "用户管理"},
            ]},
        ]}
        svc.get_user_menus.return_value = [
            {"id": "1", "name": "系统管理", "menuType": 0},
        ]
        svc.create_menu.return_value = {"id": "3", "name": "新菜单", "menuType": 1}
        svc.update_menu.return_value = {"id": "1", "name": "更新菜单", "menuType": 1}
        svc.delete_menu.return_value = None
        return svc

    @pytest.fixture
    def client(self, app, mock_user, mock_menu_service):
        from src.api.dependencies import get_current_active_user, get_menu_service
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_menu_service] = lambda: mock_menu_service
        return TestClient(app, raise_server_exceptions=False)

    auth = {"Authorization": "Bearer test_token"}

    def test_get_menu_list(self, client):
        resp = client.post("/api/system/menu", headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "系统管理"

    def test_get_menu_tree(self, client):
        resp = client.get("/api/system/menu/tree", headers=self.auth)
        assert resp.status_code == 200
        assert "children" in resp.json()["data"]

    def test_get_user_menus(self, client):
        resp = client.get("/api/system/menu/user-menus", headers=self.auth)
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1

    def test_create_menu(self, client):
        resp = client.post("/api/system/menu/create", json={
            "name": "新菜单", "menuType": 1, "path": "/new", "component": "new/index.vue",
        }, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["code"] == 201
        assert resp.json()["message"] == "创建成功"

    def test_update_menu(self, client):
        resp = client.put("/api/system/menu/1", json={"name": "更新菜单"}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "更新成功"

    def test_delete_menu(self, client):
        resp = client.delete("/api/system/menu/1", headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"
