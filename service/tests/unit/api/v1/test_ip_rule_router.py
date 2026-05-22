"""IP 规则管理路由模块单元测试。"""

from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.entities.user import UserEntity
from src.domain.enums import UserRole
from src.infrastructure.http.exception_handler_registry import register_exception_handlers


def _make_rule_entity(rule_id: str, **kw):
    defaults = {
        "id": rule_id, "ip_address": "192.168.1.1", "rule_type": "blacklist",
        "reason": "恶意扫描", "is_active": 1, "creator_id": "1", "modifier_id": None,
        "created_time": datetime(2026, 1, 1), "updated_time": None,
        "expires_at": None, "description": "test",
    }
    defaults.update(kw)
    return type("RuleEntity", (), defaults)()


@pytest.mark.unit
class TestIPRuleRouter:
    """IP 规则管理路由测试类。"""

    @pytest.fixture
    def app(self):
        _app = FastAPI()
        register_exception_handlers(_app)
        from src.api.v1.ip_rule_router import IPRuleRouter
        _app.include_router(IPRuleRouter().router, prefix="/api/system/ip-rule")
        return _app

    @pytest.fixture
    def mock_user(self):
        return {"id": "1", "username": "admin", "is_superuser": True, "is_active": 1}

    @pytest.fixture
    def mock_user_entity(self):
        return UserEntity(id="1", username="admin", password="", is_superuser=UserRole.SUPERUSER)

    @pytest.fixture
    def mock_ip_rule_service(self):
        svc = AsyncMock()
        rule1 = _make_rule_entity("r1")
        rule2 = _make_rule_entity("r2", ip_address="10.0.0.1", rule_type="whitelist")
        svc.get_ip_rules.return_value = ([rule1, rule2], 2)
        svc.get_ip_rule.return_value = rule1
        svc.create_ip_rule.return_value = type("Rule", (), {"id": "r3", "ip_address": "172.16.0.1"})()
        svc.update_ip_rule.return_value = type("Rule", (), {"id": "r1", "ip_address": "192.168.1.2"})()
        svc.delete_ip_rules.return_value = 3
        svc.clear_ip_rules.return_value = 10
        return svc

    @pytest.fixture
    def client(self, app, mock_user_entity, mock_ip_rule_service):
        from src.api.dependencies import get_current_active_user
        from src.api.dependencies.ip_rule_service import get_ip_rule_service
        app.dependency_overrides[get_current_active_user] = lambda: mock_user_entity
        app.dependency_overrides[get_ip_rule_service] = lambda: mock_ip_rule_service
        return TestClient(app, raise_server_exceptions=False)

    auth = {"Authorization": "Bearer test_token"}

    def test_get_ip_rules(self, client):
        resp = client.post("/api/system/ip-rule", json={}, headers=self.auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["code"] == 0
        assert data["data"]["total"] == 2
        assert len(data["data"]["list"]) == 2

    def test_get_ip_rule_detail(self, client):
        resp = client.get("/api/system/ip-rule/r1", headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["data"]["ipAddress"] == "192.168.1.1"

    def test_create_ip_rule(self, client):
        resp = client.post("/api/system/ip-rule/create", json={
            "ipAddress": "172.16.0.1", "ruleType": "blacklist", "isActive": 1,
        }, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["code"] == 201
        assert resp.json()["message"] == "创建成功"

    def test_update_ip_rule(self, client):
        resp = client.put("/api/system/ip-rule/r1", json={"ipAddress": "192.168.1.2"}, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "更新成功"

    def test_delete_ip_rule(self, client):
        resp = client.delete("/api/system/ip-rule/r1", headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "删除成功"

    def test_batch_delete_ip_rules(self, client):
        resp = client.post("/api/system/ip-rule/batch-delete", json={"ids": ["r1", "r2"]}, headers=self.auth)
        assert resp.status_code == 200
        assert "已删除" in resp.json()["message"]

    def test_clear_ip_rules(self, client):
        resp = client.post("/api/system/ip-rule/clear", headers=self.auth)
        assert resp.status_code == 200
        assert "已清空" in resp.json()["message"]

    def test_get_ip_rules_with_is_active_int(self, client):
        """GET 列表 with isActive as int should hit L34: is_active = int(is_active)."""
        resp = client.post("/api/system/ip-rule", json={"isActive": 1}, headers=self.auth)
        assert resp.status_code == 200

    def test_get_ip_rules_with_is_active_zero(self, client):
        """GET 列表 with isActive: 0."""
        resp = client.post("/api/system/ip-rule", json={"isActive": 0}, headers=self.auth)
        assert resp.status_code == 200

    def test_create_ip_rule_with_valid_expires_at(self, client):
        """Create with valid ISO expiresAt should hit L95-96."""
        resp = client.post("/api/system/ip-rule/create", json={
            "ipAddress": "8.8.8.8", "expiresAt": "2030-01-01T00:00:00",
        }, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["code"] == 201

    def test_create_ip_rule_with_invalid_expires_at(self, client):
        """Create with invalid expiresAt should hit L95, L98 (except branch)."""
        resp = client.post("/api/system/ip-rule/create", json={
            "ipAddress": "9.9.9.9", "expiresAt": "not-a-date",
        }, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["code"] == 201

    def test_update_ip_rule_with_valid_expires_at(self, client):
        """Update with valid ISO expiresAt should hit L122-123."""
        resp = client.put("/api/system/ip-rule/r1", json={
            "expiresAt": "2030-06-15T12:00:00",
        }, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "更新成功"

    def test_update_ip_rule_with_invalid_expires_at(self, client):
        """Update with invalid expiresAt should hit L122, L125 (except branch)."""
        resp = client.put("/api/system/ip-rule/r1", json={
            "expiresAt": "bad-date",
        }, headers=self.auth)
        assert resp.status_code == 200
        assert resp.json()["message"] == "更新成功"
