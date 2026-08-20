"""add login log username column

登录日志表（sys_userloginlog）新增 username 列，记录登录时的用户名，
供登录日志列表展示与个人安全日志（/mine-logs）按用户名过滤。

Revision ID: c4d5e6f7a8b9
Revises: a3b5c7d9e1f2
Create Date: 2026-08-23 10:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, None] = "a3b5c7d9e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 幂等处理：检查列是否已存在
    from sqlalchemy import inspect

    bind = op.get_bind()
    insp = inspect(bind)

    if "sys_userloginlog" in insp.get_table_names():
        columns = {col["name"] for col in insp.get_columns("sys_userloginlog")}
        if "username" not in columns:
            op.add_column(
                "sys_userloginlog",
                sa.Column("username", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=True),
            )


def downgrade() -> None:
    # 幂等处理：检查列是否存在后才删除
    from sqlalchemy import inspect

    bind = op.get_bind()
    insp = inspect(bind)
    columns = {col["name"] for col in insp.get_columns("sys_userloginlog")}
    if "username" in columns:
        op.drop_column("sys_userloginlog", "username")