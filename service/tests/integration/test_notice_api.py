"""通知公告接口集成测试。

验证 /api/system/notice 全链路：
- 创建时自动记录发布人信息
- 列表分页与标题模糊/类型/状态筛选
- 详情 404、更新、删除、批量删除
- /latest 仅需登录且只返回启用公告
- 权限控制：未登录 401、无 notice:view 权限 403
"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


async def _create_notice(client: AsyncClient, headers: dict[str, str], payload: dict) -> str:
    """创建公告并返回其 ID。"""
    r = await client.post("/api/system/notice/create", headers=headers, json=payload)
    assert r.status_code == 200, r.text
    return r.json()["data"]["id"]


@pytest.mark.integration
class TestNoticeApi:
    async def test_create_notice_records_publisher(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """创建公告时自动记录发布人ID与名称。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/notice/create",
            headers=super_h,
            json={"title": "系统维护通知", "content": "今晚停机维护", "noticeType": 1, "isActive": 1},
        )
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        assert data["title"] == "系统维护通知"
        assert data["publisherId"] == flow_seed.super_user_id
        assert data["publisherName"]  # 发布人名称非空
        assert data["creatorId"] == flow_seed.super_user_id

    async def test_list_with_filters(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """列表支持标题模糊匹配与类型/状态筛选。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        await _create_notice(flow_client, super_h, {"title": "版本发布说明", "noticeType": 2})
        await _create_notice(flow_client, super_h, {"title": "放假安排通知", "noticeType": 1})
        await _create_notice(flow_client, super_h, {"title": "已关闭的通知", "isActive": 0})

        # 标题模糊匹配
        r = await flow_client.post("/api/system/notice", headers=super_h, json={"title": "通知"})
        assert r.status_code == 200
        body = r.json()["data"]
        assert body["total"] == 2

        # 类型筛选
        r = await flow_client.post("/api/system/notice", headers=super_h, json={"noticeType": 2})
        assert r.json()["data"]["total"] == 1

        # 状态筛选
        r = await flow_client.post("/api/system/notice", headers=super_h, json={"isActive": 0})
        assert r.json()["data"]["total"] == 1

    async def test_get_detail_and_not_found(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """详情查询正常返回，不存在的 ID 返回 404。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        notice_id = await _create_notice(flow_client, super_h, {"title": "详情测试"})

        r = await flow_client.get(f"/api/system/notice/{notice_id}", headers=super_h)
        assert r.status_code == 200
        assert r.json()["data"]["title"] == "详情测试"

        r = await flow_client.get("/api/system/notice/not-exist-id", headers=super_h)
        assert r.status_code == 404

    async def test_update_and_delete(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """更新记录修改人，删除后详情返回 404。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        notice_id = await _create_notice(flow_client, super_h, {"title": "原标题"})

        r = await flow_client.put(
            f"/api/system/notice/{notice_id}", headers=super_h, json={"title": "新标题", "isActive": 0}
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["title"] == "新标题"
        assert data["isActive"] == 0
        assert data["modifierId"] == flow_seed.super_user_id

        r = await flow_client.delete(f"/api/system/notice/{notice_id}", headers=super_h)
        assert r.status_code == 200

        r = await flow_client.get(f"/api/system/notice/{notice_id}", headers=super_h)
        assert r.status_code == 404

    async def test_batch_delete(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """批量删除返回实际删除数量。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        id1 = await _create_notice(flow_client, super_h, {"title": "批量一"})
        id2 = await _create_notice(flow_client, super_h, {"title": "批量二"})

        r = await flow_client.post(
            "/api/system/notice/batch-delete", headers=super_h, json={"ids": [id1, id2, "not-exist"]}
        )
        assert r.status_code == 200
        assert r.json()["data"] == {"deleted_count": 2, "total_requested": 3}

    async def test_latest_only_login_required_and_active(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """/latest 仅需登录（无 notice:view 也可），且只返回启用公告。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        await _create_notice(flow_client, super_h, {"title": "启用公告"})
        await _create_notice(flow_client, super_h, {"title": "关闭公告", "isActive": 0})

        # operator 仅有 user:view 权限，无 notice:view
        op_h = await _login_headers(flow_client, flow_seed.operator_username, flow_seed.operator_password)
        r = await flow_client.get("/api/system/notice/latest", headers=op_h)
        assert r.status_code == 200
        titles = [n["title"] for n in r.json()["data"]]
        assert "启用公告" in titles
        assert "关闭公告" not in titles

    async def test_requires_login(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """未登录访问返回 401。"""
        r = await flow_client.post("/api/system/notice", json={})
        assert r.status_code == 401
        r = await flow_client.get("/api/system/notice/latest")
        assert r.status_code == 401

    async def test_permission_denied_without_notice_view(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """无 notice:view 权限的用户访问列表返回 403。"""
        op_h = await _login_headers(flow_client, flow_seed.operator_username, flow_seed.operator_password)
        r = await flow_client.post("/api/system/notice", headers=op_h, json={})
        assert r.status_code == 403
