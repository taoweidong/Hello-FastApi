"""字典 CRUD 全流程集成测试。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestDictionaryFlow:
    async def test_create_dictionary(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/dictionary/create",
            headers=h,
            json={"name": "sys_status", "label": "系统状态", "value": "active", "isActive": 1},
        )
        assert r.status_code == 200
        assert r.json()["code"] == 201

    async def test_update_dictionary(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/dictionary/create",
            headers=h,
            json={"name": "sys_gender", "label": "性别", "value": "male", "isActive": 1},
        )
        did = r.json()["data"]["id"]

        r = await flow_client.put(f"/api/system/dictionary/{did}", headers=h, json={"label": "用户性别"})
        assert r.status_code == 200
        assert r.json()["data"]["name"] == "sys_gender"

    async def test_delete_dictionary(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/dictionary/create",
            headers=h,
            json={"name": "sys_del", "label": "待删字典", "value": "del", "isActive": 1},
        )
        did = r.json()["data"]["id"]

        r = await flow_client.delete(f"/api/system/dictionary/{did}", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_list_dictionaries(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        for i in range(3):
            await flow_client.post(
                "/api/system/dictionary/create",
                headers=h,
                json={"name": f"dict_list_{i}", "label": f"字典{i}", "value": f"v{i}", "isActive": 1},
            )

        r = await flow_client.post("/api/system/dictionary", headers=h, json={})
        assert r.status_code == 200
        assert r.json()["code"] == 0
        assert len(r.json()["data"]) >= 3

    async def test_get_dictionary_by_name(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        await flow_client.post(
            "/api/system/dictionary/create",
            headers=h,
            json={"name": "sys_query_type", "label": "查询类型", "value": "fuzzy", "isActive": 1},
        )

        r = await flow_client.post(
            "/api/system/dictionary/getByName",
            headers=h,
            json={"name": "sys_query_type"},
        )
        assert r.status_code == 200
        assert len(r.json()["data"]) >= 1

    async def test_create_child_dictionary(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/dictionary/create",
            headers=h,
            json={"name": "parent_dict", "label": "父字典", "value": "parent", "isActive": 1},
        )
        parent_id = r.json()["data"]["id"]

        r = await flow_client.post(
            "/api/system/dictionary/create",
            headers=h,
            json={"name": "child_dict", "label": "子字典", "value": "child", "parentId": parent_id, "isActive": 1},
        )
        assert r.status_code == 200
