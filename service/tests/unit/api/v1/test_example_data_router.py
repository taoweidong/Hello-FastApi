"""示例数据路由测试（Univer 表格 CRUD 示例）。"""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.dependencies import get_current_user_id
from src.api.dependencies.example_data_service import get_example_data_service
from src.application.services.example_data_service import ExampleDataService
from src.domain.entities.user import UserEntity
from src.domain.enums import UserRole
from src.domain.exceptions import BusinessError, NotFoundError
from src.infrastructure.http.exception_handler_registry import register_exception_handlers


@pytest.mark.unit
class TestExampleDataRouter:
    @pytest.fixture
    def app(self):
        _app = FastAPI()
        register_exception_handlers(_app)
        from src.api.v1.example_data_router import ExampleDataRouter

        _app.include_router(ExampleDataRouter().router, prefix="/api/system/example-data")
        return _app

    @pytest.fixture
    def mock_service(self):
        from src.application.dto.example_data_dto import ExampleDataResponseDTO

        def _dto(idx: int) -> ExampleDataResponseDTO:
            return ExampleDataResponseDTO(id=f"ex-{idx}", name=f"row{idx}", quantity=idx, price=1.5)

        svc = AsyncMock()
        # 服务层契约：返回 ExampleDataResponseDTO（路由层负责 model_dump）
        svc.get_rows.return_value = ([_dto(1)], 1)
        svc.get_row.return_value = _dto(1)
        svc.create_row.return_value = _dto(2)
        svc.batch_save.return_value = {"created": 1, "updated": 0, "deleted": 0}
        return svc

    @pytest.fixture
    def client(self, app, mock_service):
        from src.api.dependencies import get_current_active_user

        app.dependency_overrides[get_current_active_user] = lambda: UserEntity(
            id="admin-1", username="admin", password="", is_superuser=UserRole.SUPERUSER
        )
        app.dependency_overrides[get_current_user_id] = lambda: "admin-1"
        app.dependency_overrides[get_example_data_service] = lambda: mock_service
        return TestClient(app, raise_server_exceptions=False)

    auth = {"Authorization": "Bearer test_token"}

    def test_get_rows(self, client):
        resp = client.post("/api/system/example-data", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 1
        assert data["list"][0]["name"] == "row1"

    def test_create_row(self, client, mock_service):
        resp = client.post("/api/system/example-data/create", json={"name": "row2", "quantity": 2}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "row2"
        called_dto = mock_service.create_row.await_args.args[0]
        assert called_dto.quantity == 2

    def test_batch_save(self, client, mock_service):
        payload = {"creates": [{"name": "c1"}], "updates": [{"id": "ex-1", "name": "u1"}], "deletes": []}
        resp = client.post("/api/system/example-data/batch-save", json=payload, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["data"] == {"created": 1, "updated": 0, "deleted": 0}

    def test_batch_save_business_error_400(self, app):
        svc = AsyncMock(spec=ExampleDataService)
        svc.batch_save = AsyncMock(side_effect=BusinessError("示例数据名称 'dup' 已存在"))
        from src.api.dependencies import get_current_active_user

        app.dependency_overrides[get_current_active_user] = lambda: UserEntity(
            id="admin-1", username="admin", password="", is_superuser=UserRole.SUPERUSER
        )
        app.dependency_overrides[get_current_user_id] = lambda: "admin-1"
        app.dependency_overrides[get_example_data_service] = lambda: svc
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.post(
            "/api/system/example-data/batch-save", json={"creates": [{"name": "dup"}]}, headers=self.auth
        )
        assert resp.status_code == 400
        assert "已存在" in resp.json()["message"]

    def test_get_row_missing_404(self, app):
        svc = AsyncMock(spec=ExampleDataService)
        svc.get_row = AsyncMock(side_effect=NotFoundError("示例数据 ID 'x' 不存在"))
        from src.api.dependencies import get_current_active_user

        app.dependency_overrides[get_current_active_user] = lambda: UserEntity(
            id="admin-1", username="admin", password="", is_superuser=UserRole.SUPERUSER
        )
        app.dependency_overrides[get_current_user_id] = lambda: "admin-1"
        app.dependency_overrides[get_example_data_service] = lambda: svc
        client = TestClient(app, raise_server_exceptions=False)

        resp = client.get("/api/system/example-data/nope", headers=self.auth)
        assert resp.status_code == 404

    def test_delete_row(self, client, mock_service):
        mock_service.delete_row = AsyncMock(return_value=True)
        resp = client.delete("/api/system/example-data/ex-1", headers=self.auth)
        assert resp.status_code == 200
        mock_service.delete_row.assert_awaited_once_with("ex-1")
