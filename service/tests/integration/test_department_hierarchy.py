"""部门层级关系全流程集成测试。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestDepartmentHierarchy:
    async def test_create_root_dept(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/dept/create",
            headers=h,
            json={"name": "流程技术部", "rank": 1, "isActive": True, "code": "TECH"},
        )
        assert r.status_code == 200
        assert r.json()["code"] == 201

    async def test_create_child_dept(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/dept/create",
            headers=h,
            json={"name": "流程研发部", "parentId": flow_seed.dept_root_id, "rank": 2, "isActive": True, "code": "RD"},
        )
        assert r.status_code == 200
        child_id = r.json()["data"]["id"]
        assert child_id

        r = await flow_client.get("/api/system/dept/tree", headers=h)
        assert r.status_code == 200
        tree = r.json()["data"]
        assert len(tree) >= 1

    async def test_update_dept(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/dept/create",
            headers=h,
            json={"name": "流程待更新部门", "rank": 3, "isActive": True, "code": "UPD"},
        )
        dept_id = r.json()["data"]["id"]

        r = await flow_client.put(f"/api/system/dept/{dept_id}", headers=h, json={"name": "已更新部门"})
        assert r.status_code == 200
        assert r.json()["data"]["name"] == "已更新部门"

    async def test_delete_dept(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/dept/create",
            headers=h,
            json={"name": "流程待删除部门", "rank": 99, "isActive": True, "code": "DEL_DEPT"},
        )
        dept_id = r.json()["data"]["id"]

        r = await flow_client.delete(f"/api/system/dept/{dept_id}", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_dept_list_contains_seed(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/dept", headers=h, json={})
        assert r.status_code == 200
        names = [d["name"] for d in r.json()["data"]]
        assert "流程总部" in names

    async def test_dept_tree_query(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.get("/api/system/dept/tree", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0
