"""用户角色分配全流程集成测试。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestUserRoleAssignmentFlow:
    async def test_assign_role_to_user(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/user/create",
            headers=h,
            json={
                "username": "role_assign_user",
                "password": "RoleAssign123!",
                "email": "assign@flow.test",
                "isActive": True,
            },
        )
        uid = r.json()["data"]["id"]

        r = await flow_client.post(
            "/api/system/user/assign-role", headers=h, json={"userId": uid, "roleIds": [flow_seed.role_admin_id]}
        )
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_list_user_role_ids(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/user/create",
            headers=h,
            json={
                "username": "role_list_user",
                "password": "RoleList123!",
                "email": "rolelist@flow.test",
                "isActive": True,
            },
        )
        uid = r.json()["data"]["id"]

        await flow_client.post(
            "/api/system/user/assign-role", headers=h, json={"userId": uid, "roleIds": [flow_seed.role_ops_id]}
        )

        r = await flow_client.post("/api/system/list-role-ids", headers=h, json={"userId": uid})
        assert r.status_code == 200
        assert flow_seed.role_ops_id in r.json()["data"]

    async def test_operator_initial_role(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/list-role-ids", headers=h, json={"userId": flow_seed.operator_user_id})
        assert r.status_code == 200
        assert flow_seed.role_ops_id in r.json()["data"]

    async def test_role_menu_lookup(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/role-menu", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_role_menu_ids_lookup(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/role-menu-ids", headers=h, json={"id": flow_seed.role_admin_id})
        assert r.status_code == 200
        assert flow_seed.menu_root_id in r.json()["data"]

    async def test_assign_multiple_roles(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/user/create",
            headers=h,
            json={
                "username": "multi_role_user",
                "password": "MultiRole123!",
                "email": "multi@flow.test",
                "isActive": True,
            },
        )
        uid = r.json()["data"]["id"]

        r = await flow_client.post(
            "/api/system/user/assign-role",
            headers=h,
            json={"userId": uid, "roleIds": [flow_seed.role_admin_id, flow_seed.role_ops_id]},
        )
        assert r.status_code == 200

        r = await flow_client.post("/api/system/list-role-ids", headers=h, json={"userId": uid})
        assert r.status_code == 200
        assert flow_seed.role_admin_id in r.json()["data"]
        assert flow_seed.role_ops_id in r.json()["data"]
