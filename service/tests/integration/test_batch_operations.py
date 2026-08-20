"""批量操作全流程集成测试：用户批量删除、IP 规则批量删除、日志批量删除。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestBatchOperations:
    async def test_batch_delete_users(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        ids = []
        for i in range(3):
            r = await flow_client.post(
                "/api/system/user/create",
                headers=h,
                json={
                    "username": f"batch_user_{i}",
                    "password": "BatchUser123!",
                    "email": f"batch{i}@test.com",
                    "isActive": True,
                },
            )
            ids.append(r.json()["data"]["id"])

        r = await flow_client.post("/api/system/user/batch-delete", headers=h, json={"ids": ids})
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_batch_delete_ip_rules(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        ids = []
        for i in range(4):
            r = await flow_client.post(
                "/api/system/ip-rule/create",
                headers=h,
                json={"ipAddress": f"10.10.10.{i}", "ruleType": "blacklist", "isActive": 1},
            )
            ids.append(r.json()["data"]["id"])

        r = await flow_client.post("/api/system/ip-rule/batch-delete", headers=h, json={"ids": ids})
        assert r.status_code == 200
        assert r.json()["data"]["deleted"] == 4

    async def test_batch_delete_login_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/login-logs/batch-delete", headers=h, json={"ids": [flow_seed.login_log_id]}
        )
        assert r.status_code == 200

    async def test_batch_delete_operation_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/operation-logs/batch-delete", headers=h, json={"ids": [flow_seed.system_log_id]}
        )
        assert r.status_code == 200

    async def test_batch_delete_empty_ids(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/user/batch-delete", headers=h, json={"ids": []})
        assert r.status_code == 200

    async def test_batch_delete_nonexistent_users(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/user/batch-delete", headers=h, json={"ids": ["nonexistent-id-1", "nonexistent-id-2"]}
        )
        assert r.status_code == 200
