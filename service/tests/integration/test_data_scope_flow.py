"""角色 data_scope 数据权限过滤集成测试。

验证不同数据权限范围（全部/自定义/本部门/本部门及以下/仅本人）
对 /api/system/user 用户列表的过滤效果。
"""

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.enums import DataScope
from src.domain.services.password_service import PasswordService
from src.infrastructure.database.models import Department, Role, RoleDeptLink, RoleMenuLink, User, UserRole
from tests.integration.db_seed import FlowSeedData

OP_USERNAME = "scope_operator"
OP_PASSWORD = "ScopeOpPass123"


async def _login_headers(client: AsyncClient, username: str, password: str) -> dict[str, str]:
    r = await client.post("/api/system/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    token = r.json()["data"]["accessToken"]
    return {"Authorization": f"Bearer {token}"}


async def _setup_scope_env(
    session: AsyncSession, flow_seed: FlowSeedData, data_scope: DataScope, custom_dept_codes: tuple[str, ...] = ()
) -> dict[str, str]:
    """构建数据权限测试环境：部门树 + 各部门用户 + 指定 data_scope 的角色 + 操作人。

    Returns:
        部门 code → dept_id 映射
    """
    pwd = PasswordService.hash_password

    # 1. 部门树：总部（种子已有） → 分部；另设无隶属关系的兄弟部门
    child_dept = Department(name="流程分部", parent_id=flow_seed.dept_root_id, rank=1, is_active=True, code="SUB")
    other_dept = Department(name="流程兄弟部门", parent_id=None, rank=1, is_active=True, code="OTH")
    session.add(child_dept)
    session.add(other_dept)
    await session.flush()
    dept_ids = {"HQ": flow_seed.dept_root_id, "SUB": child_dept.id, "OTH": other_dept.id}

    # 2. 各部门用户
    def _make_user(username: str, dept_id: str, password: str = "ScopeUserPass123") -> User:
        return User(
            username=username,
            email=f"{username}@scope.test",
            password=pwd(password),
            nickname=username,
            is_active=True,
            dept_id=dept_id,
        )

    u_hq = _make_user("scope_u_hq", flow_seed.dept_root_id)
    u_child = _make_user("scope_u_child", child_dept.id)
    u_other = _make_user("scope_u_other", other_dept.id)
    operator = _make_user(OP_USERNAME, flow_seed.dept_root_id, password=OP_PASSWORD)
    for u in (u_hq, u_child, u_other, operator):
        session.add(u)
    await session.flush()

    # 3. 指定 data_scope 的角色（挂接 user:view 按钮权限菜单）
    role = Role(name="数据权限测试角色", code="scope_role", is_active=True, data_scope=int(data_scope))
    session.add(role)
    await session.flush()
    session.add(RoleMenuLink(userrole_id=role.id, menu_id=flow_seed.menu_perm_id))
    session.add(UserRole(userinfo_id=operator.id, userrole_id=role.id))

    # 4. 自定义数据权限：按 code 关联指定部门
    for code in custom_dept_codes:
        session.add(RoleDeptLink(role_id=role.id, dept_id=dept_ids[code]))

    await session.commit()
    return dept_ids


async def _list_usernames(client: AsyncClient, headers: dict[str, str]) -> set[str]:
    r = await client.post("/api/system/user", headers=headers, json={"pageNum": 1, "pageSize": 50})
    assert r.status_code == 200, r.text
    assert r.json()["code"] == 0
    return {item["username"] for item in r.json()["data"]["list"]}


@pytest.mark.integration
class TestDataScopeFlow:
    """data_scope 数据权限过滤全流程测试。"""

    async def test_scope_all_sees_everyone(
        self, flow_client: AsyncClient, flow_seed: FlowSeedData, db_session: AsyncSession
    ):
        """全部数据权限（ALL）：可见所有用户。"""
        await _setup_scope_env(db_session, flow_seed, DataScope.ALL)
        h = await _login_headers(flow_client, OP_USERNAME, OP_PASSWORD)
        usernames = await _list_usernames(flow_client, h)
        assert {
            flow_seed.super_username,
            flow_seed.operator_username,
            "scope_u_hq",
            "scope_u_child",
            "scope_u_other",
            OP_USERNAME,
        } == usernames

    async def test_scope_custom_sees_linked_depts(
        self, flow_client: AsyncClient, flow_seed: FlowSeedData, db_session: AsyncSession
    ):
        """自定义数据权限（CUSTOM）：仅可见角色关联部门的用户。"""
        await _setup_scope_env(db_session, flow_seed, DataScope.CUSTOM, custom_dept_codes=("SUB",))
        h = await _login_headers(flow_client, OP_USERNAME, OP_PASSWORD)
        usernames = await _list_usernames(flow_client, h)
        assert usernames == {"scope_u_child"}

    async def test_scope_dept_sees_own_dept(
        self, flow_client: AsyncClient, flow_seed: FlowSeedData, db_session: AsyncSession
    ):
        """本部门数据权限（DEPT）：仅可见本部门用户。"""
        await _setup_scope_env(db_session, flow_seed, DataScope.DEPT)
        h = await _login_headers(flow_client, OP_USERNAME, OP_PASSWORD)
        usernames = await _list_usernames(flow_client, h)
        assert usernames == {OP_USERNAME, "scope_u_hq"}

    async def test_scope_dept_and_child(
        self, flow_client: AsyncClient, flow_seed: FlowSeedData, db_session: AsyncSession
    ):
        """本部门及以下数据权限（DEPT_AND_CHILD）：可见本部门及子部门用户。"""
        await _setup_scope_env(db_session, flow_seed, DataScope.DEPT_AND_CHILD)
        h = await _login_headers(flow_client, OP_USERNAME, OP_PASSWORD)
        usernames = await _list_usernames(flow_client, h)
        assert usernames == {OP_USERNAME, "scope_u_hq", "scope_u_child"}

    async def test_scope_self_sees_only_self(
        self, flow_client: AsyncClient, flow_seed: FlowSeedData, db_session: AsyncSession
    ):
        """仅本人数据权限（SELF）：只能看到自己。"""
        await _setup_scope_env(db_session, flow_seed, DataScope.SELF)
        h = await _login_headers(flow_client, OP_USERNAME, OP_PASSWORD)
        usernames = await _list_usernames(flow_client, h)
        assert usernames == {OP_USERNAME}

    async def test_superuser_bypasses_scope(
        self, flow_client: AsyncClient, flow_seed: FlowSeedData, db_session: AsyncSession
    ):
        """超级管理员不受数据权限限制。"""
        await _setup_scope_env(db_session, flow_seed, DataScope.SELF)
        h = await _login_headers(flow_client, flow_seed.super_username, flow_seed.super_password)
        usernames = await _list_usernames(flow_client, h)
        assert len(usernames) == 6
