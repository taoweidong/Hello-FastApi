"""add sys_logs covering index for keyset pagination

Revision ID: c8d9e0f1a2b3
Revises: b8e2f4a6d0c1
Create Date: 2026-11-23 12:00:00.000000

为日志列表 keyset 深分页建覆盖索引（PostgreSQL 专属）：

    CREATE INDEX CONCURRENTLY ix_sys_logs_covering
        ON sys_logs (created_time DESC, id)
        INCLUDE (module, path, method, ipaddress, response_code, status_code, creator_id)

- (created_time DESC, id) 与列表稳定排序一致，游标条件
  ``(created_time, id) < (before_time, before_id)`` 可直接沿索引顺序扫描，
  深分页不再 offset 全扫；
- INCLUDE 列覆盖列表行渲染所需的全部列（body/response_result 大字段除外，
  列表响应已瘦身不再返回），实现 index-only scan。

SQLite 分支直接跳过：开发/测试库无 INCLUDE 语法且数据量小，
(created_time, id) 过滤退化为全表扫描可接受。downgrade 只删索引。
"""

from collections.abc import Sequence

from alembic import op
from loguru import logger

# revision identifiers, used by Alembic.
revision: str = "c8d9e0f1a2b3"
down_revision: str | None = "b8e2f4a6d0c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_INDEX_NAME = "ix_sys_logs_covering"
# INCLUDE 列与日志列表行渲染字段（_format_operation_log）对齐
_INCLUDE_COLUMNS = "module, path, method, ipaddress, response_code, status_code, creator_id"


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        # SQLite（开发/测试库）跳过：无 INCLUDE 子句且数据量小，
        # keyset 过滤退化为全表扫描可接受
        return

    try:
        # CONCURRENTLY 不锁表写入，但不能处于事务内——用 autocommit 块包裹；
        # IF NOT EXISTS 保证幂等（重复执行/部分失败重跑均安全）
        with op.get_context().autocommit_block():
            op.execute(
                f'CREATE INDEX CONCURRENTLY IF NOT EXISTS "{_INDEX_NAME}" '
                f"ON sys_logs (created_time DESC, id) INCLUDE ({_INCLUDE_COLUMNS})"
            )
    except Exception:
        # CONCURRENTLY 创建失败时退化为普通创建（短时间锁写，可接受）。
        # 失败可能残留 INVALID 索引占住名称，先清理再普通创建。
        logger.warning(f"CONCURRENTLY 创建覆盖索引失败，退化为普通创建: {_INDEX_NAME}", exc_info=True)
        with op.get_context().autocommit_block():
            op.execute(f'DROP INDEX IF EXISTS "{_INDEX_NAME}"')
        with op.get_context().autocommit_block():
            op.execute(
                f'CREATE INDEX IF NOT EXISTS "{_INDEX_NAME}" '
                f"ON sys_logs (created_time DESC, id) INCLUDE ({_INCLUDE_COLUMNS})"
            )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    try:
        with op.get_context().autocommit_block():
            op.execute(f'DROP INDEX CONCURRENTLY IF EXISTS "{_INDEX_NAME}"')
    except Exception:
        logger.warning(f"CONCURRENTLY 删除覆盖索引失败，退化为普通删除: {_INDEX_NAME}", exc_info=True)
        op.execute(f'DROP INDEX IF EXISTS "{_INDEX_NAME}"')
