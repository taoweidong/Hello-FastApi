"""add sys notice table

新增通知公告表（sys_notice），支持通知公告的发布、编辑、关闭与删除。

Revision ID: 9b2c4d5e6f78
Revises: 7d3f8a1b2c45
Create Date: 2026-08-21 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "9b2c4d5e6f78"
down_revision: Union[str, None] = "7d3f8a1b2c45"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 幂等处理：检查表是否已存在
    from sqlalchemy import inspect

    bind = op.get_bind()
    insp = inspect(bind)

    if "sys_notice" not in insp.get_table_names():
        op.create_table(
            "sys_notice",
            sa.Column("id", sqlmodel.sql.sqltypes.AutoString(length=36), nullable=False),
            sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
            sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default=""),
            sa.Column("notice_type", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("publisher_id", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
            sa.Column("publisher_name", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False, server_default=""),
            sa.Column("creator_id", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
            sa.Column("modifier_id", sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
            sa.Column("created_time", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column("updated_time", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_sys_notice_notice_type"), "sys_notice", ["notice_type"], unique=False)
        op.create_index(op.f("ix_sys_notice_is_active"), "sys_notice", ["is_active"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sys_notice_is_active"), table_name="sys_notice")
    op.drop_index(op.f("ix_sys_notice_notice_type"), table_name="sys_notice")
    op.drop_table("sys_notice")
