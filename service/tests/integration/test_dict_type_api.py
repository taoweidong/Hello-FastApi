"""字典类型公开取数接口集成测试。

验证 GET /api/system/dictionary/type/{dict_name}：
- 仅需登录即可访问（无需 dictionary:view 按钮权限）
- 只返回启用状态的子项，按 sort 升序
- 未登录返回 401
- 字典类型不存在返回空列表
- 写操作后取数结果实时反映最新数据
"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


async def _create_dict(client: AsyncClient, headers: dict[str, str], payload: dict) -> str:
    """创建字典节点并返回其 ID。"""
    r = await client.post("/api/system/dictionary/create", headers=headers, json=payload)
    assert r.status_code == 200, r.text
    return r.json()["data"]["id"]


@pytest.mark.integration
class TestDictTypeApi:
    async def test_get_dict_items_returns_active_sorted(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """返回启用状态的子项且按 sort 升序。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        root_id = await _create_dict(
            flow_client, super_h, {"name": "sys_notice_type", "label": "通知类型", "value": "", "isActive": 1}
        )
        await _create_dict(
            flow_client,
            super_h,
            {
                "name": "sys_notice_type_warn",
                "label": "警告",
                "value": "2",
                "parentId": root_id,
                "sort": 2,
                "isActive": 1,
            },
        )
        await _create_dict(
            flow_client,
            super_h,
            {
                "name": "sys_notice_type_info",
                "label": "通知",
                "value": "1",
                "parentId": root_id,
                "sort": 1,
                "isActive": 1,
            },
        )
        await _create_dict(
            flow_client,
            super_h,
            {
                "name": "sys_notice_type_off",
                "label": "停用项",
                "value": "9",
                "parentId": root_id,
                "sort": 3,
                "isActive": 0,
            },
        )

        r = await flow_client.get("/api/system/dictionary/type/sys_notice_type", headers=super_h)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data == [{"label": "通知", "value": "1"}, {"label": "警告", "value": "2"}]

    async def test_regular_user_without_dict_permission_can_access(
        self, flow_client: AsyncClient, flow_seed: FlowSeedData
    ):
        """无字典权限的普通登录用户也能访问公开取数接口。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        root_id = await _create_dict(
            flow_client, super_h, {"name": "sys_post_level", "label": "岗位职级", "value": "", "isActive": 1}
        )
        await _create_dict(
            flow_client,
            super_h,
            {"name": "sys_post_level_p1", "label": "初级", "value": "1", "parentId": root_id, "isActive": 1},
        )

        # operator 仅有 user:view 权限，无任何字典权限
        op_h = await _login_headers(flow_client, flow_seed.operator_username, flow_seed.operator_password)
        r = await flow_client.get("/api/system/dictionary/type/sys_post_level", headers=op_h)
        assert r.status_code == 200
        assert r.json()["data"] == [{"label": "初级", "value": "1"}]

    async def test_requires_login(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """未登录访问返回 401。"""
        r = await flow_client.get("/api/system/dictionary/type/sys_any")
        assert r.status_code == 401

    async def test_unknown_type_returns_empty(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """字典类型不存在时返回空列表。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.get("/api/system/dictionary/type/not_exist_type", headers=super_h)
        assert r.status_code == 200
        assert r.json()["data"] == []

    async def test_write_reflected_in_next_fetch(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """写操作后再次取数应反映最新数据（缓存失效链路正常）。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        root_id = await _create_dict(
            flow_client, super_h, {"name": "sys_cache_check", "label": "缓存校验", "value": "", "isActive": 1}
        )
        child_id = await _create_dict(
            flow_client,
            super_h,
            {"name": "sys_cache_check_a", "label": "原标签", "value": "a", "parentId": root_id, "isActive": 1},
        )

        # 首次取数
        r = await flow_client.get("/api/system/dictionary/type/sys_cache_check", headers=super_h)
        assert r.json()["data"] == [{"label": "原标签", "value": "a"}]

        # 更新子项标签后再次取数
        r = await flow_client.put(f"/api/system/dictionary/{child_id}", headers=super_h, json={"label": "新标签"})
        assert r.status_code == 200

        r = await flow_client.get("/api/system/dictionary/type/sys_cache_check", headers=super_h)
        assert r.json()["data"] == [{"label": "新标签", "value": "a"}]
