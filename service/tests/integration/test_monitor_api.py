"""服务器监控 / 缓存监控接口集成测试。

验证 /api/system/server-info 与 /api/system/cache-info：
- 超管访问成功且结构完整
- 测试环境禁用 Redis 时缓存监控降级返回（connected=False）而非报错
- 未登录 401、无 monitor:view 权限 403
"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestMonitorApi:
    async def test_server_info_success(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """超管获取服务器监控数据结构完整。"""
        headers = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        r = await flow_client.get("/api/system/server-info", headers=headers)
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        for key in ("cpu", "memory", "disk", "system", "process"):
            assert key in data
        assert data["cpu"]["coreCount"] >= 1
        assert data["system"]["pythonVersion"]
        assert data["process"]["pid"] > 0

    async def test_cache_info_degraded_without_redis(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """测试环境禁用 Redis，缓存监控应降级返回而非报错。"""
        headers = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        r = await flow_client.get("/api/system/cache-info", headers=headers)
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        assert data["connected"] is False
        assert data["message"]

    async def test_server_info_requires_auth(self, flow_client: AsyncClient):
        """未登录访问返回 401。"""
        r = await flow_client.get("/api/system/server-info")
        assert r.status_code == 401
        r = await flow_client.get("/api/system/cache-info")
        assert r.status_code == 401

    async def test_server_info_forbidden_without_permission(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """operator 仅持 user:view，无 monitor:view 权限应返回 403。"""
        op_h = await _login_headers(flow_client, flow_seed.operator_username, flow_seed.operator_password)
        r = await flow_client.get("/api/system/server-info", headers=op_h)
        assert r.status_code == 403
        r = await flow_client.get("/api/system/cache-info", headers=op_h)
        assert r.status_code == 403
