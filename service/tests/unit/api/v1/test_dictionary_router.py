"""字典管理路由模块单元测试。"""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.infrastructure.http.exception_handler_registry import register_exception_handlers


@pytest.mark.unit
class TestDictionaryRouter:
    """字典管理路由测试类。"""

    @pytest.fixture
    def app(self):
        _app = FastAPI()
        register_exception_handlers(_app)
        from src.api.v1.dictionary_router import DictionaryRouter
        _app.include_router(DictionaryRouter().router, prefix="/api/system")
        return _app

    @pytest.fixture
    def mock_user(self):
        return {"id": "1", "username": "admin", "is_superuser": True, "is_active": 1}

    @pytest.fixture
    def mock_dict_service(self):
        svc = AsyncMock()
        dicts = [
            {"id": "d1", "name": "性别", "label": "男", "value": "1", "isActive": 1},
            {"id": "d2", "name": "性别", "label": "女", "value": "2", "isActive": 1},
        ]
        svc.get_dictionaries.return_value = [type("Dict", (), {"model_dump": lambda self, d=d: d})() for d in dicts]
        svc.get_dictionary_by_name.return_value = [
            type("Dict", (), {"model_dump": lambda self, d=d: d})() for d in dicts
        ]
        svc.create_dictionary.return_value = type("Dict", (), {"id": "d3", "name": "状态"})()
        svc.update_dictionary.return_value = type("Dict", (), {"id": "d1", "name": "更新字典"})()
        svc.delete_dictionary.return_value = None
        return svc

    @pytest.fixture
    def client(self, app, mock_user, mock_dict_service):
        from src.api.dependencies import get_current_active_user, get_dictionary_service
        app.dependency_overrides[get_current_active_user] = lambda: mock_user
        app.dependency_overrides[get_dictionary_service] = lambda: mock_dict_service
        return TestClient(app, raise_server_exceptions=False)

    auth = {"Authorization": "Bearer test_token"}

    def test_get_dictionary_list(self, client):
        resp = client.post("/api/system/dictionary", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert len(data["data"]) == 2

    def test_get_dictionary_by_name(self, client):
        resp = client.post("/api/system/dictionary/getByName", json={"name": "性别"}, headers=self.auth)
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    def test_create_dictionary_success(self, client):
        resp = client.post("/api/system/dictionary/create", json={
            "name": "状态", "label": "启用", "value": "1", "isActive": 1,
        }, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["code"] == 201
        assert resp.json()["message"] == "创建成功"

    def test_create_dictionary_validation_error(self, client):
        resp = client.post("/api/system/dictionary/create", json={}, headers=self.auth)
        assert resp.status_code == 422

    def test_update_dictionary(self, client):
        resp = client.put("/api/system/dictionary/d1", json={"name": "更新字典"}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "更新成功"

    def test_delete_dictionary(self, client):
        resp = client.delete("/api/system/dictionary/d1", headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"
