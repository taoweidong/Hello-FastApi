"""add sys post tables

新增岗位表（sys_post）与用户-岗位关联表（sys_user_post）。

Revision ID: a3b5c7d9e1f2
Revises: 9b2c4d5e6f78
Create Date: 2026-08-22 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a3b5c7d9e1f2'
down_revision: Union[str, None] = '9b2c4d5e6f78'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 幂等处理：检查表是否已存在
    from sqlalchemy import inspect
    bind = op.get_bind()
    insp = inspect(bind)
    existing_tables = insp.get_table_names()

    if 'sys_post' not in existing_tables:
        op.create_table(
            'sys_post',
            sa.Column('id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=False),
            sa.Column('post_code', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
            sa.Column('post_name', sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False),
            sa.Column('post_sort', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('is_active', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('remark', sqlmodel.sql.sqltypes.AutoString(length=256), nullable=False, server_default=''),
            sa.Column('creator_id', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
            sa.Column('modifier_id', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
            sa.Column('created_time', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.Column('updated_time', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_sys_post_post_code'), 'sys_post', ['post_code'], unique=False)

    if 'sys_user_post' not in existing_tables:
        op.create_table(
            'sys_user_post',
            sa.Column('id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=False),
            sa.Column('user_id', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False),
            sa.Column('post_id', sqlmodel.sql.sqltypes.AutoString(length=36), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['sys_users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['post_id'], ['sys_post.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index(op.f('ix_sys_user_post_user_id'), 'sys_user_post', ['user_id'], unique=False)
        op.create_index(op.f('ix_sys_user_post_post_id'), 'sys_user_post', ['post_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_sys_user_post_post_id'), table_name='sys_user_post')
    op.drop_index(op.f('ix_sys_user_post_user_id'), table_name='sys_user_post')
    op.drop_table('sys_user_post')
    op.drop_index(op.f('ix_sys_post_post_code'), table_name='sys_post')
    op.drop_table('sys_post')
