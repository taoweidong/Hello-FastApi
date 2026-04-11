"""集成测试：清空库表并按业务顺序写入模拟数据（真实 ORM / 会话，无 Mock）。"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.constants import DEFAULT_PERMISSIONS
from src.domain.services.password_service import PasswordService
from src.infrastructure.database.models import (
    Department,
    LoginLog,
    Menu,
    OperationLog,
    Permission,
    Role,
    RoleMenuLink,
    RolePermissionLink,
    SystemLog,
    User,
    UserRole,
)


# 测试库为 SQLite，关闭外键检查后清空，避免自引用表顺序问题
async def clear_all_test_data(session: AsyncSession) -> None:
    """删除当前库中所有业务数据（测试库专用）。"""
    await session.execute(text("PRAGMA foreign_keys=OFF"))
    for table in (
        "sys_role_menus",
        "sys_role_permissions",
        "sys_user_roles",
        "sys_login_logs",
        "sys_operation_logs",
        "sys_system_logs",
        "sys_menus",
        "sys_users",
        "sys_roles",
        "sys_permissions",
        "sys_departments",
        "sys_ip_rules",
    ):
        await session.execute(text(f"DELETE FROM {table}"))
    await session.execute(text("PRAGMA foreign_keys=ON"))
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
    perm_by_code: dict[str, str] = field(default_factory=dict)
    menu_root_id: str = ""
    dept_root_id: str = ""
    login_log_id: str = ""
    operation_log_id: str = ""
    system_log_id: str = ""


async def insert_flow_seed_data(session: AsyncSession) -> FlowSeedData:
    """按依赖顺序插入权限 → 角色 → 关联 → 用户 → 菜单/部门/日志。"""
    out = FlowSeedData()
    pwd = PasswordService.hash_password

    perms: list[Permission] = []
    for p in DEFAULT_PERMISSIONS:
        perm = Permission(name=p["name"], code=p["code"], resource=p.get("resource"), action=p.get("action"), status=1)
        session.add(perm)
        perms.append(perm)
    await session.flush()
    for perm in perms:
        out.perm_by_code[perm.code] = perm.id

    role_admin = Role(name="流程测试管理员", code="admin", description="全权限", status=1)
    role_ops = Role(name="流程测试用户专员", code="flow_user_ops", description="仅用户部分权限", status=1)
    session.add(role_admin)
    session.add(role_ops)
    await session.flush()
    out.role_admin_id = role_admin.id
    out.role_ops_id = role_ops.id

    for perm in perms:
        session.add(RolePermissionLink(role_id=role_admin.id, permission_id=perm.id))
    for code in ("user:view", "user:add", "user:edit"):
        session.add(RolePermissionLink(role_id=role_ops.id, permission_id=out.perm_by_code[code]))
    await session.flush()

    user_super = User(
        username=out.super_username,
        email="flow_super@seed.test",
        hashed_password=pwd(out.super_password),
        nickname="流程超级管理员",
        status=1,
        is_superuser=True,
    )
    user_op = User(
        username=out.operator_username,
        email="flow_operator@seed.test",
        hashed_password=pwd(out.operator_password),
        nickname="流程受限用户",
        status=1,
        is_superuser=False,
    )
    session.add(user_super)
    session.add(user_op)
    await session.flush()
    out.super_user_id = user_super.id
    out.operator_user_id = user_op.id

    session.add(UserRole(user_id=user_op.id, role_id=role_ops.id))
    await session.flush()

    menu = Menu(name="流程根菜单", title="流程根菜单", path="/flow-root", status=1, order_num=0)
    session.add(menu)
    await session.flush()
    out.menu_root_id = menu.id

    session.add(RoleMenuLink(role_id=role_admin.id, menu_id=menu.id))
    dept = Department(name="流程总部", parent_id=None, sort=0, status=1)
    session.add(dept)
    await session.flush()
    out.dept_root_id = dept.id

    ll = LoginLog(username=out.super_username, ip="127.0.0.1", status=1, behavior="seed")
    ol = OperationLog(username=out.super_username, ip="127.0.0.1", status=1, summary="seed", module="test")
    sl = SystemLog(level="INFO", module="test", url="/seed", method="GET", ip="127.0.0.1", takes_time=1.0)
    session.add(ll)
    session.add(ol)
    session.add(sl)
    await session.flush()
    out.login_log_id = ll.id
    out.operation_log_id = ol.id
    out.system_log_id = sl.id

    return out


async def reset_db_and_seed(session: AsyncSession) -> FlowSeedData:
    """测试流程入口：先清空再写入种子数据。"""
    await clear_all_test_data(session)
    return await insert_flow_seed_data(session)
