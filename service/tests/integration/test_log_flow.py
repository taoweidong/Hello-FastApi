"""日志管理全流程集成测试：登录日志、操作日志、系统日志。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestLogFlow:
    async def test_list_login_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/login-logs", headers=h, json={"pageNum": 1, "pageSize": 10})
        assert r.status_code == 200
        assert r.json()["data"]["total"] >= 1

    async def test_batch_delete_login_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/login-logs/batch-delete", headers=h, json={"ids": [flow_seed.login_log_id]}
        )
        assert r.status_code == 200
        assert r.json()["data"]["deleted"] == 1

    async def test_clear_login_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/login-logs/clear", headers=h)
        assert r.status_code == 200
        assert r.json()["data"]["deleted"] >= 0

    async def test_list_operation_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/operation-logs", headers=h, json={"pageNum": 1, "pageSize": 10})
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_batch_delete_operation_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/operation-logs/batch-delete", headers=h, json={"ids": [flow_seed.system_log_id]}
        )
        assert r.status_code == 200
        assert r.json()["data"]["deleted"] >= 0

    async def test_clear_operation_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/operation-logs/clear", headers=h)
        assert r.status_code == 200
        assert r.json()["data"]["deleted"] >= 0

    async def test_list_system_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/system-logs", headers=h, json={"pageNum": 1, "pageSize": 10})
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_system_log_detail(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/system-logs-detail", headers=h, json={"id": flow_seed.system_log_id})
        assert r.status_code == 200
        assert r.json()["code"] == 0
