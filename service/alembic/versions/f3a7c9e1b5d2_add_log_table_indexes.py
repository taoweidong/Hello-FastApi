"""add log table indexes

Revision ID: f3a7c9e1b5d2
Revises: e8f9a0b1c2d3
Create Date: 2026-11-22 10:00:00.000000

为两张日志表补查询索引。复合索引设计依据 PG18 B-tree skip scan：
低基数前导列（状态/创建人）+ 时间排序，可同时服务
「按状态筛选 + 按时间倒序分页」与「纯时间倒序分页」两类查询。
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "f3a7c9e1b5d2"
down_revision: str | None = "e8f9a0b1c2d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (索引名, 表名, 列)
_LOG_INDEXES: list[tuple[str, str, list[str]]] = [
    ("ix_sys_userloginlog_created_time", "sys_userloginlog", ["created_time"]),
    ("ix_sys_userloginlog_username_created_time", "sys_userloginlog", ["username", "created_time"]),
    ("ix_sys_logs_status_code_created_time", "sys_logs", ["status_code", "created_time"]),
    ("ix_sys_logs_creator_id_created_time", "sys_logs", ["creator_id", "created_time"]),
]

# append-heavy 日志表的 PG 表级 autovacuum 参数：
# - 降低 vacuum/analyze 触发阈值（日志表只有插入与删除，死元组比例高）；
# - fillfactor=100：日志行插入后不再更新，页无需预留更新空间。
_AUTOVACUUM_DDL = (
    "ALTER TABLE sys_userloginlog SET (autovacuum_vacuum_scale_factor=0.02, "
    "autovacuum_analyze_scale_factor=0.01, fillfactor=100)",
    "ALTER TABLE sys_logs SET (autovacuum_vacuum_scale_factor=0.02, "
    "autovacuum_analyze_scale_factor=0.01, fillfactor=100)",
)


def upgrade() -> None:
    # 使用 IF NOT EXISTS 语义（先查现有索引）避免重复创建，模仿 6cace61fd0c8 的幂等写法
    bind = op.get_bind()
    insp = inspect(bind)
    existing_indexes = {idx["name"] for tbl in insp.get_table_names() for idx in insp.get_indexes(tbl)}
    is_postgresql = bind.dialect.name == "postgresql"

    for name, table, columns in _LOG_INDEXES:
        if name in existing_indexes:
            continue
        if is_postgresql:
            # CONCURRENTLY 不锁表写入，但不能再处于事务内——用 autocommit block 包裹
            with op.get_context().autocommit_block():
                op.create_index(name, table, columns, unique=False, postgresql_concurrently=True)
        else:
            op.create_index(name, table, columns, unique=False)

    # PG 专属：append-heavy 日志表的 autovacuum 调优（SQLite 无此概念）
    if is_postgresql:
        with op.get_context().autocommit_block():
            for ddl in _AUTOVACUUM_DDL:
                op.execute(ddl)


def downgrade() -> None:
    bind = op.get_bind()
    is_postgresql = bind.dialect.name == "postgresql"

    if is_postgresql:
        with op.get_context().autocommit_block():
            for table in ("sys_userloginlog", "sys_logs"):
                op.execute(
                    f"ALTER TABLE {table} RESET (autovacuum_vacuum_scale_factor, "
                    "autovacuum_analyze_scale_factor, fillfactor)"
                )

    for name, table, _columns in reversed(_LOG_INDEXES):
        if is_postgresql:
            with op.get_context().autocommit_block():
                op.drop_index(name, table_name=table, postgresql_concurrently=True)
        else:
            op.drop_index(name, table_name=table)
