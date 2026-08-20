"""系统配置 CRUD 全流程集成测试。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestSystemConfigFlow:
    async def test_create_config(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/config/create",
            headers=h,
            json={"key": "site_name", "value": "Hello-FastApi", "isActive": 1, "description": "站点名称"},
        )
        assert r.status_code == 200
        assert r.json()["code"] == 201

    async def test_read_config_detail(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/config/create", headers=h, json={"key": "max_login_attempts", "value": "5", "isActive": 1}
        )
        cid = r.json()["data"]["id"]

        r = await flow_client.get(f"/api/system/config/{cid}", headers=h)
        assert r.status_code == 200
        assert r.json()["data"]["key"] == "max_login_attempts"

    async def test_update_config(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/config/create", headers=h, json={"key": "theme", "value": "light", "isActive": 1}
        )
        cid = r.json()["data"]["id"]

        r = await flow_client.put(f"/api/system/config/{cid}", headers=h, json={"value": "dark"})
        assert r.status_code == 200
        assert r.json()["data"]["value"] == "dark"

    async def test_delete_config(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/config/create", headers=h, json={"key": "del_config", "value": "to_delete", "isActive": 1}
        )
        cid = r.json()["data"]["id"]

        r = await flow_client.delete(f"/api/system/config/{cid}", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_list_configs_paginated(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        for i in range(3):
            await flow_client.post(
                "/api/system/config/create",
                headers=h,
                json={"key": f"list_cfg_{i}", "value": f"val_{i}", "isActive": 1},
            )

        r = await flow_client.post("/api/system/config", headers=h, json={"pageNum": 1, "pageSize": 5})
        assert r.status_code == 200
        assert r.json()["data"]["total"] >= 3

    async def test_create_duplicate_key_rejected(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        await flow_client.post(
            "/api/system/config/create", headers=h, json={"key": "dup_key", "value": "v1", "isActive": 1}
        )

        r = await flow_client.post(
            "/api/system/config/create", headers=h, json={"key": "dup_key", "value": "v2", "isActive": 1}
        )
        assert r.status_code in (400, 409, 500)
