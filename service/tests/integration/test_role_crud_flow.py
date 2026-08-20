"""角色 CRUD 全流程及菜单分配集成测试。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestRoleCrudFlow:
    async def test_create_role(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/role/create",
            headers=h,
            json={"name": "flow_role", "code": "flow_role", "isActive": True, "menuIds": []},
        )
        assert r.status_code == 200
        assert r.json()["data"]["name"] == "flow_role"

    async def test_read_role_detail(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/role/create",
            headers=h,
            json={"name": "flow_role_r", "code": "flow_role_r", "isActive": True, "menuIds": []},
        )
        rid = r.json()["data"]["id"]

        r = await flow_client.get(f"/api/system/role/{rid}", headers=h)
        assert r.status_code == 200
        assert r.json()["data"]["name"] == "flow_role_r"

    async def test_update_role(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/role/create",
            headers=h,
            json={"name": "flow_role_u", "code": "flow_role_u", "description": "旧", "isActive": True, "menuIds": []},
        )
        rid = r.json()["data"]["id"]

        r = await flow_client.put(f"/api/system/role/{rid}", headers=h, json={"description": "新描述"})
        assert r.status_code == 200
        assert r.json()["data"]["description"] == "新描述"

    async def test_delete_role(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/role/create",
            headers=h,
            json={"name": "flow_role_d", "code": "flow_role_d", "isActive": True, "menuIds": []},
        )
        rid = r.json()["data"]["id"]

        r = await flow_client.delete(f"/api/system/role/{rid}", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_assign_menus_to_role(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/role/create",
            headers=h,
            json={"name": "flow_role_m", "code": "flow_role_m", "isActive": True, "menuIds": []},
        )
        rid = r.json()["data"]["id"]

        r = await flow_client.post(
            f"/api/system/role/{rid}/menus",
            headers=h,
            json={"menuIds": [flow_seed.menu_root_id, flow_seed.menu_perm_id]},
        )
        assert r.status_code == 200

        r = await flow_client.post("/api/system/role-menu-ids", headers=h, json={"id": rid})
        assert r.status_code == 200
        assert flow_seed.menu_root_id in r.json()["data"]

    async def test_assign_menus_put_endpoint(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/role/create",
            headers=h,
            json={"name": "flow_role_pm", "code": "flow_role_pm", "isActive": True, "menuIds": []},
        )
        rid = r.json()["data"]["id"]

        r = await flow_client.post(
            f"/api/system/role/{rid}/menus", headers=h, json={"menuIds": [flow_seed.menu_root_id]}
        )
        assert r.status_code == 200

    async def test_role_status_toggle(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/role/create",
            headers=h,
            json={"name": "flow_role_s", "code": "flow_role_s", "isActive": True, "menuIds": []},
        )
        rid = r.json()["data"]["id"]

        r = await flow_client.put(f"/api/system/role/{rid}/status", headers=h, json={"isActive": False})
        assert r.status_code == 200
