"""岗位管理接口集成测试。

验证 /api/system/post 全链路：
- 岗位 CRUD（编码唯一 409、创建/修改人记录、404）
- 列表分页与编码/名称模糊/状态筛选
- 批量删除、/options 仅需登录且只返回启用岗位
- /user/{user_id} 需 user:view 权限
- 用户创建/更新携带 postIds 时联动用户-岗位关联表
- 权限控制：未登录 401、无 post:view 权限 403
"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


async def _create_post(client: AsyncClient, headers: dict[str, str], payload: dict) -> str:
    """创建岗位并返回其 ID。"""
    r = await client.post("/api/system/post/create", headers=headers, json=payload)
    assert r.status_code == 200, r.text
    return r.json()["data"]["id"]


@pytest.mark.integration
class TestPostApi:
    async def test_create_post_records_creator(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """创建岗位时自动记录创建人ID。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/post/create", headers=super_h, json={"postCode": "ceo", "postName": "董事长", "postSort": 1}
        )
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        assert data["postCode"] == "ceo"
        assert data["postName"] == "董事长"
        assert data["isActive"] == 1
        assert data["creatorId"] == flow_seed.super_user_id

    async def test_create_post_duplicate_code_conflict(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """重复岗位编码创建返回 409。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        await _create_post(flow_client, super_h, {"postCode": "dev", "postName": "工程师"})

        r = await flow_client.post(
            "/api/system/post/create", headers=super_h, json={"postCode": "dev", "postName": "重复岗位"}
        )
        assert r.status_code == 409

    async def test_list_with_filters(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """列表支持编码/名称模糊匹配与状态筛选。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        await _create_post(flow_client, super_h, {"postCode": "ceo", "postName": "董事长", "postSort": 1})
        await _create_post(flow_client, super_h, {"postCode": "dev", "postName": "工程师", "postSort": 2})
        await _create_post(flow_client, super_h, {"postCode": "hr", "postName": "人事专员", "isActive": 0})

        # 名称模糊匹配
        r = await flow_client.post("/api/system/post", headers=super_h, json={"postName": "工"})
        assert r.json()["data"]["total"] == 1

        # 状态筛选
        r = await flow_client.post("/api/system/post", headers=super_h, json={"isActive": 0})
        assert r.json()["data"]["total"] == 1

        # 编码模糊匹配
        r = await flow_client.post("/api/system/post", headers=super_h, json={"postCode": "ce"})
        assert r.json()["data"]["total"] == 1

    async def test_get_detail_and_not_found(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """详情查询正常返回，不存在的 ID 返回 404。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        post_id = await _create_post(flow_client, super_h, {"postCode": "pm", "postName": "项目经理"})

        r = await flow_client.get(f"/api/system/post/{post_id}", headers=super_h)
        assert r.status_code == 200
        assert r.json()["data"]["postName"] == "项目经理"

        r = await flow_client.get("/api/system/post/not-exist-id", headers=super_h)
        assert r.status_code == 404

    async def test_update_and_delete(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """更新记录修改人，删除后详情返回 404。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        post_id = await _create_post(flow_client, super_h, {"postCode": "qa", "postName": "测试员"})

        r = await flow_client.put(
            f"/api/system/post/{post_id}", headers=super_h, json={"postName": "高级测试员", "isActive": 0}
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["postName"] == "高级测试员"
        assert data["isActive"] == 0
        assert data["modifierId"] == flow_seed.super_user_id

        r = await flow_client.delete(f"/api/system/post/{post_id}", headers=super_h)
        assert r.status_code == 200

        r = await flow_client.get(f"/api/system/post/{post_id}", headers=super_h)
        assert r.status_code == 404

    async def test_batch_delete(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """批量删除返回实际删除数量。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        id1 = await _create_post(flow_client, super_h, {"postCode": "p1", "postName": "岗位一"})
        id2 = await _create_post(flow_client, super_h, {"postCode": "p2", "postName": "岗位二"})

        r = await flow_client.post(
            "/api/system/post/batch-delete", headers=super_h, json={"ids": [id1, id2, "not-exist"]}
        )
        assert r.status_code == 200
        assert r.json()["data"] == {"deleted_count": 2, "total_requested": 3}

    async def test_options_only_login_required_and_active(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """/options 仅需登录（无 post:view 也可），且只返回启用岗位。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        await _create_post(flow_client, super_h, {"postCode": "on1", "postName": "启用岗位"})
        await _create_post(flow_client, super_h, {"postCode": "off1", "postName": "停用岗位", "isActive": 0})

        # operator 仅有 user:view 权限，无 post:view
        op_h = await _login_headers(flow_client, flow_seed.operator_username, flow_seed.operator_password)
        r = await flow_client.get("/api/system/post/options", headers=op_h)
        assert r.status_code == 200
        names = [o["postName"] for o in r.json()["data"]]
        assert "启用岗位" in names
        assert "停用岗位" not in names

    async def test_user_post_assignment_via_user_api(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """用户创建/更新携带 postIds 时联动维护用户-岗位关联。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        post_a = await _create_post(flow_client, super_h, {"postCode": "ua", "postName": "岗位甲"})
        post_b = await _create_post(flow_client, super_h, {"postCode": "ub", "postName": "岗位乙"})

        # 创建用户时分配岗位
        r = await flow_client.post(
            "/api/system/user/create",
            headers=super_h,
            json={"username": "post_user", "password": "PostUser@123", "postIds": [post_a, post_b]},
        )
        assert r.status_code == 201, r.text
        user_id = r.json()["data"]["id"]

        r = await flow_client.get(f"/api/system/post/user/{user_id}", headers=super_h)
        assert r.status_code == 200
        assert sorted(r.json()["data"]) == sorted([post_a, post_b])

        # 更新用户岗位（清空场景：传空列表）
        r = await flow_client.put(f"/api/system/user/{user_id}", headers=super_h, json={"postIds": [post_a]})
        assert r.status_code == 200, r.text
        r = await flow_client.get(f"/api/system/post/user/{user_id}", headers=super_h)
        assert r.json()["data"] == [post_a]

        r = await flow_client.put(f"/api/system/user/{user_id}", headers=super_h, json={"postIds": []})
        assert r.status_code == 200, r.text
        r = await flow_client.get(f"/api/system/post/user/{user_id}", headers=super_h)
        assert r.json()["data"] == []

    async def test_delete_post_removes_user_links(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """删除岗位时同步清理用户-岗位关联。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        post_id = await _create_post(flow_client, super_h, {"postCode": "lk", "postName": "关联岗位"})

        r = await flow_client.post(
            "/api/system/user/create",
            headers=super_h,
            json={"username": "post_link_user", "password": "PostLink@123", "postIds": [post_id]},
        )
        assert r.status_code == 201, r.text
        user_id = r.json()["data"]["id"]

        r = await flow_client.delete(f"/api/system/post/{post_id}", headers=super_h)
        assert r.status_code == 200

        # 用户的岗位关联已被清理
        r = await flow_client.get(f"/api/system/post/user/{user_id}", headers=super_h)
        assert r.json()["data"] == []

    async def test_requires_login(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """未登录访问返回 401。"""
        r = await flow_client.post("/api/system/post", json={})
        assert r.status_code == 401
        r = await flow_client.get("/api/system/post/options")
        assert r.status_code == 401

    async def test_permission_denied_without_post_view(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """无 post:view 权限的用户访问列表返回 403。"""
        op_h = await _login_headers(flow_client, flow_seed.operator_username, flow_seed.operator_password)
        r = await flow_client.post("/api/system/post", headers=op_h, json={})
        assert r.status_code == 403
