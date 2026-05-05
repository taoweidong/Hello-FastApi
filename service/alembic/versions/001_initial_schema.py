"""initial_schema

Revision ID: 001
Revises:
Create Date: 2026-04-30
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    from sqlmodel import SQLModel

    import src.infrastructure.database.models  # noqa: F401

    bind = op.get_bind()
    SQLModel.metadata.create_all(bind)


def downgrade() -> None:
    op.drop_table("sys_userrole_menu")
    op.drop_table("sys_userinfo_roles")
    op.drop_table("sys_userloginlog")
    op.drop_table("sys_logs")
    op.drop_table("sys_ip_rules")
    op.drop_table("sys_roles")
    op.drop_table("sys_menus")
    op.drop_table("sys_menumeta")
    op.drop_table("sys_departments")
    op.drop_table("sys_dictionary")
    op.drop_table("sys_systemconfig")
    op.drop_table("sys_users")
