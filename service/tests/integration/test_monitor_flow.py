"""监控端点全流程集成测试。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestMonitorFlow:
    async def test_get_online_logs(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/online-logs", headers=h, json={})
        assert r.status_code == 200
        assert r.json()["code"] == 0
        assert len(r.json()["data"]["data"]) >= 1

    async def test_online_logs_filter_by_username(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/online-logs", headers=h, json={"username": "admin"})
        assert r.status_code == 200
        assert all("admin" in item["username"] for item in r.json()["data"]["data"])

    async def test_force_offline(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/online-logs/force-offline", headers=h, json={"id": 1})
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_get_map_info(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.get("/api/system/get-map-info", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0
        assert len(r.json()["data"]) == 50

    async def test_get_card_list(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/get-card-list", headers=h, json={})
        assert r.status_code == 200
        assert r.json()["code"] == 0
        assert "list" in r.json()["data"]
        assert len(r.json()["data"]["list"]) == 48

    async def test_stubs_accessible_with_auth(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.get("/api/system/mine-logs", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0
