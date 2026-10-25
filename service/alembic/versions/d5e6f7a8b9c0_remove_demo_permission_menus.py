"""remove demo permission menus

移除「权限管理」演示目录及其子菜单/按钮权限码（7 条），这些是 pure-admin
模板的演示菜单，业务不使用。同步清理 sys_userrole_menu 关联与 sys_menumeta
元数据，避免残留孤立记录。

删除项（sys_menus.name）：
  目录：Permission
  页面：PermissionPage / PermissionButton / PermissionPerms
  权限码：permission:btn:add / permission:btn:edit / permission:btn:delete

说明：
- sys_userrole_menu.menu_id 虽带 ON DELETE CASCADE，但 Alembic 迁移连接未必
  启用 PRAGMA foreign_keys，故显式删除关联行，保证幂等与跨环境一致。
- sys_menus.parent_id 自引用外键：先删子项，再删父目录，避免自引用约束报错。
- sys_menumeta 不被级联删除，需按被删菜单的 meta_id 显式清理。
- 幂等：重复执行不报错。downgrade 为 no-op —— 数据删除不可逆，如需恢复请重跑
  `python -m scripts.cli seedrbac`（种子按 name 幂等重建）。

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-10-25 20:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5e6f7a8b9c0"
down_revision: str | None = "c4d5e6f7a8b9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# 待删除的演示菜单 name（子项先删，父目录后删）
CHILD_NAMES = [
    "permission:btn:add",
    "permission:btn:edit",
    "permission:btn:delete",
    "PermissionPerms",
    "PermissionButton",
    "PermissionPage",
]
PARENT_NAMES = ["Permission"]
ALL_NAMES = CHILD_NAMES + PARENT_NAMES


def upgrade() -> None:
    bind = op.get_bind()
    from sqlalchemy import inspect

    insp = inspect(bind)
    tables = set(insp.get_table_names())
    if "sys_menus" not in tables:
        return

    # 1. 收集待删菜单 id 与 meta_id
    placeholders = ", ".join(f":n{i}" for i in range(len(ALL_NAMES)))
    params = {f"n{i}": name for i, name in enumerate(ALL_NAMES)}
    rows = bind.execute(
        sa.text(f"SELECT id, meta_id FROM sys_menus WHERE name IN ({placeholders})"), params
    ).fetchall()
    if not rows:
        return  # 已清理过，幂等退出

    menu_ids = [r[0] for r in rows]
    meta_ids = [r[1] for r in rows if r[1]]

    menu_id_ph = ", ".join(f":m{i}" for i in range(len(menu_ids)))
    menu_id_params = {f"m{i}": v for i, v in enumerate(menu_ids)}

    # 2. 删除角色-菜单关联（显式，不依赖级联）
    if "sys_userrole_menu" in tables:
        bind.execute(
            sa.text(f"DELETE FROM sys_userrole_menu WHERE menu_id IN ({menu_id_ph})"),
            menu_id_params,
        )

    # 3. 先删子项，再删父目录（规避 parent_id 自引用外键）
    for names in (CHILD_NAMES, PARENT_NAMES):
        ph = ", ".join(f":c{i}" for i in range(len(names)))
        bind.execute(
            sa.text(f"DELETE FROM sys_menus WHERE name IN ({ph})"),
            {f"c{i}": v for i, v in enumerate(names)},
        )

    # 4. 清理孤立 sys_menumeta
    if meta_ids and "sys_menumeta" in tables:
        m_ph = ", ".join(f":k{i}" for i in range(len(meta_ids)))
        bind.execute(
            sa.text(f"DELETE FROM sys_menumeta WHERE id IN ({m_ph})"),
            {f"k{i}": v for i, v in enumerate(meta_ids)},
        )


def downgrade() -> None:
    # 数据删除不可逆：恢复请重跑 `python -m scripts.cli seedrbac`（幂等重建）
    pass
