"""菜单树全流程集成测试：创建、更新、删除、树形查询。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestMenuTreeFlow:
    async def test_create_directory_menu(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/menu/create",
            headers=h,
            json={
                "name": "flow_dir",
                "menuType": 0,
                "rank": 10,
                "path": "/flow-dir",
                "isActive": True,
                "meta": {"title": "流程目录", "isShowMenu": True, "isKeepalive": False},
            },
        )
        assert r.status_code == 200
        assert r.json()["code"] == 201

    async def test_create_page_menu_with_parent(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/menu/create",
            headers=h,
            json={
                "name": "flow_parent",
                "menuType": 0,
                "rank": 11,
                "path": "/flow-parent",
                "isActive": True,
                "meta": {"title": "父菜单", "isShowMenu": True},
            },
        )
        parent_id = r.json()["data"]["id"]

        r = await flow_client.post(
            "/api/system/menu/create",
            headers=h,
            json={
                "name": "flow_child",
                "menuType": 1,
                "rank": 12,
                "path": "/flow-child",
                "component": "flow/child/index",
                "parentId": parent_id,
                "isActive": True,
                "meta": {"title": "子菜单", "isShowMenu": True, "isKeepalive": True},
            },
        )
        assert r.status_code == 200
        assert r.json()["code"] == 201

    async def test_update_menu(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/menu/create",
            headers=h,
            json={
                "name": "flow_upd_menu",
                "menuType": 1,
                "rank": 20,
                "path": "/flow-upd",
                "component": "flow/upd/index",
                "isActive": True,
                "meta": {"title": "待更新菜单", "isShowMenu": True},
            },
        )
        mid = r.json()["data"]["id"]

        r = await flow_client.put(
            f"/api/system/menu/{mid}", headers=h, json={"rank": 99, "meta": {"title": "已更新菜单"}}
        )
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_delete_menu(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/menu/create",
            headers=h,
            json={
                "name": "flow_del_menu",
                "menuType": 1,
                "rank": 30,
                "path": "/flow-del",
                "component": "flow/del/index",
                "isActive": True,
                "meta": {"title": "待删菜单", "isShowMenu": True},
            },
        )
        mid = r.json()["data"]["id"]

        r = await flow_client.delete(f"/api/system/menu/{mid}", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_get_menu_tree_contains_seed(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.get("/api/system/menu/tree", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0

    async def test_get_user_menus(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.get("/api/system/menu/user-menus", headers=h)
        assert r.status_code == 200
        assert r.json()["code"] == 0
