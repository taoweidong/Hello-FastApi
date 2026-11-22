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

    async def test_dept_status_toggle_reflected_in_list(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """状态切换：PUT /dept/{id}/status 禁用后列表反映 isActive=0（镜像 user status 流程）。"""
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/dept/create",
            headers=h,
            json={"name": "流程待停用部门", "rank": 4, "isActive": True, "code": "TOGGLE"},
        )
        assert r.status_code == 200
        dept_id = r.json()["data"]["id"]

        r = await flow_client.put(f"/api/system/dept/{dept_id}/status", headers=h, json={"isActive": False})
        assert r.status_code == 200
        assert r.json()["message"] == "状态更新成功"

        # 列表反映新状态：isActive=0 过滤能命中，isActive=1 过滤不再包含
        r = await flow_client.post("/api/system/dept", headers=h, json={"isActive": 0})
        assert dept_id in [d["id"] for d in r.json()["data"]]
        r = await flow_client.post("/api/system/dept", headers=h, json={"isActive": 1})
        assert dept_id not in [d["id"] for d in r.json()["data"]]

        # 重新启用
        r = await flow_client.put(f"/api/system/dept/{dept_id}/status", headers=h, json={"isActive": True})
        assert r.status_code == 200
        r = await flow_client.post("/api/system/dept", headers=h, json={"isActive": 1})
        assert dept_id in [d["id"] for d in r.json()["data"]]

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
