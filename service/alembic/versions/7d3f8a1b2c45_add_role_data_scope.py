"""add role data scope

为角色增加数据权限范围字段（data_scope），并新增角色-部门关联表（sys_role_dept）
用于自定义数据权限的部门范围配置。

Revision ID: 7d3f8a1b2c45
Revises: 6cace61fd0c8
Create Date: 2026-08-19 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '7d3f8a1b2c45'
down_revision: Union[str, None] = '6cace61fd0c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 幂等处理：检查列与表是否已存在
    from sqlalchemy import inspect
    bind = op.get_bind()
    insp = inspect(bind)

    # 1. sys_roles 增加 data_scope 列（1全部/2自定义/3本部门/4本部门及以下/5仅本人）
    role_columns = {col['name'] for col in insp.get_columns('sys_roles')}
    if 'data_scope' not in role_columns:
        op.add_column('sys_roles', sa.Column('data_scope', sa.Integer(), nullable=False, server_default='1'))

    # 2. 创建角色-部门关联表（自定义数据权限）
    if 'sys_role_dept' not in insp.get_table_names():
        op.create_table(
            'sys_role_dept',
            sa.Column('id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=False),
            sa.Column('role_id', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False),
            sa.Column('dept_id', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False),
            sa.ForeignKeyConstraint(['dept_id'], ['sys_departments.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['role_id'], ['sys_roles.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_sys_role_dept_role_id'), 'sys_role_dept', ['role_id'], unique=False)
        op.create_index(op.f('ix_sys_role_dept_dept_id'), 'sys_role_dept', ['dept_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sys_role_dept_dept_id'), table_name='sys_role_dept')
    op.drop_index(op.f('ix_sys_role_dept_role_id'), table_name='sys_role_dept')
    op.drop_table('sys_role_dept')
    op.drop_column('sys_roles', 'data_scope')
