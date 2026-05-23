"""用户 CRUD 全流程集成测试。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestUserCrudFlow:
    async def test_create_user_then_read(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/user/create",
            headers=h,
            json={
                "username": "flow_crud_user",
                "password": "FlowCrud123!",
                "nickname": "CRUD用户",
                "email": "crud@flow.test",
                "isActive": True,
            },
        )
        assert r.status_code == 201
        uid = r.json()["data"]["id"]

        r = await flow_client.get(f"/api/system/user/{uid}", headers=h)
        assert r.status_code == 200
        assert r.json()["data"]["username"] == "flow_crud_user"

    async def test_update_user(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/user/create",
            headers=h,
            json={
                "username": "flow_update_u",
                "password": "FlowUpdate123!",
                "nickname": "原名",
                "email": "upd@flow.test",
                "isActive": True,
            },
        )
        uid = r.json()["data"]["id"]

        r = await flow_client.put(
            f"/api/system/user/{uid}",
            headers=h,
            json={"nickname": "新名", "description": "备注信息"},
        )
        assert r.status_code == 200
        assert r.json()["data"]["nickname"] == "新名"

    async def test_delete_user(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/user/create",
            headers=h,
            json={
                "username": "flow_delete_u",
                "password": "FlowDel123!",
                "email": "del@flow.test",
                "isActive": True,
            },
        )
        uid = r.json()["data"]["id"]

        r = await flow_client.delete(f"/api/system/user/{uid}", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0

        r = await flow_client.get(f"/api/system/user/{uid}", headers=h)
        assert r.status_code in (404, 200)

    async def test_change_password_then_login(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/user/create",
            headers=h,
            json={
                "username": "flow_pwd_user",
                "password": "OldPwd123!",
                "email": "pwd@flow.test",
                "isActive": True,
            },
        )
        assert r.status_code == 201

        h_user = await _login_headers(flow_client, "flow_pwd_user", "OldPwd123!")
        r = await flow_client.post(
            "/api/system/user/change-password",
            headers=h_user,
            json={"oldPassword": "OldPwd123!", "newPassword": "NewPwd456!"},
        )
        assert r.status_code == 200

        r = await flow_client.post("/api/system/login", json={"username": "flow_pwd_user", "password": "NewPwd456!"})
        assert r.status_code == 200

    async def test_toggle_user_status(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/user/create",
            headers=h,
            json={
                "username": "flow_status_u",
                "password": "FlowStatus123!",
                "email": "status@flow.test",
                "isActive": True,
            },
        )
        uid = r.json()["data"]["id"]

        r = await flow_client.put(f"/api/system/user/{uid}/status", headers=h, json={"isActive": False})
        assert r.status_code == 200

        r = await flow_client.post("/api/system/login", json={"username": "flow_status_u", "password": "FlowStatus123!"})
        assert r.status_code == 401

    async def test_reset_password(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/user/create",
            headers=h,
            json={
                "username": "flow_reset_u",
                "password": "Original123!",
                "email": "reset@flow.test",
                "isActive": True,
            },
        )
        uid = r.json()["data"]["id"]

        r = await flow_client.put(
            f"/api/system/user/{uid}/reset-password",
            headers=h,
            json={"newPassword": "ResetNew123!"},
        )
        assert r.status_code == 200

        r = await flow_client.post("/api/system/login", json={"username": "flow_reset_u", "password": "ResetNew123!"})
        assert r.status_code == 200
