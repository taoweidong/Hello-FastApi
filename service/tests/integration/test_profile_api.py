"""个人中心接口集成测试。

验证：
- PUT /api/system/user/profile 自助更新个人资料（不含管理字段）
- POST /api/system/user/avatar 头像上传（格式/大小校验、静态资源可访问）
- 未登录访问 401
"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData

# 最小可识别的 PNG 文件头 + 占位内容
_FAKE_PNG = b"\x89PNG\r\n\x1a\n" + b"avatar-test-content"


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestProfileApi:
    async def test_update_own_profile(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """自助更新昵称/邮箱/电话/简介后 /mine 返回新值。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.put(
            "/api/system/user/profile",
            headers=super_h,
            json={"nickname": "新昵称", "email": "self@example.com", "phone": "13800001111", "description": "个人简介"},
        )
        assert r.status_code == 200, r.text

        r = await flow_client.get("/api/system/mine", headers=super_h)
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["nickname"] == "新昵称"
        assert data["email"] == "self@example.com"
        assert data["phone"] == "13800001111"
        assert data["description"] == "个人简介"

    async def test_update_profile_ignores_admin_fields(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """自助更新不能修改 isActive 等管理字段。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.put("/api/system/user/profile", headers=super_h, json={"isActive": 0})
        assert r.status_code == 200
        assert r.json()["data"]["isActive"] == 1

    async def test_avatar_upload_and_static_access(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """上传头像返回 /media URL，静态资源可直接访问，/mine 头像已更新。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/user/avatar", headers=super_h, files={"file": ("avatar.png", _FAKE_PNG, "image/png")}
        )
        assert r.status_code == 200, r.text
        avatar_url = r.json()["data"]["avatar"]
        assert avatar_url.startswith("/media/avatars/")
        assert avatar_url.endswith(".png")

        # 静态资源可匿名访问
        r = await flow_client.get(avatar_url)
        assert r.status_code == 200
        assert r.content == _FAKE_PNG

        # /mine 返回新头像
        r = await flow_client.get("/api/system/mine", headers=super_h)
        assert r.json()["data"]["avatar"] == avatar_url

    async def test_avatar_upload_invalid_extension(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """非图片格式上传返回 422。"""
        super_h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post(
            "/api/system/user/avatar", headers=super_h, files={"file": ("evil.txt", b"not-an-image", "text/plain")}
        )
        assert r.status_code == 422

    async def test_profile_and_avatar_require_login(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        """未登录访问返回 401。"""
        r = await flow_client.put("/api/system/user/profile", json={"nickname": "x"})
        assert r.status_code == 401
        r = await flow_client.post("/api/system/user/avatar", files={"file": ("avatar.png", _FAKE_PNG, "image/png")})
        assert r.status_code == 401
