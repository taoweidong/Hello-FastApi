"""认证全流程集成测试：登录、刷新、重新访问、登出。"""

import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


def _jwt_payload(token: str) -> dict:
    """不验签解析 JWT payload（仅测试使用）。"""
    segment = token.split(".")[1]
    padded = segment + "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def _assert_expires_utc_iso(data: dict) -> None:
    """断言 expires 是带时区偏移的 ISO 8601，且与 JWT 的 exp 声明一致。

    旧实现输出 strftime("%Y/%m/%d %H:%M:%S")：UTC 墙上时间但不带时区标识，
    前端 new Date() 按本地时区（UTC+8）解析会少算 8 小时 —— token 一登录
    就「已过期」，每个 API 请求都触发一次 refresh-token。
    """
    expires = data["expires"]
    parsed = datetime.fromisoformat(expires)
    assert parsed.tzinfo is not None, f"expires 缺少时区信息: {expires!r}"
    now = datetime.now(timezone.utc)
    assert now <= parsed <= now + timedelta(minutes=31), f"expires 超出合理区间: {expires!r}"
    jwt_exp = _jwt_payload(data["accessToken"])["exp"]
    assert abs(jwt_exp - parsed.timestamp()) <= 1, "expires 与 accessToken 的 exp 声明不一致"


@pytest.mark.integration
class TestAuthRefreshFlow:
    async def test_login_and_access_mine(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        r = await flow_client.post(
            "/api/system/login", json={"username": flow_seed.super_username, "password": flow_seed.super_password}
        )
        assert r.status_code == 200
        _assert_expires_utc_iso(r.json()["data"])
        token = r.json()["data"]["accessToken"]

        r = await flow_client.get("/api/system/mine", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["data"]["username"] == flow_seed.super_username

    async def test_refresh_token_extends_session(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        login = await flow_client.post(
            "/api/system/login", json={"username": flow_seed.super_username, "password": flow_seed.super_password}
        )
        assert login.status_code == 200
        refresh = login.json()["data"]["refreshToken"]

        r = await flow_client.post("/api/system/refresh-token", json={"refreshToken": refresh})
        assert r.status_code == 200
        _assert_expires_utc_iso(r.json()["data"])
        new_token = r.json()["data"]["accessToken"]
        assert new_token

        r = await flow_client.get("/api/system/mine", headers={"Authorization": f"Bearer {new_token}"})
        assert r.status_code == 200

    async def test_logout_invalidates_token(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        login = await flow_client.post(
            "/api/system/login", json={"username": flow_seed.super_username, "password": flow_seed.super_password}
        )
        token = login.json()["data"]["accessToken"]
        h = {"Authorization": f"Bearer {token}"}

        r = await flow_client.post("/api/system/logout", headers=h)
        assert r.status_code == 200

    async def test_wrong_password_rejected(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        r = await flow_client.post(
            "/api/system/login", json={"username": flow_seed.super_username, "password": "WrongPassword123!"}
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
            "/api/system/login", json={"username": "flow_auth_reg", "password": "FlowAuthReg123!"}
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
            "/api/system/login", json={"username": flow_seed.super_username, "password": flow_seed.super_password}
        )
        h = {"Authorization": f"Bearer {login.json()['data']['accessToken']}"}

        r = await flow_client.get("/api/system/get-async-routes", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0
