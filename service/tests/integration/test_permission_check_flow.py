"""RBAC 权限校验全流程集成测试。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestPermissionCheckFlow:
    async def test_superuser_can_delete_user(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h_super = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/user/create",
            headers=h_super,
            json={
                "username": "perm_victim",
                "password": "PermVictim123!",
                "email": "victim@perm.test",
                "isActive": True,
            },
        )
        assert r.status_code == 201
        uid = r.json()["data"]["id"]

        r = await flow_client.delete(f"/api/system/user/{uid}", headers=h_super)
        assert r.status_code == 200

    async def test_operator_cannot_delete_user(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h_super = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/user/create",
            headers=h_super,
            json={
                "username": "perm_victim2",
                "password": "PermVictim123!",
                "email": "victim2@perm.test",
                "isActive": True,
            },
        )
        uid = r.json()["data"]["id"]

        h_op = await _login_headers(flow_client, flow_seed.operator_username, flow_seed.operator_password)
        r = await flow_client.delete(f"/api/system/user/{uid}", headers=h_op)
        assert r.status_code == 403

    async def test_operator_can_list_users(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h_op = await _login_headers(flow_client, flow_seed.operator_username, flow_seed.operator_password)

        r = await flow_client.post("/api/system/user", headers=h_op, json={"pageNum": 1, "pageSize": 10})
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_unauthenticated_user_cannot_access(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        r = await flow_client.post("/api/system/user", json={"pageNum": 1, "pageSize": 10})
        assert r.status_code in (401, 403)

    async def test_operator_cannot_create_user(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h_op = await _login_headers(flow_client, flow_seed.operator_username, flow_seed.operator_password)

        r = await flow_client.post(
            "/api/system/user/create",
            headers=h_op,
            json={
                "username": "perm_fail_create",
                "password": "PermFail123!",
                "email": "fail@perm.test",
                "isActive": True,
            },
        )
        assert r.status_code == 403

    async def test_superuser_can_manage_roles(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/role/create",
            headers=h,
            json={"name": "perm_role", "code": "perm_role", "isActive": True, "menuIds": []},
        )
        assert r.status_code == 200

    async def test_list_all_roles_accessible(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.get("/api/system/list-all-role", headers=h)
        assert r.status_code == 200
        assert len(r.json()["data"]) >= 2
