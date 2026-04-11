"""API 真实流程集成测试：不使用 Mock，依赖内存 SQLite + 清空库表 + 种子数据 + HTTP 全链路。"""

import pytest
from httpx import AsyncClient

from tests.integration.db_seed import FlowSeedData


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["code"] == 0
    token = body["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.integration
class TestAuthRealFlow:
    async def test_login_refresh_logout_mine(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.get("/api/system/mine", headers=h)
        assert r.status_code == 200
        assert r.json()["data"]["username"] == flow_seed.super_username

        r = await flow_client.post("/api/system/logout", headers=h)
        assert r.status_code == 200

        login = await flow_client.post("/api/system/login", json={"username": flow_seed.super_username, "password": flow_seed.super_password})
        refresh = login.json()["data"]["refreshToken"]
        r = await flow_client.post("/api/system/refresh-token", json={"refreshToken": refresh})
        assert r.status_code == 200
        assert r.json()["data"]["accessToken"]

    async def test_register_then_login(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        r = await flow_client.post("/api/system/register", json={"username": "flow_registered", "password": "RegPass123!", "nickname": "注册用户", "email": "reg@flow.test"})
        assert r.status_code == 200
        assert r.json()["data"]["username"] == "flow_registered"

        r = await flow_client.post("/api/system/login", json={"username": "flow_registered", "password": "RegPass123!"})
        assert r.status_code == 200


@pytest.mark.integration
class TestRbacRealFlow:
    async def test_operator_can_list_and_create_user_cannot_delete(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h_super = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        r = await flow_client.post("/api/system/user/create", headers=h_super, json={"username": "victim_user", "password": "VictimPass123!", "nickname": "待删", "email": "victim@flow.test", "status": 1})
        assert r.status_code == 201
        victim_id = r.json()["data"]["id"]

        h_op = await _login_headers(flow_client, flow_seed.operator_username, flow_seed.operator_password)
        r = await flow_client.post("/api/system/user", headers=h_op, json={"pageNum": 1, "pageSize": 10})
        assert r.status_code == 200
        assert r.json()["code"] == 0

        r = await flow_client.delete(f"/api/system/user/{victim_id}", headers=h_op)
        assert r.status_code == 403

        r = await flow_client.delete(f"/api/system/user/{victim_id}", headers=h_super)
        assert r.status_code == 200


@pytest.mark.integration
class TestUserManagementRealFlow:
    async def test_user_crud_and_change_password(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/user/create", headers=h, json={"username": "crud_user", "password": "CrudPass123!", "nickname": "CRUD", "email": "crud@flow.test", "status": 1})
        assert r.status_code == 201
        uid = r.json()["data"]["id"]

        r = await flow_client.get(f"/api/system/user/{uid}", headers=h)
        assert r.status_code == 200
        assert r.json()["data"]["username"] == "crud_user"

        r = await flow_client.put(f"/api/system/user/{uid}", headers=h, json={"nickname": "已更新", "remark": "备注"})
        assert r.status_code == 200
        assert r.json()["data"]["nickname"] == "已更新"

        h_user = await _login_headers(flow_client, "crud_user", "CrudPass123!")
        r = await flow_client.post("/api/system/user/change-password", headers=h_user, json={"oldPassword": "CrudPass123!", "newPassword": "NewCrudPass123!"})
        assert r.status_code == 200

        r = await flow_client.post("/api/system/login", json={"username": "crud_user", "password": "NewCrudPass123!"})
        assert r.status_code == 200

        r = await flow_client.put(f"/api/system/user/{uid}/status", headers=h, json={"status": 0})
        assert r.status_code == 200

        h2 = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        r = await flow_client.delete(f"/api/system/user/{uid}", headers=h2)
        assert r.status_code == 200


@pytest.mark.integration
class TestRolePermissionMenuRealFlow:
    async def test_role_permission_menu_dept_aux(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/role/create", headers=h, json={"name": "流程新角色", "code": "flow_new_role", "status": 1, "permissionIds": []})
        assert r.status_code == 200
        rid = r.json()["data"]["id"]

        r = await flow_client.get(f"/api/system/role/{rid}", headers=h)
        assert r.status_code == 200

        pid = flow_seed.perm_by_code["role:view"]
        r = await flow_client.post(f"/api/system/role/{rid}/permissions", headers=h, json={"permissionIds": [pid]})
        assert r.status_code == 200

        r = await flow_client.get("/api/system/permission/list", headers=h, params={"pageNum": 1, "pageSize": 5})
        assert r.status_code == 200
        assert r.json()["data"]["total"] >= 1

        r = await flow_client.post("/api/system/menu/create", headers=h, json={"title": "接口建菜单", "menuType": 0, "rank": 1, "path": "/flow-menu"})
        assert r.status_code == 200
        mid = r.json()["data"]["id"]

        r = await flow_client.post(f"/api/system/role/{rid}/menu", headers=h, json={"menuIds": [mid, flow_seed.menu_root_id]})
        assert r.status_code == 200

        r = await flow_client.post("/api/system/dept/create", headers=h, json={"name": "接口部门", "sort": 1, "status": 1})
        assert r.status_code == 200

        r = await flow_client.get("/api/system/list-all-role", headers=h)
        assert r.status_code == 200
        assert len(r.json()["data"]) >= 2

        r = await flow_client.post("/api/system/list-role-ids", headers=h, json={"userId": flow_seed.operator_user_id})
        assert r.status_code == 200
        assert flow_seed.role_ops_id in r.json()["data"]

        r = await flow_client.post("/api/system/role-menu", headers=h)
        assert r.status_code == 200
        r = await flow_client.post("/api/system/role-menu-ids", headers=h, json={"id": flow_seed.role_admin_id})
        assert r.status_code == 200
        assert flow_seed.menu_root_id in r.json()["data"]


@pytest.mark.integration
class TestSystemLogsRealFlow:
    async def test_log_endpoints_read_and_mutate(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)

        r = await flow_client.post("/api/system/login-logs", headers=h, json={"pageNum": 1, "pageSize": 10})
        assert r.status_code == 200
        assert r.json()["data"]["total"] >= 1

        r = await flow_client.post("/api/system/operation-logs", headers=h, json={"pageNum": 1, "pageSize": 10})
        assert r.status_code == 200

        r = await flow_client.post("/api/system/system-logs", headers=h, json={"pageNum": 1, "pageSize": 10})
        assert r.status_code == 200

        r = await flow_client.post("/api/system/system-logs-detail", headers=h, json={"id": flow_seed.system_log_id})
        assert r.status_code == 200

        r = await flow_client.post("/api/system/login-logs/batch-delete", headers=h, json={"ids": [flow_seed.login_log_id]})
        assert r.status_code == 200

        r = await flow_client.post("/api/system/dept", headers=h, json={})
        assert r.status_code == 200
        assert any(d["name"] == "流程总部" for d in r.json()["data"])


@pytest.mark.integration
class TestStubRoutesRealFlow:
    async def test_stub_routes_with_auth(self, flow_client: AsyncClient, flow_seed: FlowSeedData):
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        for method, path, kw in (("GET", "/api/system/get-async-routes", {}), ("GET", "/api/system/mine-logs", {}), ("GET", "/api/system/get-map-info", {}), ("POST", "/api/system/online-logs", {"json": {}}), ("POST", "/api/system/get-card-list", {"json": {}})):
            if method == "GET":
                r = await flow_client.get(path, headers=h)
            else:
                r = await flow_client.post(path, headers=h, **kw)
            assert r.status_code == 200, (path, r.text)
            assert r.json()["code"] == 0
