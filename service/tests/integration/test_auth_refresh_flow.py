"""认证全流程集成测试：登录、刷新、重新访问、登出。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


@pytest.mark.integration
class TestAuthRefreshFlow:
    async def test_login_and_access_mine(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        r = await flow_client.post(
            "/api/system/login",
            json={"username": flow_seed.super_username, "password": flow_seed.super_password},
        )
        assert r.status_code == 200
        token = r.json()["data"]["accessToken"]

        r = await flow_client.get("/api/system/mine", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["data"]["username"] == flow_seed.super_username

    async def test_refresh_token_extends_session(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        login = await flow_client.post(
            "/api/system/login",
            json={"username": flow_seed.super_username, "password": flow_seed.super_password},
        )
        assert login.status_code == 200
        refresh = login.json()["data"]["refreshToken"]

        r = await flow_client.post("/api/system/refresh-token", json={"refreshToken": refresh})
        assert r.status_code == 200
        new_token = r.json()["data"]["accessToken"]
        assert new_token

        r = await flow_client.get("/api/system/mine", headers={"Authorization": f"Bearer {new_token}"})
        assert r.status_code == 200

    async def test_logout_invalidates_token(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        login = await flow_client.post(
            "/api/system/login",
            json={"username": flow_seed.super_username, "password": flow_seed.super_password},
        )
        token = login.json()["data"]["accessToken"]
        h = {"Authorization": f"Bearer {token}"}

        r = await flow_client.post("/api/system/logout", headers=h)
        assert r.status_code == 200

    async def test_wrong_password_rejected(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        r = await flow_client.post(
            "/api/system/login",
            json={"username": flow_seed.super_username, "password": "WrongPassword123!"},
        )
        assert r.status_code == 401

    async def test_register_then_login_then_refresh(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        r = await flow_client.post(
            "/api/system/register",
            json={
                "username": "flow_auth_reg",
                "password": "FlowAuthReg123!",
                "nickname": "认证流程用户",
                "email": "authreg@flow.test",
            },
        )
        assert r.status_code == 200

        r = await flow_client.post(
            "/api/system/login",
            json={"username": "flow_auth_reg", "password": "FlowAuthReg123!"},
        )
        assert r.status_code == 200
        refresh = r.json()["data"]["refreshToken"]

        r = await flow_client.post("/api/system/refresh-token", json={"refreshToken": refresh})
        assert r.status_code == 200
        assert r.json()["data"]["accessToken"]

    async def test_no_token_returns_401(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        r = await flow_client.get("/api/system/mine")
        assert r.status_code in (401, 403)

    async def test_get_async_routes(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        login = await flow_client.post(
            "/api/system/login",
            json={"username": flow_seed.super_username, "password": flow_seed.super_password},
        )
        h = {"Authorization": f"Bearer {login.json()['data']['accessToken']}"}

        r = await flow_client.get("/api/system/get-async-routes", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0
