"""集成测试：清空库表并按业务顺序写入模拟数据（真实 ORM / 会话，无 Mock）。"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.services.password_service import PasswordService
from src.infrastructure.database.models import (
    Department,
    LoginLog,
    Menu,
    MenuMeta,
    Role,
    RoleMenuLink,
    SystemLog,
    User,
    UserRole,
)


# 测试库为 SQLite，关闭外键检查后清空，避免自引用表顺序问题
async def clear_all_test_data(session: AsyncSession) -> None:
    """删除当前库中所有业务数据（测试库专用）。"""
    await session.exec(text("PRAGMA foreign_keys=OFF"))  # type: ignore[arg-type]
    for table in (
        "sys_userrole_menu",
        "sys_userinfo_roles",
        "sys_userloginlog",
        "sys_logs",
        "sys_menus",
        "sys_menumeta",
        "sys_users",
        "sys_roles",
        "sys_departments",
        "sys_ip_rules",
        "sys_systemconfig",
    ):
        await session.exec(text(f"DELETE FROM {table}"))  # type: ignore[arg-type]
    await session.exec(text("PRAGMA foreign_keys=ON"))  # type: ignore[arg-type]
    await session.commit()


@dataclass
class FlowSeedData:
    """种子数据句柄，供用例断言与链式调用接口。"""

    super_username: str = "flow_super"
    super_password: str = "FlowSuperPass123"
    super_user_id: str = ""
    operator_username: str = "flow_operator"
    operator_password: str = "FlowOperatorPass123"
    operator_user_id: str = ""
    role_admin_id: str = ""
    role_ops_id: str = ""
    menu_root_id: str = ""
    menu_perm_id: str = ""
    dept_root_id: str = ""
    login_log_id: str = ""
    system_log_id: str = ""


async def insert_flow_seed_data(session: AsyncSession) -> FlowSeedData:
    """按依赖顺序插入角色 → 关联 → 用户 → 菜单/部门/日志。"""
    out = FlowSeedData()
    pwd = PasswordService.hash_password

    # 1. 角色
    role_admin = Role(name="流程测试管理员", code="admin", description="全权限", is_active=True)
    role_ops = Role(name="流程测试用户专员", code="flow_user_ops", description="仅用户部分权限", is_active=True)
    session.add(role_admin)
    session.add(role_ops)
    await session.flush()
    out.role_admin_id = role_admin.id
    out.role_ops_id = role_ops.id

    # 2. 用户
    user_super = User(
        username=out.super_username,
        email="flow_super@seed.test",
        password=pwd(out.super_password),
        nickname="流程超级管理员",
        is_active=True,
        is_superuser=True,
    )
    user_op = User(
        username=out.operator_username,
        email="flow_operator@seed.test",
        password=pwd(out.operator_password),
        nickname="流程受限用户",
        is_active=True,
        is_superuser=False,
    )
    session.add(user_super)
    session.add(user_op)
    await session.flush()
    out.super_user_id = user_super.id
    out.operator_user_id = user_op.id

    # 3. 用户-角色关联
    session.add(UserRole(userinfo_id=user_op.id, userrole_id=role_ops.id))
    await session.flush()

    # 4. 菜单元数据 + 菜单
    menu_meta = MenuMeta(title="流程根菜单", icon="menu", is_show_menu=True, is_keepalive=True)
    session.add(menu_meta)
    await session.flush()

    menu = Menu(name="flow_root", menu_type=0, path="/flow-root", rank=0, is_active=True, meta_id=menu_meta.id)
    session.add(menu)
    await session.flush()
    out.menu_root_id = menu.id

    # 5. PERMISSION类型菜单（按钮权限）
    perm_meta = MenuMeta(title="用户查看", is_show_menu=False, is_keepalive=False)
    session.add(perm_meta)
    await session.flush()

    menu_perm = Menu(name="user:view", menu_type=2, method="GET",         path="/api/system/user",
        is_active=True,
        parent_id=menu.id,
        meta_id=perm_meta.id,
    )
    session.add(menu_perm)
    await session.flush()
    out.menu_perm_id = menu_perm.id

    # 6. 角色-菜单关联
    session.add(RoleMenuLink(userrole_id=role_admin.id, menu_id=menu.id))
    session.add(RoleMenuLink(userrole_id=role_admin.id, menu_id=menu_perm.id))
    session.add(RoleMenuLink(userrole_id=role_ops.id, menu_id=menu_perm.id))
    await session.flush()

    # 7. 部门
    dept = Department(name="流程总部", parent_id=None, rank=0, is_active=True, code="HQ")
    session.add(dept)
    await session.flush()
    out.dept_root_id = dept.id

    # 8. 日志
    ll = LoginLog(status=1, ipaddress="127.0.0.1", browser="test", system="test", agent="seed", login_type=0)
    sl = SystemLog(module="test", path="/seed", method="GET", ipaddress="127.0.0.1")
    session.add(ll)
    session.add(sl)
    await session.flush()
    out.login_log_id = ll.id
    out.system_log_id = sl.id

    return out


async def reset_db_and_seed(session: AsyncSession) -> FlowSeedData:
    """测试流程入口：先清空再写入种子数据。"""
    await clear_all_test_data(session)
    return await insert_flow_seed_data(session)
