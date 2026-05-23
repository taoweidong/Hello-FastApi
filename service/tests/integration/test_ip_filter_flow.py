"""IP 规则黑白名单全流程集成测试。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestIpFilterFlow:
    async def test_create_blacklist_rule(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/ip-rule/create",
            headers=h,
            json={"ipAddress": "10.0.0.1", "ruleType": "blacklist", "reason": "恶意IP", "isActive": 1},
        )
        assert r.status_code == 200
        assert r.json()["data"]["ipAddress"] == "10.0.0.1"

    async def test_create_whitelist_rule(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/ip-rule/create",
            headers=h,
            json={"ipAddress": "10.0.0.2", "ruleType": "whitelist", "reason": "信任IP", "isActive": 1},
        )
        assert r.status_code == 200
        assert r.json()["data"]["ipAddress"] == "10.0.0.2"

    async def test_update_ip_rule(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/ip-rule/create",
            headers=h,
            json={"ipAddress": "10.0.0.3", "ruleType": "blacklist", "reason": "原原因", "isActive": 1},
        )
        rid = r.json()["data"]["id"]

        r = await flow_client.put(f"/api/system/ip-rule/{rid}", headers=h, json={"reason": "更新后的原因"})
        assert r.status_code == 200

    async def test_delete_ip_rule(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/ip-rule/create",
            headers=h,
            json={"ipAddress": "10.0.0.4", "ruleType": "blacklist", "isActive": 1},
        )
        rid = r.json()["data"]["id"]

        r = await flow_client.delete(f"/api/system/ip-rule/{rid}", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_batch_delete_ip_rules(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        ids = []
        for i in range(3):
            r = await flow_client.post(
                "/api/system/ip-rule/create",
                headers=h,
                json={"ipAddress": f"10.0.0.{10 + i}", "ruleType": "blacklist", "isActive": 1},
            )
            ids.append(r.json()["data"]["id"])

        r = await flow_client.post("/api/system/ip-rule/batch-delete", headers=h, json={"ids": ids})
        assert r.status_code == 200
        assert r.json()["data"]["deleted"] == 3

    async def test_get_ip_rule_list_paginated(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        for i in range(5):
            await flow_client.post(
                "/api/system/ip-rule/create",
                headers=h,
                json={"ipAddress": f"10.0.1.{i}", "ruleType": "blacklist", "isActive": 1},
            )

        r = await flow_client.post("/api/system/ip-rule", headers=h, json={"pageNum": 1, "pageSize": 3})
        assert r.status_code == 200
        assert r.json()["data"]["total"] >= 5

    async def test_clear_all_ip_rules(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        for i in range(2):
            await flow_client.post(
                "/api/system/ip-rule/create",
                headers=h,
                json={"ipAddress": f"10.0.2.{i}", "ruleType": "blacklist", "isActive": 1},
            )

        r = await flow_client.post("/api/system/ip-rule/clear", headers=h)
        assert r.status_code == 200
        assert r.json()["data"]["deleted"] >= 2
