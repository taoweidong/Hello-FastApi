"""add pg_trgm fuzzy search indexes

Revision ID: b8e2f4a6d0c1
Revises: f3a7c9e1b5d2
Create Date: 2026-11-22 12:00:00.000000

为模糊搜索（ILIKE '%v%'）建 pg_trgm GIN 索引（PostgreSQL 专属）：
- sys_logs.module（操作日志按模块筛选）
- sys_users.username / sys_users.phone（用户搜索升级为包含匹配后，
  B-tree 索引对非前缀 LIKE 失效，trgm GIN 保证 LIKE/ILIKE 走索引）

SQLite 分支直接跳过：开发/测试环境数据量小，LIKE 全表扫描可接受，
且 SQLite 无 pg_trgm 扩展概念。downgrade 只删索引，不卸载扩展
（扩展可能被其他对象依赖，卸载属破坏性操作）。
"""

from collections.abc import Sequence

from alembic import op
from loguru import logger
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "b8e2f4a6d0c1"
down_revision: str | None = "f3a7c9e1b5d2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (索引名, 表名, 列)
_TRGM_INDEXES: list[tuple[str, str, str]] = [
    ("ix_sys_logs_module_trgm", "sys_logs", "module"),
    ("ix_sys_users_username_trgm", "sys_users", "username"),
    ("ix_sys_users_phone_trgm", "sys_users", "phone"),
]


def _create_trgm_index(name: str, table: str, column: str, concurrently: bool) -> None:
    """创建 trgm GIN 索引；concurrently=True 时必须处于 autocommit 块中。"""
    op.create_index(
        name,
        table,
        [column],
        unique=False,
        postgresql_using="gin",
        postgresql_ops={column: "gin_trgm_ops"},
        postgresql_concurrently=concurrently,
    )


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # SQLite（开发/测试库）跳过：数据量小，LIKE 全扫可接受，无 pg_trgm 扩展
        return

    # 使用先查后建避免重复创建（模仿 f3a7c9e1b5d2 的幂等写法）
    insp = inspect(bind)
    existing_indexes = {idx["name"] for tbl in insp.get_table_names() for idx in insp.get_indexes(tbl)}

    # 扩展创建不能回滚，放入 autocommit 块（幂等：已存在则跳过）
    with op.get_context().autocommit_block():
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    for name, table, column in _TRGM_INDEXES:
        if name in existing_indexes:
            continue
        try:
            # CONCURRENTLY 不锁表写入，但不能处于事务内——用 autocommit 块包裹
            with op.get_context().autocommit_block():
                _create_trgm_index(name, table, column, concurrently=True)
        except Exception:
            # CONCURRENTLY 创建失败时退化为普通创建（短时间锁写，可接受）。
            # 失败可能残留 INVALID 索引占住名称，先清理再普通创建。
            logger.warning(f"CONCURRENTLY 创建 trgm 索引失败，退化为普通创建: {name}", exc_info=True)
            with op.get_context().autocommit_block():
                op.execute(f'DROP INDEX IF EXISTS "{name}"')
            _create_trgm_index(name, table, column, concurrently=False)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for name, table, _column in reversed(_TRGM_INDEXES):
        try:
            with op.get_context().autocommit_block():
                op.drop_index(name, table_name=table, postgresql_concurrently=True)
        except Exception:
            logger.warning(f"CONCURRENTLY 删除 trgm 索引失败，退化为普通删除: {name}", exc_info=True)
            op.drop_index(name, table_name=table)

    # 不卸载 pg_trgm 扩展：可能被其他对象依赖，卸载属破坏性操作
