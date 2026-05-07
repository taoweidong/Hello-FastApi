"""部门管理路由模块单元测试。"""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.infrastructure.http.exception_handler_registry import register_exception_handlers


@pytest.mark.unit
class TestDeptRouter:
    """部门管理路由测试类。"""

    @pytest.fixture
    def app(self):
        _app = FastAPI()
        register_exception_handlers(_app)
        from src.api.v1.dept_router import DeptRouter
        _app.include_router(DeptRouter().router, prefix="/api/system")
        return _app

    @pytest.fixture
    def mock_user(self):
        return {"id": "1", "username": "admin", "is_superuser": True, "is_active": 1}

    @pytest.fixture
    def mock_dept_service(self):
        svc = AsyncMock()
        depts = [
            {"id": "d1", "name": "技术部", "code": "tech", "isActive": 1, "parentId": None},
            {"id": "d2", "name": "开发组", "code": "dev", "isActive": 1, "parentId": "d1"},
        ]
        svc.get_departments.return_value = [type("Dept", (), {"model_dump": lambda self, d=d: d})() for d in depts]
        svc.create_department.return_value = type("Dept", (), {"id": "d3", "name": "测试部"})()
        svc.update_department.return_value = type("Dept", (), {"id": "d1", "name": "更新部"})()
        svc.delete_department.return_value = None
        svc.get_dept_tree.return_value = [
            {"id": "d1", "name": "技术部", "children": [{"id": "d2", "name": "开发组"}]},
        ]
        return svc

    @pytest.fixture
    def client(self, app, mock_user, mock_dept_service):
        from src.api.dependencies import get_current_active_user, get_department_service
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_department_service] = lambda: mock_dept_service
        return TestClient(app, raise_server_exceptions=False)

    auth = {"Authorization": "Bearer test_token"}

    def test_get_dept_list(self, client):
        resp = client.post("/api/system/dept", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]) == 2

    def test_create_dept_success(self, client):
        resp = client.post("/api/system/dept/create", json={
            "name": "测试部", "code": "test", "isActive": 1,
        }, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["code"] == 201
        assert resp.json()["message"] == "创建成功"

    def test_create_dept_validation_error(self, client):
        resp = client.post("/api/system/dept/create", json={}, headers=self.auth)
        assert resp.status_code == 422

    def test_update_dept(self, client):
        resp = client.put("/api/system/dept/d1", json={"name": "更新部"}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "更新成功"

    def test_delete_dept(self, client):
        resp = client.delete("/api/system/dept/d1", headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"

    def test_get_dept_tree(self, client):
        resp = client.get("/api/system/dept/tree", headers=self.auth)
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 1
        assert resp.json()["data"][0]["name"] == "技术部"
