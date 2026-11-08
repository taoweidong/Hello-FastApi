"""add sys_example_data (Univer 表格 CRUD 示例表)

Revision ID: e8f9a0b1c2d3
Revises: d5e6f7a8b9c0
Create Date: 2026-11-08 09:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e8f9a0b1c2d3"
down_revision: str | None = "d5e6f7a8b9c0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 幂等处理：基线迁移（001_initial_schema）用 SQLModel.metadata.create_all
    # 创建全部已注册模型，本表可能已由基线建出——检查后再创建。
    from sqlalchemy import inspect

    bind = op.get_bind()
    insp = inspect(bind)

    if "sys_example_data" not in insp.get_table_names():
        op.create_table(
            "sys_example_data",
            sa.Column("id", sa.String(length=32), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("category", sa.String(length=64), nullable=True),
            sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("price", sa.Float(), nullable=False, server_default="0"),
            sa.Column("record_date", sa.Date(), nullable=True),
            sa.Column("note", sa.String(length=512), nullable=True),
            sa.Column("is_active", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("creator_id", sa.String(length=32), nullable=True),
            sa.Column("modifier_id", sa.String(length=32), nullable=True),
            sa.Column("created_time", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.Column("updated_time", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_sys_example_data_name", "sys_example_data", ["name"])


def downgrade() -> None:
    # 幂等：表不存在时跳过
    from sqlalchemy import inspect

    insp = inspect(op.get_bind())
    if "sys_example_data" in insp.get_table_names():
        op.drop_index("ix_sys_example_data_name", table_name="sys_example_data")
        op.drop_table("sys_example_data")
